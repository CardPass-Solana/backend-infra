from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChallengeRequest(BaseModel):
    wallet: str = Field(..., description="Wallet public key (base58 for Solana)")
    purpose: str = Field("Login", description="Purpose string for the challenge")
    domain: Optional[str] = Field(None, description="Domain to display in message")


class ChallengeResponse(BaseModel):
    wallet: str
    nonce: str
    issued_at: str
    expires_at: str
    message: str


class VerifyRequest(BaseModel):
    wallet: str = Field(..., description="Wallet public key (base58 for Solana)")
    nonce: str
    signature: str = Field(..., description="Signature over the challenge message")
    signature_encoding: str = Field(
        "base64", description="Encoding of signature: base64 or hex"
    )


class VerifyResponse(BaseModel):
    ok: bool
    wallet: str
    used_nonce: str
    token_expires_at: Optional[str] = None


class ChallengeRecord(BaseModel):
    wallet: str
    nonce: str
    issued_at: datetime
    expires_at: datetime
    purpose: str
    domain: str
    message: str
    used: bool = False


class MeResponse(BaseModel):
    sub: str
    iss: str
    iat: int
    exp: int
    nonce: str
    purpose: str
    domain: str
    aud: Optional[str] = None
