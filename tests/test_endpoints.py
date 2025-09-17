import base64
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


settings = get_settings()

JWT_TTL_SECONDS = settings.JWT_TTL_SECONDS
JWT_COOKIE_NAME = settings.JWT_COOKIE_NAME
JWT_COOKIE_SAMESITE = settings.JWT_COOKIE_SAMESITE
JWT_COOKIE_PATH = settings.JWT_COOKIE_PATH
JWT_COOKIE_SECURE = settings.JWT_COOKIE_SECURE
JWT_COOKIE_DOMAIN = settings.JWT_COOKIE_DOMAIN
JWT_SECRET = settings.JWT_SECRET
JWT_ALG = settings.JWT_ALG


# Base58 helpers matching app.auth.auth alphabet
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58_encode(b: bytes) -> str:
    n = int.from_bytes(b, byteorder="big")
    if n == 0:
        # still may need to account for leading zeros
        result = ""
    else:
        result = ""
        while n > 0:
            n, rem = divmod(n, 58)
            result = _B58_ALPHABET[rem] + result
    # Add one '1' for each leading 0x00
    leading_zeros = len(b) - len(b.lstrip(b"\x00"))
    return ("1" * leading_zeros) + result


client = TestClient(app, base_url="https://testserver")


def test_root_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def _gen_wallet_and_signature(message: str):
    from nacl.signing import SigningKey

    sk = SigningKey.generate()
    vk = sk.verify_key
    pubkey_bytes = vk.encode()  # 32 bytes
    pubkey_b58 = b58_encode(pubkey_bytes)
    sig = sk.sign(message.encode("utf-8")).signature  # 64 bytes
    sig_b64 = base64.b64encode(sig).decode()
    return pubkey_b58, sig_b64


def test_auth_challenge_and_verify_flow():
    # 1) Build a keypair and request a challenge for that wallet
    from nacl.signing import SigningKey

    sk = SigningKey.generate()
    vk = sk.verify_key
    pubkey_b58 = b58_encode(vk.encode())

    r1 = client.post(
        "/auth/challenge",
        json={"wallet": pubkey_b58, "purpose": "Login", "domain": "example.com"},
    )
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    assert set(data1.keys()) == {"wallet", "nonce", "issued_at", "expires_at", "message"}
    assert data1["wallet"] == pubkey_b58
    assert isinstance(data1["nonce"], str) and len(data1["nonce"]) > 10

    # 2) Sign the received message
    sig = sk.sign(data1["message"].encode("utf-8")).signature
    sig_b64 = base64.b64encode(sig).decode()

    # 3) Verify with correct wallet, nonce, signature
    r2 = client.post(
        "/auth/verify",
        json={
            "wallet": pubkey_b58,
            "nonce": data1["nonce"],
            "signature": sig_b64,
            "signature_encoding": "base64",
        },
    )
    assert r2.status_code == 200, r2.text
    data2 = r2.json()

    # Response body assertions
    assert data2["ok"] is True
    assert data2["wallet"] == pubkey_b58
    assert data2["used_nonce"] == data1["nonce"]
    assert "token" not in data2
    assert isinstance(data2["token_expires_at"], str)

    token_cookie = client.cookies.get(JWT_COOKIE_NAME)
    assert isinstance(token_cookie, str) and len(token_cookie) > 10

    # Set-Cookie assertions
    set_cookie = r2.headers.get("set-cookie", "")
    assert f"{JWT_COOKIE_NAME}=" in set_cookie
    assert f"Path={JWT_COOKIE_PATH}" in set_cookie
    assert ("Secure" in set_cookie) == bool(JWT_COOKIE_SECURE)
    # SameSite casing may vary between servers; check substring case-insensitively
    assert (f"samesite={JWT_COOKIE_SAMESITE}" in set_cookie.lower())
    # Domain is optional
    if JWT_COOKIE_DOMAIN:
        assert f"Domain={JWT_COOKIE_DOMAIN}" in set_cookie
    assert f"Max-Age={JWT_TTL_SECONDS}" in set_cookie
    assert "HttpOnly" in set_cookie

    # JWT payload assertions
    decoded = jwt.decode(token_cookie, JWT_SECRET, algorithms=[JWT_ALG], options={"verify_aud": False})
    assert decoded["sub"] == pubkey_b58
    assert decoded["nonce"] == data1["nonce"]
    assert decoded["purpose"] == "Login"
    # exp is approximately now + JWT_TTL_SECONDS
    now = datetime.now(timezone.utc)
    exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    delta = exp - now
    # Allow small tolerance for runtime skew
    assert timedelta(seconds=JWT_TTL_SECONDS - 5) <= delta <= timedelta(seconds=JWT_TTL_SECONDS + 5)

    # 4) Call /auth/me with existing cookie (client uses https base URL so Secure cookies apply)
    r_me_cookie = client.get("/auth/me")
    assert r_me_cookie.status_code == 200
    me_cookie = r_me_cookie.json()
    assert me_cookie["sub"] == pubkey_b58
    assert me_cookie["nonce"] == data1["nonce"]

    # 5) Call /auth/me with Authorization header (fresh client, no cookies)
    client2 = TestClient(app, base_url="https://testserver")
    r_me_bearer = client2.get(
        "/auth/me", headers={"Authorization": f"Bearer {token_cookie}"}
    )
    assert r_me_bearer.status_code == 200
    me2 = r_me_bearer.json()
    assert me2["sub"] == pubkey_b58
    assert me2["nonce"] == data1["nonce"]


def test_auth_logout():
    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    # Ensure cookie deletion header present
    set_cookie = r.headers.get("set-cookie", "")
    assert f"{JWT_COOKIE_NAME}=" in set_cookie
    # Should contain an Expires in the past or Max-Age=0
    assert ("Max-Age=0" in set_cookie) or ("expires=" in set_cookie.lower())


def test_auth_me_errors():
    # No token provided
    client3 = TestClient(app, base_url="https://testserver")
    r = client3.get("/auth/me")
    assert r.status_code == 401
    assert r.json().get("detail") in {"missing token", "invalid token"}

    # Invalid token in header
    r2 = client3.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r2.status_code == 401
    assert r2.json().get("detail") == "invalid token"
