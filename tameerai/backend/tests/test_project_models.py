"""
Unit and Integration Tests for Phase 01C.3 - Project Workspace & Document Models

Verifies:
1. Model metadata registration on Base.metadata
2. Project UUID primary key and public code attributes
3. Project ownership relationship (User.owned_projects <-> Project.owner)
4. Scoped duplicate public-code constraints (same user duplicate fails, different user succeeds)
5. Project membership uniqueness (UNIQUE(project_id, user_id))
6. Project membership role constraints (owner, lead_engineer, architect, contractor, viewer)
7. Project activity relationships & audit preservation (ON DELETE SET NULL)
8. Document-to-project relationship (Project.documents <-> Document.project)
9. Financial precision (NUMERIC budget_crore & budget_raw PKR calculation)
10. Pydantic response serialization (model_dump(by_alias=True) returns camelCase id matching frontend)
11. Document scoped uniqueness (UNIQUE(project_id, code))
12. Document category validation constraint
13. Alembic Revision 02 dependency chain & structure
14. Regression: Identity models & previous tests unaffected
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Generator
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select, event, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User, UserSettings, UserSession
from app.models.project import Project, ProjectMember, ProjectActivity
from app.models.document import Document
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectActivityRead,
)
from app.schemas.document import (
    DocumentCreate,
    DocumentRead,
    DocumentCategory,
)
from app.core.identifiers import is_valid_project_code, is_valid_document_code, format_project_code, format_document_code


# ---------------------------------------------------------------------------
# Fixture: Isolated in-memory SQLite database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def in_memory_db() -> Generator[Session, None, None]:
    """
    Creates an isolated in-memory SQLite database enforcing foreign keys.
    """
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
# Test 1: Model Registration on Base.metadata
# ---------------------------------------------------------------------------

def test_model_registration():
    """Verify that all 4 Phase 01C.3 tables are registered on Base.metadata."""
    tables = Base.metadata.tables
    assert "projects" in tables
    assert "project_members" in tables
    assert "project_activities" in tables
    assert "documents" in tables


# ---------------------------------------------------------------------------
# Test 2: Project UUID Primary Key & Public Code
# ---------------------------------------------------------------------------

def test_project_uuid_and_code():
    """Verify default UUID generation and code assignment."""
    proj = Project(
        code="PRJ-001",
        user_id=uuid.uuid4(),
        name="DHA Commercial Plaza",
        location="Sector G, DHA Phase 6, Lahore",
    )
    assert isinstance(proj.id, uuid.UUID)
    assert proj.code == "PRJ-001"
    assert is_valid_project_code(proj.code) is True


# ---------------------------------------------------------------------------
# Test 3: Project Ownership Relationships
# ---------------------------------------------------------------------------

def test_project_ownership_relationship(in_memory_db: Session):
    """Verify bidirectional relationship between User and owned Project."""
    user = User(
        email="owner@tameerai.pk",
        hashed_password="hash",
        full_name="Owner Engineer",
    )
    in_memory_db.add(user)
    in_memory_db.commit()

    proj = Project(
        code="PRJ-001",
        owner=user,
        name="Model Town Heights",
        location="Model Town, Lahore",
        city="Lahore",
    )
    in_memory_db.add(proj)
    in_memory_db.commit()

    # Query back
    fetched_user = in_memory_db.scalar(select(User).where(User.id == user.id))
    assert len(fetched_user.owned_projects) == 1
    assert fetched_user.owned_projects[0].name == "Model Town Heights"
    assert fetched_user.owned_projects[0].owner.email == "owner@tameerai.pk"


# ---------------------------------------------------------------------------
# Test 4: Scoped Unique Code Constraint (user_id, code)
# ---------------------------------------------------------------------------

def test_duplicate_project_code_same_user_fails(in_memory_db: Session):
    """Verify same user cannot create two projects with identical code."""
    user = User(email="user_a@tameerai.pk", hashed_password="h", full_name="User A")
    in_memory_db.add(user)
    in_memory_db.commit()

    p1 = Project(code="PRJ-001", user_id=user.id, name="Project 1", location="L1")
    in_memory_db.add(p1)
    in_memory_db.commit()

    p2 = Project(code="PRJ-001", user_id=user.id, name="Project 2", location="L2")
    in_memory_db.add(p2)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


def test_duplicate_project_code_different_users_succeeds(in_memory_db: Session):
    """Verify two different users CAN each have a project with code 'PRJ-001'."""
    u1 = User(email="u1@tameerai.pk", hashed_password="h", full_name="User 1")
    u2 = User(email="u2@tameerai.pk", hashed_password="h", full_name="User 2")
    in_memory_db.add_all([u1, u2])
    in_memory_db.commit()

    p1 = Project(code="PRJ-001", user_id=u1.id, name="U1 Project", location="L1")
    p2 = Project(code="PRJ-001", user_id=u2.id, name="U2 Project", location="L2")
    in_memory_db.add_all([p1, p2])
    in_memory_db.commit()

    assert p1.id != p2.id
    assert p1.code == p2.code == "PRJ-001"


# ---------------------------------------------------------------------------
# Test 5: Project Membership Uniqueness (project_id, user_id)
# ---------------------------------------------------------------------------

def test_project_member_uniqueness(in_memory_db: Session):
    """Verify duplicate membership record for same user on same project raises error."""
    owner = User(email="proj_owner@tameerai.pk", hashed_password="h", full_name="Owner")
    member = User(email="collab@tameerai.pk", hashed_password="h", full_name="Collab")
    in_memory_db.add_all([owner, member])
    in_memory_db.commit()

    proj = Project(code="PRJ-001", user_id=owner.id, name="P", location="L")
    in_memory_db.add(proj)
    in_memory_db.commit()

    m1 = ProjectMember(project_id=proj.id, user_id=member.id, role="architect")
    in_memory_db.add(m1)
    in_memory_db.commit()

    # Attempt duplicate membership
    m2 = ProjectMember(project_id=proj.id, user_id=member.id, role="viewer")
    in_memory_db.add(m2)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 6: Project Member Roles Constraint
# ---------------------------------------------------------------------------

def test_project_member_valid_roles(in_memory_db: Session):
    """Verify valid membership roles succeed and invalid roles (including 'owner') fail check constraint."""
    owner = User(email="owner_role@tameerai.pk", hashed_password="h", full_name="Owner")
    in_memory_db.add(owner)
    in_memory_db.commit()

    proj = Project(code="PRJ-ROLE", user_id=owner.id, name="Role Project", location="Loc")
    in_memory_db.add(proj)
    in_memory_db.commit()

    valid_roles = ["lead_engineer", "architect", "contractor", "viewer"]
    for idx, role in enumerate(valid_roles):
        user = User(email=f"member_{idx}@tameerai.pk", hashed_password="h", full_name=f"Member {idx}")
        in_memory_db.add(user)
        in_memory_db.commit()
        pm = ProjectMember(project_id=proj.id, user_id=user.id, role=role)
        in_memory_db.add(pm)
        in_memory_db.commit()
        assert pm.role == role

    # 'owner' role is disallowed in project_members because projects.user_id is the sole owner
    owner_user = User(email="fake_owner@tameerai.pk", hashed_password="h", full_name="Fake Owner")
    in_memory_db.add(owner_user)
    in_memory_db.commit()
    bad_owner_pm = ProjectMember(project_id=proj.id, user_id=owner_user.id, role="owner")
    in_memory_db.add(bad_owner_pm)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()

    # Invalid arbitrary role test
    bad_user = User(email="bad_role@tameerai.pk", hashed_password="h", full_name="Bad Role")
    in_memory_db.add(bad_user)
    in_memory_db.commit()
    bad_pm = ProjectMember(project_id=proj.id, user_id=bad_user.id, role="invalid_super_admin")
    in_memory_db.add(bad_pm)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 7: Project Activity Audit Trail (ON DELETE SET NULL)
# ---------------------------------------------------------------------------

def test_project_activity_and_user_deletion(in_memory_db: Session):
    """Verify activity audit log is preserved with user_id=None when user is removed."""
    owner = User(email="act_owner@tameerai.pk", hashed_password="h", full_name="Owner")
    actor = User(email="act_user@tameerai.pk", hashed_password="h", full_name="Engr. Tariq")
    in_memory_db.add_all([owner, actor])
    in_memory_db.commit()

    proj = Project(code="PRJ-ACT", user_id=owner.id, name="Activity Plaza", location="L")
    in_memory_db.add(proj)
    in_memory_db.commit()

    act = ProjectActivity(
        project_id=proj.id,
        user_id=actor.id,
        actor_name="Engr. Tariq",
        action="Architectural CAD Audit completed against PBC 2021",
        activity_type="compliance",
        detail="Setback and egress widths verified for floors 1 to 6.",
        metadata_json={"compliance_score": 88, "findings_count": 2},
    )
    in_memory_db.add(act)
    in_memory_db.commit()

    # Delete actor user
    in_memory_db.delete(actor)
    in_memory_db.commit()
    in_memory_db.expire_all()

    # Activity must still exist with user_id=None and cached actor_name intact
    fetched_act = in_memory_db.scalar(select(ProjectActivity).where(ProjectActivity.project_id == proj.id))
    assert fetched_act is not None
    assert fetched_act.user_id is None
    assert fetched_act.actor_name == "Engr. Tariq"
    assert fetched_act.action == "Architectural CAD Audit completed against PBC 2021"


# ---------------------------------------------------------------------------
# Test 8: Document to Project Relationships
# ---------------------------------------------------------------------------

def test_document_to_project_relationship(in_memory_db: Session):
    """Verify bidirectional relationship between Project and Document."""
    owner = User(email="doc_owner@tameerai.pk", hashed_password="h", full_name="Doc Owner")
    in_memory_db.add(owner)
    in_memory_db.commit()

    proj = Project(code="PRJ-DOC", user_id=owner.id, name="Doc Plaza", location="L")
    in_memory_db.add(proj)
    in_memory_db.commit()

    doc = Document(
        code="DOC-01",
        project=proj,
        uploader=owner,
        name="Structural-Drawings-Rev4.dwg",
        file_type="CAD Drawing",
        document_category="blueprint",
        file_size_bytes=44564480,
        file_size_human="42.5 MB",
        storage_path="projects/PRJ-DOC/documents/uuid-drawings.dwg",
        uploaded_by="Engr. Tariq",
    )
    in_memory_db.add(doc)
    in_memory_db.commit()

    fetched_proj = in_memory_db.scalar(select(Project).where(Project.id == proj.id))
    assert len(fetched_proj.documents) == 1
    assert fetched_proj.documents[0].code == "DOC-01"
    assert fetched_proj.documents[0].name == "Structural-Drawings-Rev4.dwg"
    assert fetched_proj.documents[0].project.code == "PRJ-DOC"


# ---------------------------------------------------------------------------
# Test 9: Financial Precision & Calculations
# ---------------------------------------------------------------------------

def test_financial_precision_and_crore_conversion():
    """Verify NUMERIC budget_crore to budget_raw calculation in PKR."""
    proj = Project(
        code="PRJ-FIN",
        user_id=uuid.uuid4(),
        name="Finance Tower",
        location="Gulberg, Lahore",
        budget_crore=Decimal("12.5000"),
    )
    # 12.5 Crore = 125,000,000 PKR
    assert proj.budget_crore == Decimal("12.5000")
    assert proj.budget_raw == Decimal("125000000.00")


# ---------------------------------------------------------------------------
# Test 10: Pydantic Response Serialization (Frontend Alignment)
# ---------------------------------------------------------------------------

def test_pydantic_project_serialization():
    """Verify ProjectRead serializes DB 'code' into JSON 'id' and matches frontend types."""
    now = datetime.now(timezone.utc)
    proj = Project(
        id=uuid.uuid4(),
        code="PRJ-001",
        user_id=uuid.uuid4(),
        name="DHA Commercial Plaza",
        name_urdu="ڈی ایچ اے کمرشل پلازہ",
        location="Phase 6, Sector G, Lahore",
        city="Lahore",
        type="Commercial G+12",
        budget_crore=Decimal("12.0000"),
        budget_raw=Decimal("120000000.00"),
        spent_crore=Decimal("7.2000"),
        status="Under Analysis",
        compliance_score=84,
        floors=13,
        area_sqft="45,000 sq ft",
        engineer="Engr. Tariq Mehmood",
        governing_authority="DHA Lahore & PBC 2021",
        created_at=now,
        updated_at=now,
    )

    schema = ProjectRead.model_validate(proj)
    dumped = schema.model_dump(by_alias=True)

    # Core frontend contract assertions
    assert dumped["id"] == "PRJ-001"  # Human-readable public code
    assert "uuid" in dumped  # Internal UUID
    assert dumped["name"] == "DHA Commercial Plaza"
    assert dumped["nameUrdu"] == "ڈی ایچ اے کمرشل پلازہ"
    assert dumped["city"] == "Lahore"
    assert dumped["budgetCrore"] == 12.0
    assert isinstance(dumped["budgetCrore"], float)
    assert dumped["budgetRaw"] == 120000000.0
    assert isinstance(dumped["budgetRaw"], float)
    assert dumped["spentCrore"] == 7.2
    assert isinstance(dumped["spentCrore"], float)
    assert dumped["complianceScore"] == 84
    assert isinstance(dumped["complianceScore"], int)
    assert dumped["floors"] == 13
    assert dumped["areaSqft"] == "45,000 sq ft"
    assert dumped["engineer"] == "Engr. Tariq Mehmood"
    assert dumped["governingAuthority"] == "DHA Lahore & PBC 2021"


def test_pydantic_project_nullable_serialization():
    """Verify unassessed project serializes complianceScore=None and governingAuthority=None as JSON null."""
    now = datetime.now(timezone.utc)
    proj = Project(
        id=uuid.uuid4(),
        code="PRJ-UNASSESSED",
        user_id=uuid.uuid4(),
        name="Raw Plaza",
        location="Islamabad",
        compliance_score=None,
        governing_authority=None,
        created_at=now,
        updated_at=now,
    )
    schema = ProjectRead.model_validate(proj)
    dumped = schema.model_dump(by_alias=True)

    assert dumped["complianceScore"] is None
    assert dumped["governingAuthority"] is None
    assert dumped["budgetCrore"] == 0.0
    assert isinstance(dumped["budgetCrore"], float)
    assert dumped["spentCrore"] == 0.0
    assert isinstance(dumped["spentCrore"], float)
    assert dumped["budgetRaw"] == 0.0
    assert isinstance(dumped["budgetRaw"], float)


def test_pydantic_document_serialization():
    """Verify DocumentRead serializes DB 'code' into JSON 'id' matching ProjectDocument."""
    now = datetime.now(timezone.utc)
    doc = Document(
        id=uuid.uuid4(),
        code="DOC-01",
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="DHA-Plaza-Structural.dwg",
        file_type="CAD Drawing",
        document_category="blueprint",
        file_size_bytes=44564480,
        file_size_human="42.5 MB",
        storage_path="projects/PRJ-001/documents/doc-1.dwg",
        uploaded_by="Engr. Tariq",
        status="Verified",
        created_at=now,
        updated_at=now,
    )

    schema = DocumentRead.model_validate(doc)
    dumped = schema.model_dump(by_alias=True)

    assert dumped["id"] == "DOC-01"
    assert dumped["name"] == "DHA-Plaza-Structural.dwg"
    assert dumped["type"] == "CAD Drawing"
    assert dumped["category"] == "blueprint"
    assert dumped["size"] == "42.5 MB"
    assert dumped["uploadedBy"] == "Engr. Tariq"
    assert dumped["status"] == "Verified"


# ---------------------------------------------------------------------------
# Test 11: Document Scoped Unique Constraint (project_id, code)
# ---------------------------------------------------------------------------

def test_document_scoped_unique_constraint(in_memory_db: Session):
    """Verify duplicate document code within the same project fails, but succeeds across projects."""
    user = User(email="doc_uniq@tameerai.pk", hashed_password="h", full_name="User")
    in_memory_db.add(user)
    in_memory_db.commit()

    p1 = Project(code="PRJ-1", user_id=user.id, name="P1", location="L1")
    p2 = Project(code="PRJ-2", user_id=user.id, name="P2", location="L2")
    in_memory_db.add_all([p1, p2])
    in_memory_db.commit()

    d1 = Document(code="DOC-01", project_id=p1.id, user_id=user.id, name="D1", file_type="CAD", storage_path="/p1/d1")
    in_memory_db.add(d1)
    in_memory_db.commit()

    # Same code on DIFFERENT project succeeds
    d2 = Document(code="DOC-01", project_id=p2.id, user_id=user.id, name="D2", file_type="CAD", storage_path="/p2/d2")
    in_memory_db.add(d2)
    in_memory_db.commit()

    # Same code on SAME project fails
    d3 = Document(code="DOC-01", project_id=p1.id, user_id=user.id, name="D3", file_type="CAD", storage_path="/p1/d3")
    in_memory_db.add(d3)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 12: Document Category Validation Constraint
# ---------------------------------------------------------------------------

def test_document_category_constraint(in_memory_db: Session):
    """Verify valid document categories succeed and invalid categories fail."""
    user = User(email="cat_user@tameerai.pk", hashed_password="h", full_name="User")
    in_memory_db.add(user)
    in_memory_db.commit()

    proj = Project(code="PRJ-CAT", user_id=user.id, name="Cat Plaza", location="L")
    in_memory_db.add(proj)
    in_memory_db.commit()

    valid_cats = ["blueprint", "building_code", "contract", "boq", "general_project_document"]
    for idx, cat in enumerate(valid_cats):
        doc = Document(
            code=f"DOC-{idx+1:02d}",
            project_id=proj.id,
            user_id=user.id,
            name=f"File-{cat}.pdf",
            file_type="PDF",
            document_category=cat,
            storage_path=f"/path/{cat}.pdf",
        )
        in_memory_db.add(doc)
        in_memory_db.commit()
        assert doc.document_category == cat

    # Invalid category
    bad_doc = Document(
        code="DOC-99",
        project_id=proj.id,
        user_id=user.id,
        name="Bad.pdf",
        file_type="PDF",
        document_category="invalid_unapproved_category",
        storage_path="/path/bad.pdf",
    )
    in_memory_db.add(bad_doc)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 13: Alembic Revision 02 Structure & Dependency
# ---------------------------------------------------------------------------

def test_alembic_revision_02_metadata():
    """Verify that Revision 02 cleanly depends on 001_identity_tables."""
    import importlib.util
    from pathlib import Path

    migration_file = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "002_create_project_and_document_tables.py"
    assert migration_file.exists(), f"Revision 02 file missing at {migration_file}"

    spec = importlib.util.spec_from_file_location("revision_002", migration_file)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "002_project_and_document_tables"
    assert mod.down_revision == "001_identity_tables"
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# ---------------------------------------------------------------------------
# Test 14: Financial Non-Negative Check Constraints
# ---------------------------------------------------------------------------

def test_financial_non_negative_constraints(in_memory_db: Session):
    """Verify negative budget_raw or spent_raw triggers database check constraint violation."""
    owner = User(email="fin_owner@tameerai.pk", hashed_password="h", full_name="Fin Owner")
    in_memory_db.add(owner)
    in_memory_db.commit()

    # Negative budget_raw
    bad_proj1 = Project(
        code="PRJ-NEG-1",
        user_id=owner.id,
        name="Negative Budget Plaza",
        location="Lahore",
        budget_raw=Decimal("-500000.00"),
    )
    in_memory_db.add(bad_proj1)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Negative spent_raw
    bad_proj2 = Project(
        code="PRJ-NEG-2",
        user_id=owner.id,
        name="Negative Spent Plaza",
        location="Lahore",
        spent_raw=Decimal("-1000.00"),
    )
    in_memory_db.add(bad_proj2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 15: Compliance Score NULL Default & Range Constraint
# ---------------------------------------------------------------------------

def test_compliance_score_null_default_and_range(in_memory_db: Session):
    """Verify compliance_score defaults to None (unassessed) and respects 0-100 range check."""
    owner = User(email="comp_owner@tameerai.pk", hashed_password="h", full_name="Comp Owner")
    in_memory_db.add(owner)
    in_memory_db.commit()

    # Default is None
    p_default = Project(
        code="PRJ-COMP-1",
        user_id=owner.id,
        name="Unassessed Project",
        location="Islamabad",
    )
    in_memory_db.add(p_default)
    in_memory_db.commit()
    assert p_default.compliance_score is None

    # Valid score
    p_valid = Project(
        code="PRJ-COMP-2",
        user_id=owner.id,
        name="Assessed Project",
        location="Islamabad",
        compliance_score=85,
    )
    in_memory_db.add(p_valid)
    in_memory_db.commit()
    assert p_valid.compliance_score == 85

    # Out of range: > 100
    p_bad_high = Project(
        code="PRJ-COMP-3",
        user_id=owner.id,
        name="Invalid High Project",
        location="Islamabad",
        compliance_score=105,
    )
    in_memory_db.add(p_bad_high)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Out of range: < 0
    p_bad_low = Project(
        code="PRJ-COMP-4",
        user_id=owner.id,
        name="Invalid Low Project",
        location="Islamabad",
        compliance_score=-5,
    )
    in_memory_db.add(p_bad_low)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 16: Governing Authority Nullable Default
# ---------------------------------------------------------------------------

def test_governing_authority_nullable_default(in_memory_db: Session):
    """Verify governing_authority defaults to None (jurisdiction-neutral) unless explicitly provided."""
    owner = User(email="auth_owner@tameerai.pk", hashed_password="h", full_name="Auth Owner")
    in_memory_db.add(owner)
    in_memory_db.commit()

    p = Project(
        code="PRJ-AUTH",
        user_id=owner.id,
        name="Karachi Port Facility",
        location="Clifton, Karachi",
        city="Karachi",
    )
    in_memory_db.add(p)
    in_memory_db.commit()
    assert p.governing_authority is None

    # Explicit authority
    p.governing_authority = "SBCA & KDA"
    in_memory_db.commit()
    in_memory_db.expire_all()
    fetched = in_memory_db.scalar(select(Project).where(Project.id == p.id))
    assert fetched.governing_authority == "SBCA & KDA"


# ---------------------------------------------------------------------------
# Test 17: Document Deletion Behavior (Project CASCADE, Uploader RESTRICT)
# ---------------------------------------------------------------------------

def test_document_deletion_cascades_and_uploader_restrict(in_memory_db: Session):
    """
    Verify:
    1. documents.project_id ON DELETE CASCADE: deleting project removes associated documents.
    2. documents.user_id ON DELETE RESTRICT: deleting uploader is blocked while active documents exist.
    """
    owner = User(email="doc_owner2@tameerai.pk", hashed_password="h", full_name="Doc Owner 2")
    uploader = User(email="uploader_user@tameerai.pk", hashed_password="h", full_name="Engr. Uploader")
    in_memory_db.add_all([owner, uploader])
    in_memory_db.commit()

    proj = Project(code="PRJ-CASCADE", user_id=owner.id, name="Cascade Test", location="Loc")
    in_memory_db.add(proj)
    in_memory_db.commit()

    doc = Document(
        code="DOC-01",
        project_id=proj.id,
        user_id=uploader.id,
        name="Submittal-Drawing.dwg",
        file_type="CAD Drawing",
        storage_path="/files/doc.dwg",
    )
    in_memory_db.add(doc)
    in_memory_db.commit()

    # Attempting to delete the uploader MUST fail due to RESTRICT constraint
    in_memory_db.delete(uploader)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Deleting the project MUST cascade and delete the document
    in_memory_db.delete(proj)
    in_memory_db.commit()

    # Document is now gone
    docs = in_memory_db.scalars(select(Document).where(Document.project_id == proj.id)).all()
    assert len(docs) == 0

    # Now that the document is gone, uploader can be deleted cleanly
    in_memory_db.delete(uploader)
    in_memory_db.commit()


# ---------------------------------------------------------------------------
# Test 18: Document Status and Analysis Status Constraints
# ---------------------------------------------------------------------------

def test_document_status_check_constraints(in_memory_db: Session):
    """Verify document status and analysis_status enforce enumerated check constraints."""
    user = User(email="doc_status_user@tameerai.pk", hashed_password="h", full_name="User")
    in_memory_db.add(user)
    in_memory_db.commit()

    proj = Project(code="PRJ-STATUS", user_id=user.id, name="Status Project", location="Loc")
    in_memory_db.add(proj)
    in_memory_db.commit()

    # Invalid status
    bad_doc1 = Document(
        code="DOC-BAD-1",
        project_id=proj.id,
        user_id=user.id,
        name="Test.pdf",
        file_type="PDF",
        status="InvalidStatus",
        storage_path="/p/bad1.pdf",
    )
    in_memory_db.add(bad_doc1)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Invalid analysis_status
    bad_doc2 = Document(
        code="DOC-BAD-2",
        project_id=proj.id,
        user_id=user.id,
        name="Test.pdf",
        file_type="PDF",
        analysis_status="invalid_pipeline_state",
        storage_path="/p/bad2.pdf",
    )
    in_memory_db.add(bad_doc2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Negative file size
    bad_doc3 = Document(
        code="DOC-BAD-3",
        project_id=proj.id,
        user_id=user.id,
        name="Test.pdf",
        file_type="PDF",
        file_size_bytes=-10,
        storage_path="/p/bad3.pdf",
    )
    in_memory_db.add(bad_doc3)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

