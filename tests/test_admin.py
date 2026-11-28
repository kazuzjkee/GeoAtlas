def test_admin_groups_unauthorized(anon_client):
    res = anon_client.get("/api/admin/groups")
    assert res.status_code == 401

def test_admin_groups_ok(client, auth_headers):
    res = client.get("/api/admin/groups", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_admin_results_ok(client, auth_headers):
    res = client.get("/api/admin/results", headers=auth_headers)
    assert res.status_code == 200


def test_user_analytics_empty_db_and_access_control(anon_client, client, auth_headers):
    # Guest blocked
    assert anon_client.get("/api/admin/user-analytics").status_code == 401
    admin_guest = anon_client.get("/admin", follow_redirects=False)
    assert admin_guest.status_code in (302, 401)

    # Empty DB returns zero metrics cleanly
    res = client.get("/api/admin/user-analytics?days=30", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["period_days"] == 30
    assert body["users"]["total"] == 0
    assert body["users"]["verified"] == 0
    assert body["users"]["unverified"] == 0
    assert len(body["charts"]["registrations_by_day"]) == 30
    assert body["platform"]["completed_tests"] == 0


def test_user_analytics_periods_verified_activity_and_student_forbidden(anon_client, client, auth_headers):
    import time
    import db
    import auth_service

    now = time.time()
    conn = db._conn()
    try:
        # 1 verified user registered today, 1 unverified registered 10 days ago, 1 verified registered 25 days ago
        conn.execute(
            """
            INSERT INTO users (email, full_name, grp, password_hash, role, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'student', ?, ?, ?)
            """,
            ("u1@sfedu.ru", "U1", "G1", "hash_secret_1", 1, now - 60, now - 60),
        )
        u1_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """
            INSERT INTO users (email, full_name, grp, password_hash, role, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'student', ?, ?, ?)
            """,
            ("u2@gmail.com", "U2", "G1", "hash_secret_2", 0, now - 10 * 86400, now - 10 * 86400),
        )
        conn.execute(
            """
            INSERT INTO users (email, full_name, grp, password_hash, role, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'student', ?, ?, ?)
            """,
            ("u3@gmail.com", "U3", "G2", "hash_secret_3", 1, now - 25 * 86400, now - 25 * 86400),
        )
        u3_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Sessions: u1 active today, u3 active 12 days ago
        conn.execute(
            "INSERT INTO user_sessions (session_id_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            ("sess_1", u1_id, now - 30, now + 3600),
        )
        conn.execute(
            "INSERT INTO user_sessions (session_id_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            ("sess_3", u3_id, now - 12 * 86400, now + 3600),
        )

        # Completed test on Rostov map
        conn.execute(
            "INSERT INTO results (submission_id, date, email, name, grp, quiz_type, score, max_score, accuracy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("sub_ua_1", "2026-11-28", "u1@sfedu.ru", "U1", "G1", "rostov", 10, 10, 100),
        )
        conn.commit()
    finally:
        conn.close()

    # Period = 7 days
    r7 = client.get("/api/admin/user-analytics?days=7", headers=auth_headers)
    assert r7.status_code == 200
    d7 = r7.json()
    assert d7["period_days"] == 7
    assert len(d7["charts"]["registrations_by_day"]) == 7
    assert d7["users"]["total"] == 3
    assert d7["users"]["verified"] == 2
    assert d7["users"]["unverified"] == 1
    assert d7["users"]["registrations_today"] == 1
    assert d7["users"]["registrations_7d"] == 1
    assert d7["users"]["registrations_30d"] == 3
    assert d7["users"]["active_7d"] == 1
    assert d7["users"]["active_30d"] == 2
    assert d7["platform"]["completed_tests"] == 1
    assert d7["platform"]["map_usage"][0]["region"] == "rostov"

    # No PII leaked
    raw_text = r7.text
    assert "u1@sfedu.ru" not in raw_text
    assert "hash_secret" not in raw_text
    assert "sess_1" not in raw_text

    # Register normal student -> role must be 'student' and /admin + analytics must be forbidden (403)
    anon_client.post("/api/auth/register", json={
        "email": "student_reg@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Student Reg",
        "accept_terms": True,
    })
    code = next(m["code"] for m in reversed(auth_service.MOCK_MAILBOX) if m["to"] == "student_reg@gmail.com")
    anon_client.post("/api/auth/verify-code", json={"email": "student_reg@gmail.com", "code": code})
    me = anon_client.get("/api/auth/me").json()
    assert me["user"]["role"] == "student"
    assert anon_client.get("/api/admin/user-analytics").status_code == 403
    assert anon_client.get("/admin").status_code == 403


def test_admin_bootstrap_production_creates_once_no_duplicates(tmp_path, monkeypatch):
    import db

    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "boot_admin.db"))
    db.init_db()
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_USERNAME", "bootadmin")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "StrongBootPass123!")

    teachers_first = db.load_teachers_db()
    assert len(teachers_first) == 1
    assert teachers_first[0]["username"] == "bootadmin"
    assert teachers_first[0]["role"] == "dean"

    # Second call must not duplicate
    teachers_second = db.load_teachers_db()
    assert len(teachers_second) == 1
