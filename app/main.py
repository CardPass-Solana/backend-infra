from __future__ import annotations

import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict

import jwt
from fastapi import Body, FastAPI, HTTPException, Response, status, Request

from app.auth.auth import (
    build_message,
    now_utc,
    verify_signature_solana_base58_pubkey_message_signature,
    format_ts,
    mint_jwt,
    get_token_from_request,
    decode_jwt
)
from app.auth.types import (
    ChallengeRecord,
    ChallengeRequest,
    ChallengeResponse,
    VerifyRequest,
    VerifyResponse,
    MeResponse,
)
from app.config import get_settings

app = FastAPI()
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


# --- Simple health/test routes ---

@app.get("/")
def read_root():
    return {"status": "ok"}


# --- Auth via wallet challenge/response ---

_challenges: Dict[str, ChallengeRecord] = {}
_lock = threading.Lock()

def _sweep_expired():
    while True:
        now = now_utc()
        with _lock:
            for k, v in list(_challenges.items()):
                if v.expires_at < now:
                    _challenges.pop(k, None)
        time.sleep(60)

threading.Thread(target=_sweep_expired, daemon=True).start()


@app.post("/auth/challenge", response_model=ChallengeResponse)
def create_challenge(payload: ChallengeRequest = Body(...)):
    domain = payload.domain or DEFAULT_DOMAIN
    if not payload.wallet or len(payload.wallet) < 20:
        raise HTTPException(status_code=400, detail="invalid wallet")

    issued = now_utc()
    expires = issued + timedelta(seconds=CHALLENGE_TTL_SECONDS)
    nonce = secrets.token_urlsafe(24)
    message = build_message(domain, payload.wallet, nonce, issued, expires, payload.purpose)

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


@app.post("/auth/verify", response_model=VerifyResponse)
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
        # Reserve single-use atomically
        rec.used = True
        _challenges.pop(payload.nonce, None)

    ok = verify_signature_solana_base58_pubkey_message_signature(
        rec.wallet, rec.message, payload.signature, payload.signature_encoding
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

    # Mark nonce used and remove from store
    with _lock:
        rec.used = True
        _challenges.pop(payload.nonce, None)

    # Mint JWT and attach as HttpOnly cookie + return in body
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

    return VerifyResponse(
        ok=True,
        wallet=rec.wallet,
        used_nonce=rec.nonce,
        token=token,
        token_expires_at=format_ts(exp),
    )


@app.post("/auth/logout")
def logout(response: Response):
    """Clears the auth cookie; clients should also clear any stored tokens."""
    response.delete_cookie(
        key=JWT_COOKIE_NAME,
        domain=JWT_COOKIE_DOMAIN,
        path=JWT_COOKIE_PATH,
    )
    return {"ok": True}


@app.get("/auth/me", response_model=MeResponse)
def auth_me(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    try:
        payload = decode_jwt(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

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
