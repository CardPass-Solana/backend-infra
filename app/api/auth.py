from __future__ import annotations

import secrets
import threading
import time
from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Body, HTTPException, Request, Response, status

from app.auth.auth import (
    build_message,
    decode_jwt,
    format_ts,
    get_token_from_request,
    mint_jwt,
    now_utc,
    verify_signature_solana_base58_pubkey_message_signature,
)
from app.schemas.auth import (
    ChallengeRecord,
    ChallengeRequest,
    ChallengeResponse,
    MeResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.config import get_settings

settings = get_settings()

DEFAULT_DOMAIN = settings.AUTH_DOMAIN
CHALLENGE_TTL_SECONDS = settings.AUTH_CHALLENGE_TTL_SECONDS

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

router = APIRouter(prefix="/auth", tags=["auth"])

_challenges: Dict[str, ChallengeRecord] = {}
_lock = threading.Lock()


def _sweep_expired() -> None:
    while True:
        now = now_utc()
        with _lock:
            for key, value in list(_challenges.items()):
                if value.expires_at < now:
                    _challenges.pop(key, None)
        time.sleep(60)


threading.Thread(target=_sweep_expired, daemon=True).start()


@router.post("/challenge", response_model=ChallengeResponse)
def create_challenge(payload: ChallengeRequest = Body(...)):
    domain = payload.domain or DEFAULT_DOMAIN
    if not payload.wallet or len(payload.wallet) < 20:
        raise HTTPException(status_code=400, detail="invalid wallet")

    issued = now_utc()
    expires = issued + timedelta(seconds=CHALLENGE_TTL_SECONDS)
    nonce = secrets.token_urlsafe(24)
    message = build_message(
        domain, payload.wallet, nonce, issued, expires, payload.purpose
    )

    rec = ChallengeRecord(
        wallet=payload.wallet,
        nonce=nonce,
        issued_at=issued,
        expires_at=expires,
        purpose=payload.purpose,
        domain=domain,
        message=message,
    )
    with _lock:
        _challenges[nonce] = rec

    return ChallengeResponse(
        wallet=payload.wallet,
        nonce=nonce,
        issued_at=format_ts(issued),
        expires_at=format_ts(expires),
        message=message,
    )


@router.post("/verify", response_model=VerifyResponse)
def verify_challenge(response: Response, payload: VerifyRequest = Body(...)):
    with _lock:
        rec = _challenges.get(payload.nonce)
        if rec is None:
            raise HTTPException(400, "unknown or expired nonce")
        if rec.used:
            raise HTTPException(400, "nonce already used")
        if now_utc() > rec.expires_at:
            _challenges.pop(payload.nonce, None)
            raise HTTPException(400, "nonce expired")
        rec.used = True
        _challenges.pop(payload.nonce, None)

    ok = verify_signature_solana_base58_pubkey_message_signature(
        rec.wallet, rec.message, payload.signature, payload.signature_encoding
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature"
        )

    token, exp = mint_jwt(rec.wallet, rec.nonce, rec.purpose, rec.domain)

    response.set_cookie(
        key=JWT_COOKIE_NAME,
        value=token,
        max_age=JWT_TTL_SECONDS,
        httponly=True,
        secure=JWT_COOKIE_SECURE,
        samesite=JWT_COOKIE_SAMESITE,
        domain=JWT_COOKIE_DOMAIN,
        path=JWT_COOKIE_PATH,
    )
    _ensure_partitioned_cookie(response)

    return VerifyResponse(
        ok=True,
        wallet=rec.wallet,
        used_nonce=rec.nonce,
        token_expires_at=format_ts(exp),
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=JWT_COOKIE_NAME,
        domain=JWT_COOKIE_DOMAIN,
        path=JWT_COOKIE_PATH,
    )
    _ensure_partitioned_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def auth_me(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token"
        )
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc

    return MeResponse(
        sub=payload.get("sub"),
        iss=payload.get("iss"),
        iat=payload.get("iat"),
        exp=payload.get("exp"),
        nonce=payload.get("nonce"),
        purpose=payload.get("purpose"),
        domain=payload.get("domain"),
        aud=payload.get("aud"),
    )

def _ensure_partitioned_cookie(response: Response) -> None:
    if not JWT_COOKIE_PARTITIONED:
        return
    cookie_prefix = f"{JWT_COOKIE_NAME}".lower() + "="
    updated = False
    new_headers = []
    for key, value in response.raw_headers:
        if key == b"set-cookie":
            value_str = value.decode("latin-1")
            if value_str.lower().startswith(cookie_prefix) and "partitioned" not in value_str.lower():
                value_str = f"{value_str}; Partitioned"
                value = value_str.encode("latin-1")
                updated = True
        new_headers.append((key, value))
    if updated:
        response.raw_headers = new_headers
