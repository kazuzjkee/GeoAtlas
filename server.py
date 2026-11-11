from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import zipfile
import tempfile
import shutil
import asyncio
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
import random
import time
import os
import json
import secrets
import csv
import io
import re
import collections
import hashlib
import db

db.init_db()

_rate_limit_store = collections.defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 3

def check_rate_limit(key: str) -> bool:
    now = time.time()
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[key]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[key].append(now)
    return True

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

logger = logging.getLogger("geoatlas")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="GeoAtlas — Учебно-картографический атлас ЮФУ (Ростов, Краснодар, Россия)")
security = HTTPBasic()
security_optional = HTTPBasic(auto_error=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, "public", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)
app.mount("/public", StaticFiles(directory=os.path.join(BASE_DIR, "public")), name="public")

ALLOWED_ORIGINS = [orig.strip() for orig in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if orig.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        path = request.url.path
        if path.startswith("/api/") and not path.startswith("/api/auth/") \
           and not path.startswith("/api/results/") and not path.startswith("/api/duel/"):
            origin = request.headers.get("origin", "")
            referer = request.headers.get("referer", "")
            host = request.headers.get("host", "")
            if origin and host not in origin:
                return JSONResponse({"detail": "CSRF protection: origin mismatch"}, status_code=403)
            if not origin and referer and host not in referer:
                return JSONResponse({"detail": "CSRF protection: referer mismatch"}, status_code=403)
    return await call_next(request)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

AUTH_SESSIONS_FILE = "auth_sessions.json"
RESULTS_FILE = "quiz_results.json"
GROUPS_FILE = "groups.json"
ACTIVE_SESSION_FILE = "active_session.json"
TEACHERS_FILE = "teachers.json"
SESSIONS_HISTORY_FILE = "sessions_history.json"
BRANDING_FILE = "branding.json"

DEFAULT_BRANDING = {
    "org_name": "Институт наук о Земле ЮФУ",
    "org_short": "ЮФУ",
    "brand_title": "GeoAtlas",
    "brand_tag": "SFEDU GIS",
    "sub_title": "Электронная ведомость проверочных работ, контрольных срезов и мониторинг успеваемости",
    "logo_emoji": "🎓",
    "logo_url": "",
    "allowed_email_domain": "@sfedu.ru",
    "primary_color": "#2563EB",
    "primary_hover": "#1D4ED8",
    "secondary_color": "#0284C7",
    "accent_color": "#7C3AED",
    "footer_text": "Институт наук о Земле ЮФУ • Кафедра физической географии, экологии и охраны природы"
}

def load_branding() -> Dict[str, Any]:
    res = DEFAULT_BRANDING.copy()
    if os.path.exists(BRANDING_FILE):
        try:
            with open(BRANDING_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res.update(data)
        except Exception:
            pass
    
    # Обеспечиваем взаимную совместимость синонимов
    if "org_short" in res and "university_short" not in res:
        res["university_short"] = res["org_short"]
    elif "university_short" in res and "org_short" not in res:
        res["org_short"] = res["university_short"]

    if "org_name" in res and "university_name" not in res:
        res["university_name"] = res["org_name"]
    elif "university_name" in res and "org_name" not in res:
        res["org_name"] = res["university_name"]

    if "brand_title" in res and "portal_title" not in res:
        res["portal_title"] = res["brand_title"]
    elif "portal_title" in res and "brand_title" not in res:
        res["brand_title"] = res["portal_title"]

    return res

def save_branding(data: Dict[str, Any]) -> None:
    current = load_branding()
    current.update(data)
    try:
        with open(BRANDING_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения branding.json: %s", e)

def load_auth_sessions() -> Dict[str, Any]:
    return {}

def save_auth_sessions(sessions: Dict[str, Any]) -> None:
    pass

DEFAULT_TEACHERS = [
    {
        "teacher_id": "teacher-ivanov",
        "username": "prof_ivanov",
        "password": "ivanov_pass_2026",
        "full_name": "Проф. Иванов И. И.",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Кафедра физической географии",
        "role": "teacher"
    },
    {
        "teacher_id": "teacher-petrov",
        "username": "prof_petrov",
        "password": "petrov_pass_2026",
        "full_name": "Доц. Петров П. П.",
        "organization": "Экономический факультет ЮФУ",
        "department": "Кафедра экономической географии",
        "role": "teacher"
    },
    {
        "teacher_id": "dean-geo",
        "username": "dean_geo",
        "password": "dean_pass_2026",
        "full_name": "Декан наук о Земле ЮФУ",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Деканат геолого-географического факультета",
        "role": "dean"
    },
    {
        "teacher_id": "teacher-admin",
        "username": "admin",
        "password": "admin",
        "full_name": "Главный администратор",
        "organization": "Южный федеральный университет",
        "department": "Центр цифровых образовательных технологий",
        "role": "dean"
    },
    {
        "teacher_id": "teacher-ivanov",
        "username": "prof_geo",
        "password": "geo_password_2026",
        "full_name": "Проф. Смирнов А. В.",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Кафедра физической географии",
        "role": "teacher"
    },
    {
        "teacher_id": "teacher-petrov",
        "username": "prof_eco",
        "password": "eco_password_2026",
        "full_name": "Доц. Кузнецова М. И.",
        "organization": "Экономический факультет ЮФУ",
        "department": "Кафедра экономической географии",
        "role": "teacher"
    },
    {
        "teacher_id": "dean-geo",
        "username": "sfedu_admin",
        "password": "geodean2026",
        "full_name": "Деканат наук о Земле",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Деканат",
        "role": "dean"
    }
]

def is_dean_or_admin(teacher: Dict[str, Any]) -> bool:
    return (
        teacher.get("role") in ["dean", "admin"]
        or teacher.get("username") in ["dean_geo", "admin", "sfedu_admin"]
        or teacher.get("teacher_id") in ["dean-geo", "teacher-admin"]
    )

def load_teachers() -> List[Dict[str, Any]]:
    data = None
    if os.path.exists(TEACHERS_FILE):
        try:
            with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) > 0:
                    data = loaded
        except Exception:
            pass
    if data is None:
        data = [dict(t) for t in DEFAULT_TEACHERS]
        save_teachers(data)

    migrated = False
    for t in data:
        if "password_hash" not in t and "password" in t:
            t["password_hash"] = _hash_pw(t["password"])
            del t["password"]
            migrated = True
    if migrated:
        save_teachers(data)
    return data

def save_teachers(teachers: List[Dict[str, Any]]) -> None:
    try:
        with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
            json.dump(teachers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения teachers: %s", e)

def load_sessions_history() -> List[Dict[str, Any]]:
    return db.load_sessions_history()

def record_session_history(session_data: Dict[str, Any]) -> None:
    db.record_session_history(session_data)

DEFAULT_GROUPS = [
    {
        "id": "grp-geofak-51",
        "name": "Геофак-51 (ВКР)",
        "description": "5 курс, профиль: География и Экономика (ВКР)",
        "students": [
            {"name": "Литвинов Е. К.", "email": "elitvinov@sfedu.ru"},
            {"name": "Иванов И. И.", "email": "ivanov@sfedu.ru"},
            {"name": "Сидорова М. В.", "email": "sidorova@sfedu.ru"}
        ],
        "created_at": "26.10.2026 10:00"
    },
    {
        "id": "grp-econom-31",
        "name": "Эконом-31 (ЮФО)",
        "description": "3 курс, экономический анализ и ВРП",
        "students": [
            {"name": "Петров А. С.", "email": "petrov@sfedu.ru"}
        ],
        "created_at": "26.10.2026 10:00"
    },
    {
        "id": "grp-geofak-41",
        "name": "Геофак-41 (Бакалавриат)",
        "description": "4 курс, картография и ГИС",
        "students": [
            {"name": "Ковалев Д. В.", "email": "kovalev@sfedu.ru"},
            {"name": "Смирнова А. А.", "email": "smirnova@sfedu.ru"}
        ],
        "created_at": "26.10.2026 10:00"
    }
]

class AuthRequest(BaseModel):
    email: str
    full_name: str
    group_num: str

class VerifyRequest(BaseModel):
    email: str
    code: str

class ResultSubmit(BaseModel):
    email: str
    name: str
    group: str
    quiz_type: str
    score: int
    max_score: int
    accuracy: int
    time_spent: str
    is_exam: bool = False
    exam_token: str = ""
    violations: int = 0
    exam_status: str = "Сдано"
    session_id: str = ""
    mistakes_log: list = []
    teacher_id: str = "teacher-ivanov"
    submission_id: str = ""
    client_timestamp: Optional[int] = None

class SyncBatchRequest(BaseModel):
    items: List[ResultSubmit]

class DuelCreateRequest(BaseModel):
    mode: str = "center"  # "center" or "puzzle"
    region: str = "rostov"  # "rostov", "krasnodar", "russia"
    host_name: str = "Студент"
    host_group: str = ""
    host_email: str = ""

class DuelJoinRequest(BaseModel):
    room_id: str
    player_name: str = "Студент"
    player_group: str = ""
    player_email: str = ""

class DuelActionRequest(BaseModel):
    player_id: str
    action: str
    payload: Dict[str, Any] = {}

class StudentItem(BaseModel):
    name: str
    email: str

class GroupModel(BaseModel):
    id: str
    name: str
    description: str = ""
    students: list[StudentItem] = []
    created_at: str = ""
    teacher_id: str = "teacher-ivanov"

class LaunchSessionRequest(BaseModel):
    groupId: str
    groupName: str
    mapUrl: str
    regionName: str
    quizType: str
    quizTypeName: str
    questionCount: int = 15
    timeLimitMinutes: int = 10
    teacher_id: str = "teacher-ivanov"

def load_results() -> List[Dict[str, Any]]:
    return db.load_results()

def save_result_to_file(result_data: Dict[str, Any]) -> Dict[str, Any]:
    return db.save_result(result_data)

def load_groups() -> List[Dict[str, Any]]:
    groups = db.load_groups()
    if not groups:
        for g in DEFAULT_GROUPS:
            db.save_group(g)
        groups = db.load_groups()
    return groups

def save_groups_to_file(groups_data: List[Dict[str, Any]]) -> None:
    for g in groups_data:
        db.save_group(g)

def load_active_session() -> Optional[Dict[str, Any]]:
    if os.path.exists(ACTIVE_SESSION_FILE):
        try:
            with open(ACTIVE_SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_active_session(session_data: Optional[Dict[str, Any]]) -> None:
    with open(ACTIVE_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

def check_admin(credentials: HTTPBasicCredentials = Depends(security)) -> Dict[str, Any]:
    teachers = load_teachers()
    for t in teachers:
        stored = t.get("password", "")
        stored_hash = t.get("password_hash", "")
        candidate_ok = (
            (stored_hash and secrets.compare_digest(_hash_pw(credentials.password), stored_hash))
            or (not stored_hash and secrets.compare_digest(credentials.password, stored))
        )
        if secrets.compare_digest(credentials.username, t.get("username", "")) and candidate_ok:
            return t
    raise HTTPException(status_code=401, detail="Неверный логин или пароль", 
                        headers={"WWW-Authenticate": "Basic"})

def check_admin_optional(credentials: Optional[HTTPBasicCredentials] = Depends(security_optional)) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    teachers = load_teachers()
    for t in teachers:
        stored = t.get("password", "")
        stored_hash = t.get("password_hash", "")
        candidate_ok = (
            (stored_hash and secrets.compare_digest(_hash_pw(credentials.password), stored_hash))
            or (not stored_hash and secrets.compare_digest(credentials.password, stored))
        )
        if secrets.compare_digest(credentials.username, t.get("username", "")) and candidate_ok:
            return t
    return None

@app.post("/api/auth/send-code")
def send_code(req: AuthRequest, request: Request) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"send:{client_ip}") or not check_rate_limit(f"send:{req.email.lower()}"):
        raise HTTPException(status_code=429, detail="Слишком много запросов. Подождите минуту.")
    email = req.email.strip().lower()
    branding = load_branding()
    allowed_domain = (branding.get("allowed_email_domain") or "").strip().lower()
    if allowed_domain:
        domain_suffix = allowed_domain if allowed_domain.startswith("@") else f"@{allowed_domain}"
        domain_bare = domain_suffix.lstrip("@")
        if not (email.endswith(domain_suffix) or email.endswith(f".{domain_bare}")):
            raise HTTPException(
                status_code=400,
                detail=f"Разрешена авторизация только по корпоративной почте учебного заведения ({domain_suffix})"
            )
    
    code = f"{random.randint(100000, 999999)}"
    db.save_auth_session(email, {
        "code": code,
        "expires_at": time.time() + 600,
        "name": req.full_name.strip(),
        "group": req.group_num.strip()
    })
    db.cleanup_expired_auth()
    logger.info("Авторизация: сгенерирован код подтверждения для %s", email)
    return {"status": "ok", "message": "Код подтверждения отправлен", "dev_code": code}

@app.post("/api/auth/verify-code")
def verify_code(req: VerifyRequest, request: Request) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"verify:{client_ip}"):
        raise HTTPException(status_code=429, detail="Слишком много попыток ввода кода")
    email = req.email.strip().lower()
    record = db.pop_auth_session(email)
    if not record or time.time() > record.get("expires_at", 0) or record.get("code") != req.code.strip():
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")
    
    user_data = {"email": email, "name": record.get("name", ""), "group": record.get("group", "")}
    return {"status": "ok", "user": user_data}

def process_quiz_result(res: ResultSubmit) -> Dict[str, Any]:
    assigned_teacher_id = res.teacher_id or "teacher-geo-01"

    if res.session_id:
        active_sess = load_active_session()
        if active_sess and (active_sess.get("sessionId") == res.session_id or active_sess.get("session_id") == res.session_id):
            assigned_teacher_id = active_sess.get("teacher_id", assigned_teacher_id)
        else:
            history = load_sessions_history()
            for s in history:
                if s.get("sessionId") == res.session_id or s.get("session_id") == res.session_id:
                    assigned_teacher_id = s.get("teacher_id", assigned_teacher_id)
                    break
    
    if assigned_teacher_id in ["teacher-ivanov", "teacher-geo-01"] and res.group:
        all_groups = load_groups()
        for g in all_groups:
            if g.get("name") == res.group or g.get("id") == res.group:
                assigned_teacher_id = g.get("teacher_id", assigned_teacher_id)
                break

    data = {
        "date": time.strftime("%d.%m.%Y %H:%M"),
        "email": res.email,
        "name": res.name,
        "group": res.group,
        "quiz_type": res.quiz_type,
        "score": res.score,
        "max_score": res.max_score,
        "accuracy": res.accuracy,
        "time_spent": res.time_spent,
        "is_exam": res.is_exam,
        "exam_token": res.exam_token,
        "violations": res.violations,
        "exam_status": res.exam_status,
        "session_id": res.session_id,
        "mistakes_log": res.mistakes_log,
        "teacher_id": assigned_teacher_id,
        "submission_id": res.submission_id or f"sub_{int(time.time()*1000)}_{secrets.token_hex(4)}",
        "client_timestamp": res.client_timestamp or int(time.time()*1000)
    }
    return save_result_to_file(data)

@app.post("/api/results/save")
def save_quiz_result(res: ResultSubmit) -> Dict[str, Any]:
    outcome = process_quiz_result(res)
    return {"status": "ok", "deduplicated": outcome.get("deduplicated", False)}

@app.post("/api/results/sync-batch")
def sync_batch_results(req: SyncBatchRequest) -> Dict[str, Any]:
    synced = 0
    duplicates = 0
    for item in req.items:
        outcome = process_quiz_result(item)
        if outcome.get("deduplicated"):
            duplicates += 1
        else:
            synced += 1
    return {
        "status": "ok",
        "synced_count": synced,
        "duplicates_count": duplicates,
        "total": len(req.items)
    }

@app.get("/api/results/leaderboard")
def get_leaderboard() -> List[Dict[str, Any]]:
    results = load_results()
    sorted_res = sorted(results, key=lambda x: (x.get("accuracy", 0), x.get("score", 0)), reverse=True)
    return sorted_res[:25]

@app.get("/api/admin/groups")
def get_admin_groups(teacher: Dict[str, Any] = Depends(check_admin)) -> List[Dict[str, Any]]:
    groups = load_groups()
    if is_dean_or_admin(teacher):
        return groups
    return [g for g in groups if g.get("teacher_id", "teacher-ivanov") == teacher.get("teacher_id")]

@app.post("/api/admin/groups")
def save_or_update_group(group: GroupModel, teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, Any]:
    groups = load_groups()
    group_dict = group.model_dump()
    group_dict["teacher_id"] = teacher.get("teacher_id", "teacher-ivanov")
    if not group_dict.get("created_at"):
        group_dict["created_at"] = time.strftime("%d.%m.%Y %H:%M")
    idx = next((i for i, g in enumerate(groups) if g.get("id") == group.id), -1)
    if idx >= 0:
        if not is_dean_or_admin(teacher) and groups[idx].get("teacher_id", "teacher-ivanov") != teacher.get("teacher_id"):
            raise HTTPException(status_code=403, detail="У вас нет прав на редактирование группы другого преподавателя")
    db.save_group(group_dict)
    all_groups = load_groups()
    if is_dean_or_admin(teacher):
        return {"status": "ok", "groups": all_groups}
    return {"status": "ok", "groups": [g for g in all_groups if g.get("teacher_id", "teacher-ivanov") == teacher.get("teacher_id")]}

@app.delete("/api/admin/groups/{group_id}")
def delete_group(group_id: str, teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, Any]:
    groups = load_groups()
    target = next((g for g in groups if g.get("id") == group_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    if not is_dean_or_admin(teacher) and target.get("teacher_id", "teacher-ivanov") != teacher.get("teacher_id"):
        raise HTTPException(status_code=403, detail="У вас нет прав на удаление группы другого преподавателя")
    db.delete_group(group_id)
    all_groups = load_groups()
    if is_dean_or_admin(teacher):
        return {"status": "ok", "groups": all_groups}
    return {"status": "ok", "groups": [g for g in all_groups if g.get("teacher_id", "teacher-ivanov") == teacher.get("teacher_id")]}

@app.get("/api/admin/students")
def get_all_students(teacher: Dict[str, Any] = Depends(check_admin)) -> List[Dict[str, Any]]:
    is_super = is_dean_or_admin(teacher)
    t_id = teacher.get("teacher_id")
    groups = load_groups() if is_super else [g for g in load_groups() if g.get("teacher_id", "teacher-ivanov") == t_id]
    results = load_results() if is_super else [r for r in load_results() if r.get("teacher_id", "teacher-ivanov") == t_id]
    students_map = {}
    for g in groups:
        for s in g.get("students", []):
            key = (s.get("email") or s.get("name") or "").strip().lower()
            if key and key not in students_map:
                students_map[key] = {"name": s.get("name"), "email": s.get("email", ""), "group": g.get("name"), "teacher_id": g.get("teacher_id", "teacher-ivanov")}
    for r in results:
        email = (r.get("email") or "").strip().lower()
        name = r.get("name")
        if email and email != "-" and email not in students_map:
            students_map[email] = {"name": name, "email": email, "group": r.get("group", ""), "teacher_id": r.get("teacher_id", "teacher-ivanov")}
    return list(students_map.values())

@app.get("/api/server-time")
def get_server_time() -> Dict[str, int]:
    return {"server_time": int(time.time() * 1000)}

@app.post("/api/exam/launch")
def launch_exam_session(req: LaunchSessionRequest, teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, Any]:
    now_ms = int(time.time() * 1000)
    duration_ms = req.timeLimitMinutes * 60 * 1000
    sess_id = f"SES-SFEDU-{int(time.time())}"
    teacher_id = teacher.get("teacher_id", "teacher-ivanov")
    session_data = {
        "sessionId": sess_id,
        "session_id": sess_id,
        "groupId": req.groupId,
        "group_id": req.groupId,
        "groupName": req.groupName,
        "group_name": req.groupName,
        "mapUrl": req.mapUrl,
        "map_url": req.mapUrl,
        "regionName": req.regionName,
        "region_name": req.regionName,
        "quizType": req.quizType,
        "quiz_type": req.quizType,
        "mode": req.quizType,
        "quizTypeName": req.quizTypeName,
        "quiz_type_name": req.quizTypeName,
        "questionCount": req.questionCount,
        "questions_count": req.questionCount,
        "timeLimitMinutes": req.timeLimitMinutes,
        "time_limit_minutes": req.timeLimitMinutes,
        "sessionStartedAt": now_ms,
        "started_at": now_ms,
        "durationMs": duration_ms,
        "duration_ms": duration_ms,
        "endTime": now_ms + duration_ms,
        "end_time": now_ms + duration_ms,
        "status": "active",
        "created_date": time.strftime("%d.%m.%Y %H:%M:%S"),
        "teacher_id": teacher_id,
        "teacher_name": teacher.get("full_name", teacher.get("username", "Преподаватель")),
        "organization": teacher.get("organization", "")
    }
    save_active_session(session_data)
    record_session_history(session_data)
    return {"status": "ok", "session": session_data, "server_time": now_ms}

@app.get("/api/exam/active-session")
def get_active_exam_session(teacher: Optional[Dict[str, Any]] = Depends(check_admin_optional)) -> Dict[str, Any]:
    session = load_active_session()
    now_ms = int(time.time() * 1000)
    if not session or session.get("status") in ["stopped", "completed"]:
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}
    
    # Преподавателю показываем только его сессию (декану / суперадмину — любую)
    if teacher and not is_dean_or_admin(teacher) and session.get("teacher_id") != teacher.get("teacher_id"):
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}

    started = session.get("sessionStartedAt", 0) or session.get("started_at", 0)
    duration = session.get("durationMs", 0) or session.get("duration_ms", 0)
    remaining_sec = max(0, int((started + duration - now_ms) / 1000))

    if remaining_sec <= 0 and session.get("status") == "active":
        session["status"] = "completed"
        save_active_session(session)
        record_session_history(session)
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}

    session_copy = dict(session)
    session_copy["server_time"] = now_ms
    session_copy["remaining_seconds"] = remaining_sec
    return {"session": session_copy, "current_server_time": now_ms, "remaining_seconds": remaining_sec}

@app.post("/api/exam/stop")
def stop_exam_session(teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, str]:
    session = load_active_session()
    if session:
        if is_dean_or_admin(teacher) or session.get("teacher_id") == teacher.get("teacher_id"):
            session["status"] = "stopped"
            save_active_session(session)
            record_session_history(session)
    return {"status": "ok"}

@app.get("/admin", response_class=HTMLResponse, response_model=None)
@app.get("/admin.html", response_class=HTMLResponse, response_model=None)
def admin_panel(teacher: Dict[str, Any] = Depends(check_admin)):
    t_id = teacher.get("teacher_id")
    is_super = is_dean_or_admin(teacher)
    all_results = load_results()
    all_groups = load_groups()
    active_session = load_active_session()
    all_teachers = load_teachers()

    results = all_results if is_super else [r for r in all_results if r.get("teacher_id", "teacher-ivanov") == t_id]
    groups = all_groups if is_super else [g for g in all_groups if g.get("teacher_id", "teacher-ivanov") == t_id]
    
    teacher_session = None
    if active_session and (is_super or active_session.get("teacher_id") == t_id):
        teacher_session = active_session

    admin_path = os.path.join(os.path.dirname(__file__), "admin.html")
    if os.path.exists(admin_path):
        with open(admin_path, "r", encoding="utf-8") as f:
            template = f.read()
        results_json = json.dumps(results, ensure_ascii=False)
        groups_json = json.dumps(groups, ensure_ascii=False)
        session_json = json.dumps(teacher_session, ensure_ascii=False)
        teacher_json = json.dumps(teacher, ensure_ascii=False)
        all_teachers_json = json.dumps(all_teachers, ensure_ascii=False)
        branding_json = json.dumps(load_branding(), ensure_ascii=False)

        rendered = template.replace("__SERVER_RESULTS_JSON__", results_json)
        rendered = rendered.replace("__SERVER_GROUPS_JSON__", groups_json)
        rendered = rendered.replace("__SERVER_SESSION_JSON__", session_json)
        rendered = rendered.replace("__SERVER_TEACHER_JSON__", teacher_json)
        rendered = rendered.replace("__SERVER_ALL_TEACHERS_JSON__", all_teachers_json)
        rendered = rendered.replace("__SERVER_BRANDING_JSON__", branding_json)
        return HTMLResponse(content=rendered)

    total_tests = len(results)
    avg_accuracy = round(sum(r.get("accuracy", 0) for r in results) / total_tests, 1) if total_tests else 0
    return HTMLResponse(f"<h2>{teacher.get('organization', 'Институт наук о Земле ЮФУ')}</h2><p>Преподаватель: {teacher.get('full_name')}</p><p>Всего сдано тестов: {total_tests}, средняя точность: {avg_accuracy}%</p>")

@app.get("/api/branding")
def get_branding_endpoint() -> Dict[str, Any]:
    return load_branding()

@app.post("/api/branding")
def update_branding_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    save_branding(payload)
    return {"status": "ok", "branding": load_branding()}

@app.get("/api/student/dashboard")
def get_student_dashboard(email: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
    all_results = load_results()
    student_records = []
    clean_email = (email or "").strip().lower()
    clean_name = (name or "").strip().lower()

    for r in all_results:
        r_email = str(r.get("email", "")).strip().lower()
        r_name = str(r.get("name", "")).strip().lower()
        if (clean_email and r_email == clean_email) or (clean_name and (clean_name in r_name or r_name in clean_name)):
            student_records.append(r)

    total_tests = len(student_records)
    avg_accuracy = round(sum(int(r.get("accuracy", 0)) for r in student_records) / total_tests) if total_tests else 0
    total_score = sum(int(r.get("score", 0)) for r in student_records)
    violations = sum(int(r.get("violations", 0)) for r in student_records)
    integrity = max(70, min(100, 100 - violations * 5)) if total_tests else 100

    def calc_region_mastery(pattern_list: List[str], default_acc: int = 0):
        matched = []
        for r in student_records:
            q_type = str(r.get("quiz_type", "")).lower()
            if any(p.lower() in q_type for p in pattern_list):
                matched.append(r)
        cnt = len(matched)
        if cnt > 0:
            acc = round(sum(int(m.get("accuracy", 0)) for m in matched) / cnt)
            best = max(int(m.get("accuracy", 0)) for m in matched)
        else:
            acc = default_acc
            best = default_acc
        status = "Освоено (Отлично)" if acc >= 85 else ("В процессе изучения" if acc >= 50 else "Требуется повторение")
        return {
            "tests_count": cnt,
            "avg_accuracy": acc,
            "best_accuracy": best,
            "status": status,
            "mastered": acc >= 80
        }

    rostov_stats = calc_region_mastery(["ростов", "55", "center", "neighbor", "районы", "пазл"], default_acc=85 if total_tests else 0)
    krasnodar_stats = calc_region_mastery(["краснодар", "кубань", "44", "сочи"], default_acc=92 if total_tests else 0)
    russia_stats = calc_region_mastery(["россия", "рф", "комплекс", "федерац"], default_acc=78 if total_tests else 0)

    if total_tests > 0:
        if krasnodar_stats["tests_count"] == 0:
            krasnodar_stats["avg_accuracy"] = min(100, max(60, avg_accuracy + 4))
            krasnodar_stats["best_accuracy"] = krasnodar_stats["avg_accuracy"]
        if russia_stats["tests_count"] == 0:
            russia_stats["avg_accuracy"] = min(100, max(50, avg_accuracy - 8))
            russia_stats["best_accuracy"] = russia_stats["avg_accuracy"]

    recent_history = list(reversed(student_records))[:8]

    return {
        "status": "ok",
        "student": {
            "name": name or (student_records[0].get("name") if student_records else "Студент"),
            "email": email or (student_records[0].get("email") if student_records else "student@sfedu.ru"),
            "group": (student_records[0].get("group") if student_records else "Учебная группа")
        },
        "stats": {
            "total_tests": total_tests,
            "avg_accuracy": avg_accuracy,
            "total_score": total_score,
            "violations": violations,
            "integrity": integrity
        },
        "regions": {
            "rostov": {
                "name": "Ростовская область",
                "tag": "Пилотный полигон ЮФО • 55 районов",
                "icon": "🌻",
                **rostov_stats
            },
            "krasnodar": {
                "name": "Краснодарский край",
                "tag": "Кубань и Черноморье • 44 округа",
                "icon": "🍇",
                **krasnodar_stats
            },
            "russia": {
                "name": "Российская Федерация",
                "tag": "Общероссийский срез • 89 субъектов",
                "icon": "🇷🇺",
                **russia_stats
            }
        },
        "recent_history": recent_history
    }

@app.get("/api/admin/results")
def get_admin_results(teacher: Dict[str, Any] = Depends(check_admin)) -> List[Dict[str, Any]]:
    results = load_results()
    if is_dean_or_admin(teacher):
        return results
    return [r for r in results if r.get("teacher_id", "teacher-ivanov") == teacher.get("teacher_id")]

@app.get("/admin/export-csv", response_class=PlainTextResponse, response_model=None)
def export_csv(teacher: Dict[str, Any] = Depends(check_admin)):
    t_id = teacher.get("teacher_id")
    is_super = is_dean_or_admin(teacher)
    results = load_results() if is_super else [r for r in load_results() if r.get("teacher_id", "teacher-ivanov") == t_id]
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Дата', 'ФИО студента', 'Email', 'Группа', 'Категория/Тема', 'Режим',
        'Статус сдачи', 'Нарушений фокуса', 'Цифровой токен сдачи',
        'Баллы', 'Макс баллов', 'Успешность (%)', 'Затраченное время', 'ID Преподавателя'
    ])
    
    for r in results:
        is_exam = bool(r.get('is_exam', False))
        status_text = r.get('exam_status', 'Сдано' if is_exam else 'Пройдено')
        writer.writerow([
            r.get('date', ''),
            r.get('name', 'Анонимно'),
            r.get('email', '-'),
            r.get('group', '-'),
            r.get('quiz_type', 'Общий'),
            'Контрольный срез' if is_exam else 'Практика',
            status_text,
            r.get('violations', 0),
            r.get('exam_token', '-'),
            r.get('score', 0),
            r.get('max_score', 0),
            f"{r.get('accuracy', 0)}%",
            r.get('time_spent', '-'),
            r.get('teacher_id', t_id)
        ])
    response = PlainTextResponse(output.getvalue(), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f"attachment; filename=vedomost_{teacher.get('username', 'export')}.csv"
    return response

@app.get("/api/admin/export-moodle")
def export_moodle(
    format: str = "xml",
    teacher: Dict[str, Any] = Depends(check_admin)
) -> Response:
    is_super = is_dean_or_admin(teacher)
    t_id = teacher.get("teacher_id")
    results = load_results() if is_super else [r for r in load_results() if r.get("teacher_id", "teacher-ivanov") == t_id]

    if format.lower() == "json":
        lti_payload = {
            "https://purl.imsglobal.org/spec/lti-ags/scope/score": {
                "context": {
                    "id": "sfedu-geoatlas-2026",
                    "label": "Институт наук о Земле ЮФУ — Географический атлас",
                    "exported_by": teacher.get("full_name", "Преподаватель"),
                    "organization": teacher.get("organization", "ЮФУ"),
                    "department": teacher.get("department", "Геофак"),
                    "is_executive_summary": is_super
                },
                "lineItem": {
                    "id": "https://moodle.sfedu.ru/mod/lti/service/lineitem/geoatlas-exam",
                    "label": "Контрольные срезы и практические работы GeoAtlas",
                    "scoreMaximum": 100
                },
                "scores": [
                    {
                        "userId": r.get("email", ""),
                        "userName": r.get("name", "Анонимный студент"),
                        "userGroup": r.get("group", ""),
                        "scoreGiven": int(r.get("accuracy", 0)),
                        "scoreMaximum": 100,
                        "pointsScored": int(r.get("score", 0)),
                        "pointsTotal": int(r.get("max_score", 0)),
                        "activityProgress": "Completed",
                        "gradingProgress": "FullyGraded",
                        "comment": f"GeoAtlas: {r.get('quiz_type', 'Тест')}, статус: {r.get('exam_status', 'Сдано')}, нарушений: {r.get('violations', 0)}",
                        "timestamp": r.get("date", "")
                    }
                    for r in results
                ]
            }
        }
        content = json.dumps(lti_payload, ensure_ascii=False, indent=2)
        response = PlainTextResponse(content, media_type="application/json; charset=utf-8")
        response.headers["Content-Disposition"] = "attachment; filename=moodle_lti_grades_sfedu.json"
        return response

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<results xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
        '  <gradebook>',
        '    <generator>GeoAtlas B2B SaaS LMS Exporter</generator>',
        '    <institution>Южный федеральный университет (ЮФУ)</institution>',
        f'    <faculty>{teacher.get("organization", "Институт наук о Земле ЮФУ")}</faculty>',
        f'    <teacher>{teacher.get("full_name", "Преподаватель")}</teacher>',
        f'    <exported_at>{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</exported_at>',
        f'    <is_dean_summary>{str(is_super).lower()}</is_dean_summary>',
        '    <items>'
    ]

    for idx, r in enumerate(results, start=1):
        clean_email = (r.get("email") or "student@sfedu.ru").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean_name = (r.get("name") or "Студент").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean_group = (r.get("group") or "-").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean_type = (r.get("quiz_type") or "Общий").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        id_num = clean_email.split("@")[0]
        
        xml_lines.extend([
            f'      <result id="{idx}">',
            f'        <assignment id="geoatlas_exam_{idx}">{clean_type}</assignment>',
            '        <student>',
            f'          <email>{clean_email}</email>',
            f'          <idnumber>{id_num}</idnumber>',
            f'          <fullname>{clean_name}</fullname>',
            f'          <group>{clean_group}</group>',
            '        </student>',
            f'        <score>{r.get("score", 0)}</score>',
            f'        <maxscore>{r.get("max_score", 0)}</maxscore>',
            f'        <percentage>{r.get("accuracy", 0)}</percentage>',
            f'        <status>{r.get("exam_status", "Сдано")}</status>',
            f'        <violations>{r.get("violations", 0)}</violations>',
            f'        <token>{r.get("exam_token", "")}</token>',
            '        <feedback>Сдано в системе интерактивного геоатласа GeoAtlas ЮФУ</feedback>',
            f'        <timestamp>{r.get("date", "")}</timestamp>',
            '      </result>'
        ])

    xml_lines.extend([
        '    </items>',
        '  </gradebook>',
        '</results>'
    ])
    xml_content = "\n".join(xml_lines)
    response = PlainTextResponse(xml_content, media_type="application/xml; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=moodle_grades_sfedu.xml"
    return response

REGION_DATA_CACHE = {}

def find_map_file(filename_or_slug: str) -> Optional[str]:
    clean = str(filename_or_slug).strip().replace('/', os.sep).replace('\\', os.sep)
    basename = os.path.basename(clean)
    stem = basename.replace('_quiz_map.html', '').replace('.html', '')

    candidates = [
        clean,
        os.path.join("public", "maps", basename),
        os.path.join("public", "maps", f"{stem}_quiz_map.html"),
        f"{stem}_quiz_map.html",
        os.path.join("public", "maps", f"{stem}.html"),
        f"{stem}.html"
    ]
    for c in candidates:
        if c and os.path.exists(c) and os.path.isfile(c):
            return c
    return None

def get_region_data(region_key: str) -> Optional[Dict[str, Any]]:
    clean = region_key.lower().strip()
    clean = clean.replace('_meta.json', '').replace('_quiz_map.html', '').replace('.html', '').replace('.json', '').strip()
    if clean in REGION_DATA_CACHE:
        return REGION_DATA_CACHE[clean]

    target_meta_file = None
    if os.path.exists(MAPS_DIR):
        for fname in os.listdir(MAPS_DIR):
            if fname.lower().endswith('_meta.json'):
                stem = fname[:-10].lower()
                if stem == clean or clean in stem or stem in clean:
                    target_meta_file = os.path.join(MAPS_DIR, fname)
                    clean = stem
                    break

    if not target_meta_file or not os.path.exists(target_meta_file):
        direct_cand = os.path.join(MAPS_DIR, f"{clean}_meta.json")
        if os.path.exists(direct_cand):
            target_meta_file = direct_cand

    if not target_meta_file or not os.path.exists(target_meta_file):
        return None

    try:
        with open(target_meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        data = {
            "status": "ok",
            "region": clean,
            "map_url": f"public/maps/{clean}_quiz_map.html",
            "bounds": meta.get("REGION_BOUNDS"),
            "districts": meta.get("EMBEDDED_DISTRICTS"),
            "centers": meta.get("EMBEDDED_CENTERS"),
            "neighbors": meta.get("EMBEDDED_NEIGHBORS"),
            "rivers": meta.get("EMBEDDED_RIVERS"),
            "puzzle_data": meta.get("EMBEDDED_PUZZLE_DATA"),
            "outline_geojson": meta.get("REGION_OUTLINE_GEOJSON"),
            "REGION_BOUNDS": meta.get("REGION_BOUNDS"),
            "EMBEDDED_DISTRICTS": meta.get("EMBEDDED_DISTRICTS"),
            "EMBEDDED_CENTERS": meta.get("EMBEDDED_CENTERS"),
            "EMBEDDED_NEIGHBORS": meta.get("EMBEDDED_NEIGHBORS"),
            "EMBEDDED_RIVERS": meta.get("EMBEDDED_RIVERS"),
            "EMBEDDED_PUZZLE_DATA": meta.get("EMBEDDED_PUZZLE_DATA"),
            "REGION_OUTLINE_GEOJSON": meta.get("REGION_OUTLINE_GEOJSON")
        }
        REGION_DATA_CACHE[clean] = data
        return data
    except Exception as e:
        logger.warning("Ошибка чтения метаданных региона %s: %s", region_key, e)
        return None

@app.get("/api/region/{region_id}/data")
def api_region_data(region_id: str) -> Dict[str, Any]:
    data = get_region_data(region_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail=f"Регион '{region_id}' не найден")

REGIONS_INFO: Dict[str, Dict[str, Any]] = {
    "rostov": {
        "id": "rostov",
        "title": "Ростовская область",
        "center": [47.5, 40.5],
        "zoom": 8,
        "map_file": os.path.join("public", "maps", "rostov_quiz_map.html"),
        "geojson_file": "raion.shp",
        "is_rf": False,
        "aliases": ["rostov", "ростов", "ростовская", "ростовская область", "rnd", "ростов-на-дону"]
    },
    "krasnodar": {
        "id": "krasnodar",
        "title": "Краснодарский край",
        "center": [45.2, 39.0],
        "zoom": 8,
        "map_file": os.path.join("public", "maps", "krasnodar_quiz_map.html"),
        "geojson_file": "boundary-3857.shp",
        "is_rf": False,
        "aliases": ["krasnodar", "краснодар", "краснодарский", "краснодарский край", "кубань", "kuban"]
    },
    "russia": {
        "id": "russia",
        "title": "Российская Федерация",
        "center": [63.0, 95.0],
        "zoom": 3,
        "map_file": os.path.join("public", "maps", "russia_quiz_map.html"),
        "geojson_file": "gadm41_RUS_1.shp",
        "is_rf": True,
        "aliases": ["russia", "россия", "рф", "rf", "российская федерация", "rus"]
    }
}

def resolve_region_info(region_query: Optional[str] = None) -> Dict[str, Any]:
    if not region_query:
        return REGIONS_INFO["rostov"]
    
    clean = str(region_query).lower().strip()
    clean = clean.replace("_quiz_map.html", "").replace(".html", "").replace("/", "").replace("\\", "").strip()

    for key, info in REGIONS_INFO.items():
        if clean == key or clean in info.get("aliases", []):
            return info

    candidate_file = find_map_file(f"{clean}_quiz_map.html") or find_map_file(clean)
    if candidate_file:
        title = clean.replace("_", " ").title()
        return {
            "id": clean,
            "title": title,
            "center": [55.75, 37.61],
            "zoom": 7,
            "map_file": candidate_file,
            "geojson_file": f"{clean}.geojson",
            "is_rf": False,
            "aliases": [clean]
        }

    for key, info in REGIONS_INFO.items():
        if key in clean or any(a in clean for a in info.get("aliases", [])):
            return info

    return REGIONS_INFO["rostov"]

def render_dynamic_map_response(region_query: Optional[str] = None) -> HTMLResponse:
    info = resolve_region_info(region_query)
    map_file = find_map_file(info.get("map_file", "")) or find_map_file("rostov_quiz_map.html")
    if not map_file or not os.path.exists(map_file):
        return HTMLResponse(
            "<h2>Карта еще не сгенерирована. Запустите 'python main.py' локально.</h2>",
            status_code=503
        )

    try:
        with open(map_file, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
    except Exception as e:
        logger.error("Ошибка чтения карты %s: %s", map_file, e)
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла карты: {map_file}")

    web_map_url = info.get("map_file", "").replace("\\", "/")
    if "public/maps/" in web_map_url:
        web_map_url = "/public/maps/" + web_map_url.split("public/maps/")[-1]
    elif not web_map_url.startswith("/") and web_map_url:
        web_map_url = "/" + web_map_url

    context_obj = {
        "region": info["id"],
        "title": info["title"],
        "center": info["center"],
        "zoom": info["zoom"],
        "map_url": web_map_url,
        "geojson_file": info.get("geojson_file", ""),
        "is_rf": info.get("is_rf", False)
    }
    context_json = json.dumps(context_obj, ensure_ascii=False)

    body_attrs = (
        f'data-region="{info["id"]}" '
        f'data-region-title="{info["title"]}" '
        f'data-center-lat="{info["center"][0]}" '
        f'data-center-lng="{info["center"][1]}" '
        f'data-zoom="{info["zoom"]}" '
        f'data-map-url="{web_map_url}"'
    )
    if "<body" in html:
        if 'data-region="' in html:
            html = re.sub(r'data-region="[^"]*"', lambda m: f'data-region="{info["id"]}"', html, count=1)
            html = re.sub(r'data-region-title="[^"]*"', lambda m: f'data-region-title="{info["title"]}"', html, count=1)
            html = re.sub(r'data-center-lat="[^"]*"', lambda m: f'data-center-lat="{info["center"][0]}"', html, count=1)
            html = re.sub(r'data-center-lng="[^"]*"', lambda m: f'data-center-lng="{info["center"][1]}"', html, count=1)
            html = re.sub(r'data-zoom="[^"]*"', lambda m: f'data-zoom="{info["zoom"]}"', html, count=1)
            html = re.sub(r'data-map-url="[^"]*"', lambda m: f'data-map-url="{web_map_url}"', html, count=1)
        else:
            html = re.sub(r'<body([^>]*)>', lambda m: f'<body{m.group(1)} {body_attrs}>', html, count=1)

    context_script = f"""<script id="server-region-context" type="application/json">
{context_json}
</script>
<script>
window.SERVER_REGION_CONTEXT = {context_json};
window.currentRegionKey = "{info['id']}";
window.currentRegionTitle = "{info['title']}";
window.serverMapCenter = {json.dumps(info['center'])};
window.serverMapZoom = {info['zoom']};
</script>"""

    branding = load_branding()
    brand_primary = branding.get("primary_color", "#2563EB")
    brand_hover = branding.get("primary_hover", "#1D4ED8")
    brand_accent = branding.get("accent_color", "#7C3AED")
    brand_script = f"""<style id="server-branding-style">
:root {{
    --primary: {brand_primary};
    --primary-hover: {brand_hover};
    --accent: {brand_accent};
}}
.nav-top-btn,
#top-nav-panel a,
#top-nav-panel a:hover,
#top-nav-panel a:visited,
#top-nav-panel a:active {{
    text-decoration: none !important;
}}
</style>
<script id="server-branding-context">
window.GEOATLAS_BRANDING = {json.dumps(branding, ensure_ascii=False)};
</script>"""

    html = re.sub(r'<script id="server-region-context"[^>]*>[\s\S]*?</script>\s*<script>[\s\S]*?window\.SERVER_REGION_CONTEXT[\s\S]*?</script>', '', html)
    html = re.sub(r'<style id="server-branding-style">[\s\S]*?</style>\s*<script id="server-branding-context">[\s\S]*?</script>', '', html)

    full_injected = f"{brand_script}\n{context_script}"

    if "<body" in html:
        html = re.sub(r'(<body[^>]*>)', lambda m: f'{m.group(1)}\n{full_injected}', html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", f"{full_injected}\n</head>", 1)
    else:
        html = f"{full_injected}\n{html}"

    # Очистка устаревшего встроенного quiz.js из старых файлов Folium, чтобы /quiz.js был единственным источником правды
    html = re.sub(r'(window\.serverMapZoom\s*=\s*[\d\.]+;)([\s\S]*?)(</script>)', r'\1\n\3', html, count=1)

    if "/quiz.js" not in html:
        if "</body>" in html:
            html = html.replace("</body>", '<script src="/quiz.js"></script>\n</body>', 1)
        elif "</html>" in html:
            html = html.replace("</html>", '<script src="/quiz.js"></script>\n</html>', 1)
        else:
            html = f'{html}\n<script src="/quiz.js"></script>'

    return HTMLResponse(content=html, media_type="text/html")

@app.post("/api/upload-map")
async def upload_map(
    file: UploadFile = File(...),
    region_name: Optional[str] = Form(None),
    teacher: Dict[str, Any] = Depends(check_admin)
) -> Dict[str, Any]:
    """Распаковка архива Shapefile и генерация интерактивной карты."""
    fname = (file.filename or "").lower()
    if not fname.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Недопустимый формат файла. Загрузите архив в формате ZIP (.zip), содержащий файлы Shapefile (.shp, .dbf, .shx, .prj)."
        )

    import geopandas as gpd
    from main import InteractiveAtlas, slugify_name

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "uploaded_archive.zip")
        try:
            content = await file.read()
            with open(zip_path, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error("Ошибка сохранения загруженного ZIP: %s", e)
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения загруженного файла: {e}")

        # Защита от Zip Slip
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                resolved_temp_dir = os.path.realpath(temp_dir)
                for member in zf.infolist():
                    target_path = os.path.realpath(os.path.join(resolved_temp_dir, member.filename))
                    if not (target_path == resolved_temp_dir or target_path.startswith(resolved_temp_dir + os.sep)):
                        raise HTTPException(
                            status_code=400,
                            detail="Обнаружена недопустимая попытка распаковки за пределы временной директории (Zip Slip)"
                        )
                zf.extractall(temp_dir)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Ошибка распаковки ZIP-архива: %s", e)
            raise HTTPException(status_code=400, detail=f"Не удалось распаковать ZIP-архив: {e}")

        shp_files = []
        for root_dir, _, filenames in os.walk(temp_dir):
            for f_name in filenames:
                if f_name.lower().endswith(".shp"):
                    shp_files.append(os.path.join(root_dir, f_name))

        if not shp_files:
            raise HTTPException(
                status_code=400,
                detail="В архиве не найден файл с расширением .shp. Убедитесь, что внутри архива содержатся файлы шейп-файла (.shp, .dbf, .shx, .prj)."
            )

        main_shp = None
        for s in shp_files:
            bname = os.path.basename(s).lower()
            if any(k in bname for k in ['district', 'raion', 'region', 'boundary', 'rayon', 'border', 'adm']):
                main_shp = s
                break
        if not main_shp:
            main_shp = shp_files[0]

        rivers_shp = next((s for s in shp_files if s != main_shp and any(k in os.path.basename(s).lower() for k in ['river', 'река', 'reka', 'water_line', 'water-line'])), None)
        lakes_shp = next((s for s in shp_files if s != main_shp and any(k in os.path.basename(s).lower() for k in ['lake', 'водоем', 'ozero', 'water_bodies', 'water-bodies', 'water_poly', 'water-poly'])), None)
        cities_shp = next((s for s in shp_files if s != main_shp and any(k in os.path.basename(s).lower() for k in ['city', 'cities', 'center', 'gorod', 'raicentr'])), None)

        try:
            districts_gdf = gpd.read_file(main_shp)
        except Exception as e:
            logger.error("Ошибка чтения Shapefile через GeoPandas: %s", e)
            raise HTTPException(status_code=400, detail=f"Ошибка чтения Shapefile: {e}")

        if districts_gdf.empty:
            raise HTTPException(status_code=400, detail="Загруженный Shapefile пуст (не содержит геометрических объектов)")

        clean_title = (region_name or "").strip()
        if not clean_title:
            base_name = os.path.splitext(os.path.basename(main_shp))[0]
            clean_title = base_name.replace("_", " ").replace("-", " ").title()

        c_rivers = gpd.read_file(rivers_shp) if rivers_shp else None
        c_lakes = gpd.read_file(lakes_shp) if lakes_shp else None
        c_cities = gpd.read_file(cities_shp) if cities_shp else None

        try:
            atlas = InteractiveAtlas(
                region_name=clean_title,
                region_districts=districts_gdf,
                clipped_rivers=c_rivers,
                clipped_lakes=c_lakes,
                clipped_cities=c_cities
            )
            atlas.add_districts()
            atlas.add_water_bodies()
            atlas.add_rivers()
            atlas.add_district_centers()
            output_filepath = atlas.save()
        except Exception as e:
            logger.error("Ошибка генерации карты в InteractiveAtlas: %s", e)
            raise HTTPException(status_code=500, detail=f"Ошибка генерации интерактивной карты: {e}")

        map_filename = os.path.basename(output_filepath)
        direct_url = f"/public/maps/{map_filename}"
        slug = atlas.slug

        REGIONS_INFO[slug] = {
            "id": slug,
            "title": atlas.ru_title,
            "center": atlas.center,
            "zoom": atlas.zoom,
            "map_file": output_filepath,
            "geojson_file": f"{slug}.shp",
            "is_rf": False,
            "aliases": [slug, atlas.ru_title.lower()]
        }

        logger.info("Новая карта успешно сгенерирована: %s (%s)", atlas.ru_title, direct_url)

        return {
            "status": "ok",
            "message": f"Карта «{atlas.ru_title}» успешно создана и сохранена!",
            "region_name": atlas.ru_title,
            "slug": slug,
            "filename": map_filename,
            "map_url": direct_url,
            "direct_url": direct_url,
            "districts_count": len(atlas.districts_gdf) if atlas.districts_gdf is not None else len(districts_gdf)
        }

@app.get("/api/maps")
def get_maps_list(teacher: Optional[Dict[str, Any]] = Depends(check_admin_optional)) -> List[Dict[str, Any]]:
    if not os.path.exists(MAPS_DIR):
        return []

    maps_list = []
    for fname in os.listdir(MAPS_DIR):
        if not fname.lower().endswith(".html"):
            continue
        filepath = os.path.join(MAPS_DIR, fname)
        if not os.path.isfile(filepath):
            continue

        try:
            stat = os.stat(filepath)
            size_bytes = stat.st_size
            ts = stat.st_mtime if stat.st_mtime > 0 else stat.st_ctime

            if size_bytes >= 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.2f} МБ"
            elif size_bytes >= 1024:
                size_str = f"{size_bytes / 1024:.1f} КБ"
            else:
                size_str = f"{size_bytes} Б"

            created_str = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")

            maps_list.append({
                "name": fname,
                "filename": fname,
                "size": size_bytes,
                "size_formatted": size_str,
                "created_at": created_str,
                "date": created_str,
                "timestamp": ts,
                "url": f"/public/maps/{fname}"
            })
        except Exception:
            continue

    maps_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return maps_list

@app.delete("/api/maps/{filename}")
def delete_map(
    filename: str,
    teacher: Optional[Dict[str, Any]] = Depends(check_admin_optional)
) -> Dict[str, Any]:
    safe_name = os.path.basename(filename.strip())
    if not safe_name.lower().endswith(".html"):
        raise HTTPException(status_code=400, detail="Разрешено удаление только HTML-файлов карт")

    target_path = os.path.realpath(os.path.join(MAPS_DIR, safe_name))
    resolved_maps_dir = os.path.realpath(MAPS_DIR)

    if not (target_path == resolved_maps_dir or target_path.startswith(resolved_maps_dir + os.sep)):
        raise HTTPException(status_code=400, detail="Недопустимый путь к файлу")

    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        raise HTTPException(status_code=404, detail=f"Карта «{safe_name}» не найдена")

    try:
        os.remove(target_path)
    except Exception as e:
        logger.error("Ошибка при удалении файла карты %s: %s", safe_name, e)
        raise HTTPException(status_code=500, detail=f"Не удалось удалить файл: {e}")

    slug_to_remove = None
    for slug, info in REGIONS_INFO.items():
        if os.path.basename(info.get("map_file", "")) == safe_name:
            slug_to_remove = slug
            break
    if slug_to_remove and slug_to_remove not in ["rostov", "krasnodar", "russia"]:
        REGIONS_INFO.pop(slug_to_remove, None)

    return {
        "status": "ok",
        "message": f"Карта «{safe_name}» успешно удалена",
        "filename": safe_name
    }

@app.get("/public/maps/{file_name}", response_model=None)
def get_public_map_file(file_name: str):
    target = os.path.join("public", "maps", file_name)
    if os.path.exists(target) and os.path.isfile(target):
        return FileResponse(target)
    if os.path.exists(file_name) and os.path.isfile(file_name):
        return FileResponse(file_name)
    raise HTTPException(status_code=404, detail=f"Карта '{file_name}' не найдена в public/maps/")

@app.get("/", response_model=None)
def get_index(region: Optional[str] = None):
    if region:
        return render_dynamic_map_response(region)
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return render_dynamic_map_response("rostov")

@app.get("/map", response_model=None)
def get_map_query(region: Optional[str] = "rostov"):
    return render_dynamic_map_response(region)

@app.get("/map/{region}", response_model=None)
def get_map_path(region: str):
    return render_dynamic_map_response(region)

@app.get("/region/{region}", response_model=None)
def get_region_path(region: str):
    return render_dynamic_map_response(region)

@app.get("/api/region/context", response_model=None)
def api_get_region_context(region: Optional[str] = "rostov") -> Dict[str, Any]:
    info = resolve_region_info(region)
    return {"status": "ok", "context": info}

@app.get("/api/region/{region_id}/context", response_model=None)
def api_get_region_context_by_id(region_id: str) -> Dict[str, Any]:
    info = resolve_region_info(region_id)
    return {"status": "ok", "context": info}

@app.get("/quiz.js", response_model=None)
def get_quiz_js():
    if os.path.exists("quiz.js"):
        return FileResponse("quiz.js", media_type="application/javascript")
    raise HTTPException(status_code=404, detail="quiz.js не найден")

@app.get("/sw.js", response_model=None)
def get_service_worker():
    sw_file = os.path.join(BASE_DIR, "sw.js")
    if os.path.exists(sw_file):
        return FileResponse(
            sw_file,
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache"
            }
        )
    raise HTTPException(status_code=404, detail="sw.js не найден")

# ========================================================
# ⚔️ DUEL MULTIPLAYER 1V1 (WEBSOCKETS & REST POLLING)
# ========================================================

class DuelPlayer:
    def __init__(self, player_id: str, name: str, group: str = "", email: str = "", is_host: bool = False):
        self.player_id = player_id
        self.name = name or "Игрок"
        self.group = group or "-"
        self.email = email or ""
        self.is_host = is_host
        self.ready = False
        self.score = 0
        self.progress = 0
        self.total = 7
        self.mistakes = 0
        self.finished = False
        self.finish_time: Optional[float] = None
        self.ws: Optional[WebSocket] = None
        self.last_ping = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "group": self.group,
            "email": self.email,
            "is_host": self.is_host,
            "ready": self.ready,
            "score": self.score,
            "progress": self.progress,
            "total": self.total,
            "mistakes": self.mistakes,
            "finished": self.finished,
            "finish_time": self.finish_time,
            "online": (self.ws is not None) or (time.time() - self.last_ping < 15)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DuelPlayer":
        p = cls(
            player_id=data.get("player_id", ""),
            name=data.get("name", "Игрок"),
            group=data.get("group", "-"),
            email=data.get("email", ""),
            is_host=bool(data.get("is_host", False))
        )
        p.ready = bool(data.get("ready", False))
        p.score = int(data.get("score", 0))
        p.progress = int(data.get("progress", 0))
        p.total = int(data.get("total", 7))
        p.mistakes = int(data.get("mistakes", 0))
        p.finished = bool(data.get("finished", False))
        p.finish_time = data.get("finish_time")
        p.last_ping = data.get("last_ping", time.time())
        return p

class DuelRoom:
    def __init__(self, room_id: str, mode: str, region: str, host: DuelPlayer):
        self.room_id = room_id.upper()
        self.mode = mode if mode in ["center", "puzzle"] else "center"
        self.region = region or "rostov"
        self.created_at = time.time()
        self.status = "waiting"  # "waiting", "ready", "countdown", "playing", "finished"
        self.players: Dict[str, DuelPlayer] = {host.player_id: host}
        self.questions: List[Dict[str, Any]] = []
        self.winner: Optional[str] = None
        self.winner_reason: str = ""
        self.winner_name: str = ""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.countdown: int = 3

        if self.mode == "center":
            self.generate_center_questions()
        else:
            self.init_puzzle_config()

    def generate_center_questions(self):
        reg_data = get_region_data(self.region) or {}
        centers = reg_data.get("EMBEDDED_CENTERS", [])
        if not centers:
            centers = [
                {"name": "Ростов-на-Дону", "lat": 47.222, "lon": 39.718},
                {"name": "Таганрог", "lat": 47.217, "lon": 38.917},
                {"name": "Шахты", "lat": 47.708, "lon": 40.216},
                {"name": "Новочеркасск", "lat": 47.422, "lon": 40.093},
                {"name": "Батайск", "lat": 47.139, "lon": 39.751},
                {"name": "Волгодонск", "lat": 47.514, "lon": 42.153},
                {"name": "Азов", "lat": 47.112, "lon": 39.424}
            ]
        sample_size = min(7, len(centers))
        selected = random.sample(centers, sample_size)
        self.questions = [
            {
                "index": i,
                "name": c.get("name", ""),
                "lat": float(c.get("lat", 0.0)),
                "lon": float(c.get("lon", 0.0)),
                "status": c.get("status", "райцентр")
            }
            for i, c in enumerate(selected)
        ]
        for p in self.players.values():
            p.total = len(self.questions)

    def init_puzzle_config(self):
        reg_data = get_region_data(self.region) or {}
        puz = reg_data.get("EMBEDDED_PUZZLE_DATA", [])
        count = len(puz) if puz else 25
        for p in self.players.values():
            p.total = count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "mode": self.mode,
            "region": self.region,
            "status": self.status,
            "created_at": self.created_at,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "questions": self.questions if self.mode == "center" else [],
            "players": [p.to_dict() for p in self.players.values()],
            "winner": self.winner,
            "winner_name": self.winner_name,
            "winner_reason": self.winner_reason,
            "countdown": self.countdown
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DuelRoom":
        room = cls.__new__(cls)
        room.room_id = str(data.get("room_id", "")).upper()
        room.mode = data.get("mode", "center")
        room.region = data.get("region", "rostov")
        room.created_at = float(data.get("created_at", time.time()))
        room.status = data.get("status", "waiting")
        room.questions = data.get("questions", [])
        room.winner = data.get("winner")
        room.winner_reason = data.get("winner_reason", "")
        room.winner_name = data.get("winner_name", "")
        room.start_time = data.get("start_time")
        room.end_time = data.get("end_time")
        room.countdown = int(data.get("countdown", 3))
        room.players = {}
        for p_data in data.get("players", []):
            if isinstance(p_data, dict):
                p = DuelPlayer.from_dict(p_data)
                room.players[p.player_id] = p
        return room

    async def broadcast(self, message: Dict[str, Any]):
        for p in list(self.players.values()):
            if p.ws:
                try:
                    await p.ws.send_json(message)
                except Exception:
                    p.ws = None

    def check_finished(self):
        if self.status == "finished":
            return

        players_list = list(self.players.values())
        if len(players_list) < 2:
            return

        p1, p2 = players_list[0], players_list[1]

        if self.mode == "center":
            if p1.finished and p2.finished:
                self.status = "finished"
                self.end_time = time.time()
                if p1.score > p2.score:
                    self.winner = p1.player_id
                    self.winner_name = p1.name
                    self.winner_reason = f"{p1.name} победил(а) по баллам ({p1.score} : {p2.score})!"
                elif p2.score > p1.score:
                    self.winner = p2.player_id
                    self.winner_name = p2.name
                    self.winner_reason = f"{p2.name} победил(а) по баллам ({p2.score} : {p1.score})!"
                else:
                    t1 = (p1.finish_time or 999999) - (self.start_time or 0)
                    t2 = (p2.finish_time or 999999) - (self.start_time or 0)
                    if t1 < t2:
                        self.winner = p1.player_id
                        self.winner_name = p1.name
                        self.winner_reason = f"При равных баллах ({p1.score}) {p1.name} оказался(лась) быстрее!"
                    elif t2 < t1:
                        self.winner = p2.player_id
                        self.winner_name = p2.name
                        self.winner_reason = f"При равных баллах ({p2.score}) {p2.name} оказался(лась) быстрее!"
                    else:
                        self.winner = "draw"
                        self.winner_name = "Ничья"
                        self.winner_reason = f"Боевая ничья! ({p1.score} : {p2.score})"

        elif self.mode == "puzzle":
            if p1.finished or p2.finished or (p1.progress >= p1.total) or (p2.progress >= p2.total):
                self.status = "finished"
                self.end_time = time.time()
                if p1.progress > p2.progress:
                    self.winner = p1.player_id
                    self.winner_name = p1.name
                    self.winner_reason = f"{p1.name} собрал(а) больше районов ({p1.progress}/{p1.total})!"
                elif p2.progress > p1.progress:
                    self.winner = p2.player_id
                    self.winner_name = p2.name
                    self.winner_reason = f"{p2.name} собрал(а) больше районов ({p2.progress}/{p2.total})!"
                else:
                    if p1.mistakes < p2.mistakes:
                        self.winner = p1.player_id
                        self.winner_name = p1.name
                        self.winner_reason = f"{p1.name} допустил(а) меньше ошибок ({p1.mistakes} vs {p2.mistakes})!"
                    elif p2.mistakes < p1.mistakes:
                        self.winner = p2.player_id
                        self.winner_name = p2.name
                        self.winner_reason = f"{p2.name} допустил(а) меньше ошибок ({p2.mistakes} vs {p1.mistakes})!"
                    else:
                        self.winner = "draw"
                        self.winner_name = "Ничья"
                        self.winner_reason = "Боевая ничья!"

DUEL_ROOMS_FILE = os.path.join(BASE_DIR, "duel_rooms.json")
active_duel_rooms: Dict[str, DuelRoom] = {}

def save_duel_rooms_to_disk() -> None:
    try:
        now = time.time()
        active_data = {
            rid: r.to_dict()
            for rid, r in active_duel_rooms.items()
            if (now - r.created_at) < 86400
        }
        with open(DUEL_ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(active_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения duel_rooms.json: %s", e)

def load_duel_rooms_from_disk() -> None:
    global active_duel_rooms
    if not os.path.exists(DUEL_ROOMS_FILE):
        return
    try:
        now = time.time()
        with open(DUEL_ROOMS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, dict):
                count = 0
                for rid, r_data in raw.items():
                    if isinstance(r_data, dict):
                        room = DuelRoom.from_dict(r_data)
                        if (now - room.created_at) < 86400:
                            active_duel_rooms[room.room_id] = room
                            count += 1
                logger.info("Загружено %d комнат дуэлей из duel_rooms.json", count)
    except Exception as e:
        logger.error("Ошибка загрузки duel_rooms.json: %s", e)

def load_room_fresh(room_id: str) -> Optional["DuelRoom"]:
    """Возвращает комнату из памяти или с диска (для multi-worker / cold start)."""
    code = room_id.strip().upper()
    if code in active_duel_rooms:
        return active_duel_rooms[code]
    if not os.path.exists(DUEL_ROOMS_FILE):
        return None
    try:
        with open(DUEL_ROOMS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if code in raw and isinstance(raw[code], dict):
            room = DuelRoom.from_dict(raw[code])
            active_duel_rooms[room.room_id] = room
            logger.info("Duel room %s lazy-loaded from disk", code)
            return room
    except Exception as e:
        logger.error("Ошибка lazy-load комнаты %s: %s", code, e)
    return None

# Первичная загрузка с диска при старте приложения
load_duel_rooms_from_disk()

@app.on_event("startup")
def on_app_startup():
    db.init_db()
    db.migrate_legacy_json(BASE_DIR)
    load_duel_rooms_from_disk()

def clean_stale_duel_rooms():
    now = time.time()
    stale = [rid for rid, r in active_duel_rooms.items() if now - r.created_at > 7200]
    if stale:
        for rid in stale:
            active_duel_rooms.pop(rid, None)
        save_duel_rooms_to_disk()

@app.post("/api/duel/create")
def create_duel_room(req: DuelCreateRequest) -> Dict[str, Any]:
    clean_stale_duel_rooms()
    room_code = f"DUEL-{random.randint(1000, 9999)}"
    while room_code in active_duel_rooms:
        room_code = f"DUEL-{random.randint(1000, 9999)}"

    player_id = f"p_{secrets.token_hex(4)}"
    host = DuelPlayer(
        player_id=player_id,
        name=req.host_name,
        group=req.host_group,
        email=req.host_email,
        is_host=True
    )
    room = DuelRoom(room_code, req.mode, req.region, host)
    active_duel_rooms[room_code] = room
    logger.info("Duel room created: %s (mode=%s, region=%s)", room_code, req.mode, req.region)
    save_duel_rooms_to_disk()

    map_url = f"/map/{req.region}?duel={room_code}&player={player_id}&role=host"
    return {
        "status": "ok",
        "room_id": room_code,
        "player_id": player_id,
        "role": "host",
        "mode": room.mode,
        "region": room.region,
        "map_url": map_url,
        "room": room.to_dict()
    }

@app.post("/api/duel/join")
def join_duel_room(req: DuelJoinRequest) -> Dict[str, Any]:
    clean_stale_duel_rooms()
    code = req.room_id.strip().upper()
    room = load_room_fresh(code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната дуэли '{code}' не найдена")

    if room.status == "finished":
        raise HTTPException(status_code=400, detail="Эта дуэль уже завершена")

    existing_player = next((p for p in room.players.values() if p.name == req.player_name and p.email == req.player_email), None)
    if existing_player:
        player_id = existing_player.player_id
        role = "host" if existing_player.is_host else "join"
    else:
        if len(room.players) >= 2:
            raise HTTPException(status_code=400, detail="В этой комнате уже находятся два игрока")
        player_id = f"p_{secrets.token_hex(4)}"
        join_player = DuelPlayer(
            player_id=player_id,
            name=req.player_name,
            group=req.player_group,
            email=req.player_email,
            is_host=False
        )
        room.players[player_id] = join_player
        role = "join"
        if len(room.players) == 2 and room.status == "waiting":
            room.status = "ready"
        save_duel_rooms_to_disk()

    map_url = f"/map/{room.region}?duel={code}&player={player_id}&role={role}"
    return {
        "status": "ok",
        "room_id": code,
        "player_id": player_id,
        "role": role,
        "mode": room.mode,
        "region": room.region,
        "map_url": map_url,
        "room": room.to_dict()
    }

@app.get("/api/duel/state/{room_id}")
def get_duel_room_state(room_id: str, player_id: Optional[str] = None) -> Dict[str, Any]:
    code = room_id.strip().upper()
    room = load_room_fresh(code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната '{code}' не найдена")

    if player_id and player_id in room.players:
        room.players[player_id].last_ping = time.time()

    return {"status": "ok", "room": room.to_dict()}

@app.post("/api/duel/action/{room_id}")
def handle_duel_action(room_id: str, req: DuelActionRequest) -> Dict[str, Any]:
    code = room_id.strip().upper()
    room = load_room_fresh(code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната '{code}' не найдена")

    player = room.players.get(req.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден в комнате")

    player.last_ping = time.time()
    action = req.action
    payload = req.payload or {}

    if action == "ready":
        player.ready = bool(payload.get("ready", True))
        if len(room.players) == 2 and all(p.ready for p in room.players.values()):
            room.status = "playing"
            room.start_time = time.time()

    elif action == "start":
        room.status = "playing"
        room.start_time = time.time()

    elif action == "answer_center":
        pts = int(payload.get("points", 0))
        dist = float(payload.get("distance", 999))
        player.score += pts
        player.progress = int(payload.get("question_index", player.progress)) + 1
        if dist > 80:
            player.mistakes += 1
        if player.progress >= player.total:
            player.finished = True
            player.finish_time = time.time()
        room.check_finished()

    elif action == "place_piece":
        player.progress = int(payload.get("placed_count", player.progress + 1))
        player.mistakes = int(payload.get("mistakes", player.mistakes))
        if player.progress >= player.total:
            player.finished = True
            player.finish_time = time.time()
        room.check_finished()

    elif action == "surrender":
        player.finished = True
        player.finish_time = time.time()
        opp = next((p for pid, p in room.players.items() if pid != player.player_id), None)
        room.status = "finished"
        room.end_time = time.time()
        if opp:
            room.winner = opp.player_id
            room.winner_name = opp.name
            room.winner_reason = f"{player.name} отказался от дуэли. Техническое поражение."
        else:
            room.winner = "draw"
            room.winner_name = "Ничья"
            room.winner_reason = "Игрок отказался от дуэли, соперник отсутствует."

    elif action == "finish":
        player.finished = True
        player.finish_time = time.time()
        room.check_finished()

    save_duel_rooms_to_disk()
    return {"status": "ok", "room": room.to_dict()}

@app.websocket("/ws/duel/{room_id}/{player_id}")
async def websocket_duel_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    await websocket.accept()
    code = room_id.strip().upper()
    room = load_room_fresh(code)

    if not room or player_id not in room.players:
        await websocket.send_json({"type": "error", "message": "Комната или игрок не найдены"})
        await websocket.close()
        return

    player = room.players[player_id]
    player.ws = websocket
    player.last_ping = time.time()

    await room.broadcast({
        "type": "player_connected",
        "player_id": player_id,
        "player_name": player.name,
        "room": room.to_dict()
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            player.last_ping = time.time()

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": time.time()})

            elif msg_type == "ready":
                player.ready = bool(data.get("ready", True))
                await room.broadcast({"type": "player_ready_changed", "player_id": player_id, "ready": player.ready, "room": room.to_dict()})

                if len(room.players) == 2 and all(p.ready for p in room.players.values()):
                    room.status = "countdown"
                    await room.broadcast({"type": "countdown", "seconds": 3, "room": room.to_dict()})
                    await asyncio.sleep(1)
                    await room.broadcast({"type": "countdown", "seconds": 2, "room": room.to_dict()})
                    await asyncio.sleep(1)
                    await room.broadcast({"type": "countdown", "seconds": 1, "room": room.to_dict()})
                    await asyncio.sleep(1)
                    room.status = "playing"
                    room.start_time = time.time()
                    save_duel_rooms_to_disk()
                    await room.broadcast({"type": "game_start", "room": room.to_dict()})

            elif msg_type == "answer_center":
                pts = int(data.get("points", 0))
                dist = float(data.get("distance", 999))
                q_idx = int(data.get("question_index", player.progress))
                player.score += pts
                player.progress = q_idx + 1
                if dist > 80:
                    player.mistakes += 1
                if player.progress >= player.total:
                    player.finished = True
                    player.finish_time = time.time()
                room.check_finished()
                save_duel_rooms_to_disk()

                await room.broadcast({
                    "type": "opponent_action",
                    "player_id": player_id,
                    "action": "answer_center",
                    "points": pts,
                    "distance": dist,
                    "score": player.score,
                    "progress": player.progress,
                    "target_name": data.get("target_name", ""),
                    "room": room.to_dict()
                })

                if room.status == "finished":
                    await room.broadcast({"type": "game_over", "room": room.to_dict()})

            elif msg_type == "place_piece":
                p_count = int(data.get("placed_count", player.progress + 1))
                mistakes = int(data.get("mistakes", player.mistakes))
                player.progress = p_count
                player.mistakes = mistakes
                if player.progress >= player.total:
                    player.finished = True
                    player.finish_time = time.time()
                room.check_finished()
                save_duel_rooms_to_disk()

                await room.broadcast({
                    "type": "opponent_action",
                    "player_id": player_id,
                    "action": "place_piece",
                    "district_name": data.get("district_name", ""),
                    "placed_count": player.progress,
                    "mistakes": player.mistakes,
                    "room": room.to_dict()
                })

                if room.status == "finished":
                    await room.broadcast({"type": "game_over", "room": room.to_dict()})

            elif msg_type == "finish":
                player.finished = True
                player.finish_time = time.time()
                room.check_finished()
                save_duel_rooms_to_disk()
                await room.broadcast({"type": "player_finished", "player_id": player_id, "room": room.to_dict()})
                if room.status == "finished":
                    await room.broadcast({"type": "game_over", "room": room.to_dict()})

            elif msg_type == "surrender":
                player.finished = True
                player.finish_time = time.time()
                opp = next((p for pid, p in room.players.items() if pid != player_id), None)
                room.status = "finished"
                room.end_time = time.time()
                if opp:
                    room.winner = opp.player_id
                    room.winner_name = opp.name
                    room.winner_reason = f"{player.name} отказался от дуэли. Техническое поражение."
                else:
                    room.winner = "draw"
                    room.winner_name = "Ничья"
                    room.winner_reason = "Игрок отказался от дуэли, соперник отсутствует."
                save_duel_rooms_to_disk()
                await room.broadcast({"type": "game_over", "room": room.to_dict()})

    except WebSocketDisconnect:
        player.ws = None
        await room.broadcast({
            "type": "player_disconnected",
            "player_id": player_id,
            "player_name": player.name,
            "room": room.to_dict()
        })
    except Exception as e:
        player.ws = None

@app.get("/{slug}", response_model=None)
def get_slug_route(slug: str):
    clean = slug.lower().strip()

    if clean in ["admin", "admin.html"]:
        return RedirectResponse("/admin")
    if clean in ["index", "index.html"]:
        return FileResponse("index.html") if os.path.exists("index.html") else render_dynamic_map_response("rostov")
    if clean == "quiz.js":
        return get_quiz_js()

    if clean in REGIONS_INFO or any(clean in info.get("aliases", []) for info in REGIONS_INFO.values()):
        return render_dynamic_map_response(clean)

    matched_html = find_map_file(clean)
    if matched_html:
        if "_quiz_map" in clean or "_quiz_map" in matched_html:
            return render_dynamic_map_response(clean)
        return FileResponse(matched_html)

    candidate_map = find_map_file(f"{clean}_quiz_map.html")
    if candidate_map:
        return render_dynamic_map_response(clean)

    raise HTTPException(status_code=404, detail=f"Страница или регион '{slug}' не найден")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)