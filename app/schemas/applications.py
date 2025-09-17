from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models import ApplicationStatus, DepositStatus


class ApplicationCreate(BaseModel):
    bounty_id: uuid.UUID
    applicant_wallet: str
    referrer_wallet: Optional[str]
    public_profile: Dict[str, Any] = Field(..., description="Public traits ultimately minted to CNFT")
    private_payload_base64: Optional[str] = Field(
        None,
        description="Optional base64 encoded private profile to upload in-line; alternative is to request upload URL.",
    )


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    bounty_id: uuid.UUID
    applicant_wallet: str
    referrer_wallet: Optional[str]
    public_profile: Dict[str, Any]
    cnft_mint: Optional[str]
    status: ApplicationStatus
    access_granted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrivateVersionResponse(BaseModel):
    id: uuid.UUID
    s3_key: str
    payload_sha256: str
    uploaded_at: datetime


class DepositCreate(BaseModel):
    amount: float = Field(..., gt=0)
    tx_signature: str = Field(..., min_length=8)


class DepositResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    recruiter_id: uuid.UUID
    amount: float
    tx_signature: str
    status: DepositStatus
    cleared_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
