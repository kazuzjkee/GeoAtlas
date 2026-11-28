import os
import json
import sqlite3
import threading
import time
import tempfile
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = os.environ.get("GEOATLAS_DATA_DIR", tempfile.gettempdir())
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "geoatlas.db")
_lock = threading.Lock()

def _conn():
    c = sqlite3.connect(DB_FILE, timeout=10.0)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=10000;")
    return c

def init_db():
    with _lock:
        conn = _conn()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS results (
                    submission_id TEXT PRIMARY KEY,
                    date TEXT,
                    email TEXT,
                    name TEXT,
                    grp TEXT,
                    quiz_type TEXT,
                    score INTEGER,
                    max_score INTEGER,
                    accuracy INTEGER,
                    time_spent TEXT,
                    is_exam INTEGER,
                    is_adaptive INTEGER DEFAULT 0,
                    exam_token TEXT,
                    violations INTEGER,
                    exam_status TEXT,
                    session_id TEXT,
                    teacher_id TEXT,
                    mistakes_log TEXT,
                    client_timestamp INTEGER,
                    created_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_results_email ON results(email);
                CREATE INDEX IF NOT EXISTS idx_results_teacher ON results(teacher_id);
                CREATE INDEX IF NOT EXISTS idx_results_session ON results(session_id);
                CREATE INDEX IF NOT EXISTS idx_results_exam_token ON results(exam_token);

                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    students TEXT,
                    teacher_id TEXT,
                    created_at TEXT,
                    updated_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_groups_teacher ON groups(teacher_id);

                CREATE TABLE IF NOT EXISTS auth_sessions (
                    email TEXT PRIMARY KEY,
                    code TEXT,
                    expires_at REAL,
                    name TEXT,
                    grp TEXT
                );

                CREATE TABLE IF NOT EXISTS sessions_history (
                    session_id TEXT PRIMARY KEY,
                    data TEXT,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS teachers (
                    teacher_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    organization TEXT,
                    department TEXT,
                    role TEXT
                );

                CREATE TABLE IF NOT EXISTS branding (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS active_session (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    session_data TEXT NOT NULL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS site_stats (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL DEFAULT 0,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL DEFAULT '',
                    grp TEXT NOT NULL DEFAULT '',
                    password_hash TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'student',
                    email_verified INTEGER NOT NULL DEFAULT 0,
                    email_verified_at REAL,
                    university_verified INTEGER NOT NULL DEFAULT 0,
                    university_email_verified INTEGER NOT NULL DEFAULT 0,
                    university_auth_provider TEXT NOT NULL DEFAULT '',
                    university_verified_at REAL,
                    oidc_subject TEXT,
                    oidc_issuer TEXT,
                    accepted_terms_at REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oidc_sub ON users(oidc_issuer, oidc_subject) WHERE oidc_subject IS NOT NULL;

                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0,
                    auth_method TEXT NOT NULL DEFAULT 'password'
                );
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);

                CREATE TABLE IF NOT EXISTS email_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 5,
                    expires_at REAL NOT NULL,
                    used_at REAL,
                    created_at REAL NOT NULL,
                    resend_available_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_email_verif_lookup ON email_verifications(email, purpose, created_at);

                CREATE TABLE IF NOT EXISTS oidc_states (
                    state_hash TEXT PRIMARY KEY,
                    nonce TEXT NOT NULL,
                    code_verifier TEXT NOT NULL,
                    next_url TEXT NOT NULL DEFAULT '/',
                    expires_at REAL NOT NULL,
                    used_at REAL
                );
            """)
            conn.commit()
            for alter_sql in (
                "ALTER TABLE results ADD COLUMN is_adaptive INTEGER DEFAULT 0",
                "ALTER TABLE results ADD COLUMN user_id INTEGER DEFAULT NULL",
            ):
                try:
                    conn.execute(alter_sql)
                    conn.commit()
                except Exception:
                    pass
        finally:
            conn.close()

# Results

def load_results() -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute("SELECT * FROM results ORDER BY created_at ASC")
            out = []
            for row in cur.fetchall():
                d = dict(row)
                d["is_exam"] = bool(d.get("is_exam"))
                d["is_adaptive"] = bool(d.get("is_adaptive", 0))
                d["max_score"] = d.get("max_score") or 0
                d["accuracy"] = d.get("accuracy") or 0
                try:
                    d["mistakes_log"] = json.loads(d.get("mistakes_log") or "[]")
                except Exception:
                    d["mistakes_log"] = []
                d["group"] = d.pop("grp", "")
                if not d.get("teacher_id"):
                    d["teacher_id"] = "teacher-petrov" if "эконом" in str(d.get("group", "")).lower() else "teacher-ivanov"
                out.append(d)
            return out
        finally:
            conn.close()

def save_result(result: Dict[str, Any]) -> Dict[str, Any]:
    sub_id = str(result.get("submission_id") or "").strip()
    if not sub_id:
        return {"status": "error", "detail": "submission_id required"}
    with _lock:
        conn = _conn()
        try:
            existing = conn.execute(
                "SELECT score, accuracy FROM results WHERE submission_id = ?",
                (sub_id,)
            ).fetchone()
            if existing:
                if (result.get("score", 0) > existing["score"]) or \
                   (result.get("accuracy", 0) > existing["accuracy"]):
                    conn.execute("""
                        UPDATE results SET
                            date=?, email=?, name=?, grp=?, quiz_type=?,
                            score=?, max_score=?, accuracy=?, time_spent=?,
                            is_exam=?, is_adaptive=?, exam_token=?, violations=?, exam_status=?,
                            session_id=?, teacher_id=?, mistakes_log=?,
                            client_timestamp=?, created_at=?
                        WHERE submission_id=?
                    """, (
                        result.get("date", ""),
                        result.get("email", ""),
                        result.get("name", ""),
                        result.get("group", ""),
                        result.get("quiz_type", ""),
                        result.get("score", 0),
                        result.get("max_score", 0),
                        result.get("accuracy", 0),
                        result.get("time_spent", ""),
                        1 if result.get("is_exam") else 0,
                        1 if result.get("is_adaptive") else 0,
                        result.get("exam_token", ""),
                        result.get("violations", 0),
                        result.get("exam_status", "Сдано"),
                        result.get("session_id", ""),
                        result.get("teacher_id", ""),
                        json.dumps(result.get("mistakes_log", []), ensure_ascii=False),
                        result.get("client_timestamp", 0),
                        time.time(),
                        sub_id
                    ))
                    conn.commit()
                    return {"status": "ok", "deduplicated": True, "updated": True}
                return {"status": "ok", "deduplicated": True, "updated": False}
            conn.execute("""
                INSERT INTO results (
                    submission_id, date, email, name, grp, quiz_type,
                    score, max_score, accuracy, time_spent, is_exam, is_adaptive,
                    exam_token, violations, exam_status, session_id,
                    teacher_id, mistakes_log, client_timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_id,
                result.get("date", ""),
                result.get("email", ""),
                result.get("name", ""),
                result.get("group", ""),
                result.get("quiz_type", ""),
                result.get("score", 0),
                result.get("max_score", 0),
                result.get("accuracy", 0),
                result.get("time_spent", ""),
                1 if result.get("is_exam") else 0,
                1 if result.get("is_adaptive") else 0,
                result.get("exam_token", ""),
                result.get("violations", 0),
                result.get("exam_status", "Сдано"),
                result.get("session_id", ""),
                result.get("teacher_id", ""),
                json.dumps(result.get("mistakes_log", []), ensure_ascii=False),
                result.get("client_timestamp", 0),
                time.time()
            ))
            conn.commit()
            return {"status": "ok", "deduplicated": False}
        finally:
            conn.close()

# Groups

def load_groups() -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute("SELECT * FROM groups ORDER BY created_at ASC")
            out = []
            for row in cur.fetchall():
                d = dict(row)
                try:
                    d["students"] = json.loads(d.get("students") or "[]")
                except Exception:
                    d["students"] = []
                out.append(d)
            return out
        finally:
            conn.close()

def save_group(group: Dict[str, Any]) -> None:
    with _lock:
        conn = _conn()
        try:
            conn.execute("""
                INSERT INTO groups (id, name, description, students, teacher_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    students=excluded.students,
                    teacher_id=excluded.teacher_id,
                    updated_at=excluded.updated_at
            """, (
                group.get("id", ""),
                group.get("name", ""),
                group.get("description", ""),
                json.dumps(group.get("students", []), ensure_ascii=False),
                group.get("teacher_id", "teacher-ivanov"),
                group.get("created_at", ""),
                time.time()
            ))
            conn.commit()
        finally:
            conn.close()

def delete_group(group_id: str) -> None:
    with _lock:
        conn = _conn()
        try:
            conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            conn.commit()
        finally:
            conn.close()

# Auth

def save_auth_session(email: str, record: Dict[str, Any]) -> None:
    with _lock:
        conn = _conn()
        try:
            conn.execute("""
                INSERT INTO auth_sessions (email, code, expires_at, name, grp)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    code=excluded.code,
                    expires_at=excluded.expires_at,
                    name=excluded.name,
                    grp=excluded.grp
            """, (
                email,
                record.get("code", ""),
                record.get("expires_at", 0),
                record.get("name", ""),
                record.get("group", "")
            ))
            conn.commit()
        finally:
            conn.close()

def pop_auth_session(email: str) -> Optional[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            row = conn.execute("SELECT * FROM auth_sessions WHERE email = ?", (email,)).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM auth_sessions WHERE email = ?", (email,))
            conn.commit()
            d = dict(row)
            d["group"] = d.pop("grp", "")
            return d
        finally:
            conn.close()

def cleanup_expired_auth() -> None:
    with _lock:
        conn = _conn()
        try:
            conn.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (time.time(),))
            conn.commit()
        finally:
            conn.close()

# Sessions History

def load_sessions_history() -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute("SELECT data FROM sessions_history ORDER BY updated_at ASC")
            out = []
            for row in cur.fetchall():
                try:
                    out.append(json.loads(row["data"]))
                except Exception:
                    pass
            return out
        finally:
            conn.close()

def record_session_history(session_data: Dict[str, Any]) -> None:
    sess_id = session_data.get("sessionId") or session_data.get("session_id")
    if not sess_id:
        return
    with _lock:
        conn = _conn()
        try:
            conn.execute("""
                INSERT INTO sessions_history (session_id, data, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    data=excluded.data,
                    updated_at=excluded.updated_at
            """, (sess_id, json.dumps(session_data, ensure_ascii=False), time.time()))
            conn.commit()
        finally:
            conn.close()

# Heatmap Analytics

def get_student_mistakes_heatmap(email: str, region: Optional[str] = None) -> Dict[str, Any]:
    """Агрегирует статистику ошибок студента по объектам и категориям."""
    email_clean = (email or "").strip().lower()
    if not email_clean:
        return {"by_object": {}, "by_type": {}, "total_tests": 0}

    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT quiz_type, mistakes_log, accuracy, date, session_id "
                "FROM results WHERE LOWER(email) = ? ORDER BY created_at ASC",
                (email_clean,)
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    by_object = {}
    by_type = {}
    total_tests = len(rows)
    last_date = ""

    for row in rows:
        quiz_type = str(row["quiz_type"] or "").lower()
        date_str = str(row["date"] or "")
        accuracy = int(row["accuracy"] or 0)
        if date_str:
            last_date = date_str

        try:
            mistakes = json.loads(row["mistakes_log"] or "[]")
            if not isinstance(mistakes, list):
                mistakes = []
        except Exception:
            mistakes = []

        if "река" in quiz_type or "river" in quiz_type or "гидро" in quiz_type:
            q_type = "river"
        elif "центр" in quiz_type or "center" in quiz_type:
            q_type = "center"
        elif "тополог" in quiz_type or "сосед" in quiz_type or "neighbor" in quiz_type:
            q_type = "neighbor"
        elif "пазл" in quiz_type or "puzzle" in quiz_type:
            q_type = "puzzle"
        else:
            q_type = "district"

        if q_type not in by_type:
            by_type[q_type] = {"errors": 0, "total_tests": 0}
        by_type[q_type]["total_tests"] += 1
        by_type[q_type]["errors"] += len(mistakes)

        for obj_name in mistakes:
            name = str(obj_name).strip()
            if not name:
                continue
            if name not in by_object:
                by_object[name] = {
                    "errors": 0,
                    "type": q_type,
                    "last_date": date_str,
                    "sessions": set()
                }
            by_object[name]["errors"] += 1
            by_object[name]["last_date"] = date_str
            if row["session_id"]:
                by_object[name]["sessions"].add(row["session_id"])

    result_objects = {}
    for name, data in by_object.items():
        sessions_count = max(len(data["sessions"]), data["errors"])
        correct = max(0, sessions_count - data["errors"])
        accuracy = round((correct / sessions_count) * 100) if sessions_count > 0 else 0
        result_objects[name] = {
            "errors": data["errors"],
            "total_attempts": sessions_count,
            "accuracy": accuracy,
            "last_date": data["last_date"],
            "type": data["type"]
        }

    return {
        "by_object": result_objects,
        "by_type": by_type,
        "total_tests": total_tests,
        "last_updated": time.strftime("%d.%m.%Y %H:%M", time.localtime())
    }

# Branding & Configuration

DEFAULT_BRANDING = {
    "org_name": "Институт наук о Земле ЮФУ",
    "org_short": "ЮФУ",
    "brand_title": "GeoAtlas",
    "brand_tag": "SFEDU GIS",
    "sub_title": "Электронная ведомость проверочных работ, контрольных срезов и мониторинг успеваемости",
    "logo_emoji": "🎓",
    "logo_url": "",
    "allowed_email_domain": "sfedu.ru",
    "primary_color": "#2563EB",
    "primary_hover": "#1D4ED8",
    "secondary_color": "#0284C7",
    "accent_color": "#7C3AED",
    "footer_text": "Институт наук о Земле (ИНоЗ) ЮФУ • Кафедра социально-экономической географии и природопользования",
    "university_short": "ЮФУ",
    "university_name": "Институт наук о Земле ЮФУ",
    "portal_title": "GeoAtlas"
}

def load_branding_db() -> Dict[str, Any]:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute("SELECT key, value FROM branding")
            out = {}
            for row in cur.fetchall():
                k = row["key"]
                v = row["value"]
                try:
                    out[k] = json.loads(v)
                except Exception:
                    out[k] = v
            if not out:
                for k, v in DEFAULT_BRANDING.items():
                    val_str = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                    conn.execute("INSERT OR REPLACE INTO branding (key, value) VALUES (?, ?)", (k, val_str))
                conn.commit()
                return DEFAULT_BRANDING.copy()
            res = DEFAULT_BRANDING.copy()
            res.update(out)
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
        finally:
            conn.close()

def save_branding_db(data: Dict[str, Any]) -> None:
    with _lock:
        conn = _conn()
        try:
            for k, v in data.items():
                val_str = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                conn.execute("INSERT OR REPLACE INTO branding (key, value) VALUES (?, ?)", (k, val_str))
            conn.commit()
        finally:
            conn.close()

# Teachers

DEFAULT_TEACHERS = [
    {
        "teacher_id": "teacher-ivanov",
        "username": "prof_ivanov",
        "password_hash": "6f0424d3ac26d28a4326294b3a8d580934f06f603067fb397234caf44952684c",
        "full_name": "Проф. Иванов И. И.",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Кафедра социально-экономической географии и природопользования",
        "role": "teacher"
    },
    {
        "teacher_id": "teacher-petrov",
        "username": "prof_petrov",
        "password_hash": "d43801ed6e81b4819cb58151905e8ea24dfe483710c99425c4e63bb3b20d5c3f",
        "full_name": "Доц. Петров П. П.",
        "organization": "Экономический факультет ЮФУ",
        "department": "Кафедра экономической географии",
        "role": "teacher"
    },
    {
        "teacher_id": "dean-geo",
        "username": "dean_geo",
        "password_hash": "26192eefa0331ca09ed90b188972f5c678b0140e3ed1ed0804dbaaa164b5cfaf",
        "full_name": "Декан наук о Земле ЮФУ",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Дирекция Института наук о Земле (ИНоЗ) ЮФУ",
        "role": "dean"
    },
    {
        "teacher_id": "teacher-admin",
        "username": "admin",
        "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
        "full_name": "Главный администратор",
        "organization": "Южный федеральный университет",
        "department": "Центр цифровых образовательных технологий",
        "role": "dean"
    },
    {
        "teacher_id": "teacher-smirnov",
        "username": "prof_geo",
        "password_hash": "1205ca9652c34025de31248c15fbf1506be77c22fb7c8e129321fe4a534f3f08",
        "full_name": "Проф. Смирнов А. В.",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Кафедра социально-экономической географии и природопользования",
        "role": "teacher"
    },
    {
        "teacher_id": "teacher-kuznetsova",
        "username": "prof_eco",
        "password_hash": "e285965f8e5c677a00a73b6dfa08c2e99e6cf58520dd95e19c39ba9bcfa3a700",
        "full_name": "Доц. Кузнецова М. И.",
        "organization": "Экономический факультет ЮФУ",
        "department": "Кафедра экономической географии",
        "role": "teacher"
    },
    {
        "teacher_id": "sfedu-admin",
        "username": "sfedu_admin",
        "password_hash": "81ca427e9d9e82149815dd15876388c60c11c29a86e1e582636b448de6c11d50",
        "full_name": "Деканат наук о Земле",
        "organization": "Институт наук о Земле ЮФУ",
        "department": "Деканат",
        "role": "dean"
    }
]

def load_teachers_db() -> List[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute("SELECT * FROM teachers ORDER BY teacher_id ASC")
            rows = [dict(r) for r in cur.fetchall()]
            if not rows:
                env_mode = os.environ.get("ENVIRONMENT", "development").strip().lower()
                if env_mode == "production":
                    boot_user = os.environ.get("ADMIN_BOOTSTRAP_USERNAME", "").strip()
                    boot_pass = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD", "").strip()
                    if boot_user and boot_pass:
                        import auth_service
                        conn.execute("""
                            INSERT OR IGNORE INTO teachers (
                                teacher_id, username, password_hash, full_name, organization, department, role
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            f"admin-{boot_user}",
                            boot_user,
                            auth_service.hash_password(boot_pass),
                            "Администратор платформы",
                            "GeoAtlas",
                            "",
                            "admin",
                        ))
                        conn.commit()
                else:
                    for t in DEFAULT_TEACHERS:
                        conn.execute("""
                            INSERT OR REPLACE INTO teachers (
                                teacher_id, username, password_hash, full_name, organization, department, role
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            t["teacher_id"], t["username"], t["password_hash"],
                            t.get("full_name", ""), t.get("organization", ""),
                            t.get("department", ""), t.get("role", "teacher")
                        ))
                    conn.commit()
                cur = conn.execute("SELECT * FROM teachers ORDER BY teacher_id ASC")
                rows = [dict(r) for r in cur.fetchall()]
            return rows
        finally:
            conn.close()

def save_teacher_db(teacher: Dict[str, Any]) -> None:
    pw_hash = teacher.get("password_hash", "")
    if not pw_hash and teacher.get("password"):
        import hashlib
        pw_hash = hashlib.sha256(teacher["password"].encode("utf-8")).hexdigest()
    with _lock:
        conn = _conn()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO teachers (
                    teacher_id, username, password_hash, full_name, organization, department, role
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                teacher.get("teacher_id"),
                teacher.get("username"),
                pw_hash,
                teacher.get("full_name", ""),
                teacher.get("organization", ""),
                teacher.get("department", ""),
                teacher.get("role", "teacher")
            ))
            conn.commit()
        finally:
            conn.close()

# Active Exam Session

def load_active_session_db() -> Optional[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute("SELECT session_data FROM active_session WHERE id = 1")
            row = cur.fetchone()
            if not row or not row["session_data"]:
                return None
            data = json.loads(row["session_data"])
            if not data or not isinstance(data, dict):
                return None
            return data
        except Exception:
            return None
        finally:
            conn.close()

def save_active_session_db(data: Optional[Dict[str, Any]]) -> None:
    with _lock:
        conn = _conn()
        try:
            if not data:
                conn.execute("DELETE FROM active_session WHERE id = 1")
            else:
                conn.execute("""
                    INSERT OR REPLACE INTO active_session (id, session_data, updated_at)
                    VALUES (1, ?, ?)
                """, (json.dumps(data, ensure_ascii=False), time.time()))
            conn.commit()
        finally:
            conn.close()

# Legacy Migration

def migrate_legacy_json(base_dir: str):
    import os as _os
    conn = _conn()
    try:
        has_results = conn.execute("SELECT COUNT(*) as c FROM results").fetchone()["c"]
        has_groups = conn.execute("SELECT COUNT(*) as c FROM groups").fetchone()["c"]
        has_sessions = conn.execute("SELECT COUNT(*) as c FROM sessions_history").fetchone()["c"]
        has_teachers = conn.execute("SELECT COUNT(*) as c FROM teachers").fetchone()["c"]
        has_branding = conn.execute("SELECT COUNT(*) as c FROM branding").fetchone()["c"]
        has_active = conn.execute("SELECT COUNT(*) as c FROM active_session").fetchone()["c"]
    finally:
        conn.close()

    p_results = _os.path.join(base_dir, "quiz_results.json")
    if _os.path.exists(p_results):
        try:
            if has_results == 0:
                with open(p_results, "r", encoding="utf-8") as f:
                    for r in json.load(f):
                        if not r.get("submission_id"):
                            r["submission_id"] = f"legacy_{int(time.time()*1000)}_{abs(hash(str(r))) % 100000}"
                        save_result(r)
        except Exception:
            pass
        finally:
            try:
                _os.remove(p_results)
            except Exception:
                pass

    p_groups = _os.path.join(base_dir, "groups.json")
    if _os.path.exists(p_groups):
        try:
            if has_groups == 0:
                with open(p_groups, "r", encoding="utf-8") as f:
                    for g in json.load(f):
                        save_group(g)
        except Exception:
            pass
        finally:
            try:
                _os.remove(p_groups)
            except Exception:
                pass

    p_sessions = _os.path.join(base_dir, "sessions_history.json")
    if _os.path.exists(p_sessions):
        try:
            if has_sessions == 0:
                with open(p_sessions, "r", encoding="utf-8") as f:
                    for s in json.load(f):
                        record_session_history(s)
        except Exception:
            pass
        finally:
            try:
                _os.remove(p_sessions)
            except Exception:
                pass

    p_teachers = _os.path.join(base_dir, "teachers.json")
    if _os.path.exists(p_teachers):
        try:
            if has_teachers == 0:
                with open(p_teachers, "r", encoding="utf-8") as f:
                    teachers_data = json.load(f)
                    if isinstance(teachers_data, list):
                        seen_ids = set()
                        for t in teachers_data:
                            t_id = t.get("teacher_id")
                            uname = t.get("username", "")
                            if not t_id or t_id in seen_ids:
                                t_id = f"teacher-{uname}" if uname else f"teacher-{int(time.time()*1000)}"
                                t["teacher_id"] = t_id
                            seen_ids.add(t_id)
                            save_teacher_db(t)
        except Exception:
            pass
        finally:
            try:
                _os.remove(p_teachers)
            except Exception:
                pass

    p_branding = _os.path.join(base_dir, "branding.json")
    if _os.path.exists(p_branding):
        try:
            if has_branding == 0:
                with open(p_branding, "r", encoding="utf-8") as f:
                    branding_data = json.load(f)
                    if isinstance(branding_data, dict):
                        save_branding_db(branding_data)
        except Exception:
            pass
        finally:
            try:
                _os.remove(p_branding)
            except Exception:
                pass

    p_active = _os.path.join(base_dir, "active_session.json")
    if _os.path.exists(p_active):
        try:
            if has_active == 0:
                with open(p_active, "r", encoding="utf-8") as f:
                    active_data = json.load(f)
                    if isinstance(active_data, dict) and active_data:
                        save_active_session_db(active_data)
        except Exception:
            pass
        finally:
            try:
                _os.remove(p_active)
            except Exception:
                pass


def get_site_stat(key: str = "site_visits") -> int:
    """Returns persisted integer metric value (0 if not initialized yet)."""
    with _lock:
        conn = _conn()
        try:
            row = conn.execute(
                "SELECT value FROM site_stats WHERE key = ?",
                (key,),
            ).fetchone()
            return int(row["value"]) if row and row["value"] is not None else 0
        finally:
            conn.close()


def increment_site_stat(key: str = "site_visits") -> int:
    """Atomically increments a persisted SQLite counter and returns the updated total."""
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO site_stats (key, value, updated_at)
                VALUES (?, 1, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = site_stats.value + 1,
                    updated_at = excluded.updated_at
                """,
                (key, time.time()),
            )
            row = conn.execute(
                "SELECT value FROM site_stats WHERE key = ?",
                (key,),
            ).fetchone()
            conn.commit()
            return int(row["value"]) if row else 1
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# ==================== AUTHENTICATION 2.0 (USERS, SESSIONS, CODES, OIDC) ====================

def _format_user_row(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    d["group"] = d.pop("grp", "")
    d["email_verified"] = bool(d.get("email_verified"))
    d["university_verified"] = bool(d.get("university_verified"))
    d["university_email_verified"] = bool(d.get("university_email_verified"))
    return d


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    clean = (email or "").strip().lower()
    if not clean:
        return None
    with _lock:
        conn = _conn()
        try:
            row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean,)).fetchone()
            return _format_user_row(row)
        finally:
            conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _format_user_row(row)
        finally:
            conn.close()


def get_user_by_oidc(issuer: str, subject: str) -> Optional[Dict[str, Any]]:
    with _lock:
        conn = _conn()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE oidc_issuer = ? AND oidc_subject = ?",
                (issuer, subject),
            ).fetchone()
            return _format_user_row(row)
        finally:
            conn.close()


def upsert_pending_registration_user(
    email: str,
    full_name: str,
    password_hash: str,
    grp: str = "",
    accepted_terms_at: Optional[float] = None,
) -> Tuple[Dict[str, Any], bool]:
    """Creates an unverified student user or updates an unverified pending record.
    Returns (user_dict, is_already_verified). Never overwrites an already verified account!"""
    clean_email = (email or "").strip().lower()
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = ?",
                (clean_email,),
            ).fetchone()
            if existing:
                if existing["email_verified"]:
                    conn.commit()
                    return _format_user_row(existing), True
                conn.execute(
                    """
                    UPDATE users
                    SET full_name = ?, grp = ?, password_hash = ?, accepted_terms_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (full_name, grp, password_hash, accepted_terms_at or now, now, existing["id"]),
                )
                row = conn.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone()
                conn.commit()
                return _format_user_row(row), False

            cur = conn.execute(
                """
                INSERT INTO users (
                    email, full_name, grp, password_hash, role,
                    email_verified, university_verified, university_email_verified,
                    accepted_terms_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'student', 0, 0, 0, ?, ?, ?)
                """,
                (clean_email, full_name, grp, password_hash, accepted_terms_at or now, now, now),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
            conn.commit()
            return _format_user_row(row), False
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def upsert_oidc_user(
    email: str,
    full_name: str,
    issuer: str,
    subject: str,
    university_verified: bool = True,
) -> Dict[str, Any]:
    clean_email = (email or "").strip().lower()
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM users WHERE oidc_issuer = ? AND oidc_subject = ?",
                (issuer, subject),
            ).fetchone()
            if not row:
                row = conn.execute(
                    "SELECT * FROM users WHERE LOWER(email) = ?",
                    (clean_email,),
                ).fetchone()

            if row:
                conn.execute(
                    """
                    UPDATE users
                    SET full_name = CASE WHEN full_name = '' THEN ? ELSE full_name END,
                        email_verified = 1,
                        email_verified_at = COALESCE(email_verified_at, ?),
                        university_verified = CASE WHEN ? THEN 1 ELSE university_verified END,
                        university_email_verified = 1,
                        university_auth_provider = 'oidc',
                        university_verified_at = COALESCE(university_verified_at, ?),
                        oidc_issuer = ?,
                        oidc_subject = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        full_name,
                        now,
                        1 if university_verified else 0,
                        now,
                        issuer,
                        subject,
                        now,
                        row["id"],
                    ),
                )
                updated = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
                conn.commit()
                return _format_user_row(updated)

            cur = conn.execute(
                """
                INSERT INTO users (
                    email, full_name, grp, password_hash, role,
                    email_verified, email_verified_at,
                    university_verified, university_email_verified,
                    university_auth_provider, university_verified_at,
                    oidc_issuer, oidc_subject, accepted_terms_at, created_at, updated_at
                ) VALUES (?, ?, '', '', 'student', 1, ?, ?, 1, 'oidc', ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_email,
                    full_name or clean_email,
                    now,
                    1 if university_verified else 0,
                    now,
                    issuer,
                    subject,
                    now,
                    now,
                    now,
                ),
            )
            created = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
            conn.commit()
            return _format_user_row(created)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def mark_user_email_verified(email: str, university_email_verified: bool = False) -> Optional[Dict[str, Any]]:
    clean_email = (email or "").strip().lower()
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                """
                UPDATE users
                SET email_verified = 1,
                    email_verified_at = COALESCE(email_verified_at, ?),
                    university_email_verified = CASE WHEN ? THEN 1 ELSE university_email_verified END,
                    updated_at = ?
                WHERE LOWER(email) = ?
                """,
                (now, 1 if university_email_verified else 0, now, clean_email),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean_email,)).fetchone()
            return _format_user_row(row)
        finally:
            conn.close()


def update_user_password(user_id: int, new_password_hash: str) -> None:
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (new_password_hash, now, user_id),
            )
            conn.commit()
        finally:
            conn.close()


def set_user_university_verified(user_id: int, verified: bool, provider: str = "admin") -> Optional[Dict[str, Any]]:
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                """
                UPDATE users
                SET university_verified = ?,
                    university_auth_provider = ?,
                    university_verified_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (1 if verified else 0, provider if verified else "", now if verified else None, now, user_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return _format_user_row(row)
        finally:
            conn.close()


def create_email_verification_code(
    email: str,
    purpose: str,
    code_hash: str,
    ttl_seconds: int = 600,
    resend_cooldown: int = 60,
    max_attempts: int = 5,
) -> Tuple[bool, int]:
    """Stores a single-use hashed verification/reset code. Returns (created, retry_after_seconds)."""
    clean_email = (email or "").strip().lower()
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            latest = conn.execute(
                """
                SELECT resend_available_at FROM email_verifications
                WHERE email = ? AND purpose = ? AND used_at IS NULL AND expires_at > ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (clean_email, purpose, now),
            ).fetchone()
            if latest and latest["resend_available_at"] > now:
                retry_after = max(1, int(latest["resend_available_at"] - now))
                conn.commit()
                return False, retry_after

            # Invalidate prior active codes for the same email/purpose
            conn.execute(
                "UPDATE email_verifications SET used_at = ? WHERE email = ? AND purpose = ? AND used_at IS NULL",
                (now, clean_email, purpose),
            )
            conn.execute(
                """
                INSERT INTO email_verifications (
                    email, purpose, code_hash, attempts, max_attempts,
                    expires_at, used_at, created_at, resend_available_at
                ) VALUES (?, ?, ?, 0, ?, ?, NULL, ?, ?)
                """,
                (clean_email, purpose, code_hash, max_attempts, now + ttl_seconds, now, now + resend_cooldown),
            )
            conn.commit()
            return True, 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def verify_email_code_atomic(email: str, purpose: str, candidate_code_hash: str) -> Tuple[bool, str]:
    """Verifies a hashed single-use code atomically with max_attempts enforcement."""
    clean_email = (email or "").strip().lower()
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT * FROM email_verifications
                WHERE email = ? AND purpose = ? AND used_at IS NULL
                ORDER BY created_at DESC LIMIT 1
                """,
                (clean_email, purpose),
            ).fetchone()
            if not row:
                conn.commit()
                return False, "Код подтверждения не найден или уже использован."
            if now > row["expires_at"]:
                conn.execute("UPDATE email_verifications SET used_at = ? WHERE id = ?", (now, row["id"]))
                conn.commit()
                return False, "Срок действия кода истёк. Запросите новый код."
            if row["attempts"] >= row["max_attempts"]:
                conn.execute("UPDATE email_verifications SET used_at = ? WHERE id = ?", (now, row["id"]))
                conn.commit()
                return False, "Превышено максимальное количество попыток (5). Запросите новый код."

            import hmac as _hmac
            if not _hmac.compare_digest(row["code_hash"], candidate_code_hash):
                new_attempts = row["attempts"] + 1
                if new_attempts >= row["max_attempts"]:
                    conn.execute(
                        "UPDATE email_verifications SET attempts = ?, used_at = ? WHERE id = ?",
                        (new_attempts, now, row["id"]),
                    )
                    conn.commit()
                    return False, "Превышено максимальное количество попыток (5). Запросите новый код."
                conn.execute("UPDATE email_verifications SET attempts = ? WHERE id = ?", (new_attempts, row["id"]))
                conn.commit()
                return False, "Неверный код подтверждения."

            conn.execute("UPDATE email_verifications SET used_at = ? WHERE id = ?", (now, row["id"]))
            conn.commit()
            return True, "ok"
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def create_user_session(session_id_hash: str, user_id: int, ttl_seconds: int = 7 * 24 * 3600, auth_method: str = "password") -> None:
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                """
                INSERT INTO user_sessions (session_id_hash, user_id, created_at, expires_at, revoked, auth_method)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (session_id_hash, user_id, now, now + ttl_seconds, auth_method),
            )
            conn.commit()
        finally:
            conn.close()


def get_active_user_by_session_hash(session_id_hash: str) -> Optional[Dict[str, Any]]:
    if not session_id_hash:
        return None
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            row = conn.execute(
                """
                SELECT u.*, s.auth_method as session_auth_method, s.expires_at as session_expires_at
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.session_id_hash = ? AND s.revoked = 0 AND s.expires_at > ?
                """,
                (session_id_hash, now),
            ).fetchone()
            return _format_user_row(row)
        finally:
            conn.close()


def revoke_session_by_hash(session_id_hash: str) -> None:
    if not session_id_hash:
        return
    with _lock:
        conn = _conn()
        try:
            conn.execute("UPDATE user_sessions SET revoked = 1 WHERE session_id_hash = ?", (session_id_hash,))
            conn.commit()
        finally:
            conn.close()


def revoke_all_user_sessions(user_id: int) -> None:
    with _lock:
        conn = _conn()
        try:
            conn.execute("UPDATE user_sessions SET revoked = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()


def update_teacher_password_hash(teacher_id: str, new_password_hash: str) -> None:
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "UPDATE teachers SET password_hash = ? WHERE teacher_id = ?",
                (new_password_hash, teacher_id),
            )
            conn.commit()
        finally:
            conn.close()


def save_oidc_state(state_hash: str, nonce: str, code_verifier: str, next_url: str = "/", ttl_seconds: int = 600) -> None:
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                """
                INSERT INTO oidc_states (state_hash, nonce, code_verifier, next_url, expires_at, used_at)
                VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (state_hash, nonce, code_verifier, next_url, now + ttl_seconds),
            )
            conn.commit()
        finally:
            conn.close()


def pop_oidc_state(state_hash: str) -> Optional[Dict[str, Any]]:
    now = time.time()
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM oidc_states WHERE state_hash = ? AND used_at IS NULL AND expires_at > ?",
                (state_hash, now),
            ).fetchone()
            if not row:
                conn.commit()
                return None
            conn.execute("UPDATE oidc_states SET used_at = ? WHERE state_hash = ?", (now, state_hash))
            conn.commit()
            return dict(row)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_user_analytics_stats(days: int = 30) -> Dict[str, Any]:
    """Aggregated, non-PII user, activity, test and map usage metrics for the admin dashboard."""
    from datetime import datetime, timedelta, timezone

    allowed_days = {7, 14, 30, 90}
    period_days = days if days in allowed_days else 30

    now_dt = datetime.now(timezone.utc)
    today_start_dt = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_ts = today_start_dt.timestamp()
    cutoff_7d_ts = (now_dt - timedelta(days=7)).timestamp()
    cutoff_30d_ts = (now_dt - timedelta(days=30)).timestamp()
    series_start_dt = today_start_dt - timedelta(days=period_days - 1)
    series_start_ts = series_start_dt.timestamp()

    with _lock:
        conn = _conn()
        try:
            u_row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_users,
                    COALESCE(SUM(CASE WHEN email_verified = 1 THEN 1 ELSE 0 END), 0) AS verified_users,
                    COALESCE(SUM(CASE WHEN email_verified = 0 THEN 1 ELSE 0 END), 0) AS unverified_users,
                    COALESCE(SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END), 0) AS reg_today,
                    COALESCE(SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END), 0) AS reg_7d,
                    COALESCE(SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END), 0) AS reg_30d
                FROM users
                """,
                (today_start_ts, cutoff_7d_ts, cutoff_30d_ts),
            ).fetchone()

            act_row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT CASE WHEN created_at >= ? THEN user_id END) AS active_7d,
                    COUNT(DISTINCT CASE WHEN created_at >= ? THEN user_id END) AS active_30d
                FROM user_sessions
                """,
                (cutoff_7d_ts, cutoff_30d_ts),
            ).fetchone()

            reg_daily_rows = conn.execute(
                """
                SELECT strftime('%Y-%m-%d', created_at, 'unixepoch') AS day, COUNT(*) AS cnt
                FROM users
                WHERE created_at >= ?
                GROUP BY day
                """,
                (series_start_ts,),
            ).fetchall()
            reg_by_day = {r["day"]: int(r["cnt"]) for r in reg_daily_rows if r["day"]}

            act_daily_rows = conn.execute(
                """
                SELECT strftime('%Y-%m-%d', created_at, 'unixepoch') AS day, COUNT(DISTINCT user_id) AS cnt
                FROM user_sessions
                WHERE created_at >= ?
                GROUP BY day
                """,
                (series_start_ts,),
            ).fetchall()
            act_by_day = {r["day"]: int(r["cnt"]) for r in act_daily_rows if r["day"]}

            completed_tests = int(conn.execute("SELECT COUNT(*) FROM results").fetchone()[0])

            map_rows = conn.execute(
                """
                SELECT quiz_type AS region, COUNT(*) AS cnt
                FROM results
                WHERE quiz_type IS NOT NULL AND TRIM(quiz_type) != ''
                GROUP BY quiz_type
                ORDER BY cnt DESC
                LIMIT 12
                """
            ).fetchall()
            map_usage = [{"region": r["region"], "count": int(r["cnt"])} for r in map_rows]

            stat_row = conn.execute("SELECT value FROM site_stats WHERE key = 'site_visits'").fetchone()
            site_visits = int(stat_row["value"]) if stat_row else 0
        finally:
            conn.close()

    registrations_series = []
    active_users_series = []
    for offset in range(period_days):
        day_str = (series_start_dt + timedelta(days=offset)).strftime("%Y-%m-%d")
        registrations_series.append({"date": day_str, "count": reg_by_day.get(day_str, 0)})
        active_users_series.append({"date": day_str, "count": act_by_day.get(day_str, 0)})

    return {
        "period_days": period_days,
        "users": {
            "total": int(u_row["total_users"] or 0),
            "verified": int(u_row["verified_users"] or 0),
            "unverified": int(u_row["unverified_users"] or 0),
            "registrations_today": int(u_row["reg_today"] or 0),
            "registrations_7d": int(u_row["reg_7d"] or 0),
            "registrations_30d": int(u_row["reg_30d"] or 0),
            "active_7d": int(act_row["active_7d"] or 0),
            "active_30d": int(act_row["active_30d"] or 0),
            "activity_source": "user_sessions",
        },
        "charts": {
            "registrations_by_day": registrations_series,
            "active_users_by_day": active_users_series,
        },
        "platform": {
            "completed_tests": completed_tests,
            "site_visits": site_visits,
            "map_usage": map_usage,
        },
    }
