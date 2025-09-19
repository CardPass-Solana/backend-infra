from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models import ApplicationStatus, DepositStatus


class ApplicationPublicProfile(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience_years: float = Field(..., ge=0)
    region: str
    bio_short: str = Field(..., max_length=280)
    contact_price: str = Field(..., description="Quoted rate or bounty share.")
    headline: Optional[str] = None
    links: Optional[List[str]] = None

    class Config:
        extra = "allow"


class ApplicationCreate(BaseModel):
    bounty_id: uuid.UUID
    applicant_wallet: str
    referrer_wallet: Optional[str]
    public_profile: ApplicationPublicProfile = Field(
        ..., description="Public traits ultimately minted to CNFT"
    )
    private_payload_base64: Optional[str] = Field(
        None,
        description="Optional base64 encoded private profile to upload in-line; alternative is to request upload URL.",
    )


class ApplicationPrivateProfileDemo(BaseModel):
    full_name: str
    contact_email: str = Field(..., description="Preferred email for direct outreach.")
    contact_phone: Optional[str] = Field(None, description="Optional phone number for follow-ups.")
    telegram: Optional[str] = Field(None, description="Telegram handle for quick coordination.")
    resume_url: Optional[str] = Field(
        None, description="Link to a hosted resume or CV preview."
    )
    resume_excerpt: Optional[str] = Field(
        None, description="Short summary or highlights pulled from the resume."
    )
    cover_letter: Optional[str] = Field(None, description="Optional cover letter or intro note.")
    attachments: List[str] = Field(
        default_factory=list,
        description="Additional asset references such as portfolio links or case studies.",
    )


class SampleResumeResponse(BaseModel):
    public_profile: ApplicationPublicProfile
    private_profile: ApplicationPrivateProfileDemo


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    bounty_id: uuid.UUID
    applicant_wallet: str
    referrer_wallet: Optional[str]
    public_profile: ApplicationPublicProfile
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
    recruiter_wallet: str = Field(..., min_length=20)


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
