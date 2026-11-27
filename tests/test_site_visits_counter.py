import asyncio
import concurrent.futures
import json
import os
import sqlite3
import tempfile
import threading
import time
import urllib.request

import pytest
import websockets

import db
import server
from tests.test_duel import _http_json, _live_uvicorn


@pytest.fixture
def isolated_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "geoatlas_counter_test.db")
        monkeypatch.setattr(db, "DATA_DIR", tmpdir)
        monkeypatch.setattr(db, "DB_FILE", db_path)
        db.init_db()
        yield db_path


def test_counter_initial_zero_without_row(client, isolated_db):
    conn = sqlite3.connect(isolated_db)
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM site_stats WHERE key='site_visits'").fetchone()[0]
        assert cnt == 0
    finally:
        conn.close()

    assert db.get_site_stat("site_visits") == 0

    res = client.get("/api/stats/visits")
    assert res.status_code == 200
    payload = res.json()
    assert payload["visits"] == 0
    assert payload["label"] == "Посещений сайта"
    assert "no-store" in res.headers.get("Cache-Control", "")


def test_home_page_increments_counter_and_read_api_is_idempotent(client, isolated_db):
    assert client.get("/api/stats/visits").json()["visits"] == 0

    r1 = client.get("/")
    assert r1.status_code == 200
    assert "Посещений сайта:" in r1.text
    assert 'id="site-visits-badge"' in r1.text
    assert client.get("/api/stats/visits").json()["visits"] == 1
    assert client.get("/api/stats/visits").json()["visits"] == 1

    r2 = client.get("/index.html")
    assert r2.status_code == 200
    assert client.get("/api/stats/visits").json()["visits"] == 2

    # Prefetch / SW pre-cache headers must not inflate counter
    assert client.get("/", headers={"Sec-Purpose": "prefetch"}).status_code == 200
    assert client.get("/", headers={"Purpose": "prefetch"}).status_code == 200
    assert client.get("/", headers={"X-SW-Precache": "1"}).status_code == 200
    assert client.get("/api/stats/visits").json()["visits"] == 2


def test_concurrent_home_requests_lose_no_increments(isolated_db):
    total_hits = 24
    barrier = threading.Barrier(total_hits)

    with _live_uvicorn() as port:
        def hit_home():
            barrier.wait(timeout=5)
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/",
                headers={"Host": f"127.0.0.1:{port}"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.status

        with concurrent.futures.ThreadPoolExecutor(max_workers=total_hits) as pool:
            statuses = list(pool.map(lambda _: hit_home(), range(total_hits)))

    assert all(s == 200 for s in statuses)
    assert db.get_site_stat("site_visits") == total_hits


def test_static_assets_tiles_apis_and_websocket_do_not_increment(client, isolated_db, monkeypatch):
    client.get("/")
    assert db.get_site_stat("site_visits") == 1

    # Map pages (including /?region=rostov), static JS/CSS/images, tiles, and polling APIs
    assert client.get("/?region=rostov").status_code == 200
    assert client.get("/map/rostov").status_code == 200
    assert client.get("/rostov_quiz_map.html").status_code == 200
    assert client.get("/quiz.js").status_code == 200
    assert client.get("/sw.js").status_code == 200
    assert client.get("/public/map.css").status_code == 200
    assert client.get("/public/images/logo-sfedu-on-light.png").status_code == 200
    monkeypatch.setenv("CARTO_KEY", "")
    assert client.get("/tiles/carto/voyager/7/78/44.png").status_code == 503
    assert client.get("/api/maps").status_code == 200
    assert client.get("/api/region/context?region=rostov").status_code == 200
    assert client.get("/api/stats/visits").status_code == 200
    assert db.get_site_stat("site_visits") == 1

    # Real WebSocket duel connect + ping + state polling must not change visits
    with _live_uvicorn() as port:
        _, created = _http_json(port, "/api/duel/create", {"mode": "center", "region": "rostov", "host_name": "WS"})
        rid = created["room_id"]
        pid = created["player_id"]

        async def _ws_ping():
            async with websockets.connect(f"ws://127.0.0.1:{port}/ws/duel/{rid}/{pid}") as ws:
                await ws.send(json.dumps({"type": "ping"}))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                assert json.loads(raw)["type"] in ("pong", "player_connected", "game_start")

        asyncio.run(_ws_ping())
        _, state = _http_json(port, f"/api/duel/state/{rid}?player_id={pid}")
        assert state["status"] == "ok"

    assert db.get_site_stat("site_visits") == 1


def test_counter_persists_across_reinit_and_preserves_legacy_db_schema(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        legacy_db = os.path.join(tmpdir, "legacy_prod.db")

        # Simulate existing production SQLite DB prior to site_stats migration
        conn = sqlite3.connect(legacy_db)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.executescript("""
            CREATE TABLE results (
                submission_id TEXT PRIMARY KEY,
                date TEXT, email TEXT, name TEXT, grp TEXT, quiz_type TEXT,
                score INTEGER, max_score INTEGER, accuracy INTEGER, time_spent TEXT,
                is_exam INTEGER, exam_token TEXT, violations INTEGER, exam_status TEXT,
                session_id TEXT, teacher_id TEXT, mistakes_log TEXT,
                client_timestamp INTEGER, created_at REAL
            );
            CREATE TABLE groups (
                id TEXT PRIMARY KEY, name TEXT, description TEXT,
                students TEXT, teacher_id TEXT, created_at TEXT, updated_at REAL
            );
            CREATE TABLE auth_sessions (email TEXT PRIMARY KEY, code TEXT, expires_at REAL, name TEXT, grp TEXT);
            CREATE TABLE sessions_history (session_id TEXT PRIMARY KEY, data TEXT, updated_at REAL);
            CREATE TABLE teachers (
                teacher_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, full_name TEXT, organization TEXT, department TEXT, role TEXT
            );
            CREATE TABLE branding (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE active_session (id INTEGER PRIMARY KEY CHECK (id = 1), session_data TEXT NOT NULL, updated_at REAL);
        """)
        conn.execute(
            "INSERT INTO results (submission_id, email, name, grp, quiz_type, score, accuracy) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("sub-legacy-1", "student@sfedu.ru", "Иванов И.", "Гео-51", "center", 18, 90),
        )
        conn.execute(
            "INSERT INTO groups (id, name, description, students) VALUES (?, ?, ?, ?)",
            ("grp-1", "Гео-51", "Тест", "[]"),
        )
        conn.execute(
            "INSERT INTO branding (key, value) VALUES (?, ?)",
            ("university_short", "ЮФУ"),
        )
        conn.commit()
        conn.close()

        monkeypatch.setattr(db, "DATA_DIR", tmpdir)
        monkeypatch.setattr(db, "DB_FILE", legacy_db)

        # Compatible migration adds site_stats without touching existing records
        db.init_db()
        assert db.get_site_stat("site_visits") == 0
        assert db.increment_site_stat("site_visits") == 1
        assert db.increment_site_stat("site_visits") == 2

        # Re-initializing app/DB (container restart/update) preserves count and legacy rows
        db.init_db()
        assert db.get_site_stat("site_visits") == 2

        verify_conn = sqlite3.connect(legacy_db)
        try:
            mode = verify_conn.execute("PRAGMA journal_mode;").fetchone()[0]
            assert str(mode).lower() == "wal"

            cols = [r[1] for r in verify_conn.execute("PRAGMA table_info(site_stats)").fetchall()]
            assert cols == ["key", "value", "updated_at"]

            res_row = verify_conn.execute("SELECT email, score FROM results WHERE submission_id='sub-legacy-1'").fetchone()
            assert res_row == ("student@sfedu.ru", 18)

            grp_row = verify_conn.execute("SELECT name FROM groups WHERE id='grp-1'").fetchone()
            assert grp_row == ("Гео-51",)

            brand_row = verify_conn.execute("SELECT value FROM branding WHERE key='university_short'").fetchone()
            assert brand_row == ("ЮФУ",)
        finally:
            verify_conn.close()
