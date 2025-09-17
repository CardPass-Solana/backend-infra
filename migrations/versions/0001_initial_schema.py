"""initial schema for bounty platform

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

account_role_enum = sa.Enum(
    "recruiter", "candidate", "referrer", "admin", name="account_role"
)
bounty_status_enum = sa.Enum(
    "draft", "open", "paused", "filled", "closed", name="bounty_status"
)
application_status_enum = sa.Enum(
    "submitted", "shortlisted", "hired", "rejected", "withdrawn", name="application_status"
)
deposit_status_enum = sa.Enum(
    "pending", "cleared", "refunded", name="deposit_status"
)
event_entity_enum = sa.Enum(
    "bounty", "application", "deposit", "payout", name="event_entity"
)


def upgrade() -> None:
    account_role_enum.create(op.get_bind(), checkfirst=True)
    bounty_status_enum.create(op.get_bind(), checkfirst=True)
    application_status_enum.create(op.get_bind(), checkfirst=True)
    deposit_status_enum.create(op.get_bind(), checkfirst=True)
    event_entity_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wallet", sa.String(length=128), nullable=False),
        sa.Column("role", account_role_enum, nullable=False),
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
        sa.Column("status", bounty_status_enum, nullable=False),
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
        sa.Column("status", application_status_enum, nullable=False),
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
    )
    op.create_unique_constraint(
        "uq_application_payload_hash",
        "application_private_versions",
        ["application_id", "payload_sha256"],
    )
    op.create_index(
        "ix_private_versions_application",
        "application_private_versions",
        ["application_id"],
        unique=False,
    )

    op.create_foreign_key(
        constraint_name="fk_application_private_current_version",
        source="applications",
        referent="application_private_versions",
        local_cols=["private_current_version_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "deposits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("tx_signature", sa.String(length=255), nullable=False),
        sa.Column("status", deposit_status_enum, nullable=False),
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
        sa.Column("entity_type", event_entity_enum, nullable=False),
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

    op.drop_index("ix_application_applicant_wallet", table_name="applications")
    op.drop_index("ix_application_bounty_id", table_name="applications")
    op.drop_index("ix_application_status", table_name="applications")
    op.drop_table("applications")

    op.drop_index("ix_bounty_status", table_name="bounties")
    op.drop_table("bounties")

    op.drop_index("ix_accounts_wallet", table_name="accounts")
    op.drop_table("accounts")

    event_entity_enum.drop(op.get_bind(), checkfirst=True)
    deposit_status_enum.drop(op.get_bind(), checkfirst=True)
    application_status_enum.drop(op.get_bind(), checkfirst=True)
    bounty_status_enum.drop(op.get_bind(), checkfirst=True)
    account_role_enum.drop(op.get_bind(), checkfirst=True)
