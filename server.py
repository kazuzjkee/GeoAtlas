from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import zipfile
import tempfile
import shutil
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

logger = logging.getLogger("geoatlas")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="GeoAtlas — Учебно-картографический атлас ЮФУ (Ростов, Краснодар, Россия)")
security = HTTPBasic()
security_optional = HTTPBasic(auto_error=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, "public", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)
app.mount("/public", StaticFiles(directory=os.path.join(BASE_DIR, "public")), name="public")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SESSIONS_FILE = "auth_sessions.json"
RESULTS_FILE = "quiz_results.json"
GROUPS_FILE = "groups.json"
ACTIVE_SESSION_FILE = "active_session.json"
TEACHERS_FILE = "teachers.json"
SESSIONS_HISTORY_FILE = "sessions_history.json"

def load_auth_sessions() -> Dict[str, Any]:
    if os.path.exists(AUTH_SESSIONS_FILE):
        try:
            with open(AUTH_SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_auth_sessions(sessions: Dict[str, Any]) -> None:
    try:
        with open(AUTH_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения auth_sessions: %s", e)

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
    if os.path.exists(TEACHERS_FILE):
        try:
            with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
    save_teachers(DEFAULT_TEACHERS)
    return DEFAULT_TEACHERS

def save_teachers(teachers: List[Dict[str, Any]]) -> None:
    try:
        with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
            json.dump(teachers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения teachers: %s", e)

def load_sessions_history() -> List[Dict[str, Any]]:
    if os.path.exists(SESSIONS_HISTORY_FILE):
        try:
            with open(SESSIONS_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def record_session_history(session_data: Dict[str, Any]) -> None:
    history = load_sessions_history()
    sess_id = session_data.get("sessionId") or session_data.get("session_id")
    idx = next((i for i, s in enumerate(history) if (s.get("sessionId") or s.get("session_id")) == sess_id), -1)
    if idx >= 0:
        history[idx] = session_data
    else:
        history.append(session_data)
    try:
        with open(SESSIONS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка сохранения sessions_history: %s", e)

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
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for r in data:
                        if not r.get("teacher_id"):
                            r["teacher_id"] = "teacher-petrov" if "эконом" in str(r.get("group", "")).lower() else "teacher-ivanov"
                    return data
        except Exception:
            return []
    return []

def save_result_to_file(result_data: Dict[str, Any]) -> None:
    results = load_results()
    results.append(result_data)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def load_groups() -> List[Dict[str, Any]]:
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    for g in data:
                        if not g.get("teacher_id"):
                            g["teacher_id"] = "teacher-petrov" if "эконом" in str(g.get("name", "")).lower() else "teacher-ivanov"
                    return data
        except Exception:
            pass
    save_groups_to_file(DEFAULT_GROUPS)
    return DEFAULT_GROUPS

def save_groups_to_file(groups_data: List[Dict[str, Any]]) -> None:
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(groups_data, f, ensure_ascii=False, indent=2)

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
        if secrets.compare_digest(credentials.username, t.get("username", "")) and \
           secrets.compare_digest(credentials.password, t.get("password", "")):
            return t
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный логин или пароль преподавателя",
        headers={"WWW-Authenticate": "Basic"},
    )

def check_admin_optional(credentials: Optional[HTTPBasicCredentials] = Depends(security_optional)) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    teachers = load_teachers()
    for t in teachers:
        if secrets.compare_digest(credentials.username, t.get("username", "")) and \
           secrets.compare_digest(credentials.password, t.get("password", "")):
            return t
    return None

@app.post("/api/auth/send-code")
def send_code(req: AuthRequest) -> Dict[str, Any]:
    email = req.email.strip().lower()
    if not (email.endswith("@sfedu.ru") or email.endswith(".sfedu.ru")):
        raise HTTPException(status_code=400, detail="Разрешена авторизация только по корпоративной почте ЮФУ (@sfedu.ru)")
    
    code = f"{random.randint(100000, 999999)}"
    sessions = load_auth_sessions()
    sessions[email] = {
        "code": code,
        "expires_at": time.time() + 600,
        "name": req.full_name.strip(),
        "group": req.group_num.strip()
    }
    save_auth_sessions(sessions)
    logger.info("ЮФУ Авторизация: сгенерирован код подтверждения для %s", email)
    return {"status": "ok", "message": "Код подтверждения отправлен", "dev_code": code}

@app.post("/api/auth/verify-code")
def verify_code(req: VerifyRequest) -> Dict[str, Any]:
    email = req.email.strip().lower()
    sessions = load_auth_sessions()
    record = sessions.get(email)
    if not record or time.time() > record.get("expires_at", 0) or record.get("code") != req.code.strip():
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")
    
    user_data = {"email": email, "name": record.get("name", ""), "group": record.get("group", "")}
    sessions.pop(email, None)
    save_auth_sessions(sessions)
    return {"status": "ok", "user": user_data}

@app.post("/api/results/save")
def save_quiz_result(res: ResultSubmit) -> Dict[str, str]:
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
        "teacher_id": assigned_teacher_id
    }
    save_result_to_file(data)
    return {"status": "ok"}

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
        groups[idx] = group_dict
    else:
        groups.append(group_dict)
    save_groups_to_file(groups)
    if is_dean_or_admin(teacher):
        return {"status": "ok", "groups": groups}
    return {"status": "ok", "groups": [g for g in groups if g.get("teacher_id", "teacher-ivanov") == teacher.get("teacher_id")]}

@app.delete("/api/admin/groups/{group_id}")
def delete_group(group_id: str, teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, Any]:
    groups = load_groups()
    target = next((g for g in groups if g.get("id") == group_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    if not is_dean_or_admin(teacher) and target.get("teacher_id", "teacher-ivanov") != teacher.get("teacher_id"):
        raise HTTPException(status_code=403, detail="У вас нет прав на удаление группы другого преподавателя")
    groups = [g for g in groups if g.get("id") != group_id]
    save_groups_to_file(groups)
    if is_dean_or_admin(teacher):
        return {"status": "ok", "groups": groups}
    return {"status": "ok", "groups": [g for g in groups if g.get("teacher_id", "teacher-ivanov") == teacher.get("teacher_id")]}

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

        rendered = template.replace("__SERVER_RESULTS_JSON__", results_json)
        rendered = rendered.replace("__SERVER_GROUPS_JSON__", groups_json)
        rendered = rendered.replace("__SERVER_SESSION_JSON__", session_json)
        rendered = rendered.replace("__SERVER_TEACHER_JSON__", teacher_json)
        rendered = rendered.replace("__SERVER_ALL_TEACHERS_JSON__", all_teachers_json)
        return HTMLResponse(content=rendered)

    total_tests = len(results)
    avg_accuracy = round(sum(r.get("accuracy", 0) for r in results) / total_tests, 1) if total_tests else 0
    return HTMLResponse(f"<h2>{teacher.get('organization', 'Институт наук о Земле ЮФУ')}</h2><p>Преподаватель: {teacher.get('full_name')}</p><p>Всего сдано тестов: {total_tests}, средняя точность: {avg_accuracy}%</p>")

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

    html = re.sub(r'<script id="server-region-context"[^>]*>[\s\S]*?</script>\s*<script>[\s\S]*?window\.SERVER_REGION_CONTEXT[\s\S]*?</script>', '', html)

    if "<body" in html:
        html = re.sub(r'(<body[^>]*>)', lambda m: f'{m.group(1)}\n{context_script}', html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", f"{context_script}\n</head>", 1)
    else:
        html = f"{context_script}\n{html}"

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