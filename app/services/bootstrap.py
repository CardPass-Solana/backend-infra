from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AccountRole,
    Application,
    Bounty,
    BountyStatus,
    Deposit,
    DepositStatus,
)
from app.services.accounts import get_or_create_account


async def seed_poc_data(session: AsyncSession) -> None:
    """Populate the database with a minimal data set for the POC."""
    bounty_count = await session.execute(select(func.count()).select_from(Bounty))
    if bounty_count.scalar_one() > 0:
        return

    recruiter_alex = await get_or_create_account(
        session, "R3cruiterAlexWallet1111111111111111111", AccountRole.RECRUITER, "Helios Labs"
    )
    recruiter_jane = await get_or_create_account(
        session, "RecJaneWallet2222222222222222222222", AccountRole.RECRUITER, "Orbit Talent"
    )

    bounty_a = Bounty(
        recruiter_id=recruiter_alex.id,
        title="Senior Rust Engineer",
        description="Work on Solana core tooling and performance-critical on-chain programs.",
        reward_amount=Decimal("7500"),
        currency="USDC",
        company="Helios Labs",
        region="Remote - North America",
        employment_type="full-time",
        skills=["Rust", "Solana", "Anchor", "Performance"],
        status=BountyStatus.OPEN,
    )
    bounty_b = Bounty(
        recruiter_id=recruiter_jane.id,
        title="Growth Product Manager",
        description="Own go-to-market experiments for a crypto payments client.",
        reward_amount=Decimal("4200"),
        currency="USDC",
        company="Orbit Talent",
        region="Hybrid - Lisbon",
        employment_type="contract",
        skills=["Product", "Growth", "Payments", "Analytics"],
        status=BountyStatus.OPEN,
    )
    bounty_c = Bounty(
        recruiter_id=recruiter_jane.id,
        title="DeFi Smart Contract Auditor",
        description="Security review for a new perpetuals protocol ahead of launch.",
        reward_amount=Decimal("9800"),
        currency="USDC",
        company="Orbit Talent",
        region="Remote - Global",
        employment_type="freelance",
        skills=["Solidity", "Security", "EVM", "Auditing"],
        status=BountyStatus.OPEN,
    )

    session.add_all([bounty_a, bounty_b, bounty_c])
    await session.flush()

    candidate = await get_or_create_account(
        session,
        "CandWallet333333333333333333333333333333",
        AccountRole.CANDIDATE,
        "Nova Dev",
    )

    application = Application(
        bounty_id=bounty_a.id,
        applicant_wallet=candidate.wallet,
        referrer_wallet=None,
        public_profile={
            "skills": ["Rust", "Anchor", "Solana", "TypeScript"],
            "experience_years": 6,
            "region": "Toronto, Canada",
            "bio_short": "Solana core contributor, ex-Defi Labs. Built high-throughput trading infra.",
            "contact_price": "150 USDC/hour",
            "headline": "Senior Rust + Solana Engineer",
            "links": [
                "https://github.com/novadev",
                "https://linkedin.com/in/novadev",
            ],
        },
    )
    session.add(application)
    await session.flush()

    deposit = Deposit(
        application_id=application.id,
        recruiter_id=recruiter_alex.id,
        amount=Decimal("3000"),
        tx_signature="sample-helius-deposit-tx",
        status=DepositStatus.CLEARED,
        cleared_at=datetime.now(timezone.utc),
    )
    session.add(deposit)

    await session.commit()

