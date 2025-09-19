from __future__ import annotations

import uuid

import asyncio
import base64
import binascii
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db_session
from app.models import (
    AccountRole,
    Application,
    ApplicationPrivateVersion,
    Bounty,
    Deposit,
    DepositStatus,
)
from app.schemas import (
    ApplicationCreate,
    ApplicationPrivateProfileDemo,
    ApplicationPublicProfile,
    ApplicationResponse,
    DepositCreate,
    DepositResponse,
    SampleResumeResponse,
)
from app.services.accounts import get_or_create_account
from app.services.storage import get_private_storage_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate, session: AsyncSession = Depends(get_db_session)
):
    bounty = await session.get(Bounty, payload.bounty_id)
    if bounty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bounty not found")

    applicant_account = await get_or_create_account(
        session=session,
        wallet=payload.applicant_wallet,
        role=AccountRole.CANDIDATE,
    )

    if payload.referrer_wallet:
        await get_or_create_account(
            session=session,
            wallet=payload.referrer_wallet,
            role=AccountRole.REFERRER,
        )

    public_profile = payload.public_profile.model_dump()

    application = Application(
        bounty_id=bounty.id,
        applicant_wallet=payload.applicant_wallet,
        referrer_wallet=payload.referrer_wallet,
        public_profile=public_profile,
    )
    session.add(application)
    await session.flush()

    if payload.private_payload_base64:
        try:
            private_bytes = base64.b64decode(payload.private_payload_base64)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid private payload"
            ) from exc

        storage = get_private_storage_service()
        version_id = uuid.uuid4()
        key = storage.build_private_key(application.id, version_id)
        payload_sha256 = storage.compute_sha256(private_bytes)
        await asyncio.to_thread(storage.put_object, key, private_bytes)

        private_version = ApplicationPrivateVersion(
            id=version_id,
            application_id=application.id,
            s3_key=key,
            payload_sha256=payload_sha256,
            uploaded_by_id=applicant_account.id,
        )
        session.add(private_version)
        await session.flush()
        application.private_current_version_id = private_version.id

    await session.commit()
    await session.refresh(application)
    return application


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(Application).options(selectinload(Application.bounty))
    )
    return result.scalars().unique().all()


@router.get("/sample-resume", response_model=SampleResumeResponse)
async def get_sample_resume() -> SampleResumeResponse:
    public_profile = ApplicationPublicProfile(
        skills=["Solana", "TypeScript", "Rust", "React"],
        experience_years=6,
        region="Remote - North America",
        bio_short="Senior blockchain engineer delivering production-ready Solana apps.",
        contact_price="18% bounty share",
        headline="Senior Solana Engineer",
        links=[
            "https://github.com/sample-engineer",
            "https://www.linkedin.com/in/sample-solana-engineer",
        ],
    )

    private_profile = ApplicationPrivateProfileDemo(
        full_name="Ava Solana",
        contact_email="ava.solana@example.dev",
        contact_phone="+1-415-555-2048",
        telegram="@ava_solana",
        resume_url="https://example.dev/resume/ava-solana.pdf",
        resume_excerpt=(
            "Principal engineer with 6+ years building DeFi infrastructure and"
            " wallet experiences across Solana and Ethereum."
        ),
        cover_letter=(
            "Hi team — I'm excited about the opportunity to build recruitment"
            " automation with you. I've led engineering teams shipping two"
            " Solana programs to mainnet and would love to support your stack."
        ),
        attachments=[
            "https://github.com/sample-engineer/rust-solana-examples",
            "https://dev.to/sample-engineer/optimizing-solana-programs",
        ],
    )

    return SampleResumeResponse(public_profile=public_profile, private_profile=private_profile)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: uuid.UUID = Path(...),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Application)
            .options(selectinload(Application.bounty))
            .where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="application not found")
    return application


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
    result = await session.execute(
        select(Application)
        .options(selectinload(Application.bounty))
        .where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="application not found")

    recruiter_account = await get_or_create_account(
        session=session,
        wallet=payload.recruiter_wallet,
        role=AccountRole.RECRUITER,
    )

    if application.bounty.recruiter_id != recruiter_account.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recruiter does not own the bounty for this application",
        )

    deposit = Deposit(
        application_id=application.id,
        recruiter_id=recruiter_account.id,
        amount=Decimal(str(payload.amount)),
        tx_signature=payload.tx_signature,
        status=DepositStatus.PENDING,
    )
    session.add(deposit)
    await session.commit()
    await session.refresh(deposit)
    return deposit
