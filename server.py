from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

verification_storage = {}
RESULTS_FILE = "quiz_results.json"
GROUPS_FILE = "groups.json"
ACTIVE_SESSION_FILE = "active_session.json"

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

class StudentItem(BaseModel):
    name: str
    email: str

class GroupModel(BaseModel):
    id: str
    name: str
    description: str = ""
    students: list[StudentItem] = []
    created_at: str = ""

class LaunchSessionRequest(BaseModel):
    groupId: str
    groupName: str
    mapUrl: str
    regionName: str
    quizType: str
    quizTypeName: str
    questionCount: int = 15
    timeLimitMinutes: int = 10

def load_results() -> List[Dict[str, Any]]:
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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
                    return data
        except Exception:
            pass
    # Если файл не существует, инициализируем дефолтными группами
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

def check_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_user = secrets.compare_digest(credentials.username, "sfedu_admin")
    correct_pass = secrets.compare_digest(credentials.password, "geodean2026")
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль преподавателя",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.post("/api/auth/send-code")
def send_code(req: AuthRequest) -> Dict[str, Any]:
    email = req.email.strip().lower()
    if not (email.endswith("@sfedu.ru") or email.endswith(".sfedu.ru")):
        raise HTTPException(status_code=400, detail="Разрешена авторизация только по корпоративной почте ЮФУ (@sfedu.ru)")
    
    code = f"{random.randint(100000, 999999)}"
    verification_storage[email] = {
        "code": code,
        "expires_at": time.time() + 600,
        "name": req.full_name.strip(),
        "group": req.group_num.strip()
    }
    logger.info("ЮФУ Авторизация: сгенерирован код подтверждения для %s", email)
    return {"status": "ok", "message": "Код подтверждения отправлен", "dev_code": code}

@app.post("/api/auth/verify-code")
def verify_code(req: VerifyRequest) -> Dict[str, Any]:
    email = req.email.strip().lower()
    record = verification_storage.get(email)
    if not record or time.time() > record["expires_at"] or record["code"] != req.code.strip():
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")
    
    user_data = {"email": email, "name": record["name"], "group": record["group"]}
    del verification_storage[email]
    return {"status": "ok", "user": user_data}

@app.post("/api/results/save")
def save_quiz_result(res: ResultSubmit) -> Dict[str, str]:
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
        "session_id": res.session_id
    }
    save_result_to_file(data)
    return {"status": "ok"}

@app.get("/api/results/leaderboard")
def get_leaderboard() -> List[Dict[str, Any]]:
    results = load_results()
    sorted_res = sorted(results, key=lambda x: (x.get("accuracy", 0), x.get("score", 0)), reverse=True)
    return sorted_res[:25]

# ==========================================
# LMS УПРАВЛЕНИЕ ГРУППАМИ И СИНХРОННЫМИ СЕССИЯМИ
# ==========================================
@app.get("/api/admin/groups")
def get_admin_groups() -> List[Dict[str, Any]]:
    return load_groups()

@app.post("/api/admin/groups")
def save_or_update_group(group: GroupModel) -> Dict[str, Any]:
    groups = load_groups()
    group_dict = group.model_dump()
    if not group_dict.get("created_at"):
        group_dict["created_at"] = time.strftime("%d.%m.%Y %H:%M")
    idx = next((i for i, g in enumerate(groups) if g.get("id") == group.id), -1)
    if idx >= 0:
        groups[idx] = group_dict
    else:
        groups.append(group_dict)
    save_groups_to_file(groups)
    return {"status": "ok", "groups": groups}

@app.delete("/api/admin/groups/{group_id}")
def delete_group(group_id: str) -> Dict[str, Any]:
    groups = load_groups()
    groups = [g for g in groups if g.get("id") != group_id]
    save_groups_to_file(groups)
    return {"status": "ok", "groups": groups}

@app.get("/api/admin/students")
def get_all_students() -> List[Dict[str, Any]]:
    groups = load_groups()
    results = load_results()
    students_map = {}
    for g in groups:
        for s in g.get("students", []):
            key = (s.get("email") or s.get("name") or "").strip().lower()
            if key and key not in students_map:
                students_map[key] = {"name": s.get("name"), "email": s.get("email", ""), "group": g.get("name")}
    for r in results:
        email = (r.get("email") or "").strip().lower()
        name = r.get("name")
        if email and email != "-" and email not in students_map:
            students_map[email] = {"name": name, "email": email, "group": r.get("group", "")}
    return list(students_map.values())

@app.get("/api/server-time")
def get_server_time() -> Dict[str, int]:
    return {"server_time": int(time.time() * 1000)}

@app.post("/api/exam/launch")
def launch_exam_session(req: LaunchSessionRequest) -> Dict[str, Any]:
    now_ms = int(time.time() * 1000)
    duration_ms = req.timeLimitMinutes * 60 * 1000
    sess_id = f"SES-SFEDU-{int(time.time())}"
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
        "created_date": time.strftime("%d.%m.%Y %H:%M:%S")
    }
    save_active_session(session_data)
    return {"status": "ok", "session": session_data, "server_time": now_ms}

@app.get("/api/exam/active-session")
def get_active_exam_session() -> Dict[str, Any]:
    session = load_active_session()
    now_ms = int(time.time() * 1000)
    if not session or session.get("status") in ["stopped", "completed"]:
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}
    
    started = session.get("sessionStartedAt", 0) or session.get("started_at", 0)
    duration = session.get("durationMs", 0) or session.get("duration_ms", 0)
    remaining_sec = max(0, int((started + duration - now_ms) / 1000))

    if remaining_sec <= 0 and session.get("status") == "active":
        session["status"] = "completed"
        save_active_session(session)
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}

    session_copy = dict(session)
    session_copy["server_time"] = now_ms
    session_copy["remaining_seconds"] = remaining_sec
    return {"session": session_copy, "current_server_time": now_ms, "remaining_seconds": remaining_sec}

@app.post("/api/exam/stop")
def stop_exam_session() -> Dict[str, str]:
    session = load_active_session()
    if session:
        session["status"] = "stopped"
        save_active_session(session)
    return {"status": "ok"}

@app.get("/admin", response_class=HTMLResponse, response_model=None)
@app.get("/admin.html", response_class=HTMLResponse, response_model=None)
def admin_panel(username: str = Depends(check_admin)):
    results = load_results()
    groups = load_groups()
    active_session = load_active_session()
    admin_path = os.path.join(os.path.dirname(__file__), "admin.html")
    if os.path.exists(admin_path):
        with open(admin_path, "r", encoding="utf-8") as f:
            template = f.read()
        results_json = json.dumps(results, ensure_ascii=False)
        groups_json = json.dumps(groups, ensure_ascii=False)
        session_json = json.dumps(active_session, ensure_ascii=False)
        rendered = template.replace("__SERVER_RESULTS_JSON__", results_json)
        rendered = rendered.replace("__SERVER_GROUPS_JSON__", groups_json)
        rendered = rendered.replace("__SERVER_SESSION_JSON__", session_json)
        return HTMLResponse(content=rendered)

    total_tests = len(results)
    avg_accuracy = round(sum(r.get("accuracy", 0) for r in results) / total_tests, 1) if total_tests else 0
    return HTMLResponse(f"<h2>Институт наук о Земле ЮФУ</h2><p>Всего сдано тестов: {total_tests}, средняя точность: {avg_accuracy}%</p>")

@app.get("/api/admin/results")
def get_admin_results(username: str = Depends(check_admin)) -> List[Dict[str, Any]]:
    return load_results()

@app.get("/admin/export-csv", response_class=PlainTextResponse, response_model=None)
def export_csv(username: str = Depends(check_admin)):
    results = load_results()
    output = io.StringIO()
    # Add BOM for Excel Russian character support
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Дата', 'ФИО студента', 'Email', 'Группа', 'Категория/Тема', 'Режим',
        'Статус сдачи', 'Нарушений фокуса', 'Цифровой токен сдачи',
        'Баллы', 'Макс баллов', 'Успешность (%)', 'Затраченное время'
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
            'Контрольная (Экзамен)' if is_exam else ('Пазл (Сборка региона)' if 'Пазл' in str(r.get('quiz_type', '')) else 'Обычная викторина'),
            status_text,
            r.get('violations', 0),
            r.get('exam_token', '-'),
            r.get('score', 0),
            r.get('max_score', 0),
            r.get('accuracy', 0),
            r.get('time_spent', '-')
        ])
    
    response = PlainTextResponse(output.getvalue(), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = "attachment; filename=vedomost_sfedu_geos.csv"
    return response

REGION_DATA_CACHE = {}

def get_region_data(region_key: str) -> Optional[Dict[str, Any]]:
    clean = region_key.lower().strip().replace('_quiz_map.html', '').replace('.html', '')
    if clean in REGION_DATA_CACHE:
        return REGION_DATA_CACHE[clean]

    candidates = [
        f"{clean}_quiz_map.html",
        f"{clean}.html"
    ]
    matched_file = None
    for c in candidates:
        if os.path.exists(c):
            matched_file = c
            break

    if not matched_file:
        return None

    try:
        with open(matched_file, 'r', encoding='utf-8') as f:
            html = f.read()

        def extract_var(name, text):
            m = re.search(r'const\s+' + name + r'\s*=\s*(.*?);\s*(?=const|\n|$)', text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1).strip())
                except Exception:
                    return None
            return None

        data = {
            "status": "ok",
            "region": clean,
            "map_url": matched_file,
            "bounds": extract_var('REGION_BOUNDS', html),
            "districts": extract_var('EMBEDDED_DISTRICTS', html),
            "centers": extract_var('EMBEDDED_CENTERS', html),
            "neighbors": extract_var('EMBEDDED_NEIGHBORS', html),
            "rivers": extract_var('EMBEDDED_RIVERS', html),
            "puzzle_data": extract_var('EMBEDDED_PUZZLE_DATA', html),
            "outline_geojson": extract_var('REGION_OUTLINE_GEOJSON', html)
        }
        REGION_DATA_CACHE[clean] = data
        return data
    except Exception as e:
        logger.warning("Ошибка извлечения данных региона %s: %s", region_key, e)
        return None

@app.get("/api/region/{region_id}/data")
def api_region_data(region_id: str) -> Dict[str, Any]:
    data = get_region_data(region_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail=f"Регион '{region_id}' не найден")

# ==========================================
# ДИНАМИЧЕСКИЙ РЕГИОНАЛЬНЫЙ КОНТЕКСТ И МАРШРУТИЗАЦИЯ
# ==========================================
REGIONS_INFO: Dict[str, Dict[str, Any]] = {
    "rostov": {
        "id": "rostov",
        "title": "Ростовская область",
        "center": [47.5, 40.5],
        "zoom": 8,
        "map_file": "rostov_quiz_map.html",
        "geojson_file": "raion.shp",
        "is_rf": False,
        "aliases": ["rostov", "ростов", "ростовская", "ростовская область", "rnd", "ростов-на-дону"]
    },
    "krasnodar": {
        "id": "krasnodar",
        "title": "Краснодарский край",
        "center": [45.2, 39.0],
        "zoom": 8,
        "map_file": "krasnodar_quiz_map.html",
        "geojson_file": "boundary-3857.shp",
        "is_rf": False,
        "aliases": ["krasnodar", "краснодар", "краснодарский", "краснодарский край", "кубань", "kuban"]
    },
    "russia": {
        "id": "russia",
        "title": "Российская Федерация",
        "center": [63.0, 95.0],
        "zoom": 3,
        "map_file": "russia_quiz_map.html",
        "geojson_file": "gadm41_RUS_1.shp",
        "is_rf": True,
        "aliases": ["russia", "россия", "рф", "rf", "российская федерация", "rus"]
    }
}

def resolve_region_info(region_query: Optional[str] = None) -> Dict[str, Any]:
    """Разрешает идентификатор региона, проверяя канонические ключи, алиасы и существующие файлы карт."""
    if not region_query:
        return REGIONS_INFO["rostov"]
    
    clean = str(region_query).lower().strip()
    clean = clean.replace("_quiz_map.html", "").replace(".html", "").replace("/", "").replace("\\", "").strip()

    # 1. Прямое совпадение или через псевдонимы
    for key, info in REGIONS_INFO.items():
        if clean == key or clean in info.get("aliases", []):
            return info

    # 2. Проверка наличия файла карты на диске
    candidate_file = f"{clean}_quiz_map.html"
    if os.path.exists(candidate_file):
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

    # 3. Частичное совпадение с известными регионами
    for key, info in REGIONS_INFO.items():
        if key in clean or any(a in clean for a in info.get("aliases", [])):
            return info

    return REGIONS_INFO["rostov"]

def render_dynamic_map_response(region_query: Optional[str] = None) -> HTMLResponse:
    """Динамически формирует HTML-ответ карты с контекстом, data-атрибутами и серверными переменными."""
    info = resolve_region_info(region_query)
    map_file = info.get("map_file")
    if not map_file or not os.path.exists(map_file):
        map_file = "rostov_quiz_map.html"
        if not os.path.exists(map_file):
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

    context_obj = {
        "region": info["id"],
        "title": info["title"],
        "center": info["center"],
        "zoom": info["zoom"],
        "map_url": info["map_file"],
        "geojson_file": info.get("geojson_file", ""),
        "is_rf": info.get("is_rf", False)
    }
    context_json = json.dumps(context_obj, ensure_ascii=False)

    # 1. Инъекция динамических data-атрибутов в тег <body>
    body_attrs = (
        f'data-region="{info["id"]}" '
        f'data-region-title="{info["title"]}" '
        f'data-center-lat="{info["center"][0]}" '
        f'data-center-lng="{info["center"][1]}" '
        f'data-zoom="{info["zoom"]}" '
        f'data-map-url="{info["map_file"]}"'
    )
    if "<body" in html:
        if 'data-region="' in html:
            html = re.sub(r'data-region="[^"]*"', f'data-region="{info["id"]}"', html, count=1)
            html = re.sub(r'data-region-title="[^"]*"', f'data-region-title="{info["title"]}"', html, count=1)
            html = re.sub(r'data-center-lat="[^"]*"', f'data-center-lat="{info["center"][0]}"', html, count=1)
            html = re.sub(r'data-center-lng="[^"]*"', f'data-center-lng="{info["center"][1]}"', html, count=1)
            html = re.sub(r'data-zoom="[^"]*"', f'data-zoom="{info["zoom"]}"', html, count=1)
            html = re.sub(r'data-map-url="[^"]*"', f'data-map-url="{info["map_file"]}"', html, count=1)
        else:
            html = re.sub(r'<body([^>]*)>', rf'<body\1 {body_attrs}>', html, count=1)

    # 2. Инъекция глобального серверного контекста JavaScript
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

    # Очищаем старый контекстный блок, если он уже существовал
    html = re.sub(r'<script id="server-region-context"[^>]*>[\s\S]*?</script>\s*<script>[\s\S]*?window\.SERVER_REGION_CONTEXT[\s\S]*?</script>', '', html)

    if "<body" in html:
        html = re.sub(r'(<body[^>]*>)', rf'\1\n{context_script}', html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", f"{context_script}\n</head>", 1)
    else:
        html = f"{context_script}\n{html}"

    return HTMLResponse(content=html, media_type="text/html")

@app.get("/", response_model=None)
def get_index(region: Optional[str] = None):
    """Корневой эндпоинт: при наличии параметра ?region=... отдает карту указанного региона, иначе стартовый портал index.html."""
    if region:
        return render_dynamic_map_response(region)
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return render_dynamic_map_response("rostov")

@app.get("/map", response_model=None)
def get_map_query(region: Optional[str] = "rostov"):
    """Эндпоинт карты с query-параметром /map?region=krasnodar|russia|rostov."""
    return render_dynamic_map_response(region)

@app.get("/map/{region}", response_model=None)
def get_map_path(region: str):
    """Эндпоинт карты с path-параметром /map/{region}."""
    return render_dynamic_map_response(region)

@app.get("/region/{region}", response_model=None)
def get_region_path(region: str):
    """Эндпоинт карты с path-параметром /region/{region}."""
    return render_dynamic_map_response(region)

@app.get("/api/region/context", response_model=None)
def api_get_region_context(region: Optional[str] = "rostov") -> Dict[str, Any]:
    """Возвращает метаданные и настройки региона (центр, зум, файлы)."""
    info = resolve_region_info(region)
    return {"status": "ok", "context": info}

@app.get("/api/region/{region_id}/context", response_model=None)
def api_get_region_context_by_id(region_id: str) -> Dict[str, Any]:
    """Возвращает метаданные и настройки региона по path-параметру."""
    info = resolve_region_info(region_id)
    return {"status": "ok", "context": info}

@app.get("/quiz.js", response_model=None)
def get_quiz_js():
    if os.path.exists("quiz.js"):
        return FileResponse("quiz.js", media_type="application/javascript")
    raise HTTPException(status_code=404, detail="quiz.js не найден")

@app.get("/{slug}", response_model=None)
def get_slug_route(slug: str):
    """Динамический роутинг для прямых URL регионов (/krasnodar, /russia, /rostov) и HTML-страниц."""
    clean = slug.lower().strip()

    # Зарезервированные системные эндпоинты
    if clean in ["admin", "admin.html"]:
        return admin_panel()
    if clean in ["index", "index.html"]:
        return FileResponse("index.html") if os.path.exists("index.html") else render_dynamic_map_response("rostov")
    if clean == "quiz.js":
        return get_quiz_js()

    # Проверка совпадения со slug региона (например, /krasnodar, /russia, /rostov)
    if clean in REGIONS_INFO or any(clean in info.get("aliases", []) for info in REGIONS_INFO.values()):
        return render_dynamic_map_response(clean)

    # Проверка прямого вызова .html файлов
    if clean.endswith(".html"):
        if os.path.exists(clean):
            if "_quiz_map" in clean:
                return render_dynamic_map_response(clean)
            return FileResponse(clean)
    else:
        candidate_map = f"{clean}_quiz_map.html"
        if os.path.exists(candidate_map):
            return render_dynamic_map_response(clean)
        candidate_html = f"{clean}.html"
        if os.path.exists(candidate_html):
            return FileResponse(candidate_html)

    raise HTTPException(status_code=404, detail=f"Страница или регион '{slug}' не найден")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)