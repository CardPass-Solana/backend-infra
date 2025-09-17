from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    DepositCreate,
    DepositResponse,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate, session: AsyncSession = Depends(get_db_session)
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Application submission not yet implemented; stub endpoint.",
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: uuid.UUID = Path(...),
    session: AsyncSession = Depends(get_db_session),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Application retrieval not yet implemented; stub endpoint.",
    )


@router.post(
    "/{application_id}/deposit",
    response_model=DepositResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_deposit(
    application_id: uuid.UUID,
    payload: DepositCreate,
    session: AsyncSession = Depends(get_db_session),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deposit recording not yet implemented; stub endpoint.",
    )
