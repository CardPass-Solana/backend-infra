"""extend bounty fields for poc

Revision ID: 0002_extend_bounty_fields
Revises: 0001_initial_schema
Create Date: 2024-06-07 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_extend_bounty_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bounties",
        sa.Column("company", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "bounties",
        sa.Column("region", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "bounties",
        sa.Column("employment_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "bounties",
        sa.Column(
            "skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_index("ix_bounty_company", "bounties", ["company"], unique=False)
    op.create_index("ix_bounty_region", "bounties", ["region"], unique=False)
    op.create_index(
        "ix_bounty_employment_type", "bounties", ["employment_type"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_bounty_employment_type", table_name="bounties")
    op.drop_index("ix_bounty_region", table_name="bounties")
    op.drop_index("ix_bounty_company", table_name="bounties")
    op.drop_column("bounties", "skills")
    op.drop_column("bounties", "employment_type")
    op.drop_column("bounties", "region")
    op.drop_column("bounties", "company")

