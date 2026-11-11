"""
Unit and Integration Tests for Phase 01C.5 - Chat History & RAG Knowledgebase Database Models

Covers:
1. Model registration on Base.metadata (all 4 new models: chat_sessions, chat_messages, knowledge_sources, document_chunks)
2. UUID primary keys for all models
3. Chat session ownership & project workspace relationships
4. Chat message foreign keys & cascade deletion on session purge
5. Chat message role check constraint ('user', 'assistant', 'system', 'tool')
6. Message deterministic sequence ordering
7. Language validation ('en', 'ur')
8. Structured citations & warning card JSON validation
9. Knowledge source unique short_code, authority, and versioning
10. Knowledge source verification and ingestion state constraints
11. Global document chunks (knowledge_source_id present, project/doc NULL)
12. Private document chunks (project_id & document_id present, knowledge_source NULL)
13. Document chunk scope CHECK constraint enforcement against mixed scope
14. Document chunk scope CHECK constraint enforcement against empty scope
15. Document chunk non-negative constraints (chunk_index, token_count, page_number)
16. Pydantic v2 camelCase serialization & frontend compatibility
17. Storage key confidentiality (storage_path strictly excluded from public read schemas)
18. Alembic Revision 04 migration metadata & dependency chain
"""

import importlib.util
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Generator

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.models.knowledge import KnowledgeSource, DocumentChunk

from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionRead,
    ChatMessageCreate,
    ChatMessageRead,
    ChatCitationSchema,
    ChatWarningCardSchema,
    ChatRoleEnum,
    ChatLanguageEnum,
)
from app.schemas.knowledge import (
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    DocumentChunkCreate,
    DocumentChunkRead,
    KnowledgeCategoryEnum,
    VerificationStatusEnum,
)
from app.core.identifiers import (
    is_valid_session_code,
    is_valid_knowledge_short_code,
)


# ---------------------------------------------------------------------------
# Fixture: Isolated in-memory SQLite database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def in_memory_db() -> Generator[Session, None, None]:
    """Creates an isolated in-memory SQLite database enforcing foreign keys."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# Helper: Seed core workspace fixture
# ---------------------------------------------------------------------------

def create_seed_workspace(db: Session):
    user = User(
        email=f"eng_{uuid.uuid4().hex[:6]}@tameerai.pk",
        hashed_password="hash",
        full_name="Engr. Tariq Mehmood",
        city="Lahore",
    )
    db.add(user)
    db.commit()

    project = Project(
        code=f"PRJ-{uuid.uuid4().hex[:3].upper()}",
        user_id=user.id,
        name="Gulberg Commercial Plaza",
        location="Main Boulevard, Gulberg III, Lahore",
        city="Lahore",
    )
    db.add(project)
    db.commit()

    document = Document(
        code="DOC-01",
        project_id=project.id,
        user_id=user.id,
        name="Architectural-Layout-Rev2.dwg",
        file_type="CAD Drawing",
        document_category="blueprint",
        storage_path="private/projects/PRJ-001/layout.dwg",
    )
    db.add(document)
    db.commit()

    return user, project, document


# ---------------------------------------------------------------------------
# Test 1: Model Registration
# ---------------------------------------------------------------------------

def test_chat_and_rag_models_registration():
    """Verify all 19 application tables are registered on Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        # Identity (3)
        "users", "user_settings", "user_sessions",
        # Project & Document (4)
        "projects", "project_members", "project_activities", "documents",
        # Engineering Intelligence (8)
        "compliance_audits", "compliance_findings",
        "contract_analyses", "contract_risk_cards",
        "material_rates", "boq_analyses", "boq_items", "reports",
        # Conversational AI & RAG (4)
        "chat_sessions", "chat_messages",
        "knowledge_sources", "document_chunks",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


# ---------------------------------------------------------------------------
# Test 2: UUID Primary Keys
# ---------------------------------------------------------------------------

def test_chat_and_rag_uuid_primary_keys(in_memory_db: Session):
    """Verify UUID primary keys are generated on instantiation."""
    user, project, doc = create_seed_workspace(in_memory_db)

    session = ChatSession(user_id=user.id, project_id=project.id, title="Seismic Design Query")
    msg = ChatMessage(session_id=session.id, role="user", content="What are the PBC 2021 seismic requirements?")
    source = KnowledgeSource(
        title="Building Code of Pakistan (Seismic Provisions 2021)",
        short_code="BCP_SP_2021",
        category="building_code",
        authority="Pakistan Engineering Council",
        jurisdiction="Federal - Pakistan",
    )
    in_memory_db.add_all([session, msg, source])
    in_memory_db.commit()

    chunk = DocumentChunk(
        knowledge_source_id=source.id,
        chunk_index=0,
        content="Zone 2B requires minimum ductile detailing for moment frames.",
    )
    in_memory_db.add(chunk)
    in_memory_db.commit()

    assert isinstance(session.id, uuid.UUID)
    assert isinstance(msg.id, uuid.UUID)
    assert isinstance(source.id, uuid.UUID)
    assert isinstance(chunk.id, uuid.UUID)


# ---------------------------------------------------------------------------
# Test 3: Chat Session Ownership & Relationships
# ---------------------------------------------------------------------------

def test_chat_session_ownership_and_relationships(in_memory_db: Session):
    """Verify user ownership, project link, and cascade deletion of messages."""
    user, project, _ = create_seed_workspace(in_memory_db)

    session = ChatSession(
        code="session-1",
        user_id=user.id,
        project_id=project.id,
        title="Fire Egress Consultation",
        title_urdu="آگ سے بچاؤ کے راستے",
        session_type="code",
        language="en",
    )
    in_memory_db.add(session)
    in_memory_db.commit()

    m1 = ChatMessage(session_id=session.id, sequence_number=1, role="user", content="Minimum corridor width?")
    m2 = ChatMessage(session_id=session.id, sequence_number=2, role="assistant", content="Minimum clear width is 2.4m.")
    in_memory_db.add_all([m1, m2])
    in_memory_db.commit()

    # Re-query
    loaded = in_memory_db.scalar(select(ChatSession).where(ChatSession.id == session.id))
    assert loaded.user.id == user.id
    assert loaded.project.id == project.id
    assert len(loaded.messages) == 2
    assert loaded.messages[0].sequence_number == 1
    assert loaded.messages[1].sequence_number == 2

    # Cascade deletion of session purges its messages
    in_memory_db.delete(loaded)
    in_memory_db.commit()

    remaining_msgs = in_memory_db.scalars(select(ChatMessage).where(ChatMessage.session_id == session.id)).all()
    assert len(remaining_msgs) == 0


# ---------------------------------------------------------------------------
# Test 4: Chat Message Role Check Constraint
# ---------------------------------------------------------------------------

def test_chat_message_role_check_constraint(in_memory_db: Session):
    """Verify only valid roles ('user', 'assistant', 'system', 'tool') are accepted."""
    user, _, _ = create_seed_workspace(in_memory_db)
    session = ChatSession(user_id=user.id, title="Role Test Session")
    in_memory_db.add(session)
    in_memory_db.commit()

    # Valid roles with distinct sequence numbers
    for idx, r in enumerate(["user", "assistant", "system", "tool"]):
        msg = ChatMessage(session_id=session.id, sequence_number=idx, role=r, content=f"Message as {r}")
        in_memory_db.add(msg)
    in_memory_db.commit()

    # Invalid role fails check constraint
    bad_msg = ChatMessage(session_id=session.id, sequence_number=10, role="admin", content="Invalid role test")
    in_memory_db.add(bad_msg)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 5: Chat Message Ordering & Sequence Numbers
# ---------------------------------------------------------------------------

def test_chat_message_ordering_and_sequence(in_memory_db: Session):
    """Verify messages maintain deterministic sequence ordering and non-negative constraint."""
    user, _, _ = create_seed_workspace(in_memory_db)
    session = ChatSession(user_id=user.id, title="Sequence Test")
    in_memory_db.add(session)
    in_memory_db.commit()

    # Sequence numbers
    m1 = ChatMessage(session_id=session.id, sequence_number=0, role="system", content="System Prompt")
    m2 = ChatMessage(session_id=session.id, sequence_number=1, role="user", content="Query 1")
    m3 = ChatMessage(session_id=session.id, sequence_number=2, role="assistant", content="Answer 1")
    in_memory_db.add_all([m1, m2, m3])
    in_memory_db.commit()

    loaded = in_memory_db.scalar(select(ChatSession).where(ChatSession.id == session.id))
    assert [m.sequence_number for m in loaded.messages] == [0, 1, 2]

    # Negative sequence fails
    bad_m = ChatMessage(session_id=session.id, sequence_number=-1, role="user", content="Bad seq")
    in_memory_db.add(bad_m)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Duplicate sequence number in SAME session fails unique constraint
    dup_seq_m = ChatMessage(session_id=session.id, sequence_number=1, role="assistant", content="Duplicate seq 1")
    in_memory_db.add(dup_seq_m)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 6: Language Validation
# ---------------------------------------------------------------------------

def test_language_validation_on_session_and_message(in_memory_db: Session):
    """Verify sessions and messages only accept 'en' or 'ur'."""
    user, _, _ = create_seed_workspace(in_memory_db)

    # Invalid session language fails
    bad_session = ChatSession(user_id=user.id, title="Bad Lang", language="fr")
    in_memory_db.add(bad_session)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Valid session
    good_session = ChatSession(user_id=user.id, title="Good Lang", language="ur")
    in_memory_db.add(good_session)
    in_memory_db.commit()

    # Invalid message language fails
    bad_msg = ChatMessage(session_id=good_session.id, role="user", content="Test", language="es")
    in_memory_db.add(bad_msg)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 7: Structured Citations & Warning Cards
# ---------------------------------------------------------------------------

def test_chat_message_structured_citations_and_warning_card(in_memory_db: Session):
    """Verify storing structured citations and warning cards in JSON columns."""
    user, _, _ = create_seed_workspace(in_memory_db)
    session = ChatSession(user_id=user.id, title="Citation Test")
    in_memory_db.add(session)
    in_memory_db.commit()

    citations = [
        {"code": "PBC 2021", "clause": "4.3.2.1", "docId": "DOC-01", "page": 42},
        {"code": "FIDIC Red Book", "clause": "8.4", "page": 115},
    ]
    warning_card = {
        "title": "Corridor Width Deficit",
        "titleUrdu": "راہداری کی چوڑائی میں کمی",
        "referenceCode": "PBC 2021",
        "referenceSection": "Sec 4.3",
        "referencePage": 42,
        "currentValue": "1.8 m",
        "requiredValue": "2.4 m",
        "deficit": "-0.6 m (-25%)",
        "recommendation": "Widen corridor to comply with fire safety codes.",
        "detailedNotes": ["Grid C-4 on Level 2 fails minimum egress width."],
    }

    msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="Non-compliance detected in corridor width.",
        citations=citations,
        warning_card=warning_card,
    )
    in_memory_db.add(msg)
    in_memory_db.commit()

    loaded = in_memory_db.scalar(select(ChatMessage).where(ChatMessage.id == msg.id))
    assert loaded.citations[0]["clause"] == "4.3.2.1"
    assert loaded.warning_card["currentValue"] == "1.8 m"


# ---------------------------------------------------------------------------
# Test 8: Knowledge Source Uniqueness & Constraints
# ---------------------------------------------------------------------------

def test_knowledge_source_uniqueness_and_constraints(in_memory_db: Session):
    """Verify unique short_code, category constraints, and edition year ranges."""
    source1 = KnowledgeSource(
        title="Pakistan Building Code 2021",
        short_code="PBC_2021",
        category="building_code",
        authority="Pakistan Engineering Council",
        edition_year=2021,
        jurisdiction="Federal - Pakistan",
        is_official_regulatory=True,
        verification_status="verified",
        ingestion_status="completed",
    )
    in_memory_db.add(source1)
    in_memory_db.commit()

    assert is_valid_knowledge_short_code(source1.short_code) is True

    # Duplicate short_code fails
    dup_source = KnowledgeSource(
        title="Duplicate Code Standard",
        short_code="PBC_2021",
        category="building_code",
        authority="PEC",
        jurisdiction="Federal",
    )
    in_memory_db.add(dup_source)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Invalid category fails
    bad_cat = KnowledgeSource(
        title="Invalid Category Standard",
        short_code="BAD_CAT_01",
        category="random_category",
        authority="PEC",
        jurisdiction="Federal",
    )
    in_memory_db.add(bad_cat)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


def test_knowledge_source_security_defaults(in_memory_db: Session):
    """
    Verify security defaults on new knowledge sources:
    - is_official_regulatory defaults to False (must be explicitly certified)
    - verification_status defaults to 'unverified'
    - ingestion_status defaults to 'pending'
    """
    source = KnowledgeSource(
        title="CDA Building Regulations 2020",
        short_code="CDA_2020",
        category="building_code",
        authority="Capital Development Authority",
        jurisdiction="Federal - Islamabad",
    )
    in_memory_db.add(source)
    in_memory_db.commit()

    loaded = in_memory_db.scalar(select(KnowledgeSource).where(KnowledgeSource.id == source.id))
    assert loaded.is_official_regulatory is False
    assert loaded.verification_status == "unverified"
    assert loaded.ingestion_status == "pending"


def test_project_chat_retention_and_cascade_lifecycle(in_memory_db: Session):
    """
    Verify project chat confidentiality lifecycle:
    - Project-scoped chats (project_id IS NOT NULL) CASCADE upon project deletion,
      preventing retention or leakage of proprietary project messages.
    - General personal chats (project_id IS NULL) remain intact independently.
    """
    user, project, _ = create_seed_workspace(in_memory_db)

    # 1. Project-scoped session with confidential messages
    proj_session = ChatSession(
        user_id=user.id,
        project_id=project.id,
        title="Proprietary Foundation Design Review",
    )
    in_memory_db.add(proj_session)
    in_memory_db.commit()

    proj_msg = ChatMessage(
        session_id=proj_session.id,
        sequence_number=0,
        role="user",
        content="Confidential raft thickness is 1200mm.",
    )
    in_memory_db.add(proj_msg)

    # 2. General independent session (no project)
    general_session = ChatSession(
        user_id=user.id,
        project_id=None,
        title="General PEC Code Question",
    )
    in_memory_db.add(general_session)
    in_memory_db.commit()

    gen_msg = ChatMessage(
        session_id=general_session.id,
        sequence_number=0,
        role="user",
        content="What is standard concrete curing period in summer?",
    )
    in_memory_db.add(gen_msg)
    in_memory_db.commit()

    # Verify both exist
    assert in_memory_db.scalar(select(ChatSession).where(ChatSession.id == proj_session.id)) is not None
    assert in_memory_db.scalar(select(ChatSession).where(ChatSession.id == general_session.id)) is not None

    # Delete project workspace
    in_memory_db.delete(project)
    in_memory_db.commit()

    # Project session and its messages are purged
    assert in_memory_db.scalar(select(ChatSession).where(ChatSession.id == proj_session.id)) is None
    assert in_memory_db.scalar(select(ChatMessage).where(ChatMessage.id == proj_msg.id)) is None

    # General personal session and its messages remain preserved
    surviving_general = in_memory_db.scalar(select(ChatSession).where(ChatSession.id == general_session.id))
    assert surviving_general is not None
    assert surviving_general.project_id is None
    assert in_memory_db.scalar(select(ChatMessage).where(ChatMessage.id == gen_msg.id)) is not None


# ---------------------------------------------------------------------------
# Test 9: Document Chunk Scope CHECK Constraint (Global vs Private)
# ---------------------------------------------------------------------------

def test_document_chunk_scope_check_constraint(in_memory_db: Session):
    """
    Verify strict mutual exclusion:
    1. Global chunk: knowledge_source_id IS NOT NULL, project_id IS NULL, document_id IS NULL -> PASS
    2. Private chunk: knowledge_source_id IS NULL, project_id IS NOT NULL, document_id IS NOT NULL -> PASS
    3. Mixed chunk: both knowledge_source and project/document -> FAIL
    4. Empty chunk: neither global nor private -> FAIL
    5. Partial private chunk: project without document -> FAIL
    """
    user, project, doc = create_seed_workspace(in_memory_db)
    source = KnowledgeSource(
        title="LDA Building Byelaws 2020",
        short_code="LDA_2020",
        category="planning_regulation",
        authority="Lahore Development Authority",
        jurisdiction="Punjab",
    )
    in_memory_db.add(source)
    in_memory_db.commit()

    # 1. Global chunk -> PASS
    global_chunk = DocumentChunk(
        knowledge_source_id=source.id,
        chunk_index=0,
        content="Commercial buildings facing roads less than 60ft wide require 15ft setback.",
        section="Section 12.2",
    )
    in_memory_db.add(global_chunk)
    in_memory_db.commit()
    assert global_chunk.knowledge_source_id == source.id
    assert global_chunk.project_id is None

    # 2. Private project chunk -> PASS
    private_chunk = DocumentChunk(
        project_id=project.id,
        document_id=doc.id,
        chunk_index=0,
        content="Ground Floor layout shows front setback of 18ft.",
        section="Sheet A-101",
    )
    in_memory_db.add(private_chunk)
    in_memory_db.commit()
    assert private_chunk.knowledge_source_id is None
    assert private_chunk.project_id == project.id
    assert private_chunk.document_id == doc.id

    # 3. Mixed scope chunk -> FAIL
    mixed_chunk = DocumentChunk(
        knowledge_source_id=source.id,
        project_id=project.id,
        document_id=doc.id,
        chunk_index=1,
        content="Mixed scope should be rejected by database CHECK constraint.",
    )
    in_memory_db.add(mixed_chunk)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # 4. Empty scope chunk -> FAIL
    empty_chunk = DocumentChunk(
        knowledge_source_id=None,
        project_id=None,
        document_id=None,
        chunk_index=2,
        content="Empty scope chunk with no provenance.",
    )
    in_memory_db.add(empty_chunk)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # 5. Partial private chunk (project without document) -> FAIL
    partial_chunk = DocumentChunk(
        knowledge_source_id=None,
        project_id=project.id,
        document_id=None,
        chunk_index=3,
        content="Missing document_id in private scope.",
    )
    in_memory_db.add(partial_chunk)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 10: Document Chunk Non-Negative Constraints
# ---------------------------------------------------------------------------

def test_document_chunk_non_negative_constraints(in_memory_db: Session):
    """Verify chunk_index >= 0, page_number >= 1, and token_count >= 0."""
    source = KnowledgeSource(
        title="PEC Contract Guidelines",
        short_code="PEC_GW_2022",
        category="engineering_guideline",
        authority="PEC",
        jurisdiction="Federal",
    )
    in_memory_db.add(source)
    in_memory_db.commit()

    # Negative chunk_index fails
    bad_c1 = DocumentChunk(knowledge_source_id=source.id, chunk_index=-1, content="Text")
    in_memory_db.add(bad_c1)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Zero page_number fails (pages are 1-based)
    bad_c2 = DocumentChunk(knowledge_source_id=source.id, chunk_index=0, page_number=0, content="Text")
    in_memory_db.add(bad_c2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Negative token_count fails
    bad_c3 = DocumentChunk(knowledge_source_id=source.id, chunk_index=0, token_count=-5, content="Text")
    in_memory_db.add(bad_c3)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 11: Pydantic Chat Schemas & CamelCase Parity
# ---------------------------------------------------------------------------

def test_pydantic_chat_serialization():
    """Verify Pydantic models serialize with frontend-expected camelCase aliases."""
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    session_read = ChatSessionRead(
        id=session_id,
        code="session-1",
        userId=user_id,
        projectId=proj_id,
        title="Structural Analysis Review",
        titleUrdu="سٹرکچرل اینالیسس جائزہ",
        type="code",
        language="en",
        preview="Beam deflection check passes.",
        previewUrdu="بیم کی ڈیفلیکشن درست ہے۔",
        isArchived=False,
        createdAt=now,
        updatedAt=now,
    )
    dumped = session_read.model_dump(by_alias=True)
    assert dumped["userId"] == user_id
    assert dumped["projectId"] == proj_id
    assert dumped["titleUrdu"] == "سٹرکچرل اینالیسس جائزہ"
    assert dumped["previewUrdu"] == "بیم کی ڈیفلیکشن درست ہے۔"
    assert dumped["isArchived"] is False
    assert "createdAt" in dumped

    # Message Read serialization
    msg_id = uuid.uuid4()
    msg_read = ChatMessageRead(
        id=msg_id,
        sessionId=session_id,
        sequenceNumber=1,
        role=ChatRoleEnum.ASSISTANT,
        content="Verified against PBC 2021 Chapter 5.",
        contentUrdu="پی بی سی 2021 باب 5 کے مطابق تصدیق شدہ۔",
        language=ChatLanguageEnum.EN,
        status="completed",
        createdAt=now,
    )
    msg_dump = msg_read.model_dump(by_alias=True)
    assert msg_dump["sessionId"] == session_id
    assert msg_dump["sequenceNumber"] == 1
    assert msg_dump["role"] == "assistant"
    assert msg_dump["contentUrdu"] == "پی بی سی 2021 باب 5 کے مطابق تصدیق شدہ۔"


# ---------------------------------------------------------------------------
# Test 12: Pydantic Knowledge & Chunk Scope Validation
# ---------------------------------------------------------------------------

def test_pydantic_knowledge_and_chunk_scope_validation():
    """Verify Pydantic validates scope mutual exclusion and protects private storage paths."""
    source_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    # Valid global chunk
    c_global = DocumentChunkCreate(
        knowledgeSourceId=source_id,
        content="Global regulatory passage.",
        chunkIndex=0,
    )
    assert c_global.knowledge_source_id == source_id
    assert c_global.project_id is None

    # Valid private chunk
    c_private = DocumentChunkCreate(
        projectId=proj_id,
        documentId=doc_id,
        content="Private client specification.",
        chunkIndex=0,
    )
    assert c_private.project_id == proj_id
    assert c_private.document_id == doc_id
    assert c_private.knowledge_source_id is None

    # Mixed scope raises ValidationError
    with pytest.raises(ValidationError):
        DocumentChunkCreate(
            knowledgeSourceId=source_id,
            projectId=proj_id,
            documentId=doc_id,
            content="Invalid mixed scope.",
        )

    # Empty scope raises ValidationError
    with pytest.raises(ValidationError):
        DocumentChunkCreate(
            content="Invalid empty scope.",
        )

    # Partial private scope raises ValidationError
    with pytest.raises(ValidationError):
        DocumentChunkCreate(
            projectId=proj_id,
            documentId=None,
            content="Missing documentId.",
        )

    # KnowledgeSourceRead excludes private storage_path
    k_read = KnowledgeSourceRead(
        id=source_id,
        title="Pakistan Building Code 2021",
        shortCode="PBC_2021",
        category=KnowledgeCategoryEnum.BUILDING_CODE,
        authority="PEC",
        jurisdiction="Federal",
        language="en",
        version="2.0",
        isOfficialRegulatory=True,
        verificationStatus=VerificationStatusEnum.VERIFIED,
        ingestionStatus="completed",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )
    k_dump = k_read.model_dump(by_alias=True)
    assert "storage_path" not in k_dump
    assert "storagePath" not in k_dump


# ---------------------------------------------------------------------------
# Test 13: Alembic Revision 04 Metadata
# ---------------------------------------------------------------------------

def test_alembic_revision_04_metadata():
    """Verify Revision 04 migration file correctly chains from Revision 03."""
    migration_file = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "004_create_chat_and_rag_tables.py"
    assert migration_file.exists(), f"Migration file not found: {migration_file}"

    spec = importlib.util.spec_from_file_location("migration_004", migration_file)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "004_chat_rag_foundation"
    assert migration.down_revision == "003_engineering_intelligence_tables"
    assert len(migration.revision) <= 32, "Revision ID must fit standard varchar limit"
