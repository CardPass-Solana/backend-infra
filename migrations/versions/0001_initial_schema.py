"""Initial schema for bounty platform

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2023-11-18 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


ACCOUNT_ROLES = ("recruiter", "candidate", "referrer", "admin")
BOUNTY_STATUSES = ("draft", "open", "paused", "filled", "closed")
APPLICATION_STATUSES = (
    "submitted",
    "shortlisted",
    "hired",
    "rejected",
    "withdrawn",
)
DEPOSIT_STATUSES = ("pending", "cleared", "refunded")
EVENT_ENTITIES = ("bounty", "application", "deposit", "payout")


def _enum(name: str, values: tuple[str, ...]) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, validate_strings=True)


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wallet", sa.String(length=128), nullable=False),
        sa.Column("role", _enum("hh_account_role", ACCOUNT_ROLES), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("wallet"),
    )
    op.create_index("ix_accounts_wallet", "accounts", ["wallet"], unique=False)

    op.create_table(
        "bounties",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("reward_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("escrow_account", sa.String(length=128), nullable=True),
        sa.Column(
            "status",
            _enum("hh_bounty_status", BOUNTY_STATUSES),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recruiter_id"], ["accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bounty_status", "bounties", ["status"], unique=False)

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bounty_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applicant_wallet", sa.String(length=128), nullable=False),
        sa.Column("referrer_wallet", sa.String(length=128), nullable=True),
        sa.Column("public_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cnft_mint", sa.String(length=128), nullable=True),
        sa.Column("private_current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", _enum("hh_application_status", APPLICATION_STATUSES), nullable=False),
        sa.Column("access_granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["bounty_id"], ["bounties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnft_mint"),
    )
    op.create_index(
        "ix_application_status", "applications", ["status"], unique=False
    )
    op.create_index(
        "ix_application_bounty_id", "applications", ["bounty_id"], unique=False
    )
    op.create_index(
        "ix_application_applicant_wallet",
        "applications",
        ["applicant_wallet"],
        unique=False,
    )
    op.create_index(
        "ix_application_referrer_wallet",
        "applications",
        ["referrer_wallet"],
        unique=False,
    )

    op.create_table(
        "application_private_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"], ["accounts.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "application_id", "payload_sha256", name="uq_application_payload_hash"
        ),
    )
    op.create_index(
        "ix_private_versions_application",
        "application_private_versions",
        ["application_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_application_private_current_version",
        "applications",
        "application_private_versions",
        ["private_current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "deposits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("tx_signature", sa.String(length=255), nullable=False),
        sa.Column("status", _enum("hh_deposit_status", DEPOSIT_STATUSES), nullable=False),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["recruiter_id"], ["accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deposits_application", "deposits", ["application_id"], unique=False
    )

    op.create_table(
        "payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recruit_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("referrer_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("platform_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("tx_signature", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("entity_type", _enum("hh_event_entity", EVENT_ENTITIES), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["accounts.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_events_entity", "events", ["entity_type", "entity_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_events_entity", table_name="events")
    op.drop_table("events")

    op.drop_table("payouts")

    op.drop_index("ix_deposits_application", table_name="deposits")
    op.drop_table("deposits")

    op.drop_constraint(
        "fk_application_private_current_version", "applications", type_="foreignkey"
    )
    op.drop_index(
        "ix_private_versions_application", table_name="application_private_versions"
    )
    op.drop_table("application_private_versions")

    op.drop_index("ix_application_referrer_wallet", table_name="applications")
    op.drop_index("ix_application_applicant_wallet", table_name="applications")
    op.drop_index("ix_application_bounty_id", table_name="applications")
    op.drop_index("ix_application_status", table_name="applications")
    op.drop_table("applications")

    op.drop_index("ix_bounty_status", table_name="bounties")
    op.drop_table("bounties")

    op.drop_index("ix_accounts_wallet", table_name="accounts")
    op.drop_table("accounts")
