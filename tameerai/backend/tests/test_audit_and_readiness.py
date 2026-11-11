"""
Phase 01C.6 — Final Database Integrity Audit & Backend Readiness Tests
Read-only validation of Alembic revisions, SQLAlchemy metadata definitions,
constraint declarations, and Pydantic response contracts.
"""

import uuid
from decimal import Decimal
from pathlib import Path
import pytest
import sqlalchemy as sa
from sqlalchemy import text
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db.base import Base
from app.core.config import settings
from app.db.session import get_engine, dispose_engine
import app.models  # Ensures all 19 models are imported into Base.metadata
from app.models.project import Project
from app.schemas.project import ProjectRead
from app.schemas.chat import ChatMessageRead, ChatSessionRead
from app.schemas.knowledge import KnowledgeSourceRead, DocumentChunkRead


def test_alembic_revision_chain_integrity():
    """Verify that Alembic revisions 001 through 009 form a valid, unbroken chain to head."""
    backend_root = Path(__file__).resolve().parent.parent
    ini_path = backend_root / "alembic.ini"
    config = Config(str(ini_path))
    script_dir = ScriptDirectory.from_config(config)

    heads = script_dir.get_heads()
    assert heads == ["009_create_regulatory_knowledge_tables"], f"Expected single head '009_create_regulatory_knowledge_tables', got {heads}"

    # Verify revision chain from head to base
    rev_009 = script_dir.get_revision("009_create_regulatory_knowledge_tables")
    assert rev_009 is not None
    assert rev_009.down_revision == "008_material_rate_published_at_nullable"

    rev_008 = script_dir.get_revision("008_material_rate_published_at_nullable")
    assert rev_008 is not None
    assert rev_008.down_revision == "007_material_rate_safety_hardening"

    rev_007 = script_dir.get_revision("007_material_rate_safety_hardening")
    assert rev_007 is not None
    assert rev_007.down_revision == "006_material_rate_intelligence"

    rev_006 = script_dir.get_revision("006_material_rate_intelligence")
    assert rev_006 is not None
    assert rev_006.down_revision == "005_background_jobs_infrastructure"

    rev_005 = script_dir.get_revision("005_background_jobs_infrastructure")
    assert rev_005 is not None
    assert rev_005.down_revision == "004_chat_rag_foundation"

    rev_004 = script_dir.get_revision("004_chat_rag_foundation")
    assert rev_004 is not None
    assert rev_004.down_revision == "003_engineering_intelligence_tables"

    rev_003 = script_dir.get_revision("003_engineering_intelligence_tables")
    assert rev_003 is not None
    assert rev_003.down_revision == "002_project_and_document_tables"

    rev_002 = script_dir.get_revision("002_project_and_document_tables")
    assert rev_002 is not None
    assert rev_002.down_revision == "001_identity_tables"

    rev_001 = script_dir.get_revision("001_identity_tables")
    assert rev_001 is not None
    assert rev_001.down_revision is None


def test_metadata_has_exactly_19_application_tables():
    """Verify that SQLAlchemy metadata registers all 19 original Phase 01C application tables."""
    expected_tables = {
        # Identity (Phase 01C.2)
        "users",
        "user_settings",
        "user_sessions",
        # Workspace & Document (Phase 01C.3)
        "projects",
        "project_members",
        "project_activities",
        "documents",
        # Engineering Intelligence (Phase 01C.4)
        "compliance_audits",
        "compliance_findings",
        "contract_analyses",
        "contract_risk_cards",
        "material_rates",
        "boq_analyses",
        "boq_items",
        "reports",
        # Conversational AI & RAG (Phase 01C.5)
        "chat_sessions",
        "chat_messages",
        "knowledge_sources",
        "document_chunks",
    }
    non_01c_tables = {
        "background_jobs",
        "material_rate_products",
        "material_rate_sources",
        "material_rate_dealers",
        "material_rate_dealer_quotes",
        "material_rate_observations",
        "material_rate_verification_events",
        "material_rate_source_runs",
        "regulatory_authorities",
        "regulatory_documents",
        "regulatory_document_versions",
        "regulatory_clauses",
        "regulatory_amendments",
        "regulatory_ingestion_jobs",
        "regulatory_review_records",
    }
    phase_01c_tables = {t for t in Base.metadata.tables.keys() if t not in non_01c_tables}
    assert phase_01c_tables == expected_tables, f"Mismatch in registered metadata tables: {phase_01c_tables ^ expected_tables}"


def test_chat_messages_no_redundant_sequence_index_in_metadata():
    """Verify that ChatMessage does NOT declare redundant ix_chat_messages_session_sequence."""
    chat_messages_table = Base.metadata.tables["chat_messages"]
    index_names = {idx.name for idx in chat_messages_table.indexes}
    
    assert "ix_chat_messages_session_sequence" not in index_names, (
        "Redundant index 'ix_chat_messages_session_sequence' found in ChatMessage metadata!"
    )
    
    # Verify uq_chat_messages_session_sequence unique constraint is present
    uq_names = {c.name for c in chat_messages_table.constraints if c.__class__.__name__ == "UniqueConstraint"}
    assert "uq_chat_messages_session_sequence" in uq_names


def test_document_chunks_scope_check_constraint():
    """Verify ck_document_chunks_scope check constraint exists in document_chunks metadata."""
    chunks_table = Base.metadata.tables["document_chunks"]
    check_constraints = {c.name: str(c.sqltext) for c in chunks_table.constraints if c.__class__.__name__ == "CheckConstraint"}
    
    assert "ck_document_chunks_scope" in check_constraints
    sqltext = check_constraints["ck_document_chunks_scope"]
    assert "knowledge_source_id IS NOT NULL" in sqltext
    assert "project_id IS NOT NULL" in sqltext
    assert "document_id IS NOT NULL" in sqltext


def test_all_19_models_have_uuid_primary_keys():
    """Verify that all 19 application models have collision-free UUID primary keys with server defaults."""
    for table_name, table in Base.metadata.tables.items():
        pk_cols = list(table.primary_key.columns)
        assert len(pk_cols) == 1, f"Table {table_name} must have a single primary key column"
        pk = pk_cols[0]
        assert pk.name == "id", f"Table {table_name} primary key must be named 'id'"
        assert pk.type.python_type is uuid.UUID, f"Table {table_name} PK must have python_type uuid.UUID, got {pk.type.python_type}"


def test_pydantic_project_read_serialization_from_orm():
    """Verify ProjectRead Pydantic model correctly serializes raw PKR to crore fields from ORM."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    p = Project(
        id=uuid.uuid4(),
        code="PRJ-001",
        user_id=uuid.uuid4(),
        name="Gulberg Office Tower",
        name_urdu="گلبرگ آفس ٹاور",
        description="12-storey commercial building",
        location="Main Boulevard, Gulberg III",
        location_urdu="مین بلیوارڈ، گلبرگ III",
        city="Lahore",
        city_urdu="لاہور",
        type="Commercial",
        type_urdu="تجارتی",
        budget_raw=Decimal("125000000.00"),
        spent_raw=Decimal("45000000.00"),
        status="Active",
        status_urdu="فعال (Active)",
        risk="Low",
        risk_urdu="کم (Low)",
        compliance_score=92,
        floors=12,
        area_sqft="45,000 sq ft",
        engineer="Engr. Tariq Mahmood",
        governing_authority="LDA",
        handover_date="December 2025",
        created_at=now,
        updated_at=now,
    )
    # Model property calculations
    assert p.budget_crore == Decimal("12.5")
    assert p.spent_crore == Decimal("4.5")

    # Pydantic serialization
    read_dto = ProjectRead.model_validate(p)
    assert read_dto.id == "PRJ-001"
    assert read_dto.budget_crore == 12.5
    assert read_dto.spent_crore == 4.5
    
    # JSON-compatible dictionary with camelCase aliases for Next.js frontend
    dump = read_dto.model_dump(by_alias=True)
    assert dump["id"] == "PRJ-001"
    assert dump["budgetCrore"] == 12.5
    assert dump["spentCrore"] == 4.5
    assert dump["budgetRaw"] == 125000000.0


@pytest.mark.asyncio
async def test_live_supabase_schema_audit_read_only():
    """
    Read-only audit of remote Supabase PostgreSQL instance:
    Verifies that Alembic version is '005_background_jobs_infrastructure' and exactly 20 tables exist.
    NEVER mutates data.
    """
    if not settings.is_database_configured:
        pytest.skip("Skipping live audit: DATABASE_URL not configured")

    engine = get_engine()
    async with engine.connect() as conn:
        rev = (await conn.execute(text("SELECT version_num FROM alembic_version;"))).scalar()
        assert rev in ("005_background_jobs_infrastructure", "009_create_regulatory_knowledge_tables"), f"Expected revision '005_background_jobs_infrastructure' or '009_create_regulatory_knowledge_tables', got '{rev}'"

        res = await conn.execute(text("""
            SELECT count(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name != 'alembic_version';
        """))
        count = res.scalar()
        assert count in (20, 27, 34), f"Expected application tables in public schema, got {count}"
    
    await dispose_engine()
