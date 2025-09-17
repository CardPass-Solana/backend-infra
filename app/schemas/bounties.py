from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models import BountyStatus


class BountyCreate(BaseModel):
    title: str
    description: Optional[str]
    reward_amount: Decimal = Field(..., gt=0)
    currency: str = "USDC"
    expires_at: Optional[datetime]


class BountyUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    reward_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str]
    status: Optional[BountyStatus]
    expires_at: Optional[datetime]


class BountyResponse(BaseModel):
    id: uuid.UUID
    recruiter_id: uuid.UUID
    title: str
    description: Optional[str]
    reward_amount: Decimal
    currency: str
    escrow_account: Optional[str]
    status: BountyStatus
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
