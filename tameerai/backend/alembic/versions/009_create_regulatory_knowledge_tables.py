"""009_create_regulatory_knowledge_tables

Revision ID: 009_create_regulatory_knowledge_tables
Revises: 008_material_rate_published_at_nullable
Create Date: 2026-11-08 23:30:00.000000

Phase 03.3 - Pakistan Statutory Regulatory Knowledge Base
Creates:
- regulatory_authorities
- regulatory_documents
- regulatory_document_versions
- regulatory_clauses
- regulatory_amendments
- regulatory_ingestion_jobs
- regulatory_review_records
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "009_create_regulatory_knowledge_tables"
down_revision: Union[str, None] = "008_material_rate_published_at_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: regulatory_authorities
    op.create_table(
        "regulatory_authorities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_urdu", sa.String(length=255), nullable=True),
        sa.Column("jurisdiction_level", sa.String(length=30), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("official_website", sa.String(length=500), nullable=False),
        sa.Column("regulatory_domain", sa.String(length=100), nullable=False),
        sa.Column("publication_channels", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("credibility_tier", sa.String(length=35), server_default="tier_b_official_regulatory", nullable=False),
        sa.Column("verification_status", sa.String(length=30), server_default="discovered", nullable=False),
        sa.Column("last_discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_regulatory_authorities_code"),
        sa.CheckConstraint(
            "jurisdiction_level IN ('federal', 'provincial', 'municipal', 'special_authority')",
            name="ck_regulatory_authorities_jurisdiction_level",
        ),
        sa.CheckConstraint(
            "credibility_tier IN ('tier_a_statutory', 'tier_b_official_regulatory', 'tier_c_recognized_technical', 'tier_d_secondary')",
            name="ck_regulatory_authorities_credibility_tier",
        ),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'discovered', 'unverified')",
            name="ck_regulatory_authorities_verification_status",
        ),
    )
    op.create_index(op.f("ix_regulatory_authorities_code"), "regulatory_authorities", ["code"], unique=False)
    op.create_index(op.f("ix_regulatory_authorities_jurisdiction_level"), "regulatory_authorities", ["jurisdiction_level"], unique=False)
    op.create_index(op.f("ix_regulatory_authorities_province"), "regulatory_authorities", ["province"], unique=False)
    op.create_index(op.f("ix_regulatory_authorities_city"), "regulatory_authorities", ["city"], unique=False)
    op.create_index(op.f("ix_regulatory_authorities_verification_status"), "regulatory_authorities", ["verification_status"], unique=False)

    # 2. Table: regulatory_documents
    op.create_table(
        "regulatory_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("authority_id", sa.Uuid(), nullable=False),
        sa.Column("document_code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("title_urdu", sa.String(length=300), nullable=True),
        sa.Column("official_document_number", sa.String(length=150), nullable=True),
        sa.Column("document_category", sa.String(length=50), nullable=False),
        sa.Column("legal_instrument_type", sa.String(length=50), nullable=False),
        sa.Column("legal_force_status", sa.String(length=40), server_default="mandatory_notified", nullable=False),
        sa.Column("jurisdiction_country", sa.String(length=50), server_default="Pakistan", nullable=False),
        sa.Column("jurisdiction_province", sa.String(length=100), nullable=True),
        sa.Column("jurisdiction_city", sa.String(length=100), nullable=True),
        sa.Column("applicable_districts", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="DISCOVERED", nullable=False),
        sa.Column("superseded_by_document_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["authority_id"], ["regulatory_authorities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["superseded_by_document_id"], ["regulatory_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_code", name="uq_regulatory_documents_code"),
        sa.CheckConstraint(
            "document_category IN ('building_code', 'zoning_regulation', 'act_legislation', 'bye_law', 'technical_standard', 'guideline')",
            name="ck_regulatory_documents_category",
        ),
        sa.CheckConstraint(
            "legal_instrument_type IN ('statutory_act', 'gazette_notification', 'authority_regulations', 'standard_specification', 'advisory_guideline')",
            name="ck_regulatory_documents_instrument_type",
        ),
        sa.CheckConstraint(
            "legal_force_status IN ('legally_binding', 'mandatory_notified', 'adopted_standard', 'guideline_only', 'draft_non_binding')",
            name="ck_regulatory_documents_legal_force",
        ),
        sa.CheckConstraint(
            "status IN ('DISCOVERED', 'SOURCE_VERIFIED', 'ACQUIRED', 'INGESTED', 'PARSED', 'REVIEW_REQUIRED', 'PUBLISHED', 'SUPERSEDED', 'WITHDRAWN', 'REJECTED')",
            name="ck_regulatory_documents_status",
        ),
    )
    op.create_index(op.f("ix_regulatory_documents_authority_id"), "regulatory_documents", ["authority_id"], unique=False)
    op.create_index(op.f("ix_regulatory_documents_document_code"), "regulatory_documents", ["document_code"], unique=False)
    op.create_index(op.f("ix_regulatory_documents_document_category"), "regulatory_documents", ["document_category"], unique=False)
    op.create_index(op.f("ix_regulatory_documents_legal_force_status"), "regulatory_documents", ["legal_force_status"], unique=False)
    op.create_index(op.f("ix_regulatory_documents_jurisdiction_province"), "regulatory_documents", ["jurisdiction_province"], unique=False)
    op.create_index(op.f("ix_regulatory_documents_jurisdiction_city"), "regulatory_documents", ["jurisdiction_city"], unique=False)
    op.create_index(op.f("ix_regulatory_documents_status"), "regulatory_documents", ["status"], unique=False)

    # 3. Table: regulatory_document_versions
    op.create_table(
        "regulatory_document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version_label", sa.String(length=50), nullable=False),
        sa.Column("edition", sa.String(length=50), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("notification_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("superseded_by_version_id", sa.Uuid(), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("official_source_url", sa.String(length=500), nullable=True),
        sa.Column("source_file_sha256", sa.String(length=64), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), server_default="application/pdf", nullable=True),
        sa.Column("total_pages", sa.Integer(), server_default="0", nullable=False),
        sa.Column("language", sa.String(length=10), server_default="en", nullable=False),
        sa.Column("provenance_details", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["regulatory_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["superseded_by_version_id"], ["regulatory_document_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_label", name="uq_regulatory_versions_doc_label"),
        sa.CheckConstraint("total_pages >= 0", name="ck_regulatory_versions_total_pages_non_negative"),
        sa.CheckConstraint("file_size_bytes IS NULL OR file_size_bytes >= 0", name="ck_regulatory_versions_file_size_non_negative"),
    )
    op.create_index(op.f("ix_regulatory_document_versions_document_id"), "regulatory_document_versions", ["document_id"], unique=False)
    op.create_index(op.f("ix_regulatory_document_versions_effective_date"), "regulatory_document_versions", ["effective_date"], unique=False)
    op.create_index(op.f("ix_regulatory_document_versions_is_current"), "regulatory_document_versions", ["is_current"], unique=False)
    op.create_index(op.f("ix_regulatory_document_versions_source_file_sha256"), "regulatory_document_versions", ["source_file_sha256"], unique=False)

    # 4. Table: regulatory_clauses
    op.create_table(
        "regulatory_clauses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("chapter_number", sa.String(length=50), nullable=True),
        sa.Column("chapter_title", sa.String(length=255), nullable=True),
        sa.Column("section_number", sa.String(length=50), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("clause_number", sa.String(length=100), nullable=False),
        sa.Column("clause_title", sa.String(length=255), nullable=True),
        sa.Column("subclause_number", sa.String(length=50), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=30), server_default="text", nullable=False),
        sa.Column("table_data_json", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("extraction_method", sa.String(length=30), server_default="native_pdf", nullable=False),
        sa.Column("ocr_confidence", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("legal_significance", sa.String(length=35), server_default="mandatory_requirement", nullable=False),
        sa.Column("review_status", sa.String(length=30), server_default="unreviewed", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["regulatory_document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "content_type IN ('text', 'table', 'formula', 'figure_caption', 'annexure', 'schedule', 'definition')",
            name="ck_regulatory_clauses_content_type",
        ),
        sa.CheckConstraint(
            "extraction_method IN ('native_pdf', 'docx_xml', 'structured_text', 'ocr')",
            name="ck_regulatory_clauses_extraction_method",
        ),
        sa.CheckConstraint(
            "legal_significance IN ('mandatory_requirement', 'prohibition', 'conditional_exception', 'procedural_step', 'technical_formula', 'definition', 'guideline')",
            name="ck_regulatory_clauses_legal_significance",
        ),
        sa.CheckConstraint(
            "review_status IN ('unreviewed', 'reviewed', 'flagged_uncertain')",
            name="ck_regulatory_clauses_review_status",
        ),
        sa.CheckConstraint("page_start >= 1", name="ck_regulatory_clauses_page_start_positive"),
        sa.CheckConstraint("page_end >= page_start", name="ck_regulatory_clauses_page_end_valid"),
    )
    op.create_index(op.f("ix_regulatory_clauses_version_id"), "regulatory_clauses", ["version_id"], unique=False)
    op.create_index(op.f("ix_regulatory_clauses_clause_number"), "regulatory_clauses", ["clause_number"], unique=False)
    op.create_index(op.f("ix_regulatory_clauses_review_status"), "regulatory_clauses", ["review_status"], unique=False)

    # 5. Table: regulatory_amendments
    op.create_table(
        "regulatory_amendments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("base_version_id", sa.Uuid(), nullable=False),
        sa.Column("amending_version_id", sa.Uuid(), nullable=True),
        sa.Column("amendment_gazette_number", sa.String(length=150), nullable=True),
        sa.Column("notification_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("affected_clause_reference", sa.String(length=100), nullable=False),
        sa.Column("amendment_type", sa.String(length=30), nullable=False),
        sa.Column("prior_text", sa.Text(), nullable=True),
        sa.Column("amended_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["base_version_id"], ["regulatory_document_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["amending_version_id"], ["regulatory_document_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "amendment_type IN ('substitution', 'insertion', 'deletion', 'modification')",
            name="ck_regulatory_amendments_type",
        ),
    )
    op.create_index(op.f("ix_regulatory_amendments_base_version_id"), "regulatory_amendments", ["base_version_id"], unique=False)
    op.create_index(op.f("ix_regulatory_amendments_effective_date"), "regulatory_amendments", ["effective_date"], unique=False)
    op.create_index(op.f("ix_regulatory_amendments_affected_clause_reference"), "regulatory_amendments", ["affected_clause_reference"], unique=False)

    # 6. Table: regulatory_ingestion_jobs
    op.create_table(
        "regulatory_ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_code", sa.String(length=100), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("source_url_or_path", sa.String(length=500), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=True),
        sa.Column("total_pages_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("clauses_extracted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tables_extracted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("errors_json", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["regulatory_document_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_regulatory_ingestion_jobs_status",
        ),
        sa.CheckConstraint("total_pages_processed >= 0", name="ck_regulatory_ingestion_jobs_pages_non_neg"),
        sa.CheckConstraint("clauses_extracted_count >= 0", name="ck_regulatory_ingestion_jobs_clauses_non_neg"),
    )
    op.create_index(op.f("ix_regulatory_ingestion_jobs_document_code"), "regulatory_ingestion_jobs", ["document_code"], unique=False)
    op.create_index(op.f("ix_regulatory_ingestion_jobs_status"), "regulatory_ingestion_jobs", ["status"], unique=False)

    # 7. Table: regulatory_review_records
    op.create_table(
        "regulatory_review_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("review_verdict", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "target_type IN ('document_version', 'clause', 'amendment')",
            name="ck_regulatory_reviews_target_type",
        ),
        sa.CheckConstraint(
            "review_verdict IN ('approved', 'flagged_review_required', 'rejected')",
            name="ck_regulatory_reviews_verdict",
        ),
    )
    op.create_index(op.f("ix_regulatory_review_records_target_id"), "regulatory_review_records", ["target_id"], unique=False)
    op.create_index(op.f("ix_regulatory_review_records_reviewer_id"), "regulatory_review_records", ["reviewer_id"], unique=False)


def downgrade() -> None:
    op.drop_table("regulatory_review_records")
    op.drop_table("regulatory_ingestion_jobs")
    op.drop_table("regulatory_amendments")
    op.drop_table("regulatory_clauses")
    op.drop_table("regulatory_document_versions")
    op.drop_table("regulatory_documents")
    op.drop_table("regulatory_authorities")

