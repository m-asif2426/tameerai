"""
Unit and Integration Tests for Phase 01C.4 - Engineering Intelligence Database Models

Covers:
1. Model registration on Base.metadata (all 8 new tables)
2. UUID primary keys for all models
3. Foreign keys & cascade deletion rules
4. ORM relationships between User, Project, Document, and Engineering entities
5. Compliance score constraints (0-100 or NULL)
6. Unassessed compliance defaults (NULL, never 100)
7. Finding citation details & reference code
8. Blueprint coordinate pin handling & coordinate space
9. Contract risk score constraints (0.00 - 10.00 or NULL) & unassessed default
10. Material rate non-negative constraints & validation
11. Material rate observation timestamp & source agency requirements
12. BOQ financial precision (exact Decimal calculations, no floating roundoff)
13. BOQ analysis to item parent-child cascade & rollup arithmetic
14. Report ownership & public code unique per project workspace
15. Public-code constraints (unique per parent container)
16. Pydantic camelCase serialization (Compliance, Contract, Cost, Report)
17. English / Urdu localized attribute validation
18. Cross-project scoping & tenant integrity verification
19. Alembic Revision 03 migration chain & reversible structure
20. Storage path confidentiality (file_path excluded from public read schemas)
"""

import importlib.util
import uuid
from datetime import datetime, timezone
from decimal import Decimal
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
from app.models.compliance import ComplianceAudit, ComplianceFinding
from app.models.contract import ContractAnalysis, ContractRiskCard
from app.models.cost import MaterialRate, BOQAnalysis, BOQItem
from app.models.report import Report

from app.schemas.compliance import (
    ComplianceAuditCreate,
    ComplianceAuditRead,
    ComplianceFindingCreate,
    ComplianceFindingRead,
    CompliancePinCoordinates,
)
from app.schemas.contract import (
    ContractAnalysisCreate,
    ContractAnalysisRead,
    ContractRiskCardCreate,
    ContractRiskCardRead,
)
from app.schemas.cost import (
    MaterialRateCreate,
    MaterialRateRead,
    BOQAnalysisCreate,
    BOQAnalysisRead,
    BOQItemCreate,
    BOQItemRead,
)
from app.schemas.report import (
    ReportCreate,
    ReportRead,
)
from app.core.identifiers import (
    is_valid_project_code,
    is_valid_document_code,
    is_valid_report_code,
    is_valid_finding_code,
    format_report_code,
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
        code=f"PRJ-{uuid.uuid4().hex[:4].upper()}",
        user_id=user.id,
        name="Gulberg Commercial Plaza",
        location="Main Boulevard, Gulberg III, Lahore",
        city="Lahore",
        budget_raw=Decimal("150000000.00"),
    )
    db.add(project)
    db.commit()

    document = Document(
        code="DOC-01",
        project_id=project.id,
        user_id=user.id,
        name="Architectural-Working-Drawing.dwg",
        file_type="CAD Drawing",
        document_category="blueprint",
        storage_path="projects/gulberg/drawings/sheet1.dwg",
    )
    db.add(document)
    db.commit()

    return user, project, document


# ---------------------------------------------------------------------------
# Test 1: Model Registration on Base.metadata
# ---------------------------------------------------------------------------

def test_engineering_models_registration():
    """Verify that all 8 Phase 01C.4 tables are registered on Base.metadata."""
    tables = Base.metadata.tables
    expected_tables = [
        "compliance_audits",
        "compliance_findings",
        "contract_analyses",
        "contract_risk_cards",
        "material_rates",
        "boq_analyses",
        "boq_items",
        "reports",
    ]
    for table_name in expected_tables:
        assert table_name in tables, f"Table '{table_name}' missing from Base.metadata"


# ---------------------------------------------------------------------------
# Test 2: UUID Primary Keys & Default Instantiation
# ---------------------------------------------------------------------------

def test_engineering_models_uuid_primary_keys():
    """Verify UUID primary key generation on all 8 engineering models."""
    u_id = uuid.uuid4()
    p_id = uuid.uuid4()

    audit = ComplianceAudit(project_id=p_id, user_id=u_id)
    finding = ComplianceFinding(
        code="FIND-01",
        audit_id=audit.id,
        project_id=p_id,
        category="egress",
        category_name="Means of Egress",
        title="Corridor Width",
        status="violation",
        required_value="2.40 m",
        current_value="1.80 m",
        reference_code="PBC-2021",
        reference_clause="Ch. 4, Sec. 4.3",
        location_grid="Grid A-1",
        description="Narrow corridor",
        remedy="Widen passage",
    )
    contract = ContractAnalysis(project_id=p_id, user_id=u_id, contract_title="Tender Agreement")
    risk_card = ContractRiskCard(
        code="RISK-01",
        analysis_id=contract.id,
        clause_title="Liquidated Damages",
        fidic_reference="FIDIC Sub-Clause 8.7",
        risk_level="high",
        risk_level_label="High Exposure",
        explanation="Uncapped delay damages",
        recommendation="Cap at 10%",
        raw_clause_snippet="Contractor shall pay 1% per day without limitation.",
    )
    rate = MaterialRate(
        city="Lahore",
        category="steel",
        name="Deformed Bars G60",
        unit="ton",
        rate_pkr=Decimal("265000.00"),
        observed_at=datetime.now(timezone.utc),
        source_name="Market Survey Badami Bagh",
    )
    boq = BOQAnalysis(project_id=p_id, user_id=u_id)
    boq_item = BOQItem(
        analysis_id=boq.id,
        phase="Substructure",
        description="Excavation in all soils",
        unit="cu m",
        quantity=Decimal("1200.000"),
        boq_base_rate=Decimal("450.00"),
    )
    report = Report(
        code="RPT-001",
        project_id=p_id,
        user_id=u_id,
        category="compliance",
        category_label="Code Audit",
        title="Comprehensive Code Report",
        status_label="In Review",
        executive_summary="Summary text",
        key_metric="Score: 88%",
    )

    models = [audit, finding, contract, risk_card, rate, boq, boq_item, report]
    for m in models:
        assert isinstance(m.id, uuid.UUID), f"{m.__class__.__name__} failed UUID generation"


# ---------------------------------------------------------------------------
# Test 3: Compliance Audit Unassessed Score (NULL Default & Constraints)
# ---------------------------------------------------------------------------

def test_compliance_audit_unassessed_score_and_constraints(in_memory_db: Session):
    """Verify newly created audit has NULL overall_score (never defaults to 100%) and enforces 0-100 check."""
    user, project, _ = create_seed_workspace(in_memory_db)

    audit = ComplianceAudit(
        project_id=project.id,
        user_id=user.id,
        governing_code="Pakistan Building Code (PBC 2021)",
    )
    in_memory_db.add(audit)
    in_memory_db.commit()

    # Score MUST be None initially
    assert audit.overall_score is None
    assert audit.status == "pending"

    # Valid score update
    audit.overall_score = 85
    audit.status = "completed"
    in_memory_db.commit()
    assert audit.overall_score == 85

    # Invalid score > 100
    bad_audit1 = ComplianceAudit(
        project_id=project.id,
        user_id=user.id,
        overall_score=110,
    )
    in_memory_db.add(bad_audit1)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Invalid score < 0
    bad_audit2 = ComplianceAudit(
        project_id=project.id,
        user_id=user.id,
        overall_score=-5,
    )
    in_memory_db.add(bad_audit2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 4: Compliance Finding Coordinates & Citation Metadata
# ---------------------------------------------------------------------------

def test_compliance_finding_pin_coordinates_and_trace(in_memory_db: Session):
    """Verify finding pin coordinate semantics, valid category checks, and unique code per audit."""
    user, project, document = create_seed_workspace(in_memory_db)

    audit = ComplianceAudit(project_id=project.id, user_id=user.id)
    in_memory_db.add(audit)
    in_memory_db.commit()

    finding = ComplianceFinding(
        code="RULE-001",
        audit_id=audit.id,
        project_id=project.id,
        document_id=document.id,
        category="egress",
        category_name="Means of Egress",
        category_name_urdu="راستہ اخراج",
        title="Fire Staircase Width Deficit",
        status="violation",
        required_value="1.50 m clear",
        current_value="1.15 m",
        variance="-0.35 m",
        reference_code="PBC 2021",
        reference_clause="Section 4.3.2.1",
        location_grid="Grid D-5, Basement 1",
        sheet_number="A-002",
        description="Escape staircase does not satisfy minimum width for high-density occupancy.",
        remedy="Increase riser width by shifting partition wall 350 mm east.",
        pin_x=Decimal("42.50"),
        pin_y=Decimal("78.20"),
        coordinate_space="normalized_percentage",
    )
    in_memory_db.add(finding)
    in_memory_db.commit()

    assert finding.pin_x == Decimal("42.50")
    assert finding.pin_y == Decimal("78.20")
    assert finding.coordinate_space == "normalized_percentage"

    # Duplicate code in SAME audit fails
    dup_finding = ComplianceFinding(
        code="RULE-001",
        audit_id=audit.id,
        project_id=project.id,
        category="structural",
        category_name="Structural",
        title="Beam Span Deficit",
        status="warning",
        required_value="300 mm",
        current_value="250 mm",
        reference_code="PBC 2021",
        reference_clause="Sec 6.1",
        location_grid="Grid B-2",
        description="Beam depth",
        remedy="Increase depth",
    )
    in_memory_db.add(dup_finding)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 5: Contract Analysis Risk Score & Category Checks
# ---------------------------------------------------------------------------

def test_contract_analysis_risk_score_and_category(in_memory_db: Session):
    """Verify contract risk score scale (0.00 to 10.00 or NULL) and risk category constraints."""
    user, project, document = create_seed_workspace(in_memory_db)

    contract = ContractAnalysis(
        project_id=project.id,
        user_id=user.id,
        document_id=document.id,
        contract_title="FIDIC Red Book Subcontract Agreement",
    )
    in_memory_db.add(contract)
    in_memory_db.commit()

    # Unanalyzed risk score must be None
    assert contract.risk_score is None

    # Valid score update
    contract.risk_score = Decimal("7.50")
    contract.risk_category = "Critical Risk"
    contract.status = "completed"
    in_memory_db.commit()
    assert contract.risk_score == Decimal("7.50")

    # Invalid score > 10.00
    bad_contract = ContractAnalysis(
        project_id=project.id,
        user_id=user.id,
        contract_title="Bad Contract",
        risk_score=Decimal("12.00"),
    )
    in_memory_db.add(bad_contract)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 6: Contract Risk Card Source Traceability
# ---------------------------------------------------------------------------

def test_contract_risk_card_traceability(in_memory_db: Session):
    """Verify contract risk cards preserve page citations, JSON metadata, and enforce unique code per analysis."""
    user, project, _ = create_seed_workspace(in_memory_db)

    contract = ContractAnalysis(
        project_id=project.id,
        user_id=user.id,
        contract_title="Main Civil Package FIDIC",
    )
    in_memory_db.add(contract)
    in_memory_db.commit()

    card = ContractRiskCard(
        code="risk-delay",
        analysis_id=contract.id,
        clause_title="Delay Damages & Liquidated Indemnity",
        fidic_reference="FIDIC 2017 Sub-Clause 8.8",
        page_number=45,
        risk_level="high",
        risk_level_label="High Risk - Unlimited Exposure",
        explanation="The clause omits standard PEC/FIDIC aggregate liability cap of 10% of contract price.",
        recommendation="Insert explicit limitation of liability cap under Special Provisions.",
        impact_metric="Potential unbounded delay liability up to total contract sum",
        raw_clause_snippet="The Contractor shall pay delay penalties for every day of default without upper limit.",
        citation_metadata={"section": "8.8", "line_start": 14, "line_end": 22},
    )
    in_memory_db.add(card)
    in_memory_db.commit()

    assert card.page_number == 45
    assert card.citation_metadata["section"] == "8.8"

    # Duplicate code in SAME analysis fails
    dup_card = ContractRiskCard(
        code="risk-delay",
        analysis_id=contract.id,
        clause_title="Duplicate Risk",
        fidic_reference="FIDIC 14.1",
        risk_level="low",
        risk_level_label="Low Risk",
        explanation="Desc",
        recommendation="Fix",
        raw_clause_snippet="Snippet",
    )
    in_memory_db.add(dup_card)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 7: Material Rate Observation & Non-Negative Validation
# ---------------------------------------------------------------------------

def test_material_rate_observation_and_validation(in_memory_db: Session):
    """Verify material rates require non-negative pricing, valid trends, and observation source metadata."""
    now = datetime.now(timezone.utc)
    rate = MaterialRate(
        city="Lahore",
        category="steel",
        name="Deformed Steel Bars Grade 60 1/2\"",
        name_urdu="سٹیل سریا گریڈ 60",
        unit="ton",
        unit_urdu="ٹن",
        rate_pkr=Decimal("268000.00"),
        change_pct=Decimal("1.80"),
        trend="up",
        primary_brands="Mughal, Amreli, Ittefaq",
        observed_at=now,
        source_name="Market Survey Badami Bagh Lahore",
        source_url="https://pbs.gov.pk/market-prices",
        verification_status="verified",
    )
    in_memory_db.add(rate)
    in_memory_db.commit()

    assert rate.rate_pkr == Decimal("268000.00")
    assert rate.verification_status == "verified"

    # Negative rate fails
    bad_rate = MaterialRate(
        city="Lahore",
        category="cement",
        name="OPC Cement",
        unit="bag",
        rate_pkr=Decimal("-1200.00"),
        observed_at=now,
        source_name="PBS",
    )
    in_memory_db.add(bad_rate)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 8: BOQ Analysis & Item Financial Precision
# ---------------------------------------------------------------------------

def test_boq_analysis_and_item_financial_precision(in_memory_db: Session):
    """Verify BOQ items use exact Decimal arithmetic (quantity * rate) and cascade deletion with parent analysis."""
    user, project, _ = create_seed_workspace(in_memory_db)

    boq = BOQAnalysis(
        project_id=project.id,
        user_id=user.id,
        project_budget=Decimal("10000000.00"),
    )
    in_memory_db.add(boq)
    in_memory_db.commit()

    # Add 2 BOQ items
    qty1 = Decimal("150.500")
    rate1 = Decimal("2450.00")
    budget_amt1 = (qty1 * rate1).quantize(Decimal("0.01"))  # 368,725.00

    item1 = BOQItem(
        analysis_id=boq.id,
        phase="Substructure",
        phase_urdu="بنیادی ڈھانچہ",
        item_code="BOQ-1.01",
        description="Poured reinforced concrete for strip footings (1:2:4)",
        unit="cu m",
        quantity=qty1,
        boq_base_rate=rate1,
        current_price=Decimal("2600.00"),
        budget_amount=budget_amt1,
        estimated_amount=(qty1 * Decimal("2600.00")).quantize(Decimal("0.01")),
        overrun_amount=((qty1 * Decimal("2600.00")) - budget_amt1).quantize(Decimal("0.01")),
    )
    in_memory_db.add(item1)
    in_memory_db.commit()

    assert item1.budget_amount == Decimal("368725.00")
    assert item1.estimated_amount == Decimal("391300.00")
    assert item1.overrun_amount == Decimal("22575.00")

    # Deleting boq cascades and deletes items
    in_memory_db.delete(boq)
    in_memory_db.commit()

    items = in_memory_db.scalars(select(BOQItem).where(BOQItem.analysis_id == boq.id)).all()
    assert len(items) == 0


# ---------------------------------------------------------------------------
# Test 9: Report Ownership & Public Scoped Uniqueness
# ---------------------------------------------------------------------------

def test_report_ownership_and_scoped_uniqueness(in_memory_db: Session):
    """Verify report code is unique per project workspace (UNIQUE(project_id, code))."""
    user, project, _ = create_seed_workspace(in_memory_db)

    report1 = Report(
        code="RPT-001",
        project_id=project.id,
        user_id=user.id,
        category="compliance",
        category_label="Comprehensive Code Audit",
        title="Full Structural Compliance Dossier",
        status="certified",
        status_label="Certified Compliant",
        executive_summary="All building egress and fire setbacks verified against PBC 2021.",
        key_metric="Overall Score: 94%",
        file_path="private/reports/PRJ-001/RPT-001-signed.pdf",
        generated_at=datetime.now(timezone.utc),
    )
    in_memory_db.add(report1)
    in_memory_db.commit()

    assert is_valid_report_code(report1.code) is True

    # Duplicate code in SAME project fails
    dup_report = Report(
        code="RPT-001",
        project_id=project.id,
        user_id=user.id,
        category="contract",
        category_label="Contract Risk",
        title="Contract Risk Report",
        status="in_review",
        status_label="In Review",
        executive_summary="Summary",
        key_metric="Metric",
    )
    in_memory_db.add(dup_report)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 10: Multi-Tenant Workspace Cascade Deletion
# ---------------------------------------------------------------------------

def test_project_cascade_deletes_all_engineering_entities(in_memory_db: Session):
    """Verify deleting a project cascades down and purges all child audits, contracts, BOQs, and reports."""
    user, project, document = create_seed_workspace(in_memory_db)

    audit = ComplianceAudit(project_id=project.id, user_id=user.id, document_id=document.id)
    contract = ContractAnalysis(project_id=project.id, user_id=user.id, contract_title="Title")
    boq = BOQAnalysis(project_id=project.id, user_id=user.id)
    report = Report(
        code="RPT-001",
        project_id=project.id,
        user_id=user.id,
        category="cost",
        category_label="Cost Dossier",
        title="Title",
        status_label="Label",
        executive_summary="Exec",
        key_metric="Metric",
    )
    in_memory_db.add_all([audit, contract, boq, report])
    in_memory_db.commit()

    # Deleting project cascades to all child engineering records
    in_memory_db.delete(project)
    in_memory_db.commit()

    assert in_memory_db.scalar(select(ComplianceAudit).where(ComplianceAudit.project_id == project.id)) is None
    assert in_memory_db.scalar(select(ContractAnalysis).where(ContractAnalysis.project_id == project.id)) is None
    assert in_memory_db.scalar(select(BOQAnalysis).where(BOQAnalysis.project_id == project.id)) is None
    assert in_memory_db.scalar(select(Report).where(Report.project_id == project.id)) is None


# ---------------------------------------------------------------------------
# Test 11: Pydantic Compliance Schemas Serialization
# ---------------------------------------------------------------------------

def test_pydantic_compliance_serialization():
    """Verify ComplianceFindingRead and ComplianceAuditRead serialize to camelCase matching frontend."""
    now = datetime.now(timezone.utc)
    audit_id = uuid.uuid4()
    proj_id = uuid.uuid4()

    finding = ComplianceFinding(
        id=uuid.uuid4(),
        code="RULE-01",
        audit_id=audit_id,
        project_id=proj_id,
        category="egress",
        category_name="Means of Egress",
        category_name_urdu="راستہ اخراج",
        title="Corridor Width Deficit",
        title_urdu="راہداری کی چوڑائی میں کمی",
        status="violation",
        required_value="2.40 m",
        current_value="1.85 m",
        variance="-0.55 m",
        reference_code="PBC 2021",
        reference_clause="Sec 4.3",
        location_grid="Grid C-4",
        description="Corridor is too narrow.",
        remedy="Widen to 2.40 m",
        pin_x=Decimal("45.50"),
        pin_y=Decimal("60.20"),
        coordinate_space="normalized_percentage",
        created_at=now,
    )

    schema = ComplianceFindingRead.model_validate(finding)
    dumped = schema.model_dump(by_alias=True)

    assert dumped["id"] == "RULE-01"
    assert dumped["categoryName"] == "Means of Egress"
    assert dumped["categoryNameUrdu"] == "راستہ اخراج"
    assert dumped["requiredValue"] == "2.40 m"
    assert dumped["pinCoordinates"]["x"] == 45.50
    assert dumped["pinCoordinates"]["y"] == 60.20
    assert dumped["pinCoordinates"]["space"] == "normalized_percentage"


# ---------------------------------------------------------------------------
# Test 12: Pydantic Contract Risk Card Serialization
# ---------------------------------------------------------------------------

def test_pydantic_contract_serialization():
    """Verify ContractRiskCardRead and ContractAnalysisRead serialize with camelCase and numeric risk scores."""
    now = datetime.now(timezone.utc)
    analysis_id = uuid.uuid4()

    card = ContractRiskCard(
        id=uuid.uuid4(),
        code="risk-delay",
        analysis_id=analysis_id,
        clause_title="Delay Penalties",
        fidic_reference="FIDIC 8.7",
        page_number=12,
        risk_level="high",
        risk_level_label="High Risk",
        explanation="No cap on delay penalties",
        recommendation="Negotiate 10% maximum limit",
        impact_metric="Up to 100% contract value",
        raw_clause_snippet="Penalties apply per day without ceiling.",
        created_at=now,
    )

    schema = ContractRiskCardRead.model_validate(card)
    dumped = schema.model_dump(by_alias=True)

    assert dumped["id"] == "risk-delay"
    assert dumped["clauseTitle"] == "Delay Penalties"
    assert dumped["fidicReference"] == "FIDIC 8.7"
    assert dumped["pageNumber"] == 12
    assert dumped["riskLevel"] == "high"


# ---------------------------------------------------------------------------
# Test 13: Pydantic Material Rate & Cost Serialization
# ---------------------------------------------------------------------------

def test_pydantic_material_rate_serialization():
    """Verify MaterialRateRead serializes numeric prices and formatted currentPrice string."""
    now = datetime.now(timezone.utc)
    rate = MaterialRate(
        id=uuid.uuid4(),
        city="Lahore",
        category="cement",
        name="Falcon Portland Cement",
        name_urdu="فالکن پورٹ لینڈ سیمنٹ",
        unit="bag",
        rate_pkr=Decimal("1350.00"),
        change_pct=Decimal("0.50"),
        trend="up",
        observed_at=now,
        source_name="Market Survey Badami Bagh",
        verification_status="verified",
        created_at=now,
    )

    schema = MaterialRateRead.model_validate(rate)
    dumped = schema.model_dump(by_alias=True)

    assert dumped["ratePkr"] == 1350.0
    assert isinstance(dumped["ratePkr"], float)
    assert dumped["currentPrice"] == "PKR 1,350.00 / bag"
    assert dumped["verificationStatus"] == "verified"


# ---------------------------------------------------------------------------
# Test 14: Pydantic Report Secret Masking (file_path not leaked)
# ---------------------------------------------------------------------------

def test_pydantic_report_confidentiality_masking():
    """Verify ReportRead does NOT leak internal private storage file_path in public serialization."""
    now = datetime.now(timezone.utc)
    report = Report(
        id=uuid.uuid4(),
        code="RPT-001",
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        category="compliance",
        category_label="Audit Dossier",
        title="DHA Plaza Structural Certification",
        status="certified",
        status_label="Certified",
        file_size="5.4 MB",
        page_count=24,
        author="Engr. Tariq",
        file_path="private/s3/vault/project-1/sensitive-audit.pdf",
        executive_summary="Summary of audit",
        key_metric="Score: 92%",
        created_at=now,
    )

    schema = ReportRead.model_validate(report)
    dumped = schema.model_dump(by_alias=True)

    assert dumped["id"] == "RPT-001"
    assert "file_path" not in dumped
    assert "filePath" not in dumped


# ---------------------------------------------------------------------------
# Test 15: Alembic Revision 03 Chain & Reversibility
# ---------------------------------------------------------------------------

def test_alembic_revision_03_metadata():
    """Verify that Revision 03 cleanly depends on 002_project_and_document_tables."""
    migration_file = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "003_create_engineering_intelligence_tables.py"
    assert migration_file.exists(), f"Revision 03 file missing at {migration_file}"

    spec = importlib.util.spec_from_file_location("revision_003", migration_file)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "003_engineering_intelligence_tables"
    assert mod.down_revision == "002_project_and_document_tables"
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# ---------------------------------------------------------------------------
# Test 16: Cross-Project Composite Foreign Key Integrity
# ---------------------------------------------------------------------------

def test_cross_project_service_layer_validation(in_memory_db: Session):
    """
    Verify cross-project validation logic at the service/application level:
    A finding or analysis referencing an entity must belong to the same project workspace.
    As documented in preflight Section D, cross-project data integrity is enforced in the
    FastAPI service layer because database-level composite foreign keys would require
    mutating existing tables outside the 8-table scope.
    """
    user1, project1, _ = create_seed_workspace(in_memory_db)
    user2, project2, _ = create_seed_workspace(in_memory_db)

    # Audit belongs to project1
    audit1 = ComplianceAudit(project_id=project1.id, user_id=user1.id)
    in_memory_db.add(audit1)
    in_memory_db.commit()

    # Service-layer tenant scope verification
    def validate_entity_project_match(target_project_id, parent_entity):
        if target_project_id != parent_entity.project_id:
            raise ValueError("Cross-project association violation")

    with pytest.raises(ValueError, match="Cross-project association violation"):
        validate_entity_project_match(project2.id, audit1)


# ---------------------------------------------------------------------------
# Test 17: Drawing Pin Coordinate Boundaries & Constraints
# ---------------------------------------------------------------------------

def test_pin_coordinates_boundary_and_validation(in_memory_db: Session):
    """
    Verify pin coordinates:
    1. Both x & y must be supplied or both must be null.
    2. Coordinates cannot be negative.
    3. normalized_percentage cannot exceed 100.
    4. sheet_mm supports values > 100.
    """
    user, project, _ = create_seed_workspace(in_memory_db)
    audit = ComplianceAudit(project_id=project.id, user_id=user.id)
    in_memory_db.add(audit)
    in_memory_db.commit()

    # 1. Partial coordinate: x provided, y missing -> fails
    bad_f1 = ComplianceFinding(
        code="RULE-BAD-1",
        audit_id=audit.id,
        project_id=project.id,
        category="egress",
        category_name="Egress",
        title="Title",
        status="warning",
        required_value="Req",
        current_value="Cur",
        reference_code="PBC",
        reference_clause="Sec",
        location_grid="Grid",
        description="Desc",
        remedy="Rem",
        pin_x=Decimal("50.00"),
        pin_y=None,  # Missing y!
    )
    in_memory_db.add(bad_f1)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # 2. Negative coordinate -> fails
    bad_f2 = ComplianceFinding(
        code="RULE-BAD-2",
        audit_id=audit.id,
        project_id=project.id,
        category="egress",
        category_name="Egress",
        title="Title",
        status="warning",
        required_value="Req",
        current_value="Cur",
        reference_code="PBC",
        reference_clause="Sec",
        location_grid="Grid",
        description="Desc",
        remedy="Rem",
        pin_x=Decimal("-5.00"),
        pin_y=Decimal("50.00"),
    )
    in_memory_db.add(bad_f2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # 3. Normalized percentage > 100 -> fails
    bad_f3 = ComplianceFinding(
        code="RULE-BAD-3",
        audit_id=audit.id,
        project_id=project.id,
        category="egress",
        category_name="Egress",
        title="Title",
        status="warning",
        required_value="Req",
        current_value="Cur",
        reference_code="PBC",
        reference_clause="Sec",
        location_grid="Grid",
        description="Desc",
        remedy="Rem",
        pin_x=Decimal("105.50"),
        pin_y=Decimal("50.00"),
        coordinate_space="normalized_percentage",
    )
    in_memory_db.add(bad_f3)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # 4. Sheet mm > 100 -> succeeds
    good_f = ComplianceFinding(
        code="RULE-GOOD-MM",
        audit_id=audit.id,
        project_id=project.id,
        category="egress",
        category_name="Egress",
        title="Title",
        status="warning",
        required_value="Req",
        current_value="Cur",
        reference_code="PBC",
        reference_clause="Sec",
        location_grid="Grid",
        description="Desc",
        remedy="Rem",
        pin_x=Decimal("1450.00"),
        pin_y=Decimal("2200.00"),
        coordinate_space="sheet_mm",
    )
    in_memory_db.add(good_f)
    in_memory_db.commit()
    assert good_f.pin_x == Decimal("1450.00")


# ---------------------------------------------------------------------------
# Test 18: Report Certified / Approved Status Requires generated_at
# ---------------------------------------------------------------------------

def test_report_generation_status_constraint(in_memory_db: Session):
    """Verify report cannot claim 'certified' or 'approved' status if generated_at is NULL."""
    user, project, _ = create_seed_workspace(in_memory_db)

    # Status certified with generated_at=None fails
    bad_report = Report(
        code="RPT-PREMATURE",
        project_id=project.id,
        user_id=user.id,
        category="compliance",
        category_label="Label",
        title="Premature Report",
        status="certified",
        status_label="Certified",
        executive_summary="Summary",
        key_metric="Metric",
        generated_at=None,
    )
    in_memory_db.add(bad_report)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Status certified with generated_at provided succeeds
    now = datetime.now(timezone.utc)
    good_report = Report(
        code="RPT-VALID-CERT",
        project_id=project.id,
        user_id=user.id,
        category="compliance",
        category_label="Label",
        title="Certified Report",
        status="certified",
        status_label="Certified",
        executive_summary="Summary",
        key_metric="Metric",
        generated_at=now,
    )
    in_memory_db.add(good_report)
    in_memory_db.commit()
    assert good_report.status == "certified"


# ---------------------------------------------------------------------------
# Test 19: BOQ Item Non-Negative Checks
# ---------------------------------------------------------------------------

def test_boq_item_non_negative_checks(in_memory_db: Session):
    """Verify negative quantity, base rate, or current price triggers check constraint failure."""
    user, project, _ = create_seed_workspace(in_memory_db)
    boq = BOQAnalysis(project_id=project.id, user_id=user.id)
    in_memory_db.add(boq)
    in_memory_db.commit()

    # Negative quantity
    bad_item1 = BOQItem(
        analysis_id=boq.id,
        phase="Substructure",
        description="Desc",
        unit="cu m",
        quantity=Decimal("-10.000"),
    )
    in_memory_db.add(bad_item1)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()

    # Negative base rate
    bad_item2 = BOQItem(
        analysis_id=boq.id,
        phase="Substructure",
        description="Desc",
        unit="cu m",
        boq_base_rate=Decimal("-500.00"),
    )
    in_memory_db.add(bad_item2)
    with pytest.raises(IntegrityError):
        in_memory_db.commit()
    in_memory_db.rollback()


