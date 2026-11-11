"""008_material_rate_published_at_nullable

Revision ID: 008_material_rate_published_at_nullable
Revises: 007_material_rate_safety_hardening
Create Date: 2026-11-07 00:25:00.000000

Phase 03H / Stage 2B.1 Correction - Source Accuracy, Data Freshness & Unit Consistency
- Makes published_at nullable on material_rate_observations to support undated indicative secondary estimates.
- Makes city nullable on material_rate_observations to support observations with only regional quarry or river basin origin.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008_material_rate_published_at_nullable"
down_revision: Union[str, None] = "007_material_rate_safety_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow nullable published_at for undated indicative estimates
    op.alter_column(
        "material_rate_observations",
        "published_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )

    # 2. Allow nullable city for records where only quarry origin or river basin is confirmed
    op.alter_column(
        "material_rate_observations",
        "city",
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade() -> None:
    # 1. Revert city back to non-nullable
    op.alter_column(
        "material_rate_observations",
        "city",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    # 2. Revert published_at back to non-nullable
    op.alter_column(
        "material_rate_observations",
        "published_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
