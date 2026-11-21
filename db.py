import os
import json
import sqlite3
import threading
import time
import tempfile
from typing import Any, Dict, List, Optional

DATA_DIR = os.environ.get("GEOATLAS_DATA_DIR", tempfile.gettempdir())
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "geoatlas.db")
_lock = threading.Lock()

def _conn():
    c = sqlite3.connect(DB_FILE, timeout=10.0)
    c.row_factory = sqlite3.Row
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
            """)
            conn.commit()
            try:
                conn.execute("ALTER TABLE results ADD COLUMN is_adaptive INTEGER DEFAULT 0")
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
    "footer_text": "Институт наук о Земле ЮФУ • Кафедра физической географии, экологии и охраны природы",
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
        "department": "Кафедра физической географии",
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
        "department": "Деканат геолого-географического факультета",
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
        "department": "Кафедра физической географии",
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
