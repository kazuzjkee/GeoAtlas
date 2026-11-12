import os
import json
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

DATA_DIR = os.environ.get("GEOATLAS_DATA_DIR", "/tmp")
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
            """)
            conn.commit()
            try:
                conn.execute("ALTER TABLE results ADD COLUMN is_adaptive INTEGER DEFAULT 0")
                conn.commit()
            except Exception:
                pass  # колонка уже есть
        finally:
            conn.close()

# ---------- RESULTS ----------

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
                            client_timestamp=?
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

# ---------- GROUPS ----------

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

# ---------- AUTH ----------

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

# ---------- SESSIONS HISTORY ----------

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

# ---------- HEATMAP ----------

def get_student_mistakes_heatmap(email: str, region: Optional[str] = None) -> Dict[str, Any]:
    """
    Агрегирует все ошибки студента по объектам.
    Возвращает:
    - by_object: {object_name: {errors, total_attempts, accuracy, last_date}}
    - by_type: {district|river|center|neighbor|puzzle: {errors, total_attempts}}
    - total_tests: общее число тестов
    - last_updated: ISO timestamp
    """
    email_clean = (email or "").strip().lower()
    if not email_clean:
        return {"by_object": {}, "by_type": {}, "total_tests": 0}

    with _lock:
        conn = _conn()
        try:
            # Загружаем все результаты студента
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

    # Пул всех известных объектов (для подсчёта "сколько раз спрашивали")
    # Восстанавливаем из mistakes_log + предполагаем, что каждый тест спрашивал 
    # примерно 15 объектов (стандарт), из которых ошибки — в mistakes_log.
    # Это эвристика: точнее посчитать нельзя без сохранения всех вопросов.
    for row in rows:
        quiz_type = str(row["quiz_type"] or "").lower()
        date_str = str(row["date"] or "")
        accuracy = int(row["accuracy"] or 0)
        if date_str:
            last_date = date_str

        # Парсим mistakes_log (JSON-массив строк — имён объектов)
        try:
            mistakes = json.loads(row["mistakes_log"] or "[]")
            if not isinstance(mistakes, list):
                mistakes = []
        except Exception:
            mistakes = []

        # Определяем тип теста
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

        # Инициализируем счётчик типа
        if q_type not in by_type:
            by_type[q_type] = {"errors": 0, "total_tests": 0}
        by_type[q_type]["total_tests"] += 1
        by_type[q_type]["errors"] += len(mistakes)

        # Каждая ошибка увеличивает счётчик объекта
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

    # Рассчитываем accuracy для каждого объекта
    # Эвристика: если объект встретился в N сессиях, из них ошибочно — 
    # min(errors, N). accuracy = (N - errors) / N * 100.
    # Для базовой оценки достаточно, точнее — при накоплении данных.
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

# ---------- MIGRATION ----------

def migrate_legacy_json(base_dir: str):
    import os as _os
    conn = _conn()
    try:
        has_results = conn.execute("SELECT COUNT(*) as c FROM results").fetchone()["c"]
        has_groups = conn.execute("SELECT COUNT(*) as c FROM groups").fetchone()["c"]
        has_sessions = conn.execute("SELECT COUNT(*) as c FROM sessions_history").fetchone()["c"]
    finally:
        conn.close()

    if has_results == 0:
        p = _os.path.join(base_dir, "quiz_results.json")
        if _os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for r in json.load(f):
                        if not r.get("submission_id"):
                            r["submission_id"] = f"legacy_{int(time.time()*1000)}_{abs(hash(str(r))) % 100000}"
                        save_result(r)
            except Exception:
                pass

    if has_groups == 0:
        p = _os.path.join(base_dir, "groups.json")
        if _os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for g in json.load(f):
                        save_group(g)
            except Exception:
                pass

    if has_sessions == 0:
        p = _os.path.join(base_dir, "sessions_history.json")
        if _os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for s in json.load(f):
                        record_session_history(s)
            except Exception:
                pass
