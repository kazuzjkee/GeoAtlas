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


def test_user_analytics_empty_db_and_access_control(tmp_path, monkeypatch, anon_client, client, auth_headers):
    import db

    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "empty_analytics.db"))
    db.init_db()

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


def test_user_analytics_periods_verified_activity_and_student_forbidden(tmp_path, monkeypatch, anon_client, client, auth_headers):
    import time
    import db
    import auth_service

    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "analytics_data.db"))
    db.init_db()

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


def test_admin_bootstrap_production_creates_once_no_duplicates(tmp_path, monkeypatch, anon_client):
    import base64
    import auth_service
    import db

    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "boot_admin.db"))
    db.init_db()
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_USERNAME", "bootadmin")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "StrongBootPass123!")

    teachers_first = db.load_teachers_db()
    assert len(teachers_first) == 1
    assert teachers_first[0]["username"] == "bootadmin"
    assert teachers_first[0]["role"] == "admin"
    assert auth_service.verify_password("StrongBootPass123!", teachers_first[0]["password_hash"])

    # Second call with changed env must not overwrite existing admin/password or duplicate
    monkeypatch.setenv("ADMIN_BOOTSTRAP_USERNAME", "otheradmin")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "NewAttemptPass999!")
    teachers_second = db.load_teachers_db()
    assert len(teachers_second) == 1
    assert teachers_second[0]["username"] == "bootadmin"
    assert auth_service.verify_password("StrongBootPass123!", teachers_second[0]["password_hash"])

    # Verify HTTP access with bootstrapped admin credentials (Basic Auth & form login)
    cred = base64.b64encode(b"bootadmin:StrongBootPass123!").decode()
    headers = {"Authorization": f"Basic {cred}"}
    assert anon_client.get("/admin", headers=headers).status_code == 200
    assert anon_client.get("/api/admin/user-analytics", headers=headers).status_code == 200

    # Login via /api/auth/login (HTTPS in production) -> /api/auth/me returns role='admin' -> /admin & API accessible
    from fastapi.testclient import TestClient
    import server as srv
    prod_client = TestClient(srv.app, base_url="https://testserver")
    login_res = prod_client.post("/api/auth/login", json={"email": "bootadmin", "password": "StrongBootPass123!"})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["role"] == "admin"
    assert prod_client.get("/api/auth/me").json()["user"]["role"] == "admin"
    assert prod_client.get("/admin").status_code == 200
    assert prod_client.get("/api/admin/user-analytics").status_code == 200


def test_admin_bootstrap_with_populated_teachers_and_existing_email(tmp_path, monkeypatch, anon_client):
    import auth_service
    import db

    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "boot_populated.db"))
    db.init_db()
    monkeypatch.setenv("ENVIRONMENT", "production")

    # 1. Pre-populate teachers table with another teacher
    conn = db._conn()
    try:
        conn.execute(
            "INSERT INTO teachers (teacher_id, username, password_hash, full_name, organization, department, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("t-1", "existing_teacher", auth_service.hash_password("TeacherPass123!"), "T1", "SFEDU", "Geo", "teacher"),
        )
        conn.commit()
    finally:
        conn.close()

    # 2. Register an existing student with email & verified status
    pw_hash = auth_service.hash_password("UserSecretPass123!")
    u, _ = db.upsert_pending_registration_user("promo@sfedu.ru", "Promo User", pw_hash, "G1")
    db.mark_user_email_verified("promo@sfedu.ru", university_email_verified=True)
    # Normal sfedu.ru user must stay student
    assert db.get_user_by_email("promo@sfedu.ru")["role"] == "student"

    # 3. Wrong bootstrap password must NOT promote existing user
    monkeypatch.setenv("ADMIN_BOOTSTRAP_USERNAME", "promo@sfedu.ru")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "WrongBootstrapPass!")
    db.ensure_bootstrap_admin()
    assert db.get_user_by_email("promo@sfedu.ru")["role"] == "student"

    # 4. Exact bootstrap password promotes existing user to admin even when teachers is non-empty
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "UserSecretPass123!")
    db.ensure_bootstrap_admin()
    promoted = db.get_user_by_email("promo@sfedu.ru")
    assert promoted["role"] == "admin"
    assert auth_service.verify_password("UserSecretPass123!", promoted["password_hash"])

    # 5. Subsequent run with different password must NOT reset promoted user's password
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "AttemptReset999!")
    db.ensure_bootstrap_admin()
    assert auth_service.verify_password("UserSecretPass123!", db.get_user_by_email("promo@sfedu.ru")["password_hash"])

    # 6. Bootstrap a brand-new admin by email on a DB where teachers already has non-admin rows
    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "boot_new_email_admin.db"))
    db.init_db()
    conn = db._conn()
    try:
        conn.execute(
            "INSERT INTO teachers (teacher_id, username, password_hash, full_name, organization, department, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("t-2", "other_teacher", auth_service.hash_password("TeacherPass123!"), "T2", "SFEDU", "Geo", "teacher"),
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setenv("ADMIN_BOOTSTRAP_USERNAME", "newadmin@sfedu.ru")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "BrandNewAdmin123!")
    db.ensure_bootstrap_admin()
    new_admin = db.get_user_by_email("newadmin@sfedu.ru")
    assert new_admin is not None
    assert new_admin["role"] == "admin"

    # 7. Login via /api/auth/login with email (over HTTPS in production mode) -> role='admin' -> /admin 200
    from fastapi.testclient import TestClient
    import server as srv
    prod_client = TestClient(srv.app, base_url="https://testserver")
    l_res = prod_client.post("/api/auth/login", json={"email": "newadmin@sfedu.ru", "password": "BrandNewAdmin123!"})
    assert l_res.status_code == 200
    assert l_res.json()["user"]["role"] == "admin"
    assert prod_client.get("/api/auth/me").json()["user"]["role"] == "admin"
    assert prod_client.get("/admin").status_code == 200
    assert prod_client.get("/api/admin/user-analytics").status_code == 200

    # 8. Another sfedu.ru student must remain student and get 403 on /admin
    prod_client.post("/api/auth/logout")
    s_hash = auth_service.hash_password("StudentPass123!")
    db.upsert_pending_registration_user("ordinary@sfedu.ru", "Ordinary", s_hash, "G2")
    db.mark_user_email_verified("ordinary@sfedu.ru", university_email_verified=True)
    sl_res = prod_client.post("/api/auth/login", json={"email": "ordinary@sfedu.ru", "password": "StudentPass123!"})
    assert sl_res.status_code == 200
    assert sl_res.json()["user"]["role"] == "student"
    assert prod_client.get("/admin").status_code == 403
    assert prod_client.get("/api/admin/user-analytics").status_code == 403


def test_login_analytics_events_counting_boundaries_and_auth(tmp_path, monkeypatch, anon_client, client, auth_headers):
    from datetime import datetime, timezone
    import auth_service
    import db

    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "login_analytics.db"))
    db.init_db()

    # Guest blocked
    assert anon_client.get("/api/admin/login-analytics").status_code == 401

    # Register & verify a student (verify-code issues 1 login event)
    pw_hash = auth_service.hash_password("LoginTest123!")
    u, _ = db.upsert_pending_registration_user("login_u1@gmail.com", "User One", pw_hash, "G1")
    db.mark_user_email_verified("login_u1@gmail.com", university_email_verified=False)

    # Failed login must NOT record a login event
    bad = anon_client.post("/api/auth/login", json={"email": "login_u1@gmail.com", "password": "WrongPassword!"})
    assert bad.status_code == 401
    assert db.get_auth_login_analytics(days="30")["summary"]["total_logins"] == 0

    # Successful login records 1 event
    ok = anon_client.post("/api/auth/login", json={"email": "login_u1@gmail.com", "password": "LoginTest123!"})
    assert ok.status_code == 200
    assert db.get_auth_login_analytics(days="30")["summary"]["total_logins"] == 1

    # Session check (/api/auth/me) must NOT increase login count
    for _ in range(3):
        assert anon_client.get("/api/auth/me").status_code == 200
    assert db.get_auth_login_analytics(days="30")["summary"]["total_logins"] == 1

    # Student cannot access login-analytics
    assert anon_client.get("/api/admin/login-analytics").status_code == 403

    # 4 more logins by the same user -> 5 total logins, 1 unique user, 4 repeat logins
    import server as srv
    for _ in range(4):
        srv._rate_limit_store.clear()
        assert anon_client.post("/api/auth/login", json={"email": "login_u1@gmail.com", "password": "LoginTest123!"}).status_code == 200

    res = client.get("/api/admin/login-analytics?days=30", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["timezone"] == "Europe/Moscow"
    assert body["summary"]["total_logins"] == 5
    assert body["summary"]["unique_users"] == 1
    assert body["summary"]["repeat_logins"] == 4
    assert "login_u1@gmail.com" not in res.text

    # Midnight boundary test in Europe/Moscow (UTC+3):
    # 2026-11-10 20:59:59 UTC == 2026-11-10 23:59:59 MSK (hour 23 of 2026-11-10)
    # 2026-11-10 21:00:05 UTC == 2026-11-11 00:00:05 MSK (hour 0 of 2026-11-11)
    ts_before_midnight = datetime(2026, 11, 10, 20, 59, 59, tzinfo=timezone.utc).timestamp()
    ts_after_midnight = datetime(2026, 11, 10, 21, 0, 5, tzinfo=timezone.utc).timestamp()
    db.record_auth_login_event(user_id=901, auth_method="password", created_at=ts_before_midnight)
    db.record_auth_login_event(user_id=902, auth_method="oidc", created_at=ts_after_midnight)

    d10 = client.get("/api/admin/login-analytics?days=all&date=2026-11-10", headers=auth_headers).json()
    d11 = client.get("/api/admin/login-analytics?days=all&date=2026-11-11", headers=auth_headers).json()
    assert d10["hourly"][23]["logins"] == 1
    assert d10["hourly"][23]["unique_users"] == 1
    assert d10["hourly"][0]["logins"] == 0
    assert d11["hourly"][0]["logins"] == 1
    assert d11["hourly"][0]["unique_users"] == 1
    assert d11["summary"]["peak_hour"] == 0
