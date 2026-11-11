"""
Phase 03H / Stage 1 - Create Material Rate Intelligence Schema & Extend Background Jobs

Revision ID: 006_material_rate_intelligence
Revises: 005_background_jobs_infrastructure
Create Date: 2026-11-06 16:30:00.000000

Implements:
1. System-scope extension for background_jobs (nullable project_id/user_id with scope check and partial unique index)
2. Material catalog products (material_rate_products)
3. Data sources and providers (material_rate_sources)
4. Verified merchant/dealer directory (material_rate_dealers)
5. Direct dealer quotation submissions (material_rate_dealer_quotes)
6. Immutable time-series market observations (material_rate_observations)
7. Explainable verification event audit log (material_rate_verification_events)
8. Automated collection worker run history (material_rate_source_runs)
9. Link canonical material_rates snapshot table to catalog product_id and expand verification_status check constraint
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_material_rate_intelligence"
down_revision: Union[str, None] = "005_background_jobs_infrastructure"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Background Jobs: System-Scope Extension
    # -----------------------------------------------------------------------
    # Allow project_id and user_id to be nullable for global system jobs
    op.alter_column("background_jobs", "project_id", existing_type=sa.Uuid(), nullable=True)
    op.alter_column("background_jobs", "user_id", existing_type=sa.Uuid(), nullable=True)

    # Check constraint: project_id and user_id must be either BOTH null or BOTH not-null
    op.create_check_constraint(
        "ck_background_jobs_scope_consistency",
        "background_jobs",
        "((project_id IS NOT NULL AND user_id IS NOT NULL) OR (project_id IS NULL AND user_id IS NULL))",
    )

    # Partial unique index for global system jobs (WHERE project_id IS NULL AND idempotency_key IS NOT NULL)
    op.create_index(
        "uq_background_jobs_system_idempotency",
        "background_jobs",
        ["job_type", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL AND idempotency_key IS NOT NULL"),
        sqlite_where=sa.text("project_id IS NULL AND idempotency_key IS NOT NULL"),
    )

    # -----------------------------------------------------------------------
    # 2. Canonical Product Catalog (material_rate_products)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_products",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="Unique canonical product code"),
        sa.Column("category", sa.String(length=50), nullable=False, comment="Primary category: cement, steel, bricks, sand, crush, blocks, tiles, other"),
        sa.Column("subcategory", sa.String(length=50), nullable=True, comment="Subcategory"),
        sa.Column("canonical_name", sa.String(length=150), nullable=False, comment="Standard English material name"),
        sa.Column("canonical_name_urdu", sa.String(length=150), nullable=True, comment="Standard Urdu material name"),
        sa.Column("standard_unit", sa.String(length=50), nullable=False, comment="Standard measurement unit: bag_50kg, metric_ton, kg, 1000_bricks, cft, sqft, piece"),
        sa.Column("standard_unit_urdu", sa.String(length=50), nullable=True, comment="Urdu measurement unit"),
        sa.Column("spec_attributes", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True, comment="JSON attributes: grade, diameter, sutar, origin"),
        sa.Column("volatility_tier", sa.String(length=20), server_default="medium", nullable=False, comment="Volatility tier: low, medium, high, extreme"),
        sa.Column("max_acceptable_variance_pct", sa.Numeric(precision=5, scale=2), server_default="15.00", nullable=False, comment="Maximum expected variance percentage"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="Active status flag"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Last modification timestamp"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_products"),
        sa.CheckConstraint(
            "volatility_tier IN ('low', 'medium', 'high', 'extreme')",
            name="ck_material_rate_products_volatility_tier",
        ),
        sa.CheckConstraint(
            "max_acceptable_variance_pct >= 0 AND max_acceptable_variance_pct <= 100",
            name="ck_material_rate_products_max_variance",
        ),
    )
    op.create_index("ix_material_rate_products_code", "material_rate_products", ["code"], unique=True)
    op.create_index("ix_material_rate_products_category", "material_rate_products", ["category"], unique=False)

    # -----------------------------------------------------------------------
    # 3. Material Rate Data Sources (material_rate_sources)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_sources",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="Unique source code"),
        sa.Column("name", sa.String(length=150), nullable=False, comment="Official source name"),
        sa.Column("source_type", sa.String(length=50), nullable=False, comment="Source type: official, manufacturer, dealer_network, aggregator, manual_survey"),
        sa.Column("permission_status", sa.String(length=50), server_default="permitted", nullable=False, comment="Permission: permitted, manual_only, restricted"),
        sa.Column("reliability_tier", sa.String(length=50), server_default="indicative", nullable=False, comment="Tier: authoritative, verified, indicative, unverified"),
        sa.Column("refresh_cadence", sa.String(length=50), server_default="weekly", nullable=False, comment="Cadence: daily, weekly, monthly, ad_hoc"),
        sa.Column("freshness_ttl_days", sa.Integer(), server_default="30", nullable=False, comment="Freshness TTL in calendar days"),
        sa.Column("base_url", sa.String(length=500), nullable=True, comment="Portal or documentation base URL"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="Active source flag"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Last modification timestamp"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_sources"),
        sa.CheckConstraint(
            "source_type IN ('official', 'manufacturer', 'dealer_network', 'aggregator', 'manual_survey')",
            name="ck_material_rate_sources_source_type",
        ),
        sa.CheckConstraint(
            "permission_status IN ('permitted', 'manual_only', 'restricted')",
            name="ck_material_rate_sources_permission_status",
        ),
        sa.CheckConstraint(
            "reliability_tier IN ('authoritative', 'verified', 'indicative', 'unverified')",
            name="ck_material_rate_sources_reliability_tier",
        ),
        sa.CheckConstraint(
            "refresh_cadence IN ('daily', 'weekly', 'monthly', 'ad_hoc')",
            name="ck_material_rate_sources_refresh_cadence",
        ),
        sa.CheckConstraint(
            "freshness_ttl_days >= 1 AND freshness_ttl_days <= 365",
            name="ck_material_rate_sources_freshness_ttl",
        ),
    )
    op.create_index("ix_material_rate_sources_code", "material_rate_sources", ["code"], unique=True)

    # -----------------------------------------------------------------------
    # 4. Verified Dealers & Suppliers (material_rate_dealers)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_dealers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("user_id", sa.Uuid(), nullable=True, comment="Linked user account UUID"),
        sa.Column("business_name", sa.String(length=150), nullable=False, comment="Trading business name"),
        sa.Column("dealer_code", sa.String(length=50), nullable=False, comment="Unique dealer code"),
        sa.Column("city", sa.String(length=50), nullable=False, comment="Operating city"),
        sa.Column("market_area", sa.String(length=100), nullable=True, comment="Local market neighborhood"),
        sa.Column("address", sa.Text(), nullable=True, comment="Physical shop address"),
        sa.Column("contact_person", sa.String(length=100), nullable=True, comment="Contact person name"),
        sa.Column("contact_phone", sa.String(length=50), nullable=True, comment="Contact telephone"),
        sa.Column("ntn_number", sa.String(length=50), nullable=True, comment="National Tax Number"),
        sa.Column("verification_state", sa.String(length=50), server_default="unverified", nullable=False, comment="Status: unverified, verified, suspended, rejected"),
        sa.Column("verified_by_user_id", sa.Uuid(), nullable=True, comment="Reviewer user UUID"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True, comment="Verification timestamp"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="Active participation flag"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Last modification timestamp"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_material_rate_dealers_user_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], name="fk_material_rate_dealers_verified_by", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_dealers"),
        sa.CheckConstraint(
            "verification_state IN ('unverified', 'verified', 'suspended', 'rejected')",
            name="ck_material_rate_dealers_verification_state",
        ),
    )
    op.create_index("ix_material_rate_dealers_dealer_code", "material_rate_dealers", ["dealer_code"], unique=True)
    op.create_index("ix_material_rate_dealers_business_name", "material_rate_dealers", ["business_name"], unique=False)
    op.create_index("ix_material_rate_dealers_city", "material_rate_dealers", ["city"], unique=False)
    op.create_index("ix_material_rate_dealers_user_id", "material_rate_dealers", ["user_id"], unique=False)

    # -----------------------------------------------------------------------
    # 5. Direct Dealer Quotations (material_rate_dealer_quotes)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_dealer_quotes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("dealer_id", sa.Uuid(), nullable=False, comment="Submitting dealer UUID"),
        sa.Column("product_id", sa.Uuid(), nullable=False, comment="Canonical product UUID"),
        sa.Column("city", sa.String(length=50), nullable=False, comment="Market city"),
        sa.Column("quoted_price_pkr", sa.Numeric(precision=12, scale=2), nullable=False, comment="Raw quoted price in PKR"),
        sa.Column("quoted_unit", sa.String(length=50), nullable=False, comment="Raw quoted unit"),
        sa.Column("normalized_price_pkr", sa.Numeric(precision=12, scale=2), nullable=False, comment="Normalized price in PKR"),
        sa.Column("normalized_unit", sa.String(length=50), nullable=False, comment="Standard product unit"),
        sa.Column("quotation_date", sa.DateTime(timezone=True), nullable=False, comment="Quotation issuance timestamp"),
        sa.Column("validity_days", sa.Integer(), server_default="7", nullable=False, comment="Validity period in days"),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False, comment="Quotation expiration timestamp"),
        sa.Column("minimum_order_quantity", sa.Numeric(precision=12, scale=2), nullable=True, comment="Minimum order quantity"),
        sa.Column("delivery_charges_pkr", sa.Numeric(precision=12, scale=2), server_default="0.00", nullable=False, comment="Delivery charge in PKR"),
        sa.Column("tax_included", sa.Boolean(), server_default="true", nullable=False, comment="Taxes included flag"),
        sa.Column("payment_terms", sa.String(length=100), nullable=True, comment="Commercial payment terms"),
        sa.Column("evidence_file_path", sa.String(length=500), nullable=True, comment="Storage bucket path for evidence"),
        sa.Column("evidence_file_name", sa.String(length=255), nullable=True, comment="Evidence file name"),
        sa.Column("evidence_content_type", sa.String(length=100), nullable=True, comment="MIME type"),
        sa.Column("evidence_file_size_bytes", sa.BigInteger(), nullable=True, comment="Evidence size in bytes"),
        sa.Column("status", sa.String(length=50), server_default="pending_review", nullable=False, comment="Status: pending_review, verified, rejected, expired"),
        sa.Column("verified_by_user_id", sa.Uuid(), nullable=True, comment="Reviewer user UUID"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True, comment="Review timestamp"),
        sa.Column("rejection_reason", sa.Text(), nullable=True, comment="Rejection justification"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Last modification timestamp"),
        sa.ForeignKeyConstraint(["dealer_id"], ["material_rate_dealers.id"], name="fk_dealer_quotes_dealer_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["material_rate_products.id"], name="fk_dealer_quotes_product_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], name="fk_dealer_quotes_verified_by", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_dealer_quotes"),
        sa.CheckConstraint("quoted_price_pkr >= 0", name="ck_dealer_quotes_quoted_price_pkr"),
        sa.CheckConstraint("normalized_price_pkr >= 0", name="ck_dealer_quotes_normalized_price_pkr"),
        sa.CheckConstraint("delivery_charges_pkr >= 0", name="ck_dealer_quotes_delivery_charges"),
        sa.CheckConstraint("validity_days >= 1 AND validity_days <= 90", name="ck_dealer_quotes_validity_days"),
        sa.CheckConstraint("status IN ('pending_review', 'verified', 'rejected', 'expired')", name="ck_dealer_quotes_status"),
    )
    op.create_index("ix_dealer_quotes_dealer_id", "material_rate_dealer_quotes", ["dealer_id"], unique=False)
    op.create_index("ix_dealer_quotes_product_id", "material_rate_dealer_quotes", ["product_id"], unique=False)
    op.create_index("ix_dealer_quotes_city", "material_rate_dealer_quotes", ["city"], unique=False)
    op.create_index("ix_dealer_quotes_quotation_date", "material_rate_dealer_quotes", ["quotation_date"], unique=False)
    op.create_index("ix_dealer_quotes_valid_until", "material_rate_dealer_quotes", ["valid_until"], unique=False)
    op.create_index("ix_dealer_quotes_status", "material_rate_dealer_quotes", ["status"], unique=False)

    # -----------------------------------------------------------------------
    # 6. Immutable Rate Observations (material_rate_observations)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_observations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("source_id", sa.Uuid(), nullable=False, comment="Data source UUID"),
        sa.Column("product_id", sa.Uuid(), nullable=False, comment="Product UUID"),
        sa.Column("dealer_quote_id", sa.Uuid(), nullable=True, comment="Linked dealer quotation UUID"),
        sa.Column("city", sa.String(length=50), nullable=False, comment="Observation city"),
        sa.Column("observed_price_pkr", sa.Numeric(precision=12, scale=2), nullable=False, comment="Raw observed price in PKR"),
        sa.Column("observed_unit", sa.String(length=50), nullable=False, comment="Raw observed unit"),
        sa.Column("normalized_price_pkr", sa.Numeric(precision=12, scale=2), nullable=False, comment="Normalized price in PKR"),
        sa.Column("normalized_unit", sa.String(length=50), nullable=False, comment="Standard product unit"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, comment="Publication or quote issuance timestamp"),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="System collection timestamp"),
        sa.Column("source_url", sa.String(length=500), nullable=True, comment="Source URL or document citation"),
        sa.Column("verification_status", sa.String(length=50), server_default="unverified", nullable=False, comment="Verification status"),
        sa.Column("duplicate_fingerprint", sa.String(length=64), nullable=False, comment="SHA-256 fingerprint for deduplication"),
        sa.Column("background_job_id", sa.Uuid(), nullable=True, comment="Ingestion background job UUID"),
        sa.Column("observation_metadata", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True, comment="Context metadata dictionary"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.ForeignKeyConstraint(["source_id"], ["material_rate_sources.id"], name="fk_observations_source_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["material_rate_products.id"], name="fk_observations_product_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dealer_quote_id"], ["material_rate_dealer_quotes.id"], name="fk_observations_dealer_quote_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["background_job_id"], ["background_jobs.id"], name="fk_observations_background_job_id", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_observations"),
        sa.CheckConstraint("observed_price_pkr >= 0", name="ck_observations_observed_price_pkr"),
        sa.CheckConstraint("normalized_price_pkr >= 0", name="ck_observations_normalized_price_pkr"),
        sa.CheckConstraint(
            "verification_status IN ('unverified', 'verified_quote', 'cross_checked', 'verified_market_range', 'indicative', 'conflicted', 'stale')",
            name="ck_observations_verification_status",
        ),
    )
    op.create_index("ix_observations_fingerprint", "material_rate_observations", ["duplicate_fingerprint"], unique=True)
    op.create_index("ix_observations_source_id", "material_rate_observations", ["source_id"], unique=False)
    op.create_index("ix_observations_product_id", "material_rate_observations", ["product_id"], unique=False)
    op.create_index("ix_observations_dealer_quote_id", "material_rate_observations", ["dealer_quote_id"], unique=False)
    op.create_index("ix_observations_city", "material_rate_observations", ["city"], unique=False)
    op.create_index("ix_observations_published_at", "material_rate_observations", ["published_at"], unique=False)
    op.create_index("ix_observations_verification_status", "material_rate_observations", ["verification_status"], unique=False)
    op.create_index("ix_observations_product_city_published", "material_rate_observations", ["product_id", "city", "published_at"], unique=False)
    op.create_index("ix_observations_status_published", "material_rate_observations", ["verification_status", "published_at"], unique=False)

    # 6b. Append-Only Immutability Trigger for material_rate_observations (PostgreSQL)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            CREATE OR REPLACE FUNCTION trg_material_rate_observations_immutable()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'material_rate_observations table is strictly append-only; updates and deletions are forbidden';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER trg_protect_immutable_observations
            BEFORE UPDATE OR DELETE ON material_rate_observations
            FOR EACH ROW
            EXECUTE FUNCTION trg_material_rate_observations_immutable();
        """)

    # -----------------------------------------------------------------------
    # 7. Verification Events (material_rate_verification_events)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_verification_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("observation_id", sa.Uuid(), nullable=True, comment="Referenced observation UUID"),
        sa.Column("dealer_quote_id", sa.Uuid(), nullable=True, comment="Referenced dealer quote UUID"),
        sa.Column("previous_status", sa.String(length=50), nullable=True, comment="Previous verification status"),
        sa.Column("new_status", sa.String(length=50), nullable=False, comment="Assigned new status"),
        sa.Column("reason", sa.Text(), nullable=False, comment="Verification rationale or anomaly description"),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True, comment="Reviewer user UUID (null for system decision)"),
        sa.Column("metadata_snapshot", postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"), nullable=True, comment="Evaluation metrics snapshot"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Creation timestamp"),
        sa.ForeignKeyConstraint(["observation_id"], ["material_rate_observations.id"], name="fk_verification_events_observation", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dealer_quote_id"], ["material_rate_dealer_quotes.id"], name="fk_verification_events_dealer_quote", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_verification_events_actor", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_verification_events"),
        sa.CheckConstraint(
            "((observation_id IS NOT NULL) OR (dealer_quote_id IS NOT NULL))",
            name="ck_verification_events_target",
        ),
    )
    op.create_index("ix_verification_events_observation_id", "material_rate_verification_events", ["observation_id"], unique=False)
    op.create_index("ix_verification_events_dealer_quote_id", "material_rate_verification_events", ["dealer_quote_id"], unique=False)
    op.create_index("ix_verification_events_actor_user_id", "material_rate_verification_events", ["actor_user_id"], unique=False)

    # -----------------------------------------------------------------------
    # 8. Source Runs (material_rate_source_runs)
    # -----------------------------------------------------------------------
    op.create_table(
        "material_rate_source_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False, comment="Internal UUID primary key"),
        sa.Column("source_id", sa.Uuid(), nullable=False, comment="Referenced data source UUID"),
        sa.Column("background_job_id", sa.Uuid(), nullable=True, comment="Executing background job UUID"),
        sa.Column("status", sa.String(length=50), server_default="running", nullable=False, comment="Run state: running, completed, failed"),
        sa.Column("records_discovered", sa.Integer(), server_default="0", nullable=False, comment="Total records discovered"),
        sa.Column("records_accepted", sa.Integer(), server_default="0", nullable=False, comment="Total records accepted"),
        sa.Column("records_rejected", sa.Integer(), server_default="0", nullable=False, comment="Total records rejected"),
        sa.Column("error_summary", sa.Text(), nullable=True, comment="Sanitized error summary"),
        sa.Column("duration_seconds", sa.Numeric(precision=8, scale=2), nullable=True, comment="Duration in seconds"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Run start timestamp"),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True, comment="Run completion timestamp"),
        sa.ForeignKeyConstraint(["source_id"], ["material_rate_sources.id"], name="fk_source_runs_source_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["background_job_id"], ["background_jobs.id"], name="fk_source_runs_background_job_id", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_material_rate_source_runs"),
        sa.CheckConstraint("status IN ('running', 'completed', 'failed')", name="ck_source_runs_status"),
        sa.CheckConstraint("records_discovered >= 0", name="ck_source_runs_discovered"),
        sa.CheckConstraint("records_accepted >= 0", name="ck_source_runs_accepted"),
        sa.CheckConstraint("records_rejected >= 0", name="ck_source_runs_rejected"),
    )
    op.create_index("ix_source_runs_source_id", "material_rate_source_runs", ["source_id"], unique=False)
    op.create_index("ix_source_runs_background_job_id", "material_rate_source_runs", ["background_job_id"], unique=False)

    # -----------------------------------------------------------------------
    # 9. Link canonical material_rates snapshot table to material_rate_products
    # -----------------------------------------------------------------------
    op.add_column("material_rates", sa.Column("product_id", sa.Uuid(), nullable=True, comment="Optional link to canonical product catalog"))
    op.create_foreign_key(
        "fk_material_rates_product_id",
        "material_rates",
        "material_rate_products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_material_rates_product_id", "material_rates", ["product_id"], unique=False)

    # Expand verification_status check constraint on material_rates
    op.drop_constraint("ck_material_rates_verification_status", "material_rates", type_="check")
    op.create_check_constraint(
        "ck_material_rates_verification_status",
        "material_rates",
        "verification_status IN ('verified', 'unverified', 'stale', 'verified_quote', 'cross_checked', 'verified_market_range', 'indicative', 'conflicted')",
    )


def downgrade() -> None:
    # -----------------------------------------------------------------------
    # Revert 9. canonical material_rates snapshot changes
    # -----------------------------------------------------------------------
    op.drop_constraint("ck_material_rates_verification_status", "material_rates", type_="check")
    op.create_check_constraint(
        "ck_material_rates_verification_status",
        "material_rates",
        "verification_status IN ('verified', 'unverified', 'stale')",
    )
    op.drop_constraint("fk_material_rates_product_id", "material_rates", type_="foreignkey")
    op.drop_index("ix_material_rates_product_id", table_name="material_rates")
    op.drop_column("material_rates", "product_id")

    # -----------------------------------------------------------------------
    # Revert 8. material_rate_source_runs
    # -----------------------------------------------------------------------
    op.drop_index("ix_source_runs_background_job_id", table_name="material_rate_source_runs")
    op.drop_index("ix_source_runs_source_id", table_name="material_rate_source_runs")
    op.drop_table("material_rate_source_runs")

    # -----------------------------------------------------------------------
    # Revert 7. material_rate_verification_events
    # -----------------------------------------------------------------------
    op.drop_index("ix_verification_events_actor_user_id", table_name="material_rate_verification_events")
    op.drop_index("ix_verification_events_dealer_quote_id", table_name="material_rate_verification_events")
    op.drop_index("ix_verification_events_observation_id", table_name="material_rate_verification_events")
    op.drop_table("material_rate_verification_events")

    # -----------------------------------------------------------------------
    # Revert 6. material_rate_observations
    # -----------------------------------------------------------------------
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_protect_immutable_observations ON material_rate_observations;")
        op.execute("DROP FUNCTION IF EXISTS trg_material_rate_observations_immutable();")

    op.drop_index("ix_observations_status_published", table_name="material_rate_observations")
    op.drop_index("ix_observations_product_city_published", table_name="material_rate_observations")
    op.drop_index("ix_observations_verification_status", table_name="material_rate_observations")
    op.drop_index("ix_observations_published_at", table_name="material_rate_observations")
    op.drop_index("ix_observations_city", table_name="material_rate_observations")
    op.drop_index("ix_observations_dealer_quote_id", table_name="material_rate_observations")
    op.drop_index("ix_observations_product_id", table_name="material_rate_observations")
    op.drop_index("ix_observations_source_id", table_name="material_rate_observations")
    op.drop_index("ix_observations_fingerprint", table_name="material_rate_observations")
    op.drop_table("material_rate_observations")

    # -----------------------------------------------------------------------
    # Revert 5. material_rate_dealer_quotes
    # -----------------------------------------------------------------------
    op.drop_index("ix_dealer_quotes_status", table_name="material_rate_dealer_quotes")
    op.drop_index("ix_dealer_quotes_valid_until", table_name="material_rate_dealer_quotes")
    op.drop_index("ix_dealer_quotes_quotation_date", table_name="material_rate_dealer_quotes")
    op.drop_index("ix_dealer_quotes_city", table_name="material_rate_dealer_quotes")
    op.drop_index("ix_dealer_quotes_product_id", table_name="material_rate_dealer_quotes")
    op.drop_index("ix_dealer_quotes_dealer_id", table_name="material_rate_dealer_quotes")
    op.drop_table("material_rate_dealer_quotes")

    # -----------------------------------------------------------------------
    # Revert 4. material_rate_dealers
    # -----------------------------------------------------------------------
    op.drop_index("ix_material_rate_dealers_user_id", table_name="material_rate_dealers")
    op.drop_index("ix_material_rate_dealers_city", table_name="material_rate_dealers")
    op.drop_index("ix_material_rate_dealers_business_name", table_name="material_rate_dealers")
    op.drop_index("ix_material_rate_dealers_dealer_code", table_name="material_rate_dealers")
    op.drop_table("material_rate_dealers")

    # -----------------------------------------------------------------------
    # Revert 3. material_rate_sources
    # -----------------------------------------------------------------------
    op.drop_index("ix_material_rate_sources_code", table_name="material_rate_sources")
    op.drop_table("material_rate_sources")

    # -----------------------------------------------------------------------
    # Revert 2. material_rate_products
    # -----------------------------------------------------------------------
    op.drop_index("ix_material_rate_products_category", table_name="material_rate_products")
    op.drop_index("ix_material_rate_products_code", table_name="material_rate_products")
    op.drop_table("material_rate_products")

    # -----------------------------------------------------------------------
    # Revert 1. background_jobs system-scope changes
    # -----------------------------------------------------------------------
    op.drop_index("uq_background_jobs_system_idempotency", table_name="background_jobs")
    op.drop_constraint("ck_background_jobs_scope_consistency", "background_jobs", type_="check")
    op.alter_column("background_jobs", "user_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("background_jobs", "project_id", existing_type=sa.Uuid(), nullable=False)

