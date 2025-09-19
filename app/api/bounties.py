from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models import AccountRole, Bounty
from app.schemas import BountyCreate, BountyResponse, BountyUpdate
from app.services.accounts import get_or_create_account

router = APIRouter(prefix="/bounties", tags=["bounties"])


@router.post("", response_model=BountyResponse, status_code=status.HTTP_201_CREATED)
async def create_bounty(
    payload: BountyCreate, session: AsyncSession = Depends(get_db_session)
):
    recruiter = await get_or_create_account(
        session=session,
        wallet=payload.recruiter_wallet,
        role=AccountRole.RECRUITER,
    )

    bounty = Bounty(
        recruiter_id=recruiter.id,
        title=payload.title,
        description=payload.description,
        reward_amount=payload.reward_amount,
        currency=payload.currency,
        company=payload.company,
        region=payload.region,
        employment_type=payload.employment_type,
        skills=list(payload.skills or []),
        expires_at=payload.expires_at,
    )
    session.add(bounty)
    await session.commit()
    await session.refresh(bounty)
    return bounty


@router.get("", response_model=list[BountyResponse])
async def list_bounties(
    company: str | None = Query(default=None, description="Filter by company name"),
    region: str | None = Query(default=None, description="Filter by region"),
    employment_type: str | None = Query(
        default=None, description="Filter by employment type"
    ),
    skill: str | None = Query(
        default=None, description="Filter by required skill (case-insensitive)"
    ),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = select(Bounty).order_by(Bounty.created_at.desc())

    if company:
        stmt = stmt.where(Bounty.company.ilike(f"%{company}%"))
    if region:
        stmt = stmt.where(Bounty.region.ilike(f"%{region}%"))
    if employment_type:
        stmt = stmt.where(Bounty.employment_type.ilike(f"%{employment_type}%"))

    result = await session.execute(stmt)
    bounties: List[Bounty] = result.scalars().all()

    if skill:
        skill_lower = skill.lower()
        bounties = [
            bounty
            for bounty in bounties
            if any(s.lower() == skill_lower or skill_lower in s.lower() for s in bounty.skills or [])
        ]

    return bounties


@router.patch("/{bounty_id}", response_model=BountyResponse)
async def update_bounty(
    bounty_id: uuid.UUID,
    payload: BountyUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Bounty).where(Bounty.id == bounty_id))
    bounty = result.scalar_one_or_none()
    if bounty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bounty not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "skills" in update_data and update_data["skills"] is not None:
        update_data["skills"] = list(update_data["skills"])

    for field, value in update_data.items():
        setattr(bounty, field, value)

    await session.commit()
    await session.refresh(bounty)
    return bounty
