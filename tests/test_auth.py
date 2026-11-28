import base64
import json
import re
import time
import urllib.parse

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

import auth_service
import db
import server


@pytest.fixture(autouse=True)
def _clean_auth_state():
    auth_service.MOCK_MAILBOX.clear()
    with db._lock:
        conn = db._conn()
        try:
            conn.execute("DELETE FROM user_sessions")
            conn.execute("DELETE FROM email_verifications")
            conn.execute("DELETE FROM oidc_states")
            conn.execute("DELETE FROM users")
            conn.commit()
        finally:
            conn.close()
    yield


def _extract_code(email: str) -> str:
    msgs = [m for m in auth_service.MOCK_MAILBOX if m["to"] == email.lower()]
    assert msgs, f"No mock email sent to {email}"
    last = msgs[-1]
    if last.get("code"):
        return str(last["code"])
    match = re.search(r"\b(\d{6})\b", last.get("html") or "")
    assert match, f"No 6-digit code in email: {last}"
    return match.group(1)


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign_rs256_jwt(private_key, kid: str, payload: dict) -> str:
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    h_b64 = _b64u(json.dumps(header).encode("utf-8"))
    p_b64 = _b64u(json.dumps(payload).encode("utf-8"))
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{h_b64}.{p_b64}.{_b64u(sig)}"


def test_registration_verification_login_and_logout(anon_client):
    # 1. Weak password rejected
    weak = anon_client.post("/api/auth/register", json={
        "email": "weak@gmail.com",
        "password": "short",
        "password_confirm": "short",
        "full_name": "Test User",
        "group_num": "G1",
        "accept_terms": True,
    })
    assert weak.status_code == 400

    # 2. Valid registration with any email (non-SFEDU) + spoofed role ignored
    reg = anon_client.post("/api/auth/register", json={
        "email": "student1@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Иван Тестов",
        "group_num": "ИТ-101",
        "accept_terms": True,
        "role": "admin",
        "university_verified": True,
        "badge": "Сообщество ЮФУ",
    })
    assert reg.status_code == 200
    reg_data = reg.json()
    assert reg_data["status"] == "ok"
    assert "dev_code" not in reg_data
    assert "code" not in reg_data

    # 3. Unverified user cannot log in yet
    unverified_login = anon_client.post("/api/auth/login", json={
        "email": "student1@gmail.com",
        "password": "Password123",
    })
    assert unverified_login.status_code == 403

    # 4. Resend cooldown enforced within 60s
    cooldown = anon_client.post("/api/auth/send-code", json={
        "email": "student1@gmail.com",
        "purpose": "register",
    })
    assert cooldown.status_code == 429

    # 5. Wrong code increments attempts; correct code succeeds and sets cookie
    code = _extract_code("student1@gmail.com")
    wrong = anon_client.post("/api/auth/verify-code", json={
        "email": "student1@gmail.com",
        "code": "000000" if code != "000000" else "111111",
    })
    assert wrong.status_code == 400

    ok = anon_client.post("/api/auth/verify-code", json={
        "email": "student1@gmail.com",
        "code": code,
    })
    assert ok.status_code == 200
    user = ok.json()["user"]
    assert user["email"] == "student1@gmail.com"
    assert user["role"] == "student"
    assert user["university_email_verified"] is False
    assert user["university_verified"] is False
    assert user["badge"] == ""
    assert "geoatlas_session" in anon_client.cookies

    # 6. Reusing the same code fails
    reuse = anon_client.post("/api/auth/verify-code", json={
        "email": "student1@gmail.com",
        "code": code,
    })
    assert reuse.status_code == 400

    # 7. Duplicate verified registration does not reveal existence or send new registration email
    before_count = len(auth_service.MOCK_MAILBOX)
    dup = anon_client.post("/api/auth/register", json={
        "email": "student1@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Clone",
        "group_num": "G2",
        "accept_terms": True,
    })
    assert dup.status_code == 200
    assert len(auth_service.MOCK_MAILBOX) == before_count

    # 8. /api/auth/me works while logged in
    me = anon_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "student1@gmail.com"

    # 9. Logout revokes session and clears access
    out = anon_client.post("/api/auth/logout")
    assert out.status_code == 200
    me_after = anon_client.get("/api/auth/me")
    assert me_after.status_code == 401

    # 10. Wrong password & nonexistent user fail with 401; right password succeeds
    bad_pw = anon_client.post("/api/auth/login", json={
        "email": "student1@gmail.com",
        "password": "WrongPassword1",
    })
    assert bad_pw.status_code == 401
    no_user = anon_client.post("/api/auth/login", json={
        "email": "missing@gmail.com",
        "password": "Password123",
    })
    assert no_user.status_code == 401
    server._rate_limit_store.clear()
    good_login = anon_client.post("/api/auth/login", json={
        "email": "student1@gmail.com",
        "password": "Password123",
    })
    assert good_login.status_code == 200


def test_verification_max_attempts_and_expired_code(anon_client):
    anon_client.post("/api/auth/register", json={
        "email": "lockout@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Lockout Test",
        "group_num": "L1",
        "accept_terms": True,
    })
    real_code = _extract_code("lockout@gmail.com")
    wrong_code = "999999" if real_code != "999999" else "888888"

    for i in range(4):
        server._rate_limit_store.clear()
        r = anon_client.post("/api/auth/verify-code", json={
            "email": "lockout@gmail.com",
            "code": wrong_code,
        })
        assert r.status_code == 400, f"Attempt {i+1} unexpected {r.status_code}"

    # 5th failed attempt locks/invalidates code
    server._rate_limit_store.clear()
    r5 = anon_client.post("/api/auth/verify-code", json={
        "email": "lockout@gmail.com",
        "code": wrong_code,
    })
    assert r5.status_code in (400, 429)

    # Even the real code is now rejected
    server._rate_limit_store.clear()
    r_real = anon_client.post("/api/auth/verify-code", json={
        "email": "lockout@gmail.com",
        "code": real_code,
    })
    assert r_real.status_code == 400

    # Expired code test via DB timestamp
    anon_client.post("/api/auth/register", json={
        "email": "expired_code@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Expired Code",
        "group_num": "L2",
        "accept_terms": True,
    })
    exp_code = _extract_code("expired_code@gmail.com")
    with db._lock:
        conn = db._conn()
        try:
            conn.execute(
                "UPDATE email_verifications SET expires_at = ? WHERE email = ?",
                (time.time() - 10, "expired_code@gmail.com"),
            )
            conn.commit()
        finally:
            conn.close()
    r_exp = anon_client.post("/api/auth/verify-code", json={
        "email": "expired_code@gmail.com",
        "code": exp_code,
    })
    assert r_exp.status_code == 400


def test_missing_smtp_returns_503(anon_client, monkeypatch):
    monkeypatch.setenv("MAIL_PROVIDER", "smtp")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM_EMAIL", raising=False)
    r = anon_client.post("/api/auth/register", json={
        "email": "nosmtp@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "No SMTP",
        "group_num": "G1",
        "accept_terms": True,
    })
    assert r.status_code == 503


def test_forgot_and_reset_password_invalidates_old_sessions(anon_client):
    anon_client.post("/api/auth/register", json={
        "email": "resetme@gmail.com",
        "password": "OldPassword1",
        "password_confirm": "OldPassword1",
        "full_name": "Reset User",
        "group_num": "R1",
        "accept_terms": True,
    })
    code = _extract_code("resetme@gmail.com")
    v = anon_client.post("/api/auth/verify-code", json={"email": "resetme@gmail.com", "code": code})
    assert v.status_code == 200
    old_cookie = anon_client.cookies.get("geoatlas_session")
    assert old_cookie

    # Non-existent email still returns generic 200
    fp_missing = anon_client.post("/api/auth/forgot-password", json={"email": "nobody123@gmail.com"})
    assert fp_missing.status_code == 200

    # Real email sends reset code
    fp = anon_client.post("/api/auth/forgot-password", json={"email": "resetme@gmail.com"})
    assert fp.status_code == 200
    reset_code = _extract_code("resetme@gmail.com")

    rp = anon_client.post("/api/auth/reset-password", json={
        "email": "resetme@gmail.com",
        "code": reset_code,
        "new_password": "NewPassword2",
        "new_password_confirm": "NewPassword2",
    })
    assert rp.status_code == 200

    # Reusing reset code fails
    rp_reuse = anon_client.post("/api/auth/reset-password", json={
        "email": "resetme@gmail.com",
        "code": reset_code,
        "new_password": "NewPassword3",
        "new_password_confirm": "NewPassword3",
    })
    assert rp_reuse.status_code == 400

    # Old session cookie is revoked
    anon_client.cookies.set("geoatlas_session", old_cookie)
    assert anon_client.get("/api/auth/me").status_code == 401

    # Old password fails, new password succeeds
    anon_client.cookies.clear()
    assert anon_client.post("/api/auth/login", json={
        "email": "resetme@gmail.com",
        "password": "OldPassword1",
    }).status_code == 401
    assert anon_client.post("/api/auth/login", json={
        "email": "resetme@gmail.com",
        "password": "NewPassword2",
    }).status_code == 200


def test_guest_access_restrictions_and_authenticated_access(anon_client):
    # Public pages & endpoints
    assert anon_client.get("/").status_code == 200
    assert anon_client.get("/login").status_code == 200
    assert anon_client.get("/register").status_code == 200
    assert anon_client.get("/forgot-password").status_code == 200
    assert anon_client.get("/reset-password").status_code == 200
    assert anon_client.get("/api/stats/visits").status_code == 200
    assert anon_client.get("/api/branding").status_code == 200
    assert anon_client.get("/api/server-time").status_code == 200
    assert anon_client.get("/api/auth/config").status_code == 200

    # Protected HTML redirects to /login?next=...
    for route in ["/rostov_quiz_map.html", "/map/rostov", "/region/rostov", "/admin"]:
        r = anon_client.get(route, follow_redirects=False)
        assert r.status_code == 302, f"Expected 302 for {route}, got {r.status_code}"
        assert "/login?next=" in r.headers["location"]

    # Protected static maps & APIs return 401
    assert anon_client.get("/public/maps/rostov.geojson").status_code == 401
    assert anon_client.get("/api/maps").status_code == 401
    assert anon_client.get("/api/region/context?region=rostov").status_code == 401
    assert anon_client.get("/api/results/leaderboard").status_code == 401
    assert anon_client.get("/api/student/dashboard?email=a@b.ru").status_code == 401
    assert anon_client.get("/api/student/heatmap?email=a@b.ru").status_code == 401
    assert anon_client.get("/api/exam/active-session").status_code == 401
    assert anon_client.post("/api/results/save", json={}).status_code == 401
    assert anon_client.post("/api/duel/create", json={}).status_code == 401
    assert anon_client.post("/api/branding", json={}).status_code == 401

    # Unauthenticated WS rejected
    with pytest.raises(Exception):
        with anon_client.websocket_connect("/ws/duel/DUEL-NOAUTH/p1"):
            pass

    # Register & verify student -> gains access to maps/APIs, NOT /admin
    anon_client.post("/api/auth/register", json={
        "email": "access_student@gmail.com",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Access Student",
        "group_num": "A1",
        "accept_terms": True,
    })
    code = _extract_code("access_student@gmail.com")
    anon_client.post("/api/auth/verify-code", json={"email": "access_student@gmail.com", "code": code})

    assert anon_client.get("/rostov_quiz_map.html").status_code == 200
    assert anon_client.get("/api/maps").status_code == 200
    assert anon_client.get("/api/results/leaderboard").status_code == 200
    assert anon_client.get("/admin", follow_redirects=False).status_code == 403


def test_sfedu_email_badge_and_admin_university_verify(anon_client, auth_headers):
    anon_client.post("/api/auth/register", json={
        "email": "ivanov@sfedu.ru",
        "password": "Password123",
        "password_confirm": "Password123",
        "full_name": "Иванов ЮФУ",
        "group_num": "Г-11",
        "accept_terms": True,
    })
    code = _extract_code("ivanov@sfedu.ru")
    v = anon_client.post("/api/auth/verify-code", json={"email": "ivanov@sfedu.ru", "code": code})
    assert v.status_code == 200
    u = v.json()["user"]
    assert u["university_email_verified"] is True
    assert u["university_verified"] is False
    assert u["badge"] == "Почта ЮФУ подтверждена"

    # Student cannot self-verify university status
    self_attempt = anon_client.post(f"/api/admin/users/{u['id']}/university-verify", json={"verified": True})
    assert self_attempt.status_code == 403

    # Admin upgrades user to full Сообщество ЮФУ
    admin_verify = anon_client.post(
        f"/api/admin/users/{u['id']}/university-verify",
        json={"verified": True},
        headers=auth_headers,
    )
    assert admin_verify.status_code == 200
    assert admin_verify.json()["user"]["university_verified"] is True
    assert admin_verify.json()["user"]["badge"] == "Сообщество ЮФУ"


def test_oidc_rs256_id_token_validation_and_callback(anon_client, monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_numbers = private_key.public_key().public_numbers()

    def _int_b64u(val: int) -> str:
        length = (val.bit_length() + 7) // 8
        return _b64u(val.to_bytes(length, "big"))

    kid = "sfedu-test-kid-1"
    jwks = {
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": kid,
            "n": _int_b64u(pub_numbers.n),
            "e": _int_b64u(pub_numbers.e),
        }]
    }
    issuer = "https://login.microsoftonline.com/test-tenant/v2.0"
    client_id = "test-client-id"
    nonce = "nonce-123456"
    now = int(time.time())

    valid_payload = {
        "iss": issuer,
        "aud": client_id,
        "tid": "test-tenant",
        "sub": "oid-subject-001",
        "nonce": nonce,
        "email": "petrov@sfedu.ru",
        "name": "Петров Пётр",
        "email_verified": True,
        "iat": now - 5,
        "nbf": now - 5,
        "exp": now + 300,
    }
    valid_jwt = _sign_rs256_jwt(private_key, kid, valid_payload)

    cfg = {
        "enabled": True,
        "issuer": issuer,
        "client_id": client_id,
        "client_secret": "secret-xyz",
        "redirect_uri": "http://testserver/api/auth/oidc/callback",
        "tenant_id": "test-tenant",
        "scopes": "openid profile email",
    }

    claims = auth_service.verify_oidc_id_token(
        valid_jwt,
        expected_nonce=nonce,
        cfg=cfg,
        jwks_override=jwks,
    )
    assert claims["email"] == "petrov@sfedu.ru"

    # Reject wrong issuer, wrong nonce, and alg=none
    with pytest.raises(auth_service.OIDCVerificationError):
        auth_service.verify_oidc_id_token(
            _sign_rs256_jwt(private_key, kid, {**valid_payload, "iss": "https://evil.example.com"}),
            expected_nonce=nonce, cfg=cfg, jwks_override=jwks,
        )
    with pytest.raises(auth_service.OIDCVerificationError):
        auth_service.verify_oidc_id_token(
            valid_jwt,
            expected_nonce="wrong-nonce", cfg=cfg, jwks_override=jwks,
        )
    alg_none = f"{_b64u(b'{\"alg\":\"none\"}')}.{_b64u(json.dumps(valid_payload).encode())}."
    with pytest.raises(auth_service.OIDCVerificationError):
        auth_service.verify_oidc_id_token(
            alg_none,
            expected_nonce=nonce, cfg=cfg, jwks_override=jwks,
        )

    # Full /api/auth/oidc/login -> /api/auth/oidc/callback flow
    monkeypatch.setenv("AUTH_OIDC_ENABLED", "true")
    monkeypatch.setenv("AUTH_OIDC_ISSUER", issuer)
    monkeypatch.setenv("AUTH_OIDC_CLIENT_ID", client_id)
    monkeypatch.setenv("AUTH_OIDC_CLIENT_SECRET", "secret-xyz")
    monkeypatch.setenv("AUTH_OIDC_REDIRECT_URI", "http://testserver/api/auth/oidc/callback")
    monkeypatch.setenv("AUTH_OIDC_TENANT_ID", "test-tenant")
    monkeypatch.setattr(
        auth_service,
        "fetch_oidc_discovery",
        lambda *_a, **_kw: {
            "authorization_endpoint": "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/authorize",
            "token_endpoint": "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token",
            "jwks_uri": "https://login.microsoftonline.com/test-tenant/discovery/v2.0/keys",
        },
    )

    login_redir = anon_client.get("/api/auth/oidc/login?next=/rostov_quiz_map.html", follow_redirects=False)
    assert login_redir.status_code == 302
    parsed = urllib.parse.urlparse(login_redir.headers["location"])
    qs = urllib.parse.parse_qs(parsed.query)
    state_val = qs["state"][0]
    state_hash = auth_service.hash_token(state_val, "oidc_state")
    with db._lock:
        conn = db._conn()
        try:
            row = conn.execute("SELECT nonce FROM oidc_states WHERE state_hash = ?", (state_hash,)).fetchone()
        finally:
            conn.close()
    assert row is not None
    cb_jwt = _sign_rs256_jwt(private_key, kid, {**valid_payload, "nonce": row["nonce"]})
    monkeypatch.setattr(auth_service, "_http_post_form_json", lambda *a, **kw: {"id_token": cb_jwt})
    monkeypatch.setattr(auth_service, "_http_get_json", lambda *a, **kw: jwks)

    cb = anon_client.get(f"/api/auth/oidc/callback?code=authcode1&state={state_val}", follow_redirects=False)
    assert cb.status_code == 302
    assert cb.headers["location"] == "/rostov_quiz_map.html"
    assert "geoatlas_session" in anon_client.cookies

    me = anon_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["university_verified"] is True
    assert me.json()["user"]["badge"] == "Сообщество ЮФУ"


def test_legacy_teacher_sha256_upgrades_to_scrypt_on_login(anon_client):
    # admin/admin starts as legacy SHA-256 in test DB and transparently upgrades on login
    res = anon_client.post("/api/auth/login", json={
        "email": "admin",
        "password": "admin",
    })
    assert res.status_code == 200
    assert res.json()["user"]["role"] in ("teacher", "dean", "admin")
    teacher = next(t for t in db.load_teachers_db() if t["username"] == "admin")
    assert teacher["password_hash"].startswith("scrypt$")
