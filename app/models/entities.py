from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class AccountRole(str, enum.Enum):
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    REFERRER = "referrer"
    ADMIN = "admin"


class BountyStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAUSED = "paused"
    FILLED = "filled"
    CLOSED = "closed"


class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    SHORTLISTED = "shortlisted"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    CLEARED = "cleared"
    REFUNDED = "refunded"


class EventEntity(str, enum.Enum):
    BOUNTY = "bounty"
    APPLICATION = "application"
    DEPOSIT = "deposit"
    PAYOUT = "payout"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wallet: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    role: Mapped[AccountRole] = mapped_column(
        Enum(AccountRole, name="hh_account_role", native_enum=False), nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    bounties: Mapped[List["Bounty"]] = relationship(
        back_populates="recruiter", cascade="all, delete-orphan"
    )


class Bounty(Base):
    __tablename__ = "bounties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    reward_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USDC")
    escrow_account: Mapped[Optional[str]] = mapped_column(String(128))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    region: Mapped[Optional[str]] = mapped_column(String(255))
    employment_type: Mapped[Optional[str]] = mapped_column(String(64))
    skills: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), nullable=False, default=list
    )
    status: Mapped[BountyStatus] = mapped_column(
        Enum(BountyStatus, name="hh_bounty_status", native_enum=False),
        nullable=False,
        default=BountyStatus.DRAFT,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    recruiter: Mapped[Account] = relationship(back_populates="bounties")
    applications: Mapped[List["Application"]] = relationship(
        back_populates="bounty", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_bounty_status", "status"),
        Index("ix_bounty_company", "company"),
        Index("ix_bounty_region", "region"),
        Index("ix_bounty_employment_type", "employment_type"),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bounty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bounties.id", ondelete="CASCADE"), nullable=False
    )
    applicant_wallet: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    referrer_wallet: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    public_profile: Mapped[dict] = mapped_column(JSONB, nullable=False)
    cnft_mint: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    private_current_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_private_versions.id", ondelete="SET NULL")
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="hh_application_status", native_enum=False),
        nullable=False,
        default=ApplicationStatus.SUBMITTED,
    )
    access_granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    bounty: Mapped[Bounty] = relationship(back_populates="applications")
    private_versions: Mapped[List["ApplicationPrivateVersion"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="ApplicationPrivateVersion.application_id",
    )
    private_current_version: Mapped[Optional["ApplicationPrivateVersion"]] = relationship(
        "ApplicationPrivateVersion",
        foreign_keys=[private_current_version_id],
        post_update=True,
        lazy="joined",
    )
    deposits: Mapped[List["Deposit"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", passive_deletes=True
    )
    payout: Mapped[Optional["Payout"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        Index("ix_application_status", "status"),
        Index("ix_application_bounty_id", "bounty_id"),
    )


class ApplicationPrivateVersion(Base):
    __tablename__ = "application_private_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )

    application: Mapped[Application] = relationship(
        back_populates="private_versions", foreign_keys=[application_id]
    )
    uploader: Mapped[Optional[Account]] = relationship()

    __table_args__ = (
        UniqueConstraint("application_id", "payload_sha256", name="uq_application_payload_hash"),
        Index("ix_private_versions_application", "application_id"),
    )


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tx_signature: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DepositStatus] = mapped_column(
        Enum(DepositStatus, name="hh_deposit_status", native_enum=False),
        nullable=False,
        default=DepositStatus.PENDING,
    )
    cleared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    application: Mapped[Application] = relationship(back_populates="deposits")
    recruiter: Mapped[Account] = relationship()

    __table_args__ = (
        Index("ix_deposits_application", "application_id"),
    )


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    recruit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    referrer_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    platform_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    tx_signature: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    application: Mapped[Application] = relationship(back_populates="payout")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[EventEntity] = mapped_column(
        Enum(EventEntity, name="hh_event_entity", native_enum=False), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )

    created_by: Mapped[Optional[Account]] = relationship()

    __table_args__ = (
        Index("ix_events_entity", "entity_type", "entity_id"),
    )
