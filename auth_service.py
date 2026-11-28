import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import ssl
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple


class EmailNotConfiguredError(RuntimeError):
    """Raised when SMTP settings are missing and mock provider is disabled."""


class EmailDeliveryError(RuntimeError):
    """Raised when SMTP rejects or fails to deliver an email."""


class OIDCVerificationError(ValueError):
    """Raised when OIDC state, token exchange, or ID token validation fails."""


MOCK_MAILBOX: List[Dict[str, Any]] = []
_TOKEN_PEPPER_LOCK = threading.Lock()
_CACHED_PEPPER: Optional[bytes] = None
_JWKS_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

EMAIL_REGEX = re.compile(r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+$")


def normalize_email(email: Optional[str]) -> str:
    return str(email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    clean = normalize_email(email)
    return bool(clean and len(clean) <= 254 and EMAIL_REGEX.match(clean))


def get_trusted_university_domains() -> List[str]:
    raw = os.environ.get("TRUSTED_UNIVERSITY_DOMAINS", "sfedu.ru")
    domains = [d.strip().lower().lstrip("@.") for d in raw.split(",") if d.strip()]
    return domains or ["sfedu.ru"]


def is_trusted_university_email(email: str) -> bool:
    clean = normalize_email(email)
    if "@" not in clean:
        return False
    domain = clean.rsplit("@", 1)[1]
    for trusted in get_trusted_university_domains():
        if domain == trusted or domain.endswith(f".{trusted}"):
            return True
    return False


def _get_token_pepper() -> bytes:
    global _CACHED_PEPPER
    with _TOKEN_PEPPER_LOCK:
        env_secret = (
            os.environ.get("AUTH_SESSION_SECRET")
            or os.environ.get("SESSION_SECRET")
            or ""
        ).strip()
        if env_secret:
            return env_secret.encode("utf-8")
        if _CACHED_PEPPER is not None:
            return _CACHED_PEPPER

        data_dir = os.environ.get("GEOATLAS_DATA_DIR", tempfile.gettempdir())
        os.makedirs(data_dir, exist_ok=True)
        secret_file = os.path.join(data_dir, ".auth_token_secret")
        if os.path.exists(secret_file):
            try:
                with open(secret_file, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                if val:
                    _CACHED_PEPPER = val.encode("utf-8")
                    return _CACHED_PEPPER
            except Exception:
                pass
        generated = secrets.token_urlsafe(48)
        try:
            with open(secret_file, "w", encoding="utf-8") as f:
                f.write(generated)
        except Exception:
            pass
        _CACHED_PEPPER = generated.encode("utf-8")
        return _CACHED_PEPPER


def hash_token(raw_token: str, context: str = "") -> str:
    """Returns keyed HMAC-SHA256 hex digest for storing codes/session tokens safely."""
    msg = f"{context}:{raw_token}".encode("utf-8")
    return hmac.new(_get_token_pepper(), msg, hashlib.sha256).hexdigest()


# ==================== PASSWORD HASHING (SCRYPT + LEGACY MIGRATION) ====================

_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32


def validate_password_strength(password: str) -> Optional[str]:
    if not isinstance(password, str) or len(password) < 8:
        return "Пароль должен содержать минимум 8 символов."
    if len(password) > 128:
        return "Пароль слишком длинный (максимум 128 символов)."
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(digest).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt_b64}${hash_b64}"


def needs_password_upgrade(stored_hash: Optional[str]) -> bool:
    return not (stored_hash or "").startswith("scrypt$")


def verify_password(password: str, stored_hash: Optional[str]) -> bool:
    if not password or not stored_hash:
        return False
    if stored_hash.startswith("scrypt$"):
        try:
            _, n_s, r_s, p_s, salt_b64, hash_b64 = stored_hash.split("$", 5)
            salt = base64.b64decode(salt_b64.encode("ascii"))
            expected = base64.b64decode(hash_b64.encode("ascii"))
            candidate = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=int(n_s),
                r=int(r_s),
                p=int(p_s),
                dklen=len(expected),
            )
            return hmac.compare_digest(candidate, expected)
        except Exception:
            return False

    # Legacy 64-char SHA-256 hex compatibility for pre-existing accounts
    if len(stored_hash) == 64:
        legacy_digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_digest, stored_hash)

    return False


# ==================== EMAIL DELIVERY (SMTP + TEST MOCK) ====================

def build_verification_email_html(code: str, purpose: str, full_name: str = "") -> Tuple[str, str]:
    greeting = f"Здравствуйте, {full_name}!" if full_name else "Здравствуйте!"
    if purpose == "password_reset":
        subject = "GeoAtlas — код для сброса пароля"
        title = "Восстановление пароля"
        desc = "Вы запросили сброс пароля в учебно-картографическом комплексе GeoAtlas."
    else:
        subject = "GeoAtlas — подтверждение электронной почты"
        title = "Подтверждение электронной почты"
        desc = "Используйте этот одноразовый 6-значный код для завершения регистрации и входа в GeoAtlas."

    safe_greeting = greeting.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>{subject}</title></head>
<body style="margin:0;padding:24px;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0F172A;">
  <div style="max-width:520px;margin:0 auto;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;padding:28px;box-shadow:0 8px 24px rgba(15,23,42,0.08);">
    <div style="font-size:12px;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:8px;">GeoAtlas • SFEDU GIS</div>
    <h2 style="margin:0 0 12px 0;font-size:21px;color:#0F172A;">{title}</h2>
    <p style="margin:0 0 12px 0;font-size:14px;line-height:1.55;color:#334155;">{safe_greeting}</p>
    <p style="margin:0 0 20px 0;font-size:14px;line-height:1.55;color:#334155;">{desc}</p>
    <div style="background:#EFF6FF;border:1.5px solid #BFDBFE;border-radius:12px;padding:18px;text-align:center;margin-bottom:20px;">
      <div style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px;">Код подтверждения</div>
      <div style="font-size:32px;font-weight:900;letter-spacing:8px;font-family:'Courier New',monospace;color:#0F172A;">{code}</div>
    </div>
    <p style="margin:0;font-size:12.5px;line-height:1.5;color:#64748B;">Код действует <strong>10 минут</strong> и может быть использован только один раз. Если вы не запрашивали это письмо, просто проигнорируйте его.</p>
  </div>
</body>
</html>"""
    return subject, html


def send_auth_email(to_email: str, code: str, purpose: str, full_name: str = "") -> None:
    clean_to = normalize_email(to_email)
    subject, html_body = build_verification_email_html(code, purpose, full_name)
    text_body = f"{subject}\n\nВаш код подтверждения: {code}\nСрок действия: 10 минут."

    provider = os.environ.get("MAIL_PROVIDER", "smtp").strip().lower()
    if provider == "mock":
        MOCK_MAILBOX.append({
            "to": clean_to,
            "subject": subject,
            "code": code,
            "purpose": purpose,
            "html": html_body,
            "sent_at": time.time(),
        })
        return

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port_raw = os.environ.get("SMTP_PORT", "587").strip()
    smtp_user = os.environ.get("SMTP_USERNAME", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("SMTP_FROM_EMAIL", "").strip() or smtp_user
    from_name = os.environ.get("SMTP_FROM_NAME", "GeoAtlas ЮФУ").strip()
    use_tls_mode = os.environ.get("SMTP_USE_TLS", "true").strip().lower()

    if not smtp_host or not from_email:
        raise EmailNotConfiguredError(
            "Почтовый сервер (SMTP) не настроен. Обратитесь к администратору для завершения конфигурации."
        )

    try:
        smtp_port = int(smtp_port_raw or "587")
    except ValueError:
        smtp_port = 587

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = clean_to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        ssl_ctx = ssl.create_default_context()
        if use_tls_mode == "ssl" or smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12, context=ssl_ctx) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.ehlo()
                if use_tls_mode in ("1", "true", "yes", "starttls"):
                    server.starttls(context=ssl_ctx)
                    server.ehlo()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
    except Exception as exc:
        raise EmailDeliveryError(f"Не удалось отправить письмо через SMTP: {exc.__class__.__name__}") from exc


# ==================== UNIVERSITY OIDC / ENTRA ID (PKCE + JWKS) ====================

def get_oidc_config() -> Dict[str, Any]:
    enabled_flag = os.environ.get("AUTH_OIDC_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")
    issuer = os.environ.get("AUTH_OIDC_ISSUER", "").strip().rstrip("/")
    client_id = os.environ.get("AUTH_OIDC_CLIENT_ID", "").strip()
    client_secret = os.environ.get("AUTH_OIDC_CLIENT_SECRET", "").strip()
    redirect_uri = os.environ.get("AUTH_OIDC_REDIRECT_URI", "").strip()
    tenant_id = os.environ.get("AUTH_OIDC_TENANT_ID", "").strip()

    configured = bool(enabled_flag and issuer and client_id and client_secret and redirect_uri)
    return {
        "enabled": configured,
        "issuer": issuer,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "tenant_id": tenant_id,
    }


def build_oidc_pkce_pair() -> Tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _b64url_decode(data: str) -> bytes:
    pad = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("ascii"))


def _http_get_json(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "GeoAtlas/2.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post_form_json(url: str, form_data: Dict[str, str]) -> Dict[str, Any]:
    encoded = urllib.parse.urlencode(form_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_oidc_discovery(issuer: str) -> Dict[str, Any]:
    discovery_url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
    return _http_get_json(discovery_url)


def fetch_jwks(jwks_uri: str) -> Dict[str, Any]:
    now = time.time()
    cached = _JWKS_CACHE.get(jwks_uri)
    if cached and (now - cached[0]) < 300:
        return cached[1]
    jwks = _http_get_json(jwks_uri)
    _JWKS_CACHE[jwks_uri] = (now, jwks)
    return jwks


def _verify_jwt_signature(header: Dict[str, Any], signing_input: bytes, signature: bytes, jwk: Dict[str, Any]) -> None:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

    alg = header.get("alg", "")
    if alg == "RS256":
        if jwk.get("kty") != "RSA":
            raise OIDCVerificationError("Несовместимый тип ключа JWKS для RS256")
        n_int = int.from_bytes(_b64url_decode(jwk["n"]), "big")
        e_int = int.from_bytes(_b64url_decode(jwk["e"]), "big")
        pub_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
        pub_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    elif alg == "ES256":
        if jwk.get("kty") != "EC":
            raise OIDCVerificationError("Несовместимый тип ключа JWKS для ES256")
        x_int = int.from_bytes(_b64url_decode(jwk["x"]), "big")
        y_int = int.from_bytes(_b64url_decode(jwk["y"]), "big")
        pub_key = ec.EllipticCurvePublicNumbers(x_int, y_int, ec.SECP256R1()).public_key()
        half = len(signature) // 2
        r_val = int.from_bytes(signature[:half], "big")
        s_val = int.from_bytes(signature[half:], "big")
        der_sig = encode_dss_signature(r_val, s_val)
        pub_key.verify(der_sig, signing_input, ec.ECDSA(hashes.SHA256()))
    else:
        raise OIDCVerificationError(f"Неподдерживаемый алгоритм подписи ID token: {alg}")


def verify_oidc_id_token(
    id_token: str,
    expected_nonce: str,
    cfg: Dict[str, Any],
    jwks_override: Optional[Dict[str, Any]] = None,
    jwks_uri: Optional[str] = None,
) -> Dict[str, Any]:
    parts = (id_token or "").split(".")
    if len(parts) != 3:
        raise OIDCVerificationError("Некорректный формат ID token")

    try:
        header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
        claims = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
        signature = _b64url_decode(parts[2])
    except Exception as exc:
        raise OIDCVerificationError("Не удалось декодировать ID token") from exc

    alg = header.get("alg", "")
    if alg not in ("RS256", "ES256"):
        raise OIDCVerificationError("Недопустимый алгоритм подписи ID token")

    if jwks_override is not None:
        jwks = jwks_override
    else:
        target_uri = jwks_uri
        if not target_uri:
            disc = fetch_oidc_discovery(cfg["issuer"])
            target_uri = disc.get("jwks_uri", "")
        if not target_uri:
            raise OIDCVerificationError("Не найден jwks_uri у провайдера OIDC")
        jwks = fetch_jwks(target_uri)

    keys = jwks.get("keys") or []
    kid = header.get("kid")
    matched_jwk = next((k for k in keys if not kid or k.get("kid") == kid), None)
    if not matched_jwk:
        raise OIDCVerificationError("Подходящий публичный ключ JWKS не найден")

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    try:
        _verify_jwt_signature(header, signing_input, signature, matched_jwk)
    except OIDCVerificationError:
        raise
    except Exception as exc:
        raise OIDCVerificationError("Подпись ID token недействительна") from exc

    expected_issuer = cfg["issuer"].rstrip("/")
    token_issuer = str(claims.get("iss") or "").rstrip("/")
    if not token_issuer or token_issuer != expected_issuer:
        raise OIDCVerificationError("Недоверенный issuer в ID token")

    aud = claims.get("aud")
    aud_ok = (aud == cfg["client_id"]) or (isinstance(aud, list) and cfg["client_id"] in aud)
    if not aud_ok:
        raise OIDCVerificationError("Неверный audience (aud) в ID token")

    expected_tid = cfg.get("tenant_id", "")
    if expected_tid and claims.get("tid") != expected_tid:
        raise OIDCVerificationError("Неверный tenant_id (tid) в ID token")

    now = time.time()
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or exp <= now:
        raise OIDCVerificationError("Срок действия ID token истёк")
    nbf = claims.get("nbf")
    if isinstance(nbf, (int, float)) and nbf > now + 60:
        raise OIDCVerificationError("ID token ещё не активен")

    if not expected_nonce or claims.get("nonce") != expected_nonce:
        raise OIDCVerificationError("Неверный nonce в ID token")

    email = normalize_email(claims.get("email") or claims.get("preferred_username"))
    if not is_valid_email(email):
        raise OIDCVerificationError("В ID token отсутствует корректный email")

    if claims.get("email_verified") is not True:
        raise OIDCVerificationError("Email в OIDC-профиле не подтверждён")

    if not claims.get("sub"):
        raise OIDCVerificationError("Отсутствует subject (sub) в ID token")

    return claims
