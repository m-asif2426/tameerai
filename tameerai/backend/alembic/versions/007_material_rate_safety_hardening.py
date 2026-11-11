"""007_material_rate_safety_hardening

Revision ID: 007_material_rate_safety_hardening
Revises: 006_material_rate_intelligence
Create Date: 2026-11-06 18:55:00.000000

Phase 03H / Stage 1.3 - Database Safety Remediation & Reliability Hardening
- Implements statement-level BEFORE TRUNCATE trigger on material_rate_observations.
- Revokes TRUNCATE privileges on material_rate_observations from PUBLIC and non-owner roles.
- Changes fk_observations_dealer_quote_id and fk_observations_background_job_id from SET NULL to RESTRICT.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_material_rate_safety_hardening"
down_revision: Union[str, None] = "006_material_rate_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = (bind.dialect.name == "postgresql")

    # 1. Update Foreign Keys on material_rate_observations from SET NULL to RESTRICT
    # Drop existing FK constraints
    op.drop_constraint("fk_observations_dealer_quote_id", "material_rate_observations", type_="foreignkey")
    op.drop_constraint("fk_observations_background_job_id", "material_rate_observations", type_="foreignkey")

    # Re-create FK constraints with ondelete="RESTRICT"
    op.create_foreign_key(
        "fk_observations_dealer_quote_id",
        "material_rate_observations",
        "material_rate_dealer_quotes",
        ["dealer_quote_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_observations_background_job_id",
        "material_rate_observations",
        "background_jobs",
        ["background_job_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 2. PostgreSQL-specific TRUNCATE protection trigger and privilege hardening
    if is_postgres:
        # Create statement-level TRUNCATE protection function
        op.execute("""
            CREATE OR REPLACE FUNCTION trg_material_rate_observations_prevent_truncate()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'material_rate_observations is strictly append-only; TRUNCATE is forbidden.';
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create statement-level BEFORE TRUNCATE trigger
        op.execute("""
            CREATE TRIGGER trg_protect_truncate_observations
            BEFORE TRUNCATE ON material_rate_observations
            FOR EACH STATEMENT
            EXECUTE FUNCTION trg_material_rate_observations_prevent_truncate();
        """)

        # Revoke TRUNCATE privilege from PUBLIC
        op.execute("""
            REVOKE TRUNCATE ON TABLE material_rate_observations FROM PUBLIC;
        """)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = (bind.dialect.name == "postgresql")

    if is_postgres:
        # Drop statement-level BEFORE TRUNCATE trigger and function
        op.execute("DROP TRIGGER IF EXISTS trg_protect_truncate_observations ON material_rate_observations;")
        op.execute("DROP FUNCTION IF EXISTS trg_material_rate_observations_prevent_truncate();")

    # Revert Foreign Keys back to SET NULL
    op.drop_constraint("fk_observations_dealer_quote_id", "material_rate_observations", type_="foreignkey")
    op.drop_constraint("fk_observations_background_job_id", "material_rate_observations", type_="foreignkey")

    op.create_foreign_key(
        "fk_observations_dealer_quote_id",
        "material_rate_observations",
        "material_rate_dealer_quotes",
        ["dealer_quote_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_observations_background_job_id",
        "material_rate_observations",
        "background_jobs",
        ["background_job_id"],
        ["id"],
        ondelete="SET NULL",
    )

