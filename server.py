from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import zipfile
import tempfile
import asyncio
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
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
import math
import collections
import hashlib
import base64
import threading
import urllib.request
import urllib.error
import urllib.parse
import db
import auth_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db.init_db()
db.migrate_legacy_json(BASE_DIR)
db.load_teachers_db()

# Centralized feature flag: set RUSSIA_MAP_ENABLED = True (or env RUSSIA_MAP_ENABLED=true)
# to re-enable the Russian Federation map and its UI/API surface.
RUSSIA_MAP_ENABLED = False
if os.environ.get("RUSSIA_MAP_ENABLED", "").strip().lower() in ("1", "true", "yes", "on"):
    RUSSIA_MAP_ENABLED = True

_RUSSIA_UNAVAILABLE_MSG = "Карта России временно находится в разработке. Скоро она станет доступна."
_RUSSIA_EXACT_TOKENS = {
    "russia",
    "russia_quiz_map",
    "russia_meta",
    "rf",
    "rus",
    "россия",
    "рф",
    "российская федерация",
}


def is_russia_map_target(value: Optional[str]) -> bool:
    """Returns True if a route, region id, filename, or query refers to the Russian Federation map."""
    if not value:
        return False
    decoded = urllib.parse.unquote(str(value)).strip().lower()
    path_only = decoded.split("?", 1)[0].replace("\\", "/").rstrip("/")
    basename = os.path.basename(path_only)
    if basename in ("russia_quiz_map.html", "russia_meta.json"):
        return True
    stem = basename
    for suffix in ("_quiz_map.html", "_meta.json", ".html", ".json"):
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    return stem in _RUSSIA_EXACT_TOKENS or path_only.strip("/") in _RUSSIA_EXACT_TOKENS


def render_russia_unavailable_page(status_code: int = 503) -> HTMLResponse:
    """Renders a user-friendly status page when the Russia map is temporarily disabled."""
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoAtlas — Карта России в разработке</title>
    <script src="/public/theme.js"></script>
    <style>
        :root {{
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --border: #E2E8F0;
            --text-main: #0F172A;
            --text-muted: #475569;
            --primary: #2563EB;
            --primary-hover: #1D4ED8;
        }}
        [data-theme="dark"] {{
            --bg: #0B1120;
            --surface: #111C33;
            --border: #1E293B;
            --text-main: #F8FAFC;
            --text-muted: #CBD5E1;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            background: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .notice-card {{
            max-width: 560px;
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 36px 32px;
            text-align: center;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.14);
        }}
        .notice-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 999px;
            background: rgba(245, 158, 11, 0.14);
            color: #D97706;
            border: 1px solid rgba(245, 158, 11, 0.35);
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 16px;
        }}
        [data-theme="dark"] .notice-badge {{ color: #FBBF24; }}
        h1 {{
            margin: 0 0 12px 0;
            font-size: 23px;
            line-height: 1.3;
            font-weight: 800;
        }}
        p {{
            margin: 0 0 24px 0;
            font-size: 14.5px;
            line-height: 1.55;
            color: var(--text-muted);
        }}
        .notice-actions {{
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .btn-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 11px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.15s ease;
        }}
        .btn-primary-link {{
            background: var(--primary);
            color: #FFFFFF;
        }}
        .btn-primary-link:hover {{ background: var(--primary-hover); }}
        .btn-secondary-link {{
            background: transparent;
            color: var(--text-main);
            border: 1px solid var(--border);
        }}
    </style>
</head>
<body>
    <main class="notice-card" role="main">
        <div class="notice-badge">🛠️ Временное ограничение доступа</div>
        <h1>{_RUSSIA_UNAVAILABLE_MSG}</h1>
        <p>Раздел общероссийской карты проходит академическую и картографическую доработку совместно с научным руководителем. Все карты субъектов РФ и режим дуэлей работают в штатном режиме.</p>
        <div class="notice-actions">
            <a href="/" class="btn-link btn-primary-link">← Вернуться на главную</a>
            <a href="/map/rostov" class="btn-link btn-secondary-link">🗺️ Открыть карту Ростовской области</a>
        </div>
    </main>
</body>
</html>"""
    return HTMLResponse(
        content=html,
        status_code=status_code,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


def apply_feature_flags_to_html(html: str, russia_enabled: bool) -> str:
    """Applies server feature flags cleanly into HTML responses and embeds runtime JS config."""
    if not russia_enabled:
        html = re.sub(
            r'<!--\s*RUSSIA_MAP_FEATURE_START\s*-->[\s\S]*?<!--\s*RUSSIA_MAP_FEATURE_END\s*-->',
            '',
            html,
        )
        html = re.sub(
            r'/\*\s*RUSSIA_MAP_FEATURE_START\s*\*/[\s\S]*?/\*\s*RUSSIA_MAP_FEATURE_END\s*\*/',
            '',
            html,
        )
    flags_json = json.dumps({"russia_map_enabled": bool(russia_enabled)})
    flags_tag = f'<script id="geoatlas-feature-flags">window.GEOATLAS_FEATURES = {flags_json};</script>'
    html = re.sub(r'<script id="geoatlas-feature-flags">[\s\S]*?</script>', '', html)
    if "</head>" in html:
        html = html.replace("</head>", f"{flags_tag}\n</head>", 1)
    else:
        html = f"{flags_tag}\n{html}"
    return html


def _should_count_page_visit(request: Optional[Request]) -> bool:
    """Counts genuine GET openings of the home page, excluding prefetch/SW background requests."""
    if request is None:
        return True
    if request.method != "GET":
        return False
    sec_purpose = (request.headers.get("sec-purpose") or "").lower()
    purpose = (request.headers.get("purpose") or "").lower()
    if "prefetch" in sec_purpose or purpose == "prefetch":
        return False
    if request.headers.get("x-sw-precache"):
        return False
    return True


def render_index_page(request: Optional[Request] = None, increment_visits: bool = True) -> Response:
    index_path = os.path.join(BASE_DIR, "index.html")
    if not os.path.exists(index_path):
        return render_dynamic_map_response("rostov")
    if increment_visits and _should_count_page_visit(request):
        try:
            db.increment_site_stat("site_visits")
        except Exception as e:
            logger.warning("Не удалось обновить счётчик посещений: %s", e)
    with open(index_path, "r", encoding="utf-8") as f:
        html = apply_feature_flags_to_html(f.read(), RUSSIA_MAP_ENABLED)
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 3
_rate_limit_store = collections.defaultdict(lambda: collections.deque(maxlen=RATE_LIMIT_MAX))

def check_rate_limit(key: str) -> bool:
    now = time.time()
    dq = _rate_limit_store[key]
    if len(dq) == RATE_LIMIT_MAX and now - dq[0] < RATE_LIMIT_WINDOW:
        return False
    dq.append(now)
    return True

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

logger = logging.getLogger("geoatlas")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    db.migrate_legacy_json(BASE_DIR)
    load_duel_rooms_from_disk()
    yield

app = FastAPI(title="GeoAtlas — Учебно-картографический атлас ЮФУ (Ростов, Краснодар, Россия)", lifespan=lifespan)
security = HTTPBasic()
security_optional = HTTPBasic(auto_error=False)

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

def _normalize_origin(raw_url: Optional[str]) -> Optional[str]:
    if not raw_url:
        return None
    val = raw_url.strip()
    if not val or val == "*":
        return None
    try:
        parsed = urllib.parse.urlsplit(val)
    except ValueError:
        return None
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return None
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None
    host_part = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None:
        return f"{scheme}://{host_part}:{port}"
    return f"{scheme}://{host_part}"


def get_csrf_trusted_origins() -> set[str]:
    raw = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
    if not raw and os.environ.get("ENVIRONMENT", "development").strip().lower() == "production":
        raw = "https://geoatlas.sfedu.ru"
    origins: set[str] = set()
    for item in raw.split(","):
        norm = _normalize_origin(item)
        if norm:
            origins.add(norm)
    return origins


_http_metrics = {
    "started_at": time.time(),
    "api_requests": 0,
    "api_latency_sum_ms": 0.0,
    "http_4xx": 0,
    "http_5xx": 0,
}


@app.middleware("http")
async def track_http_metrics(request: Request, call_next):
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        _http_metrics["http_5xx"] += 1
        raise
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    status_code = getattr(response, "status_code", 200)
    if 400 <= status_code < 500:
        _http_metrics["http_4xx"] += 1
    elif status_code >= 500:
        _http_metrics["http_5xx"] += 1
    if request.url.path.startswith("/api/"):
        _http_metrics["api_requests"] += 1
        _http_metrics["api_latency_sum_ms"] += elapsed_ms
    return response


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        path = request.url.path
        if path.startswith("/api/"):
            origin = request.headers.get("origin", "")
            referer = request.headers.get("referer", "")
            allowed_origins = get_csrf_trusted_origins()
            if os.environ.get("ENVIRONMENT", "development").strip().lower() != "production":
                req_origin = _normalize_origin(str(request.base_url))
                if req_origin:
                    allowed_origins.add(req_origin)

            if origin:
                norm_origin = _normalize_origin(origin)
                if not norm_origin or norm_origin not in allowed_origins:
                    return JSONResponse({"detail": "CSRF protection: origin mismatch"}, status_code=403)
            elif referer:
                norm_referer = _normalize_origin(referer)
                if not norm_referer or norm_referer not in allowed_origins:
                    return JSONResponse({"detail": "CSRF protection: referer mismatch"}, status_code=403)
    return await call_next(request)

@app.middleware("http")
async def auth_and_feature_static_guard(request: Request, call_next):
    path = urllib.parse.unquote(request.url.path).lower()
    if path.startswith("/public/maps/"):
        if not RUSSIA_MAP_ENABLED and is_russia_map_target(path):
            if path.endswith(".json"):
                return JSONResponse({"detail": _RUSSIA_UNAVAILABLE_MSG}, status_code=503)
            return render_russia_unavailable_page(status_code=503)
        if get_optional_current_user(request) is None:
            if path.endswith(".json") or path.endswith(".geojson"):
                return JSONResponse({"detail": "Требуется авторизация"}, status_code=401)
            return _redirect_to_login(request)
    return await call_next(request)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # CSP: запрещает загрузку скриптов с левых доменов, но разрешает тайловые подложки и CDN-ассеты карты
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com https://code.jquery.com https://maxcdn.bootstrapcdn.com https://netdna.bootstrapcdn.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com https://netdna.bootstrapcdn.com; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com https://netdna.bootstrapcdn.com; "
        "img-src 'self' data: https://basemaps.cartocdn.com https://*.basemaps.cartocdn.com https://*.arcgisonline.com https://*.openstreetmap.org https://*.openstreetmap.fr https://*.opentopomap.org https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://maxcdn.bootstrapcdn.com https://netdna.bootstrapcdn.com; "
        "connect-src 'self' wss://geoatlas.sfedu.ru wss: ws: https://api.openrouteservice.org https://basemaps.cartocdn.com https://*.basemaps.cartocdn.com https://*.arcgisonline.com https://*.openstreetmap.org https://*.openstreetmap.fr https://*.opentopomap.org; "
        "frame-ancestors 'self';"
    )

    path = request.url.path
    if path in ("/", "/index.html", "/index", "/sw.js"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    elif path.endswith(".html") or path in ("/quiz.js", "/public/map.css", "/public/admin.css", "/public/admin.js"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response

AUTH_SESSIONS_FILE = "auth_sessions.json"
RESULTS_FILE = "quiz_results.json"
GROUPS_FILE = "groups.json"
SESSIONS_HISTORY_FILE = "sessions_history.json"

DEFAULT_BRANDING = db.DEFAULT_BRANDING

def load_auth_sessions() -> Dict[str, Any]:
    return {}

def save_auth_sessions(sessions: Dict[str, Any]) -> None:
    pass

DEFAULT_TEACHERS = db.DEFAULT_TEACHERS

def is_dean_or_admin(teacher: Dict[str, Any]) -> bool:
    return (
        teacher.get("role") in ["dean", "admin"]
        or teacher.get("username") in ["dean_geo", "admin", "sfedu_admin"]
        or teacher.get("teacher_id") in ["dean-geo", "teacher-admin", "sfedu-admin"]
    )

def load_sessions_history() -> List[Dict[str, Any]]:
    return db.load_sessions_history()

def record_session_history(session_data: Dict[str, Any]) -> None:
    db.record_session_history(session_data)

DEFAULT_GROUPS = [
    {
        "id": "grp-geofak-51",
        "name": "ИНоЗ-51 (ВКР)",
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
        "name": "ИНоЗ-41 (Бакалавриат)",
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
    full_name: str = ""
    group_num: str = ""

class VerifyRequest(BaseModel):
    email: str
    code: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    password_confirm: str
    accept_terms: bool = False
    group_num: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str
    new_password_confirm: str

class UniversityVerifyRequest(BaseModel):
    verified: bool = True

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
    is_adaptive: bool = False
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
    player_name: str = "Соперник"
    player_group: str = ""
    player_email: str = ""
    player_id: Optional[str] = None

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

SESSION_COOKIE_NAME = "geoatlas_session"
SESSION_TTL_SECONDS = 7 * 24 * 3600


def _is_safe_next_url(raw_next: Optional[str]) -> str:
    val = (raw_next or "").strip()
    if val.startswith("/") and not val.startswith("//") and "\n" not in val and "\r" not in val:
        return val
    return "/"


def _build_public_user_dict(user: Dict[str, Any]) -> Dict[str, Any]:
    uni_verified = bool(user.get("university_verified"))
    uni_email_verified = bool(user.get("university_email_verified"))
    badge = ""
    if uni_verified:
        badge = "Сообщество ЮФУ"
    elif uni_email_verified:
        badge = "Почта ЮФУ подтверждена"

    return {
        "id": user.get("id"),
        "email": user.get("email", ""),
        "name": user.get("full_name", "") or user.get("name", ""),
        "group": user.get("group", ""),
        "role": user.get("role", "student"),
        "email_verified": bool(user.get("email_verified")),
        "university_verified": uni_verified,
        "university_email_verified": uni_email_verified,
        "university_auth_provider": user.get("university_auth_provider", ""),
        "university_verified_at": user.get("university_verified_at"),
        "badge": badge,
    }


def _set_session_cookie(response: Response, raw_token: str) -> None:
    is_prod = os.environ.get("ENVIRONMENT", "").strip().lower() == "production"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        path="/",
    )


def _issue_user_session(response: Response, user: Dict[str, Any], auth_method: str = "password") -> None:
    raw_token = secrets.token_urlsafe(32)
    token_hash = auth_service.hash_token(raw_token, "session")
    db.create_user_session(token_hash, int(user["id"]), ttl_seconds=SESSION_TTL_SECONDS, auth_method=auth_method)
    db.record_auth_login_event(int(user["id"]), auth_method=auth_method)
    db.record_audit_event("login_success", actor_role=user.get("role", "student"), summary="Успешная авторизация пользователя", meta={"auth_method": auth_method})
    _set_session_cookie(response, raw_token)


def _verify_basic_teacher_header(auth_header: str) -> Optional[Dict[str, Any]]:
    if not auth_header or not auth_header.lower().startswith("basic "):
        return None
    try:
        decoded = base64.b64decode(auth_header.split(" ", 1)[1].strip()).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return None

    for t in db.load_teachers_db():
        stored_hash = t.get("password_hash", "")
        if not secrets.compare_digest(username, t.get("username", "")):
            continue
        if stored_hash and auth_service.verify_password(password, stored_hash):
            if auth_service.needs_password_upgrade(stored_hash) and t.get("teacher_id"):
                db.update_teacher_password_hash(t["teacher_id"], auth_service.hash_password(password))
            return t
    return None


def get_optional_current_user(request: Any) -> Optional[Dict[str, Any]]:
    cookies = getattr(request, "cookies", None) or {}
    raw_cookie = cookies.get(SESSION_COOKIE_NAME)
    if raw_cookie:
        token_hash = auth_service.hash_token(raw_cookie, "session")
        user = db.get_active_user_by_session_hash(token_hash)
        if user:
            return user

    headers = getattr(request, "headers", None) or {}
    auth_header = headers.get("authorization", "")
    teacher = _verify_basic_teacher_header(auth_header)
    if teacher:
        return {
            "id": None,
            "teacher_id": teacher.get("teacher_id"),
            "username": teacher.get("username"),
            "email": f"{teacher.get('username', 'teacher')}@geoatlas.local",
            "full_name": teacher.get("full_name", teacher.get("username", "Преподаватель")),
            "organization": teacher.get("organization", ""),
            "group": teacher.get("department", ""),
            "role": teacher.get("role", "teacher"),
            "email_verified": True,
            "university_verified": False,
            "university_email_verified": False,
        }
    return None


def require_authenticated_user(request: Request) -> Dict[str, Any]:
    user = get_optional_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return user


def _redirect_to_login(request: Request) -> RedirectResponse:
    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"
    safe_next = _is_safe_next_url(target)
    return RedirectResponse(
        url=f"/login?next={urllib.parse.quote(safe_next, safe='/?=&')}",
        status_code=302,
    )


def check_admin(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security_optional),
) -> Dict[str, Any]:
    if credentials:
        for t in db.load_teachers_db():
            stored_hash = t.get("password_hash", "")
            if secrets.compare_digest(credentials.username, t.get("username", "")) and stored_hash and auth_service.verify_password(credentials.password, stored_hash):
                if auth_service.needs_password_upgrade(stored_hash) and t.get("teacher_id"):
                    db.update_teacher_password_hash(t["teacher_id"], auth_service.hash_password(credentials.password))
                return t
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = get_optional_current_user(request)
    if user:
        if user.get("role") in ("teacher", "dean", "admin"):
            return user
        raise HTTPException(status_code=403, detail="Недостаточно прав для доступа к разделу преподавателя")

    raise HTTPException(
        status_code=401,
        detail="Неверный логин или пароль",
        headers={"WWW-Authenticate": "Basic"},
    )


def check_admin_optional(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security_optional),
) -> Optional[Dict[str, Any]]:
    try:
        return check_admin(request, credentials)
    except HTTPException:
        return None


def _render_auth_page() -> HTMLResponse:
    auth_path = os.path.join(BASE_DIR, "auth.html")
    if os.path.exists(auth_path):
        with open(auth_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return HTMLResponse("<h1>Вход в GeoAtlas</h1>", status_code=200)


@app.get("/login", response_class=HTMLResponse, response_model=None)
@app.get("/register", response_class=HTMLResponse, response_model=None)
@app.get("/forgot-password", response_class=HTMLResponse, response_model=None)
@app.get("/reset-password", response_class=HTMLResponse, response_model=None)
def auth_pages():
    return _render_auth_page()


@app.get("/dictionary", response_class=HTMLResponse, response_model=None)
@app.get("/dictionary/{slug}", response_class=HTMLResponse, response_model=None)
def dictionary_pages(slug: Optional[str] = None):
    dict_html = os.path.join(BASE_DIR, "dictionary.html")
    if os.path.exists(dict_html):
        with open(dict_html, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), headers={"Cache-Control": "no-cache, must-revalidate"})
    return HTMLResponse("<h1>Географический словарь</h1>", status_code=200)


@app.get("/api/dictionary")
def get_dictionary_api() -> Response:
    dict_path = os.path.join(BASE_DIR, "public", "dictionary.json")
    if not os.path.exists(dict_path):
        raise HTTPException(status_code=404, detail="База географического словаря не найдена")
    return FileResponse(dict_path, media_type="application/json; charset=utf-8")


@app.get("/api/auth/config")
def get_auth_public_config() -> Dict[str, Any]:
    oidc = auth_service.get_oidc_config()
    return {
        "status": "ok",
        "oidc_enabled": oidc["enabled"],
        "oidc_provider_label": "Войти через аккаунт ЮФУ",
        "trusted_university_domains": auth_service.get_trusted_university_domains(),
        "min_password_length": 8,
    }


@app.get("/api/auth/me")
def get_current_user_me(user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    return {"status": "ok", "authenticated": True, "user": _build_public_user_dict(user)}


@app.post("/api/auth/register")
def register_account(req: RegisterRequest, request: Request) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    email = auth_service.normalize_email(req.email)
    if not check_rate_limit(f"reg:{client_ip}") or not check_rate_limit(f"reg:{email}"):
        raise HTTPException(status_code=429, detail="Слишком много запросов. Подождите минуту.")

    if not auth_service.is_valid_email(email):
        raise HTTPException(status_code=400, detail="Введите корректный адрес электронной почты.")
    if not req.full_name.strip():
        raise HTTPException(status_code=400, detail="Укажите имя пользователя.")
    pw_err = auth_service.validate_password_strength(req.password)
    if pw_err:
        raise HTTPException(status_code=400, detail=pw_err)
    if req.password != req.password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают.")
    if not req.accept_terms:
        raise HTTPException(status_code=400, detail="Необходимо согласиться с условиями использования и политикой обработки данных.")

    pw_hash = auth_service.hash_password(req.password)
    _, already_verified = db.upsert_pending_registration_user(
        email=email,
        full_name=req.full_name.strip(),
        password_hash=pw_hash,
        grp=req.group_num.strip(),
    )

    generic_msg = "Если указанный адрес доступен для регистрации, мы отправили на него 6-значный код подтверждения."
    if already_verified:
        return {"status": "ok", "message": generic_msg}

    code = f"{secrets.randbelow(900000) + 100000}"
    code_hash = auth_service.hash_token(code, f"register:{email}")
    created, retry_after = db.create_email_verification_code(email, "register", code_hash, ttl_seconds=600, resend_cooldown=60)
    if not created:
        raise HTTPException(status_code=429, detail=f"Повторная отправка доступна через {retry_after} сек.")

    try:
        auth_service.send_auth_email(email, code, "register", full_name=req.full_name.strip())
    except auth_service.EmailNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except auth_service.EmailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    db.record_audit_event("user_register", actor_role="student", summary="Регистрация нового пользователя")
    return {"status": "ok", "message": generic_msg}


@app.post("/api/auth/send-code")
def send_code(req: AuthRequest, request: Request) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    email = auth_service.normalize_email(req.email)
    if not check_rate_limit(f"send:{client_ip}") or not check_rate_limit(f"send:{email}"):
        raise HTTPException(status_code=429, detail="Слишком много запросов. Подождите минуту.")
    if not auth_service.is_valid_email(email):
        raise HTTPException(status_code=400, detail="Введите корректный адрес электронной почты.")

    code = f"{secrets.randbelow(900000) + 100000}"
    code_hash = auth_service.hash_token(code, f"register:{email}")
    created, retry_after = db.create_email_verification_code(email, "register", code_hash, ttl_seconds=600, resend_cooldown=60)
    if not created:
        raise HTTPException(status_code=429, detail=f"Повторная отправка кода возможна через {retry_after} сек.")

    # Create pending unverified user if none exists yet (legacy send-code compatibility)
    if not db.get_user_by_email(email):
        db.upsert_pending_registration_user(
            email=email,
            full_name=req.full_name.strip() or email.split("@", 1)[0],
            password_hash="",
            grp=req.group_num.strip(),
        )

    try:
        auth_service.send_auth_email(email, code, "register", full_name=req.full_name.strip())
    except auth_service.EmailNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except auth_service.EmailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {"status": "ok", "message": "Код подтверждения отправлен на указанную почту."}


@app.post("/api/auth/verify-code")
def verify_code(req: VerifyRequest, request: Request, response: Response) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"verify:{client_ip}"):
        raise HTTPException(status_code=429, detail="Слишком много попыток ввода кода. Подождите минуту.")

    email = auth_service.normalize_email(req.email)
    candidate_hash = auth_service.hash_token(req.code.strip(), f"register:{email}")
    ok, msg = db.verify_email_code_atomic(email, "register", candidate_hash)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    is_uni_email = auth_service.is_trusted_university_email(email)
    user = db.mark_user_email_verified(email, university_email_verified=is_uni_email)
    if not user:
        user, _ = db.upsert_pending_registration_user(email=email, full_name=email.split("@", 1)[0], password_hash="")
        user = db.mark_user_email_verified(email, university_email_verified=is_uni_email)

    _issue_user_session(response, user, auth_method="email_code")
    db.record_audit_event("email_verified", actor_role=user.get("role", "student"), summary="Подтверждение электронной почты")
    return {"status": "ok", "user": _build_public_user_dict(user)}


@app.post("/api/auth/login")
def login_account(req: LoginRequest, request: Request, response: Response) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    identifier = auth_service.normalize_email(req.email)
    if not check_rate_limit(f"login:{client_ip}") or not check_rate_limit(f"login:{identifier}"):
        raise HTTPException(status_code=429, detail="Слишком много попыток входа. Подождите минуту.")

    user = db.get_user_by_email(identifier)
    if user and user.get("password_hash") and auth_service.verify_password(req.password, user["password_hash"]):
        if not user.get("email_verified"):
            return JSONResponse(
                status_code=403,
                content={"detail": "Электронная почта ещё не подтверждена. Введите код из письма.", "needs_verification": True},
            )
        if auth_service.needs_password_upgrade(user["password_hash"]):
            db.update_user_password(int(user["id"]), auth_service.hash_password(req.password))
        _issue_user_session(response, user, auth_method="password")
        return {"status": "ok", "user": _build_public_user_dict(user)}

    # Teacher / admin fallback login via username
    for t in db.load_teachers_db():
        stored_hash = t.get("password_hash", "")
        if secrets.compare_digest(req.email.strip(), t.get("username", "")) and stored_hash and auth_service.verify_password(req.password, stored_hash):
            if auth_service.needs_password_upgrade(stored_hash) and t.get("teacher_id"):
                db.update_teacher_password_hash(t["teacher_id"], auth_service.hash_password(req.password))
            teacher_email = f"{t['username'].lower()}@geoatlas.local"
            existing_u = db.get_user_by_email(teacher_email)
            if not existing_u:
                existing_u, _ = db.upsert_pending_registration_user(
                    email=teacher_email,
                    full_name=t.get("full_name", t["username"]),
                    password_hash=auth_service.hash_password(req.password),
                    grp=t.get("department", ""),
                )
                existing_u = db.mark_user_email_verified(teacher_email, university_email_verified=False)
                # Preserve explicit role from teachers table
                with db._lock:
                    conn = db._conn()
                    try:
                        conn.execute("UPDATE users SET role = ? WHERE id = ?", (t.get("role", "teacher"), existing_u["id"]))
                        conn.commit()
                    finally:
                        conn.close()
                existing_u = db.get_user_by_id(int(existing_u["id"]))
            elif existing_u.get("role") == "student" and t.get("role") in ("teacher", "dean", "admin"):
                with db._lock:
                    conn = db._conn()
                    try:
                        conn.execute("UPDATE users SET role = ? WHERE id = ?", (t["role"], existing_u["id"]))
                        conn.commit()
                    finally:
                        conn.close()
                existing_u = db.get_user_by_id(int(existing_u["id"]))
            _issue_user_session(response, existing_u, auth_method="password")
            return {"status": "ok", "user": _build_public_user_dict(existing_u)}

    raise HTTPException(status_code=401, detail="Неверный email или пароль.")


@app.post("/api/auth/logout")
def logout_account(request: Request, response: Response) -> Dict[str, str]:
    raw_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_cookie:
        token_hash = auth_service.hash_token(raw_cookie, "session")
        db.revoke_session_by_hash(token_hash)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request) -> Dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    email = auth_service.normalize_email(req.email)
    if not check_rate_limit(f"forgot:{client_ip}") or not check_rate_limit(f"forgot:{email}"):
        raise HTTPException(status_code=429, detail="Слишком много запросов. Подождите минуту.")
    if not auth_service.is_valid_email(email):
        raise HTTPException(status_code=400, detail="Введите корректный адрес электронной почты.")

    generic_msg = "Если аккаунт с таким адресом существует, мы отправили одноразовый код для сброса пароля."
    user = db.get_user_by_email(email)
    if not user or not user.get("email_verified"):
        return {"status": "ok", "message": generic_msg}

    code = f"{secrets.randbelow(900000) + 100000}"
    code_hash = auth_service.hash_token(code, f"password_reset:{email}")
    created, retry_after = db.create_email_verification_code(email, "password_reset", code_hash, ttl_seconds=600, resend_cooldown=60)
    if not created:
        raise HTTPException(status_code=429, detail=f"Повторная отправка доступна через {retry_after} сек.")

    try:
        auth_service.send_auth_email(email, code, "password_reset", full_name=user.get("full_name", ""))
    except auth_service.EmailNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except auth_service.EmailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    db.record_audit_event("user_register", actor_role="student", summary="Регистрация нового пользователя")
    return {"status": "ok", "message": generic_msg}


@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordRequest, request: Request) -> Dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"reset:{client_ip}"):
        raise HTTPException(status_code=429, detail="Слишком много попыток. Подождите минуту.")

    pw_err = auth_service.validate_password_strength(req.new_password)
    if pw_err:
        raise HTTPException(status_code=400, detail=pw_err)
    if req.new_password != req.new_password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают.")

    email = auth_service.normalize_email(req.email)
    candidate_hash = auth_service.hash_token(req.code.strip(), f"password_reset:{email}")
    ok, msg = db.verify_email_code_atomic(email, "password_reset", candidate_hash)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="Не удалось обновить пароль.")

    db.update_user_password(int(user["id"]), auth_service.hash_password(req.new_password))
    db.revoke_all_user_sessions(int(user["id"]))
    return {"status": "ok", "message": "Пароль успешно изменён. Все прежние сессии завершены."}


@app.get("/api/auth/oidc/login")
def oidc_login(next: str = "/"):
    cfg = auth_service.get_oidc_config()
    if not cfg["enabled"]:
        raise HTTPException(status_code=503, detail="Университетская авторизация ЮФУ (OIDC) пока не настроена.")

    disc = auth_service.fetch_oidc_discovery(cfg["issuer"])
    auth_endpoint = disc.get("authorization_endpoint")
    if not auth_endpoint:
        raise HTTPException(status_code=502, detail="Не удалось получить authorization_endpoint провайдера OIDC.")

    raw_state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier, code_challenge = auth_service.build_oidc_pkce_pair()
    db.save_oidc_state(auth_service.hash_token(raw_state, "oidc_state"), nonce, code_verifier, _is_safe_next_url(next))

    params = urllib.parse.urlencode({
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "scope": "openid profile email",
        "state": raw_state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    sep = "&" if "?" in auth_endpoint else "?"
    return RedirectResponse(url=f"{auth_endpoint}{sep}{params}", status_code=302)


@app.get("/api/auth/oidc/callback")
def oidc_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    cfg = auth_service.get_oidc_config()
    if not cfg["enabled"]:
        raise HTTPException(status_code=503, detail="Университетская авторизация ЮФУ (OIDC) отключена.")
    if error:
        return RedirectResponse(url=f"/login?error={urllib.parse.quote('Ошибка университетской авторизации')}", status_code=302)
    if not code or not state:
        raise HTTPException(status_code=400, detail="Отсутствуют обязательные параметры OIDC callback.")

    saved_state = db.pop_oidc_state(auth_service.hash_token(state, "oidc_state"))
    if not saved_state:
        raise HTTPException(status_code=400, detail="Недействительный или просроченный OIDC state.")

    disc = auth_service.fetch_oidc_discovery(cfg["issuer"])
    token_endpoint = disc.get("token_endpoint")
    if not token_endpoint:
        raise HTTPException(status_code=502, detail="Не найден token_endpoint провайдера OIDC.")

    token_resp = auth_service._http_post_form_json(
        token_endpoint,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg["redirect_uri"],
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "code_verifier": saved_state["code_verifier"],
        },
    )
    id_token = token_resp.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="Провайдер OIDC не вернул ID token.")

    try:
        claims = auth_service.verify_oidc_id_token(
            id_token=id_token,
            expected_nonce=saved_state["nonce"],
            cfg=cfg,
            jwks_uri=disc.get("jwks_uri"),
        )
    except auth_service.OIDCVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    email = auth_service.normalize_email(claims.get("email") or claims.get("preferred_username"))
    full_name = str(claims.get("name") or email.split("@", 1)[0]).strip()
    user = db.upsert_oidc_user(
        email=email,
        full_name=full_name,
        issuer=cfg["issuer"],
        subject=str(claims["sub"]),
        university_verified=True,
    )
    resp = RedirectResponse(url=_is_safe_next_url(saved_state.get("next_url")), status_code=302)
    _issue_user_session(resp, user, auth_method="oidc")
    return resp


@app.post("/api/admin/users/{user_id}/university-verify")
def admin_verify_university_user(
    user_id: int,
    req: UniversityVerifyRequest,
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    updated = db.set_user_university_verified(user_id, req.verified, provider="admin")
    if not updated:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"status": "ok", "user": _build_public_user_dict(updated)}

def process_quiz_result(res: ResultSubmit) -> Dict[str, Any]:
    assigned_teacher_id = res.teacher_id or "teacher-geo-01"

    if res.session_id:
        active_sess = db.load_active_session_db()
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
        "is_adaptive": bool(res.is_adaptive),
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
def save_quiz_result(res: ResultSubmit, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    if user.get("role") == "student" and user.get("email"):
        res.email = user["email"]
        res.name = user.get("full_name") or res.name
    outcome = process_quiz_result(res)
    if not outcome.get("deduplicated", False):
        db.record_audit_event(
            "test_completed",
            actor_role=user.get("role", "student"),
            summary=f"Завершён тест ({res.quiz_type or 'map'})",
            meta={"quiz_type": res.quiz_type, "accuracy": res.accuracy},
        )
    return {"status": "ok", "deduplicated": outcome.get("deduplicated", False)}

@app.post("/api/results/sync-batch")
def sync_batch_results(req: SyncBatchRequest, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    synced = 0
    duplicates = 0
    for item in req.items:
        if user.get("role") == "student" and user.get("email"):
            item.email = user["email"]
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
def get_leaderboard(user: Dict[str, Any] = Depends(require_authenticated_user)) -> List[Dict[str, Any]]:
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


def _load_cached_quality_report() -> Optional[Dict[str, Any]]:
    """Loads a pre-generated Data Monitor JSON report if available on disk."""
    candidates = [
        os.path.join(os.environ.get("GEOATLAS_DATA_DIR") or os.path.join(BASE_DIR, "data"), "quality_report.json"),
        os.path.join(BASE_DIR, "quality_report.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "datasets" in data and "summary" in data:
                    data.setdefault("monitor_available", True)
                    data["from_cached_report"] = True
                    return data
            except Exception:
                continue
    return None


def _import_geodata_monitor():
    """Lazy import of geodata_monitor so main app startup never fails on geo/numpy errors."""
    import importlib
    return importlib.import_module("geodata_monitor")


@app.get("/api/admin/user-analytics")
def get_admin_user_analytics(
    days: int = 30,
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    data = db.get_user_analytics_stats(days=days)
    duel_rooms = list(active_duel_rooms.values())
    finished_duels = sum(1 for r in duel_rooms if getattr(r, "status", "") == "finished")
    data["platform"]["duels_total"] = len(duel_rooms)
    data["platform"]["duels_finished"] = finished_duels
    data["platform"]["duels_note"] = "Активные и сохранённые комнаты дуэлей (duel_rooms.json)"
    return data


class TelemetryEventRequest(BaseModel):
    event_type: str
    target: str = ""


_ALLOWED_TELEMETRY_TYPES = {"map_open", "passport_open", "layer_toggle", "quiz_start"}


@app.post("/api/telemetry/event")
def post_telemetry_event(req: TelemetryEventRequest, request: Request) -> Dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"telemetry:{client_ip}"):
        return {"status": "rate_limited"}
    et = (req.event_type or "").strip()
    if et not in _ALLOWED_TELEMETRY_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимый тип события телеметрии")
    db.record_telemetry_event(et, target=(req.target or "").strip())
    return {"status": "ok"}


def _build_duel_analytics(days: str = "30") -> Dict[str, Any]:
    from datetime import datetime, timedelta
    msk = db._moscow_tz()
    today_msk = datetime.now(msk).date()
    raw_days = str(days or "30").strip().lower()
    if raw_days == "all":
        start_ts = None
    else:
        num = int(raw_days) if raw_days in ("7", "30", "90") else 30
        start_d = today_msk - timedelta(days=num - 1)
        start_ts = datetime(start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=msk).timestamp()

    rooms = list(active_duel_rooms.values())
    if start_ts is not None:
        rooms = [r for r in rooms if getattr(r, "created_at", 0) >= start_ts]

    created_count = len(rooms)
    finished_rooms = [r for r in rooms if getattr(r, "status", "") == "finished"]
    finished_count = len(finished_rooms)
    center_count = sum(1 for r in rooms if getattr(r, "mode", "") == "center")
    puzzle_count = sum(1 for r in rooms if getattr(r, "mode", "") == "puzzle")
    participants = set()
    durations = []
    daily_map: Dict[str, Dict[str, int]] = {}

    for r in rooms:
        for pid in (getattr(r, "players", None) or {}).keys():
            participants.add(pid)
        c_ts = getattr(r, "created_at", None)
        if c_ts:
            d_str = datetime.fromtimestamp(float(c_ts), tz=msk).strftime("%Y-%m-%d")
            bucket = daily_map.setdefault(d_str, {"created": 0, "finished": 0})
            bucket["created"] += 1
            if getattr(r, "status", "") == "finished":
                bucket["finished"] += 1
        st = getattr(r, "start_time", None)
        et = getattr(r, "end_time", None)
        if st and et and et >= st:
            durations.append(float(et - st))

    avg_duration_sec = round(sum(durations) / len(durations), 1) if durations else None
    daily_series = [
        {"date": d, "created": v["created"], "finished": v["finished"]}
        for d, v in sorted(daily_map.items())
    ]
    return {
        "duels_created": created_count,
        "duels_finished": finished_count,
        "center_count": center_count,
        "puzzle_count": puzzle_count,
        "unique_participants": len(participants),
        "avg_duration_sec": avg_duration_sec,
        "daily": daily_series,
        "note": "Данные сформированы по активным и сохранённым комнатам дуэлей (duel_rooms.json).",
    }


@app.get("/api/admin/usage-analytics")
def get_admin_usage_analytics(
    days: str = "30",
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    data = db.get_geoatlas_usage_analytics(days=days)
    data["duels"] = _build_duel_analytics(days=days)
    return data


@app.get("/api/admin/system-health")
def get_admin_system_health(
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    db_ok = False
    db_integrity = "unknown"
    db_size_bytes = 0
    try:
        if os.path.exists(db.DB_FILE):
            db_size_bytes = os.path.getsize(db.DB_FILE)
        conn = db._conn()
        try:
            conn.execute("SELECT 1").fetchone()
            qc = conn.execute("PRAGMA quick_check").fetchone()
            db_integrity = str(qc[0]) if qc else "ok"
            db_ok = True
        finally:
            conn.close()
    except Exception as exc:
        db_integrity = f"error: {type(exc).__name__}"

    geodata_ok = os.path.isfile(os.path.join(BASE_DIR, "public", "maps", "rostov_passports.json"))
    backup_dir = os.path.join(os.path.dirname(db.DB_FILE), "backups")
    backups: List[str] = []
    if os.path.isdir(backup_dir):
        backups = sorted([f for f in os.listdir(backup_dir) if not f.startswith(".")])[-5:]

    api_reqs = _http_metrics["api_requests"]
    avg_latency = round(_http_metrics["api_latency_sum_ms"] / api_reqs, 2) if api_reqs > 0 else 0.0
    return {
        "app_status": "ok" if db_ok else "degraded",
        "uptime_seconds": int(time.time() - _http_metrics["started_at"]),
        "avg_api_response_ms": avg_latency,
        "api_requests_count": api_reqs,
        "http_4xx": _http_metrics["http_4xx"],
        "http_5xx": _http_metrics["http_5xx"],
        "sqlite_size_bytes": db_size_bytes,
        "sqlite_ok": db_ok,
        "sqlite_integrity": db_integrity,
        "geodata_available": geodata_ok,
        "backups_detected": len(backups),
        "backup_files": backups,
        "backup_note": "Резервные копии в каталоге backups не обнаружены (управляются на уровне хоста/volume)." if not backups else "Обнаружены локальные резервные копии.",
        "host_metrics_note": "Системные метрики диска и RAM хоста недоступны из изолированного контейнера и не имитируются.",
    }


@app.get("/api/admin/audit-log")
def get_admin_audit_log(
    event_type: str = "all",
    days: str = "30",
    limit: int = 100,
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    return db.get_audit_log(event_type=event_type, days=days, limit=limit)


def _build_minimal_xlsx(rows: List[List[Any]]) -> bytes:
    """Builds a valid minimal .xlsx workbook in memory using stdlib zipfile + XML."""
    import xml.sax.saxutils as saxutils

    def _col_letter(idx: int) -> str:
        res = ""
        n = idx + 1
        while n > 0:
            n, rem = divmod(n - 1, 26)
            res = chr(65 + rem) + res
        return res

    sheet_rows_xml = []
    for r_idx, row in enumerate(rows, start=1):
        cells_xml = []
        for c_idx, val in enumerate(row):
            ref = f"{_col_letter(c_idx)}{r_idx}"
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                cells_xml.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                esc = saxutils.escape("" if val is None else str(val))
                cells_xml.append(f'<c r="{ref}" t="inlineStr"><is><t>{esc}</t></is></c>')
        sheet_rows_xml.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows_xml)}</sheetData>'
        '</worksheet>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-officedocument.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    wb_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="GeoAtlas Analytics" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", wb_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buf.getvalue()


@app.get("/api/admin/analytics-export")
def export_admin_analytics(
    format: str = "csv",
    days: str = "30",
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Response:
    u_stats = db.get_user_analytics_stats(days=30 if days == "all" else int(days) if days in ("7", "30", "90") else 30)
    l_stats = db.get_auth_login_analytics(days=days)
    usage = db.get_geoatlas_usage_analytics(days=days)
    duels = _build_duel_analytics(days=days)

    u = u_stats["users"]
    ls = l_stats["summary"]
    lr = usage["learning"]
    mp = usage["maps"]

    rows: List[List[Any]] = [
        ["Категория", "Показатель", "Значение"],
        ["Пользователи", "Всего зарегистрировано", u["total"]],
        ["Пользователи", "Подтверждённые email", u["verified"]],
        ["Пользователи", "Неподтверждённые email", u["unverified"]],
        ["Пользователи", "Регистрации сегодня", u["registrations_today"]],
        ["Пользователи", "Регистрации за 7 дней", u["registrations_7d"]],
        ["Пользователи", "Регистрации за 30 дней", u["registrations_30d"]],
        ["Авторизации", "Всего успешных входов", ls["total_logins"]],
        ["Авторизации", "Уникальных пользователей", ls["unique_users"]],
        ["Авторизации", "Повторных входов", ls["repeat_logins"]],
        ["Авторизации", "DAU / WAU / MAU", f"{ls['dau']} / {ls['wau']} / {ls['mau']}"],
        ["Авторизации", "Возвращаемость (%)", ls["returning_rate_pct"]],
        ["Карты", "Открытий карт (телеметрия)", mp["total_map_opens"]],
        ["Карты", "Открытий паспортов (телеметрия)", mp["total_passport_opens"]],
        ["Карты", "Переключений слоёв", mp["total_layer_toggles"]],
        ["Обучение", "Завершённых тестов", lr["completed_tests"]],
        ["Обучение", "Средний балл", lr["avg_score"]],
        ["Обучение", "Процент правильных ответов (%)", lr["correct_answers_pct"]],
        ["Дуэли", "Создано дуэлей", duels["duels_created"]],
        ["Дуэли", "Завершено дуэлей", duels["duels_finished"]],
        ["Дуэли", "Режим Center / Puzzle", f"{duels['center_count']} / {duels['puzzle_count']}"],
    ]

    fmt = (format or "csv").strip().lower()
    if fmt == "xlsx":
        xlsx_bytes = _build_minimal_xlsx(rows)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="geoatlas_analytics.xlsx"'},
        )

    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")
    for r in rows:
        writer.writerow(r)
    csv_bytes = ("\ufeff" + out.getvalue()).encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="geoatlas_analytics.csv"'},
    )


@app.get("/api/admin/login-analytics")
def get_admin_login_analytics(
    days: str = "30",
    date: Optional[str] = None,
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    return db.get_auth_login_analytics(days=days, target_date=date)


@app.get("/api/admin/data-quality")
def get_admin_data_quality(
    check_remote: bool = False,
    teacher: Dict[str, Any] = Depends(check_admin),
) -> Dict[str, Any]:
    try:
        gm = _import_geodata_monitor()
        report = gm.build_quality_report(check_remote=check_remote)
        report.setdefault("monitor_available", True)
        return report
    except Exception as exc:
        cached = _load_cached_quality_report()
        if cached is not None:
            cached["monitor_warning"] = f"Живая проверка недоступна ({type(exc).__name__}), показан сохранённый отчёт."
            return cached
        return {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "check_remote": bool(check_remote),
            "monitor_available": False,
            "message": f"Модуль мониторинга геоданных (Data Monitor) недоступен: {type(exc).__name__}: {exc}",
            "summary": {
                "total_datasets": 0,
                "passed": 0,
                "warned": 0,
                "failed": 0,
                "stale": 0,
                "unknown": 0,
                "overall_status": "unavailable",
            },
            "datasets": [],
        }


@app.get("/api/data-sources")
def get_public_data_sources() -> Dict[str, Any]:
    try:
        gm = _import_geodata_monitor()
        return gm.get_public_sources_summary()
    except Exception as exc:
        cached = _load_cached_quality_report()
        if cached is not None:
            sources = [
                {
                    "name": ds.get("name"),
                    "region": ds.get("region"),
                    "source": ds.get("source"),
                    "license": ds.get("license"),
                    "updated_at": ds.get("generated_at") or ds.get("published_at") or ds.get("last_downloaded_at"),
                }
                for ds in cached.get("datasets", [])
                if ds.get("kind") in ("passport_json", "shapefile")
            ]
            return {"sources": sources}
        return {"sources": [], "monitor_available": False, "message": f"Data Monitor недоступен: {type(exc).__name__}"}


@app.get("/api/passports/demo")
def get_passport_demo_district() -> Dict[str, Any]:
    """Public demo slice (Azovsky district 60601000) from real rostov_passports.json for the homepage showcase."""
    passports_file = os.path.join(BASE_DIR, "public", "maps", "rostov_passports.json")
    if not os.path.exists(passports_file):
        raise HTTPException(status_code=404, detail="Демонстрационный набор паспортов не найден")
    try:
        with open(passports_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения набора паспортов: {exc}")

    territories = payload.get("territories") or {}
    territory = territories.get("60601000") or next(iter(territories.values()), None)
    if not territory:
        raise HTTPException(status_code=404, detail="Территория для демонстрации не найдена")

    meta = payload.get("metadata") or {}
    return {
        "territory": territory,
        "metadata": {
            "dataset_version": meta.get("dataset_version"),
            "updated_at": meta.get("updated_at"),
            "license": meta.get("license"),
            "attribution": meta.get("attribution"),
            "indicators": meta.get("indicators"),
        },
    }

@app.get("/api/server-time")
def get_server_time() -> Dict[str, int]:
    return {"server_time": int(time.time() * 1000)}

@app.post("/api/exam/launch")
def launch_exam_session(req: LaunchSessionRequest, teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, Any]:
    if not RUSSIA_MAP_ENABLED and (is_russia_map_target(req.mapUrl) or is_russia_map_target(req.regionName)):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
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
    db.save_active_session_db(session_data)
    record_session_history(session_data)
    return {"status": "ok", "session": session_data, "server_time": now_ms}

@app.get("/api/exam/active-session")
def get_active_exam_session(
    request: Request,
    user: Dict[str, Any] = Depends(require_authenticated_user),
    teacher: Optional[Dict[str, Any]] = Depends(check_admin_optional),
) -> Dict[str, Any]:
    session = db.load_active_session_db()
    now_ms = int(time.time() * 1000)
    if not session or session.get("status") in ["stopped", "completed"]:
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}
    if not RUSSIA_MAP_ENABLED and (is_russia_map_target(session.get("map_url")) or is_russia_map_target(session.get("region_name"))):
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}
    
    # Преподавателю показываем только его сессию (декану / суперадмину — любую)
    if teacher and not is_dean_or_admin(teacher) and session.get("teacher_id") != teacher.get("teacher_id"):
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}

    started = session.get("sessionStartedAt", 0) or session.get("started_at", 0)
    duration = session.get("durationMs", 0) or session.get("duration_ms", 0)
    remaining_sec = max(0, int((started + duration - now_ms) / 1000))

    if remaining_sec <= 0 and session.get("status") == "active":
        session["status"] = "completed"
        db.save_active_session_db(session)
        record_session_history(session)
        return {"session": None, "current_server_time": now_ms, "remaining_seconds": 0}

    session_copy = dict(session)
    session_copy["server_time"] = now_ms
    session_copy["remaining_seconds"] = remaining_sec
    return {"session": session_copy, "current_server_time": now_ms, "remaining_seconds": remaining_sec}

@app.post("/api/exam/stop")
def stop_exam_session(teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, str]:
    session = db.load_active_session_db()
    if session:
        if is_dean_or_admin(teacher) or session.get("teacher_id") == teacher.get("teacher_id"):
            session["status"] = "stopped"
            db.save_active_session_db(session)
            record_session_history(session)
    return {"status": "ok"}

@app.get("/admin", response_class=HTMLResponse, response_model=None)
@app.get("/admin.html", response_class=HTMLResponse, response_model=None)
def admin_panel(request: Request, credentials: Optional[HTTPBasicCredentials] = Depends(security_optional)):
    try:
        teacher = check_admin(request, credentials)
    except HTTPException as exc:
        if exc.status_code == 401 and not credentials:
            return _redirect_to_login(request)
        raise
    t_id = teacher.get("teacher_id")
    is_super = is_dean_or_admin(teacher)
    all_results = load_results()
    all_groups = load_groups()
    active_session = db.load_active_session_db()
    all_teachers = db.load_teachers_db()

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
        branding_json = json.dumps(db.load_branding_db(), ensure_ascii=False)

        rendered = template.replace("__SERVER_RESULTS_JSON__", results_json)
        rendered = rendered.replace("__SERVER_GROUPS_JSON__", groups_json)
        rendered = rendered.replace("__SERVER_SESSION_JSON__", session_json)
        rendered = rendered.replace("__SERVER_TEACHER_JSON__", teacher_json)
        rendered = rendered.replace("__SERVER_ALL_TEACHERS_JSON__", all_teachers_json)
        rendered = rendered.replace("__SERVER_BRANDING_JSON__", branding_json)
        rendered = apply_feature_flags_to_html(rendered, RUSSIA_MAP_ENABLED)
        return HTMLResponse(content=rendered)

    total_tests = len(results)
    avg_accuracy = round(sum(r.get("accuracy", 0) for r in results) / total_tests, 1) if total_tests else 0
    return HTMLResponse(f"<h2>{teacher.get('organization', 'Институт наук о Земле ЮФУ')}</h2><p>Преподаватель: {teacher.get('full_name')}</p><p>Всего сдано тестов: {total_tests}, средняя точность: {avg_accuracy}%</p>")

@app.get("/api/branding")
def get_branding_endpoint() -> Dict[str, Any]:
    return db.load_branding_db()

@app.post("/api/branding")
def update_branding_endpoint(payload: Dict[str, Any], teacher: Dict[str, Any] = Depends(check_admin)) -> Dict[str, Any]:
    db.save_branding_db(payload)
    return {"status": "ok", "branding": db.load_branding_db()}

@app.get("/api/student/dashboard")
def get_student_dashboard(
    email: Optional[str] = None,
    name: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_authenticated_user),
) -> Dict[str, Any]:
    if user.get("role") == "student" and user.get("email"):
        email = user["email"]
        name = user.get("full_name") or name
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

    dashboard_regions: Dict[str, Any] = {
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
        }
    }
    if RUSSIA_MAP_ENABLED:
        dashboard_regions["russia"] = {
            "name": "Российская Федерация",
            "tag": "Общероссийский срез • 89 субъектов",
            "icon": "🇷🇺",
            **russia_stats
        }

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
        "regions": dashboard_regions,
        "recent_history": recent_history
    }

@app.get("/api/student/heatmap")
def get_student_heatmap(
    email: Optional[str] = None,
    region: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_authenticated_user),
) -> Dict[str, Any]:
    if user.get("role") == "student":
        if email and auth_service.normalize_email(email) != auth_service.normalize_email(user.get("email")):
            raise HTTPException(status_code=403, detail="Доступ к чужой статистике запрещён")
        email = user.get("email") or email
    if not email:
        raise HTTPException(status_code=400, detail="Параметр email обязателен")
    
    clean_email = email.strip().lower()
    if "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Некорректный email")
    
    try:
        heatmap_data = db.get_student_mistakes_heatmap(clean_email, region)
        
        # Дополняем рекомендациями на основе Топ-5 ошибок
        by_object = heatmap_data.get("by_object", {})
        sorted_objects = sorted(
            by_object.items(),
            key=lambda x: (-x[1]["errors"], x[0])
        )
        top_problematic = [
            {
                "name": name,
                "errors": data["errors"],
                "accuracy": data["accuracy"],
                "type": data["type"],
                "last_date": data["last_date"]
            }
            for name, data in sorted_objects[:5]
        ]
        
        # Список mastered (accuracy >= 85 и есть попытки)
        mastered = [
            name for name, data in by_object.items()
            if data["accuracy"] >= 85 and data["total_attempts"] >= 2
        ]
        
        heatmap_data["top_problematic"] = top_problematic
        heatmap_data["mastered_count"] = len(mastered)
        heatmap_data["problematic_count"] = sum(
            1 for d in by_object.values() if d["accuracy"] < 50
        )
        
        return {"status": "ok", **heatmap_data}
    except Exception as e:
        logger.error("Ошибка /api/student/heatmap: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка агрегации данных")

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
                    "department": teacher.get("department", "ИНоЗ ЮФУ"),
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
        meta_files = [f for f in os.listdir(MAPS_DIR) if f.lower().endswith('_meta.json')]
        for fname in meta_files:
            stem = fname[:-10].lower()
            if stem == clean:
                target_meta_file = os.path.join(MAPS_DIR, fname)
                clean = stem
                break
        if not target_meta_file:
            for fname in meta_files:
                stem = fname[:-10].lower()
                if clean in stem or stem in clean:
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
def api_region_data(region_id: str, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    if not RUSSIA_MAP_ENABLED and is_russia_map_target(region_id):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
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
    if not RUSSIA_MAP_ENABLED and is_russia_map_target(region_query):
        return render_russia_unavailable_page(status_code=503)
    info = resolve_region_info(region_query)
    if not RUSSIA_MAP_ENABLED and (info.get("is_rf") or info.get("id") == "russia"):
        return render_russia_unavailable_page(status_code=503)
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

    branding = db.load_branding_db()
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

    # Переписываем устаревшие прямые ссылки Carto с ключом на серверный прокси (без утечки CARTO_KEY в HTML)
    html = re.sub(
        r'https://(?:[a-d]\.|[a-z]+\.)?basemaps\.cartocdn\.com/rastertiles/(voyager|dark_all|light_all)/\{z\}/\{x\}/\{y\}\.png(?:\?key=[^"\'\s]+)?',
        r'/tiles/carto/\1/{z}/{x}/{y}.png',
        html
    )
    # Обеспечиваем стартовое раскрытое состояние для ПК (адаптивность регулируется JS)
    html = re.sub(
        r'("position"\s*:\s*"bottomleft"\s*,\s*)"collapsed"\s*:\s*true',
        r'\1"collapsed": false',
        html
    )
    # Добавляем актуальную версию map.css для сброса кэша браузера/SW после обновления
    map_css_path = os.path.join(BASE_DIR, "public", "map.css")
    css_ver = int(os.path.getmtime(map_css_path)) if os.path.exists(map_css_path) else 1
    html = re.sub(
        r'href=["\']/public/map\.css(?:\?v=[^"\']*)?["\']',
        f'href="/public/map.css?v={css_ver}"',
        html
    )

    # Заменяем вшитую при генерации статичную копию quiz.js на актуальный внешний /quiz.js?v=...
    quiz_js_path = os.path.join(BASE_DIR, "quiz.js")
    quiz_ver = int(os.path.getmtime(quiz_js_path)) if os.path.exists(quiz_js_path) else 1
    inline_quiz_marker = "var _root = typeof window !== 'undefined'"
    marker_idx = html.find(inline_quiz_marker)
    if marker_idx != -1:
        end_script_idx = html.find("</script>", marker_idx)
        if end_script_idx != -1:
            html = (
                html[:marker_idx]
                + f'</script>\n<script src="/quiz.js?v={quiz_ver}"></script>'
                + html[end_script_idx + len("</script>"):]
            )

    full_injected = f"{brand_script}\n{context_script}"

    if "<body" in html:
        html = re.sub(r'(<body[^>]*>)', lambda m: f'{m.group(1)}\n{full_injected}', html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", f"{full_injected}\n</head>", 1)
    else:
        html = f"{full_injected}\n{html}"

    html = apply_feature_flags_to_html(html, RUSSIA_MAP_ENABLED)
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
    from main import InteractiveAtlas

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
def get_maps_list(user: Dict[str, Any] = Depends(require_authenticated_user)) -> List[Dict[str, Any]]:
    if not os.path.exists(MAPS_DIR):
        return []

    maps_list = []
    for fname in os.listdir(MAPS_DIR):
        if not fname.lower().endswith(".html"):
            continue
        if not RUSSIA_MAP_ENABLED and is_russia_map_target(fname):
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
def get_public_map_file(file_name: str, request: Request):
    if not RUSSIA_MAP_ENABLED and is_russia_map_target(file_name):
        if file_name.lower().endswith(".json"):
            raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
        return render_russia_unavailable_page(status_code=503)
    if get_optional_current_user(request) is None:
        if file_name.lower().endswith(".json") or file_name.lower().endswith(".geojson"):
            raise HTTPException(status_code=401, detail="Требуется авторизация")
        return _redirect_to_login(request)
    target = os.path.join("public", "maps", file_name)
    if os.path.exists(target) and os.path.isfile(target):
        return FileResponse(target)
    if os.path.exists(file_name) and os.path.isfile(file_name):
        return FileResponse(file_name)
    raise HTTPException(status_code=404, detail=f"Карта '{file_name}' не найдена в public/maps/")

@app.get("/", response_model=None)
def get_index(request: Request, region: Optional[str] = None):
    if region:
        if get_optional_current_user(request) is None:
            return _redirect_to_login(request)
        return render_dynamic_map_response(region)
    return render_index_page(request, increment_visits=True)

@app.get("/api/stats/visits")
def api_get_site_visits() -> JSONResponse:
    """Returns total site home-page opening count without storing user-identifying data."""
    visits = db.get_site_stat("site_visits")
    return JSONResponse(
        content={
            "status": "ok",
            "visits": visits,
            "label": "Посещений сайта",
            "metric": "home_page_loads",
        },
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )

@app.get("/map", response_model=None)
def get_map_query(request: Request, region: Optional[str] = "rostov"):
    if get_optional_current_user(request) is None:
        return _redirect_to_login(request)
    return render_dynamic_map_response(region)

@app.get("/map/{region}", response_model=None)
def get_map_path(region: str, request: Request):
    if get_optional_current_user(request) is None:
        return _redirect_to_login(request)
    return render_dynamic_map_response(region)

@app.get("/region/{region}", response_model=None)
def get_region_path(region: str, request: Request):
    if get_optional_current_user(request) is None:
        return _redirect_to_login(request)
    return render_dynamic_map_response(region)

@app.get("/api/region/context", response_model=None)
def api_get_region_context(region: Optional[str] = "rostov", user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    if not RUSSIA_MAP_ENABLED and is_russia_map_target(region):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
    info = resolve_region_info(region)
    if not RUSSIA_MAP_ENABLED and (info.get("is_rf") or info.get("id") == "russia"):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
    return {"status": "ok", "context": info}

@app.get("/api/region/{region_id}/context", response_model=None)
def api_get_region_context_by_id(region_id: str, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    if not RUSSIA_MAP_ENABLED and is_russia_map_target(region_id):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
    info = resolve_region_info(region_id)
    if not RUSSIA_MAP_ENABLED and (info.get("is_rf") or info.get("id") == "russia"):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
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

# Duel multiplayer (WebSockets & REST polling)

_DUEL_MODE_ALIASES = {
    "center": "center",
    "centers": "center",
    "райцентры": "center",
    "puzzle": "puzzle",
    "пазл": "puzzle",
}


def normalize_duel_mode(raw_mode: Optional[str]) -> str:
    """Normalizes and validates a duel mode name without silently overwriting invalid modes."""
    key = str(raw_mode or "center").strip().lower()
    if key in _DUEL_MODE_ALIASES:
        return _DUEL_MODE_ALIASES[key]
    raise HTTPException(status_code=400, detail=f"Неподдерживаемый режим дуэли: '{raw_mode}'")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return earth_r * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))


def _score_center_distance(distance_km: float) -> int:
    if distance_km <= 15.0:
        return 3
    if distance_km <= 40.0:
        return 2
    if distance_km <= 100.0:
        return 1
    return 0


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
        self.correct_answers = 0
        self.mistakes = 0
        self.placed_ids: List[str] = []
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
            "correct_answers": self.correct_answers,
            "mistakes": self.mistakes,
            "placed_ids": list(self.placed_ids),
            "finished": self.finished,
            "finish_time": self.finish_time,
            "online": (self.ws is not None) or (time.time() - self.last_ping < 15),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DuelPlayer":
        p = cls(
            player_id=data.get("player_id", ""),
            name=data.get("name", "Игрок"),
            group=data.get("group", "-"),
            email=data.get("email", ""),
            is_host=bool(data.get("is_host", False)),
        )
        p.ready = bool(data.get("ready", False))
        p.score = int(data.get("score", 0))
        p.progress = int(data.get("progress", 0))
        p.total = int(data.get("total", 7))
        p.correct_answers = int(data.get("correct_answers", 0))
        p.mistakes = int(data.get("mistakes", 0))
        p.placed_ids = [str(x) for x in data.get("placed_ids", []) if x]
        p.finished = bool(data.get("finished", False))
        p.finish_time = data.get("finish_time")
        p.last_ping = data.get("last_ping", time.time())
        return p


class DuelRoom:
    def __init__(self, room_id: str, mode: str, region: str, host: DuelPlayer):
        self.room_id = room_id.upper()
        self.mode = normalize_duel_mode(mode)
        self.region = resolve_region_info(region)["id"] if region else "rostov"
        self.created_at = time.time()
        self.status = "waiting"  # waiting, ready, countdown, playing, finished, cancelled
        self.players: Dict[str, DuelPlayer] = {host.player_id: host}
        self.questions: List[Dict[str, Any]] = []
        self.puzzle_anchor_id: Optional[str] = None
        self.puzzle_piece_ids: List[str] = []
        self.puzzle_total: int = 25
        self.current_round: int = 0
        self.round_duration: int = 20
        self.round_started_at: Optional[float] = None
        self.round_answers: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.winner: Optional[str] = None
        self.winner_reason: str = ""
        self.winner_name: str = ""
        self.finish_reason: str = ""  # completed | surrender | cancelled
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.countdown: int = 3
        self._round_timer_task: Optional[asyncio.Task] = None
        self._advance_task: Optional[asyncio.Task] = None

        if self.mode == "center":
            self.generate_center_questions()
        else:
            self.init_puzzle_config()

    def get_target_total(self) -> int:
        if self.mode == "puzzle":
            return max(1, self.puzzle_total)
        return max(1, len(self.questions) or 7)

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
                {"name": "Азов", "lat": 47.112, "lon": 39.424},
            ]
        sample_size = min(7, len(centers))
        selected = random.sample(centers, sample_size)
        self.questions = [
            {
                "index": i,
                "name": c.get("name", ""),
                "lat": float(c.get("lat", 0.0)),
                "lon": float(c.get("lon", 0.0)),
                "status": c.get("status", "райцентр"),
            }
            for i, c in enumerate(selected)
        ]
        total = self.get_target_total()
        for p in self.players.values():
            p.total = total

    def init_puzzle_config(self):
        reg_data = get_region_data(self.region) or {}
        puz = reg_data.get("EMBEDDED_PUZZLE_DATA", [])
        valid_ids = [str(item.get("id")) for item in puz if isinstance(item, dict) and item.get("id") is not None]
        if len(valid_ids) >= 2:
            anchor_idx = random.randrange(len(valid_ids))
            self.puzzle_anchor_id = valid_ids[anchor_idx]
            remaining = [pid for idx, pid in enumerate(valid_ids) if idx != anchor_idx]
            random.shuffle(remaining)
            self.puzzle_piece_ids = remaining
            self.puzzle_total = len(remaining)
        else:
            self.puzzle_anchor_id = None
            self.puzzle_piece_ids = []
            self.puzzle_total = max(1, len(puz) if puz else 25)
        for p in self.players.values():
            p.total = self.puzzle_total

    def cancel_timers(self):
        for attr in ("_round_timer_task", "_advance_task"):
            task = getattr(self, attr, None)
            if task and not task.done():
                task.cancel()
            setattr(self, attr, None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "mode": self.mode,
            "region": self.region,
            "status": self.status,
            "created_at": self.created_at,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "server_now": time.time(),
            "current_round": self.current_round,
            "round_duration": self.round_duration,
            "round_started_at": self.round_started_at,
            "round_answers": self.round_answers,
            "total_items": self.get_target_total(),
            "questions": self.questions if self.mode == "center" else [],
            "puzzle_anchor_id": self.puzzle_anchor_id if self.mode == "puzzle" else None,
            "puzzle_piece_ids": self.puzzle_piece_ids if self.mode == "puzzle" else [],
            "players": [p.to_dict() for p in self.players.values()],
            "winner": self.winner,
            "winner_name": self.winner_name,
            "winner_reason": self.winner_reason,
            "finish_reason": self.finish_reason,
            "countdown": self.countdown,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DuelRoom":
        room = cls.__new__(cls)
        room.room_id = str(data.get("room_id", "")).upper()
        raw_mode = str(data.get("mode", "center")).strip().lower()
        room.mode = _DUEL_MODE_ALIASES.get(raw_mode, "center")
        room.region = data.get("region", "rostov")
        room.created_at = float(data.get("created_at", time.time()))
        room.status = data.get("status", "waiting")
        room.questions = data.get("questions", [])
        room.puzzle_anchor_id = data.get("puzzle_anchor_id")
        room.puzzle_piece_ids = [str(x) for x in data.get("puzzle_piece_ids", []) if x is not None]
        room.puzzle_total = int(data.get("puzzle_total", len(room.puzzle_piece_ids) or 25))
        room.current_round = int(data.get("current_round", 0))
        room.round_duration = int(data.get("round_duration", 20))
        room.round_started_at = data.get("round_started_at")
        room.round_answers = data.get("round_answers", {}) if isinstance(data.get("round_answers"), dict) else {}
        room.winner = data.get("winner")
        room.winner_reason = data.get("winner_reason", "")
        room.winner_name = data.get("winner_name", "")
        room.finish_reason = data.get("finish_reason", "")
        room.start_time = data.get("start_time")
        room.end_time = data.get("end_time")
        room.countdown = int(data.get("countdown", 3))
        room._round_timer_task = None
        room._advance_task = None
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
        if self.status in ("finished", "cancelled"):
            return

        players_list = list(self.players.values())
        if len(players_list) < 2:
            return

        p1, p2 = players_list[0], players_list[1]

        if self.mode == "center":
            if p1.finished and p2.finished:
                self.status = "finished"
                self.finish_reason = self.finish_reason or "completed"
                self.end_time = time.time()
                db.record_audit_event("duel_finished", actor_role="system", summary="Дуэль завершена (режим Puzzle)", meta={"mode": "puzzle"})
                db.record_audit_event("duel_finished", actor_role="system", summary="Дуэль завершена (режим Center)", meta={"mode": "center"})
                self.cancel_timers()
                if p1.score > p2.score:
                    self.winner = p1.player_id
                    self.winner_name = p1.name
                    self.winner_reason = f"Обычное завершение: {p1.name} победил(а) по баллам ({p1.score} : {p2.score})."
                elif p2.score > p1.score:
                    self.winner = p2.player_id
                    self.winner_name = p2.name
                    self.winner_reason = f"Обычное завершение: {p2.name} победил(а) по баллам ({p2.score} : {p1.score})."
                elif p1.correct_answers != p2.correct_answers:
                    top = p1 if p1.correct_answers > p2.correct_answers else p2
                    self.winner = top.player_id
                    self.winner_name = top.name
                    self.winner_reason = f"При равных баллах ({p1.score}) {top.name} дал(а) больше точных ответов!"
                else:
                    t1 = (p1.finish_time or 999999) - (self.start_time or 0)
                    t2 = (p2.finish_time or 999999) - (self.start_time or 0)
                    if t1 < t2:
                        self.winner = p1.player_id
                        self.winner_name = p1.name
                        self.winner_reason = f"При равных баллах ({p1.score}) {p1.name} ответил(а) быстрее!"
                    elif t2 < t1:
                        self.winner = p2.player_id
                        self.winner_name = p2.name
                        self.winner_reason = f"При равных баллах ({p2.score}) {p2.name} ответил(а) быстрее!"
                    else:
                        self.winner = "draw"
                        self.winner_name = "Ничья"
                        self.winner_reason = f"Боевая ничья по итогам 7 раундов ({p1.score} : {p2.score})."

        elif self.mode == "puzzle":
            if p1.finished or p2.finished or (p1.progress >= p1.total) or (p2.progress >= p2.total):
                self.status = "finished"
                self.finish_reason = self.finish_reason or "completed"
                self.end_time = time.time()
                db.record_audit_event("duel_finished", actor_role="system", summary="Дуэль завершена (режим Puzzle)", meta={"mode": "puzzle"})
                db.record_audit_event("duel_finished", actor_role="system", summary="Дуэль завершена (режим Center)", meta={"mode": "center"})
                self.cancel_timers()
                if p1.progress > p2.progress:
                    self.winner = p1.player_id
                    self.winner_name = p1.name
                    self.winner_reason = f"Обычное завершение: {p1.name} собрал(а) регион первым(ой) ({p1.progress}/{p1.total})!"
                elif p2.progress > p1.progress:
                    self.winner = p2.player_id
                    self.winner_name = p2.name
                    self.winner_reason = f"Обычное завершение: {p2.name} собрал(а) регион первым(ой) ({p2.progress}/{p2.total})!"
                elif p1.score != p2.score:
                    top = p1 if p1.score > p2.score else p2
                    self.winner = top.player_id
                    self.winner_name = top.name
                    self.winner_reason = f"{top.name} победил(а) по баллам ({top.score})!"
                elif p1.mistakes < p2.mistakes:
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
                    self.winner_reason = "Боевая ничья в сборке пазла!"


DUEL_DATA_DIR = os.environ.get("DUEL_DATA_DIR", tempfile.gettempdir())
os.makedirs(DUEL_DATA_DIR, exist_ok=True)
DUEL_ROOMS_FILE = os.path.join(DUEL_DATA_DIR, "duel_rooms.json")
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


def clean_stale_duel_rooms():
    now = time.time()
    stale = [rid for rid, r in active_duel_rooms.items() if now - r.created_at > 7200]
    if stale:
        for rid in stale:
            r = active_duel_rooms.pop(rid, None)
            if r:
                r.cancel_timers()
        save_duel_rooms_to_disk()


def _record_center_answer(
    room: DuelRoom,
    player: DuelPlayer,
    q_idx: int,
    raw_points: Any,
    raw_distance: Any,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> tuple[bool, int, float, bool]:
    """Records one player's answer for the active round and returns (accepted, pts, dist, round_complete)."""
    if room.status != "playing" or room.mode != "center":
        return False, 0, 0.0, False
    total_q = len(room.questions)
    if total_q <= 0 or q_idx != room.current_round or q_idx < 0 or q_idx >= total_q:
        return False, 0, 0.0, False

    round_key = str(q_idx)
    answers_for_round = room.round_answers.setdefault(round_key, {})
    if player.player_id in answers_for_round:
        return False, 0, 0.0, False

    if lat is not None and lon is not None:
        q = room.questions[q_idx]
        dist = _haversine_km(float(lat), float(lon), float(q["lat"]), float(q["lon"]))
        pts = _score_center_distance(dist)
    else:
        dist = float(raw_distance if raw_distance is not None else 999.0)
        pts = max(0, min(3, int(raw_points or 0)))

    is_correct = pts > 0
    answers_for_round[player.player_id] = {
        "points": pts,
        "distance": round(dist, 2),
        "correct": is_correct,
        "timed_out": False,
    }
    player.score += pts
    if is_correct:
        player.correct_answers += 1
    else:
        player.mistakes += 1
    player.progress = sum(1 for r_map in room.round_answers.values() if player.player_id in r_map)
    if q_idx >= total_q - 1:
        player.finished = True
        player.finish_time = time.time()

    all_answered = len(room.players) >= 2 and all(pid in answers_for_round for pid in room.players)
    return True, pts, dist, all_answered


def _record_puzzle_piece(
    room: DuelRoom,
    player: DuelPlayer,
    district_id: Optional[str],
    placed_count: Any,
    mistakes: Any,
) -> bool:
    """Records a placed puzzle piece, updates score/progress/mistakes and checks victory."""
    if room.status != "playing" or room.mode != "puzzle":
        return False

    clean_did = str(district_id or "").strip()
    if clean_did:
        if clean_did in player.placed_ids:
            return False
        player.placed_ids.append(clean_did)
        new_progress = min(player.total, max(player.progress + 1, int(placed_count or len(player.placed_ids))))
    else:
        new_progress = min(player.total, max(player.progress, int(placed_count or (player.progress + 1))))

    delta = max(0, new_progress - player.progress)
    player.progress = new_progress
    player.correct_answers += delta
    player.score += delta * 10
    if mistakes is not None:
        player.mistakes = max(player.mistakes, int(mistakes))

    if player.progress >= player.total:
        player.finished = True
        player.finish_time = time.time()
    room.check_finished()
    return True


def _apply_surrender(room: DuelRoom, player: DuelPlayer) -> None:
    room.cancel_timers()
    player.finished = True
    player.finish_time = time.time()
    opp = next((p for pid, p in room.players.items() if pid != player.player_id), None)
    room.status = "finished"
    room.finish_reason = "surrender"
    room.end_time = time.time()
    db.record_audit_event("duel_finished", actor_role="system", summary="Дуэль завершена (сдача)", meta={"mode": getattr(room, "mode", "center")})
    if opp:
        room.winner = opp.player_id
        room.winner_name = opp.name
        room.winner_reason = f"Сдача игрока: {player.name} сдался(лась). Победа присуждена {opp.name}."
    else:
        room.winner = "draw"
        room.winner_name = "Ничья"
        room.winner_reason = f"{player.name} отказался от дуэли до подключения соперника."


def _advance_center_round_sync(room: DuelRoom, timed_out: bool = False) -> bool:
    """Advances synchronized center round or completes the match. Returns True if finished."""
    if room.status != "playing" or room.mode != "center":
        return room.status == "finished"

    round_key = str(room.current_round)
    answers_for_round = room.round_answers.setdefault(round_key, {})
    for pid, p in room.players.items():
        if pid not in answers_for_round:
            answers_for_round[pid] = {"points": 0, "distance": 9999.0, "correct": False, "timed_out": timed_out}
            p.mistakes += 1
        p.progress = sum(1 for r_map in room.round_answers.values() if pid in r_map)

    if room.current_round + 1 >= len(room.questions):
        for p in room.players.values():
            p.finished = True
            p.finish_time = p.finish_time or time.time()
        room.check_finished()
        return True

    room.current_round += 1
    room.round_started_at = time.time()
    return False


async def _schedule_round_timeout(room: DuelRoom, round_idx: int) -> None:
    try:
        await asyncio.sleep(room.round_duration)
        if room.status != "playing" or room.mode != "center" or room.current_round != round_idx:
            return
        finished = _advance_center_round_sync(room, timed_out=True)
        save_duel_rooms_to_disk()
        if finished:
            await room.broadcast({"type": "game_over", "room": room.to_dict()})
        else:
            room._round_timer_task = asyncio.create_task(_schedule_round_timeout(room, room.current_round))
            await room.broadcast({
                "type": "round_next",
                "round": room.current_round,
                "timed_out_round": round_idx,
                "round_started_at": room.round_started_at,
                "round_duration": room.round_duration,
                "room": room.to_dict(),
            })
    except asyncio.CancelledError:
        return


async def _delayed_advance_center_round(room: DuelRoom, round_idx: int) -> None:
    try:
        await asyncio.sleep(1.0)
        if room.status != "playing" or room.mode != "center" or room.current_round != round_idx:
            return
        finished = _advance_center_round_sync(room, timed_out=False)
        save_duel_rooms_to_disk()
        if finished:
            await room.broadcast({"type": "game_over", "room": room.to_dict()})
        else:
            room._round_timer_task = asyncio.create_task(_schedule_round_timeout(room, room.current_round))
            await room.broadcast({
                "type": "round_next",
                "round": room.current_round,
                "round_started_at": room.round_started_at,
                "round_duration": room.round_duration,
                "room": room.to_dict(),
            })
    except asyncio.CancelledError:
        return


@app.post("/api/duel/create")
def create_duel_room(req: DuelCreateRequest, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    clean_stale_duel_rooms()
    if not RUSSIA_MAP_ENABLED and is_russia_map_target(req.region):
        raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
    mode = normalize_duel_mode(req.mode)
    region_id = resolve_region_info(req.region)["id"] if req.region else "rostov"

    room_code = f"DUEL-{random.randint(1000, 9999)}"
    while room_code in active_duel_rooms:
        room_code = f"DUEL-{random.randint(1000, 9999)}"

    player_id = f"p_{secrets.token_hex(4)}"
    host = DuelPlayer(
        player_id=player_id,
        name=req.host_name,
        group=req.host_group,
        email=req.host_email,
        is_host=True,
    )
    room = DuelRoom(room_code, mode, region_id, host)
    active_duel_rooms[room_code] = room
    logger.info("Duel room created: %s (mode=%s, region=%s)", room_code, room.mode, room.region)
    save_duel_rooms_to_disk()

    map_url = f"/map/{room.region}?duel={room_code}&player={player_id}&role=host&mode={room.mode}"
    return {
        "status": "ok",
        "room_id": room_code,
        "player_id": player_id,
        "role": "host",
        "mode": room.mode,
        "region": room.region,
        "map_url": map_url,
        "room": room.to_dict(),
    }


@app.post("/api/duel/join")
def join_duel_room(req: DuelJoinRequest, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    clean_stale_duel_rooms()
    code = (req.room_id or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Введите корректный код комнаты")

    room = load_room_fresh(code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната дуэли '{code}' не найдена. Проверьте код.")

    if room.status == "cancelled":
        raise HTTPException(status_code=400, detail="Создатель отменил эту комнату дуэли")
    if room.status == "finished":
        raise HTTPException(status_code=400, detail="Эта дуэль уже завершена")

    req_pid = (req.player_id or "").strip()
    if req_pid and req_pid in room.players:
        existing_player = room.players[req_pid]
        player_id = existing_player.player_id
        role = "host" if existing_player.is_host else "join"
    else:
        if len(room.players) >= 2:
            raise HTTPException(status_code=400, detail="Комната заполнена: в ней уже участвуют два игрока")
        player_id = f"p_{secrets.token_hex(4)}"
        join_player = DuelPlayer(
            player_id=player_id,
            name=req.player_name or "Соперник",
            group=req.player_group,
            email=req.player_email,
            is_host=False,
        )
        join_player.total = room.get_target_total()
        room.players[player_id] = join_player
        role = "join"
        if len(room.players) == 2 and room.status == "waiting":
            room.status = "ready"
        save_duel_rooms_to_disk()

    map_url = f"/map/{room.region}?duel={code}&player={player_id}&role={role}&mode={room.mode}"
    return {
        "status": "ok",
        "room_id": code,
        "player_id": player_id,
        "role": role,
        "mode": room.mode,
        "region": room.region,
        "map_url": map_url,
        "room": room.to_dict(),
    }


def _sync_center_round_timeout_if_elapsed(room: DuelRoom) -> bool:
    """Advances expired center rounds even when clients operate purely via HTTP polling."""
    if (
        room.status == "playing"
        and room.mode == "center"
        and room.round_started_at is not None
        and (time.time() - room.round_started_at) >= room.round_duration
    ):
        _advance_center_round_sync(room, timed_out=True)
        save_duel_rooms_to_disk()
        return True
    return False


@app.get("/api/duel/state/{room_id}")
def get_duel_room_state(room_id: str, player_id: Optional[str] = None, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    code = room_id.strip().upper()
    room = load_room_fresh(code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната '{code}' не найдена")

    if player_id and player_id in room.players:
        room.players[player_id].last_ping = time.time()

    _sync_center_round_timeout_if_elapsed(room)
    return {"status": "ok", "room": room.to_dict()}


@app.post("/api/duel/action/{room_id}")
def handle_duel_action(room_id: str, req: DuelActionRequest, user: Dict[str, Any] = Depends(require_authenticated_user)) -> Dict[str, Any]:
    code = room_id.strip().upper()
    room = load_room_fresh(code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната '{code}' не найдена")

    _sync_center_round_timeout_if_elapsed(room)
    player = room.players.get(req.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден в комнате")

    player.last_ping = time.time()
    action = req.action
    payload = req.payload or {}

    if action == "ready":
        player.ready = bool(payload.get("ready", True))
        if room.status in ("waiting", "ready", "countdown") and len(room.players) == 2 and all(p.ready for p in room.players.values()):
            room.status = "playing"
            room.start_time = time.time()
            room.current_round = 0
            room.round_started_at = time.time()

    elif action == "cancel":
        if room.status in ("waiting", "ready") and player.is_host:
            room.cancel_timers()
            room.status = "cancelled"
            room.finish_reason = "cancelled"
            room.end_time = time.time()
            room.winner_reason = "Комната отменена создателем до начала матча."
        else:
            _apply_surrender(room, player)

    elif action == "start":
        if room.status in ("ready", "countdown") and len(room.players) == 2:
            room.status = "playing"
            room.start_time = time.time()
            room.current_round = 0
            room.round_started_at = time.time()

    elif action == "answer_center":
        q_idx = int(payload.get("question_index", room.current_round))
        accepted, _, _, round_done = _record_center_answer(
            room,
            player,
            q_idx,
            payload.get("points"),
            payload.get("distance"),
            lat=payload.get("lat"),
            lon=payload.get("lon"),
        )
        if accepted and round_done:
            _advance_center_round_sync(room, timed_out=False)

    elif action == "place_piece":
        _record_puzzle_piece(
            room,
            player,
            payload.get("district_id"),
            payload.get("placed_count"),
            payload.get("mistakes"),
        )

    elif action == "puzzle_mistake":
        if room.status == "playing" and room.mode == "puzzle":
            player.mistakes += 1

    elif action == "surrender":
        if room.status != "finished":
            _apply_surrender(room, player)

    elif action == "finish":
        if room.status == "playing":
            player.finished = True
            player.finish_time = time.time()
            room.check_finished()

    save_duel_rooms_to_disk()
    return {"status": "ok", "room": room.to_dict()}


@app.websocket("/ws/duel/{room_id}/{player_id}")
async def websocket_duel_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    if get_optional_current_user(websocket) is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    code = room_id.strip().upper()
    room = load_room_fresh(code)

    if not room or player_id not in room.players:
        await websocket.send_json({"type": "error", "message": "Комната или игрок не найдены"})
        await websocket.close()
        return

    if room.status == "cancelled":
        await websocket.send_json({"type": "room_cancelled", "message": "Комната отменена создателем", "room": room.to_dict()})
        await websocket.close()
        return

    player = room.players[player_id]
    old_ws = player.ws
    player.ws = websocket
    player.last_ping = time.time()
    if old_ws is not None and old_ws is not websocket:
        try:
            await old_ws.close(code=1000)
        except Exception:
            pass

    await room.broadcast({
        "type": "player_connected",
        "player_id": player_id,
        "player_name": player.name,
        "room": room.to_dict(),
    })

    if room.status == "finished":
        await websocket.send_json({"type": "game_over", "room": room.to_dict()})

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                if not isinstance(data, dict):
                    raise ValueError("Payload must be a JSON object")
            except Exception:
                await websocket.send_json({"type": "error", "message": "Некорректный формат WebSocket-сообщения"})
                continue

            msg_type = data.get("type", "")
            player.last_ping = time.time()

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "time": time.time(), "server_now": time.time()})

            elif msg_type == "ready":
                if room.status in ("finished", "cancelled"):
                    continue
                player.ready = bool(data.get("ready", True))
                await room.broadcast({
                    "type": "player_ready_changed",
                    "player_id": player_id,
                    "ready": player.ready,
                    "room": room.to_dict(),
                })

                if room.status in ("waiting", "ready") and len(room.players) == 2 and all(p.ready for p in room.players.values()):
                    room.status = "countdown"

                    async def _run_countdown():
                        try:
                            for sec in (3, 2, 1):
                                if room.status != "countdown":
                                    return
                                await room.broadcast({"type": "countdown", "seconds": sec, "room": room.to_dict()})
                                await asyncio.sleep(1)
                            if room.status != "countdown":
                                return
                            room.status = "playing"
                            room.start_time = time.time()
                            room.current_round = 0
                            room.round_started_at = time.time()
                            save_duel_rooms_to_disk()
                            if room.mode == "center":
                                room._round_timer_task = asyncio.create_task(_schedule_round_timeout(room, 0))
                            await room.broadcast({"type": "game_start", "room": room.to_dict()})
                        except asyncio.CancelledError:
                            return

                    asyncio.create_task(_run_countdown())

            elif msg_type == "answer_center":
                q_idx = int(data.get("question_index", room.current_round))
                accepted, pts, dist, round_done = _record_center_answer(
                    room,
                    player,
                    q_idx,
                    data.get("points"),
                    data.get("distance"),
                    lat=data.get("lat"),
                    lon=data.get("lon"),
                )
                if not accepted:
                    continue

                save_duel_rooms_to_disk()
                await room.broadcast({
                    "type": "opponent_action",
                    "player_id": player_id,
                    "action": "answer_center",
                    "question_index": q_idx,
                    "points": pts,
                    "distance": round(dist, 2),
                    "score": player.score,
                    "progress": player.progress,
                    "correct_answers": player.correct_answers,
                    "mistakes": player.mistakes,
                    "target_name": data.get("target_name", ""),
                    "room": room.to_dict(),
                })

                if round_done:
                    room.cancel_timers()
                    room._advance_task = asyncio.create_task(_delayed_advance_center_round(room, q_idx))

            elif msg_type == "place_piece":
                accepted = _record_puzzle_piece(
                    room,
                    player,
                    data.get("district_id"),
                    data.get("placed_count"),
                    data.get("mistakes"),
                )
                if not accepted:
                    continue

                save_duel_rooms_to_disk()
                await room.broadcast({
                    "type": "opponent_action",
                    "player_id": player_id,
                    "action": "place_piece",
                    "district_id": data.get("district_id", ""),
                    "district_name": data.get("district_name", ""),
                    "placed_count": player.progress,
                    "score": player.score,
                    "mistakes": player.mistakes,
                    "room": room.to_dict(),
                })

                if room.status == "finished":
                    await room.broadcast({"type": "game_over", "room": room.to_dict()})

            elif msg_type == "puzzle_mistake":
                if room.status == "playing" and room.mode == "puzzle":
                    player.mistakes += 1
                    save_duel_rooms_to_disk()
                    await room.broadcast({
                        "type": "opponent_action",
                        "player_id": player_id,
                        "action": "puzzle_mistake",
                        "district_name": data.get("district_name", ""),
                        "mistakes": player.mistakes,
                        "score": player.score,
                        "placed_count": player.progress,
                        "room": room.to_dict(),
                    })

            elif msg_type == "finish":
                if room.status == "playing":
                    player.finished = True
                    player.finish_time = time.time()
                    room.check_finished()
                    save_duel_rooms_to_disk()
                    await room.broadcast({"type": "player_finished", "player_id": player_id, "room": room.to_dict()})
                    if room.status == "finished":
                        await room.broadcast({"type": "game_over", "room": room.to_dict()})

            elif msg_type == "cancel":
                if room.status in ("waiting", "ready") and player.is_host:
                    room.cancel_timers()
                    room.status = "cancelled"
                    room.finish_reason = "cancelled"
                    room.end_time = time.time()
                    save_duel_rooms_to_disk()
                    await room.broadcast({"type": "room_cancelled", "room": room.to_dict()})

            elif msg_type == "surrender":
                if room.status != "finished":
                    _apply_surrender(room, player)
                    save_duel_rooms_to_disk()
                await room.broadcast({"type": "game_over", "room": room.to_dict()})

    except WebSocketDisconnect:
        if player.ws is websocket:
            player.ws = None
        if room.status not in ("finished", "cancelled"):
            await room.broadcast({
                "type": "player_disconnected",
                "player_id": player_id,
                "player_name": player.name,
                "room": room.to_dict(),
            })
    except Exception:
        if player.ws is websocket:
            player.ws = None

_CARTO_ALLOWED_STYLES = {"voyager", "dark_all", "light_all"}
_CARTO_SUBDOMAINS = ("a", "b", "c", "d")
_CARTO_INVALID_KEY_SHA256 = {
    "69be4aecf9f814ba45d585801a5aa41e79b16fc88eafec5b1954a9f06a69e6be",
    "cc3f31364a735d9a8179af36b3db7617cdff8bdb0248654ebcc3df91607abedc",
}
_TILE_CACHE: "collections.OrderedDict[tuple, bytes]" = collections.OrderedDict()
_TILE_CACHE_LOCK = threading.Lock()
_TILE_CACHE_MAX = 512

@app.get("/tiles/carto/{style}/{z}/{x}/{y}.png", response_model=None)
def proxy_carto_tile(style: str, z: int, x: int, y: int):
    if style not in _CARTO_ALLOWED_STYLES:
        raise HTTPException(status_code=400, detail="Unsupported tile style")
    if z < 0 or z > 20:
        raise HTTPException(status_code=400, detail="Invalid zoom")
    max_coord = 1 << z
    if x < 0 or x >= max_coord or y < 0 or y >= max_coord:
        raise HTTPException(status_code=400, detail="Invalid tile coordinates")

    carto_key = os.environ.get("CARTO_KEY", "").strip()
    if not carto_key:
        raise HTTPException(status_code=503, detail="CARTO_KEY is not configured")

    cache_key = (style, z, x, y)
    with _TILE_CACHE_LOCK:
        cached = _TILE_CACHE.get(cache_key)
        if cached is not None:
            _TILE_CACHE.move_to_end(cache_key)
            return Response(
                content=cached,
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"}
            )

    start_idx = (x + y) % len(_CARTO_SUBDOMAINS)
    last_err = None
    data = None
    for attempt in range(2):
        sub = _CARTO_SUBDOMAINS[(start_idx + attempt) % len(_CARTO_SUBDOMAINS)]
        upstream_url = (
            f"https://{sub}.basemaps.cartocdn.com/rastertiles/{style}/{z}/{x}/{y}.png"
            f"?key={urllib.parse.quote(carto_key, safe='')}"
        )
        try:
            req = urllib.request.Request(
                upstream_url,
                headers={"User-Agent": "GeoAtlas/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                candidate = resp.read()
                if resp.status != 200 or not candidate or ("image/" not in ctype and not candidate.startswith(b"\x89PNG")):
                    raise HTTPException(status_code=502, detail="Invalid upstream tile response")
                if hashlib.sha256(candidate).hexdigest() in _CARTO_INVALID_KEY_SHA256:
                    raise HTTPException(status_code=502, detail="CARTO API key rejected")
                data = candidate
                break
        except HTTPException:
            raise
        except Exception as e:
            last_err = e

    if data is None:
        raise HTTPException(status_code=502, detail=f"Upstream tile error: {last_err}")

    with _TILE_CACHE_LOCK:
        _TILE_CACHE[cache_key] = data
        if len(_TILE_CACHE) > _TILE_CACHE_MAX:
            _TILE_CACHE.popitem(last=False)

    return Response(
        content=data,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/{slug}", response_model=None)
def get_slug_route(slug: str, request: Request):
    clean = slug.lower().strip()

    if not RUSSIA_MAP_ENABLED and is_russia_map_target(clean):
        if clean.endswith(".json"):
            raise HTTPException(status_code=503, detail=_RUSSIA_UNAVAILABLE_MSG)
        return render_russia_unavailable_page(status_code=503)

    if clean in ["admin", "admin.html"]:
        return RedirectResponse("/admin")
    if clean in ["index", "index.html"]:
        return render_index_page(request, increment_visits=True)
    if clean == "quiz.js":
        return get_quiz_js()

    if get_optional_current_user(request) is None:
        return _redirect_to_login(request)

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