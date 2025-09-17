from datetime import datetime, timezone
import base64
from fastapi import HTTPException, Request
from typing import Dict
import jwt
from datetime import timedelta

from ..config import get_settings

settings = get_settings()

# JWT config
JWT_SECRET = settings.JWT_SECRET
JWT_ALG = settings.JWT_ALG
JWT_TTL_SECONDS = settings.JWT_TTL_SECONDS
JWT_ISSUER = settings.JWT_ISSUER
JWT_AUDIENCE = settings.JWT_AUDIENCE

# Cookie config
JWT_COOKIE_NAME = settings.JWT_COOKIE_NAME
JWT_COOKIE_DOMAIN = settings.JWT_COOKIE_DOMAIN
JWT_COOKIE_SECURE = settings.JWT_COOKIE_SECURE
JWT_COOKIE_SAMESITE = settings.JWT_COOKIE_SAMESITE
JWT_COOKIE_PATH = settings.JWT_COOKIE_PATH
JWT_COOKIE_PARTITIONED = settings.JWT_COOKIE_PARTITIONED

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def format_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_MAP = {c: i for i, c in enumerate(_B58_ALPHABET)}


def b58_decode(s: str) -> bytes:
    n = 0
    for ch in s:
        if ch not in _B58_MAP:
            raise ValueError("invalid base58 character")
        n = n * 58 + _B58_MAP[ch]
    # Convert big integer to bytes
    full = n.to_bytes((n.bit_length() + 7) // 8, byteorder="big") or b"\x00"
    # Add leading zero bytes for each leading '1'
    leading_zeros = len(s) - len(s.lstrip("1"))
    return b"\x00" * leading_zeros + full


def build_message(domain: str, wallet: str, nonce: str, issued: datetime, expires: datetime, purpose: str) -> str:
    return (
        f"Sign in to {domain}\n"
        f"Wallet: {wallet}\n"
        f"Nonce: {nonce}\n"
        f"Issued-At: {format_ts(issued)}\n"
        f"Expires-At: {format_ts(expires)}\n"
        f"Purpose: {purpose}"
    )

def verify_signature_solana_base58_pubkey_message_signature(pubkey_b58: str, message: str, signature_b64_or_hex: str, encoding: str = "base64") -> bool:
    try:
        pubkey_bytes = b58_decode(pubkey_b58)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid wallet format: not base58")

    if len(pubkey_bytes) != 32:
        raise HTTPException(status_code=400, detail="invalid wallet length: expected 32 bytes")

    if encoding.lower() == "base64":
        try:
            sig_bytes = base64.b64decode(signature_b64_or_hex, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid base64 signature")
    elif encoding.lower() == "hex":
        try:
            sig_bytes = bytes.fromhex(signature_b64_or_hex)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid hex signature")
    else:
        raise HTTPException(status_code=400, detail="unsupported signature encoding")

    # Defer import so the app can start without the dependency for other routes
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="signature verification unavailable: install 'pynacl'",
        ) from e

    try:
        vk = VerifyKey(pubkey_bytes)
        vk.verify(message.encode("utf-8"), sig_bytes)
        return True
    except BadSignatureError:
        return False


############## for JWT ###############

def mint_jwt(wallet: str, nonce: str, purpose: str, domain: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=JWT_TTL_SECONDS)
    payload = {
        "sub": wallet,
        "iss": JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "nonce": nonce,
        "purpose": purpose,
        "domain": domain,
    }
    if JWT_AUDIENCE:
        payload["aud"] = JWT_AUDIENCE
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, exp


############## for /auth/me ###############

def get_token_from_request(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1].strip()
    return request.cookies.get(JWT_COOKIE_NAME)


def decode_jwt(token: str) -> Dict[str, str]:
    verify_options = {"verify_aud": bool(JWT_AUDIENCE)}
    if JWT_AUDIENCE:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALG],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options=verify_options,
        )
    else:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALG],
            issuer=JWT_ISSUER,
            options=verify_options,
        )
