"""initial schema for bounty platform

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2023-11-18 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

account_role_values = ("recruiter", "candidate", "referrer", "admin")
bounty_status_values = ("draft", "open", "paused", "filled", "closed")
application_status_values = (
    "submitted",
    "shortlisted",
    "hired",
    "rejected",
    "withdrawn",
)
deposit_status_values = ("pending", "cleared", "refunded")
event_entity_values = ("bounty", "application", "deposit", "payout")

account_role_enum = postgresql.ENUM(
    *account_role_values, name="hh_account_role", create_type=False
)
bounty_status_enum = postgresql.ENUM(
    *bounty_status_values, name="hh_bounty_status", create_type=False
)
application_status_enum = postgresql.ENUM(
    *application_status_values, name="hh_application_status", create_type=False
)
deposit_status_enum = postgresql.ENUM(
    *deposit_status_values, name="hh_deposit_status", create_type=False
)
event_entity_enum = postgresql.ENUM(
    *event_entity_values, name="hh_event_entity", create_type=False
)


def _ensure_enum(name: str, values: tuple[str, ...]) -> None:
    literals = ", ".join(f"'{value}'" for value in values)
    stmt = text(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = :type_name) THEN
                CREATE TYPE "{name}" AS ENUM ({literals});
            END IF;
        END
        $$;
        """
    ).bindparams(type_name=name)
    op.execute(stmt)


def _drop_enum(name: str) -> None:
    stmt = text(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = :type_name) THEN
                DROP TYPE "{name}";
            END IF;
        END
        $$;
        """
    ).bindparams(type_name=name)
    op.execute(stmt)


def upgrade() -> None:
    _ensure_enum("hh_account_role", account_role_values)
    _ensure_enum("hh_bounty_status", bounty_status_values)
    _ensure_enum("hh_application_status", application_status_values)
    _ensure_enum("hh_deposit_status", deposit_status_values)
    _ensure_enum("hh_event_entity", event_entity_values)

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

    _drop_enum("hh_event_entity")
    _drop_enum("hh_deposit_status")
    _drop_enum("hh_application_status")
    _drop_enum("hh_bounty_status")
    _drop_enum("hh_account_role")
