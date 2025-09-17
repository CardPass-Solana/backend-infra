from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.schemas import BountyCreate, BountyResponse, BountyUpdate

router = APIRouter(prefix="/bounties", tags=["bounties"])


@router.post("", response_model=BountyResponse, status_code=status.HTTP_201_CREATED)
async def create_bounty(
    payload: BountyCreate, session: AsyncSession = Depends(get_db_session)
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bounty creation not yet implemented; stub endpoint.",
    )


@router.get("", response_model=list[BountyResponse])
async def list_bounties(session: AsyncSession = Depends(get_db_session)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bounty listing not yet implemented; stub endpoint.",
    )


@router.patch("/{bounty_id}", response_model=BountyResponse)
async def update_bounty(
    bounty_id: str,
    payload: BountyUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Bounty update not yet implemented; stub endpoint.",
    )
