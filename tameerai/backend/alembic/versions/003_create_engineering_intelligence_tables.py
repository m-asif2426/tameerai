"""create engineering intelligence tables (compliance, contract, cost, reports)

Revision ID: 003_engineering_intelligence_tables
Revises: 002_project_and_document_tables
Create Date: 2026-11-03 17:50:00.000000

Phase 01C.4 - Engineering Intelligence Models Migration
Defines the relational schema for:
- compliance_audits, compliance_findings
- contract_analyses, contract_risk_cards
- material_rates, boq_analyses, boq_items
- reports
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '003_engineering_intelligence_tables'
down_revision: Union[str, None] = '002_project_and_document_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure alembic_version technical table supports revision strings > 32 characters
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")

    # -----------------------------------------------------------------------
    # 1. Table: compliance_audits
    # -----------------------------------------------------------------------
    op.create_table(
        'compliance_audits',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project workspace UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Initiating engineer user UUID'),
        sa.Column('document_id', sa.Uuid(), nullable=True, comment='Source drawing / blueprint document UUID (SET NULL preserves audit if file record is removed)'),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False, comment='Audit status: pending, in_progress, completed, failed'),
        sa.Column('overall_score', sa.Integer(), nullable=True, comment='Calculated compliance score (0-100). NULL until audit execution completes.'),
        sa.Column('governing_code', sa.String(length=150), nullable=True, comment='Regulatory standard evaluated against (e.g. PBC 2021, LDA 2019, SBCA 2020)'),
        sa.Column('summary', sa.Text(), nullable=True, comment='Executive audit findings summary'),
        sa.Column('summary_urdu', sa.Text(), nullable=True, comment='Urdu executive audit findings summary'),
        sa.Column('total_checks', sa.Integer(), server_default='0', nullable=False, comment='Total rule checks evaluated'),
        sa.Column('passed_count', sa.Integer(), server_default='0', nullable=False, comment='Total checks passed'),
        sa.Column('warning_count', sa.Integer(), server_default='0', nullable=False, comment='Total advisory warnings flagged'),
        sa.Column('violation_count', sa.Integer(), server_default='0', nullable=False, comment='Total regulatory violations flagged'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when audit rule processing was finalized'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Audit creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Audit modification timestamp'),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed')", name='ck_compliance_audits_status'),
        sa.CheckConstraint('overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)', name='ck_compliance_audits_overall_score'),
        sa.CheckConstraint('total_checks >= 0 AND passed_count >= 0 AND warning_count >= 0 AND violation_count >= 0', name='ck_compliance_audits_counts_non_negative'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_compliance_audits_document_id_documents'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_compliance_audits_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_compliance_audits_user_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_compliance_audits')),
    )
    op.create_index('ix_compliance_audits_project_id', 'compliance_audits', ['project_id'], unique=False)
    op.create_index('ix_compliance_audits_user_id', 'compliance_audits', ['user_id'], unique=False)
    op.create_index('ix_compliance_audits_document_id', 'compliance_audits', ['document_id'], unique=False)

    # -----------------------------------------------------------------------
    # 2. Table: compliance_findings
    # -----------------------------------------------------------------------
    op.create_table(
        'compliance_findings',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Public-facing finding code (e.g. FIND-001 or RULE-01). Unique per audit.'),
        sa.Column('audit_id', sa.Uuid(), nullable=False, comment='Parent compliance audit UUID'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Direct project reference for tenant isolation enforcement'),
        sa.Column('document_id', sa.Uuid(), nullable=True, comment='Specific CAD/drawing document pinned'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='Domain category: egress, structural, zoning, fire'),
        sa.Column('category_name', sa.String(length=100), nullable=False, comment="Category display name (e.g. 'Means of Egress')"),
        sa.Column('category_name_urdu', sa.String(length=100), nullable=True, comment='Urdu category display name'),
        sa.Column('title', sa.String(length=200), nullable=False, comment="Finding rule title (e.g. 'Corridor Width Deficit')"),
        sa.Column('title_urdu', sa.String(length=200), nullable=True, comment='Urdu finding rule title'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='Finding status: violation, warning, passed'),
        sa.Column('required_value', sa.String(length=100), nullable=False, comment="Mandated regulatory metric (e.g. '2.40 m min clear width')"),
        sa.Column('current_value', sa.String(length=100), nullable=False, comment="Observed architectural plan metric (e.g. '1.85 m')"),
        sa.Column('variance', sa.String(length=100), nullable=True, comment="Delta metric (e.g. '-0.55 m (-23%)')"),
        sa.Column('reference_code', sa.String(length=100), nullable=False, comment="Governing code codex (e.g. 'PBC 2021', 'LDA Building Byelaws 2019')"),
        sa.Column('reference_clause', sa.String(length=200), nullable=False, comment="Exact section / clause citation (e.g. 'Chapter 4, Section 4.3.2.1')"),
        sa.Column('location_grid', sa.String(length=100), nullable=False, comment="Architectural grid coordinate / floor (e.g. 'Grid C-4, Level 2')"),
        sa.Column('sheet_number', sa.String(length=50), nullable=True, comment="Drawing sheet identifier (e.g. 'A-102')"),
        sa.Column('description', sa.Text(), nullable=False, comment='Detailed technical description of the deficiency'),
        sa.Column('description_urdu', sa.Text(), nullable=True, comment='Urdu technical description of the deficiency'),
        sa.Column('remedy', sa.Text(), nullable=False, comment='Engineering remedy or architectural correction'),
        sa.Column('remedy_urdu', sa.Text(), nullable=True, comment='Urdu engineering remedy'),
        sa.Column('pin_x', sa.Numeric(precision=8, scale=2), nullable=True, comment='Horizontal coordinate of drawing annotation pin'),
        sa.Column('pin_y', sa.Numeric(precision=8, scale=2), nullable=True, comment='Vertical coordinate of drawing annotation pin'),
        sa.Column('coordinate_space', sa.String(length=50), server_default='normalized_percentage', nullable=False, comment='Coordinate system semantics: normalized_percentage (0-100), sheet_mm, pixel'),
        sa.Column('is_resolved', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Status flag indicating architectural rectification'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Finding creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Finding last update timestamp'),
        sa.CheckConstraint("category IN ('egress', 'structural', 'zoning', 'fire')", name='ck_compliance_findings_category'),
        sa.CheckConstraint("status IN ('violation', 'warning', 'passed')", name='ck_compliance_findings_status'),
        sa.CheckConstraint("coordinate_space IN ('normalized_percentage', 'sheet_mm', 'pixel')", name='ck_compliance_findings_coordinate_space'),
        sa.CheckConstraint("(pin_x IS NULL AND pin_y IS NULL) OR (pin_x IS NOT NULL AND pin_y IS NOT NULL AND pin_x >= 0 AND pin_y >= 0 AND (coordinate_space != 'normalized_percentage' OR (pin_x <= 100 AND pin_y <= 100)))", name='ck_compliance_findings_pin_coords'),
        sa.ForeignKeyConstraint(['audit_id'], ['compliance_audits.id'], name=op.f('fk_compliance_findings_audit_id_compliance_audits'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_compliance_findings_document_id_documents'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_compliance_findings_project_id_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_compliance_findings')),
        sa.UniqueConstraint('audit_id', 'code', name='uq_compliance_findings_audit_code'),
    )
    op.create_index('ix_compliance_findings_code', 'compliance_findings', ['code'], unique=False)
    op.create_index('ix_compliance_findings_audit_id', 'compliance_findings', ['audit_id'], unique=False)
    op.create_index('ix_compliance_findings_project_id', 'compliance_findings', ['project_id'], unique=False)
    op.create_index('ix_compliance_findings_document_id', 'compliance_findings', ['document_id'], unique=False)
    op.create_index('ix_compliance_findings_category', 'compliance_findings', ['category'], unique=False)
    op.create_index('ix_compliance_findings_status', 'compliance_findings', ['status'], unique=False)

    # -----------------------------------------------------------------------
    # 3. Table: contract_analyses
    # -----------------------------------------------------------------------
    op.create_table(
        'contract_analyses',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project workspace UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Initiating legal engineer UUID'),
        sa.Column('document_id', sa.Uuid(), nullable=True, comment='Source contract PDF/DOCX document UUID'),
        sa.Column('contract_title', sa.String(length=255), nullable=False, comment="Title of the agreement (e.g. 'General Conditions of Contract - DHA Mall')"),
        sa.Column('standard_format', sa.String(length=100), server_default='FIDIC Red Book 2017 & PEC', nullable=False, comment='Benchmark standard contract template'),
        sa.Column('status', sa.String(length=50), server_default='unprocessed', nullable=False, comment='Analysis lifecycle state: unprocessed, processing, completed, failed'),
        sa.Column('risk_score', sa.Numeric(precision=4, scale=2), nullable=True, comment='Overall contract risk score on 0.00 to 10.00 scale (NULL until completed)'),
        sa.Column('risk_category', sa.String(length=50), nullable=True, comment='Summary risk categorization: Critical Risk, Moderate Risk, Low Risk'),
        sa.Column('total_clauses_audited', sa.Integer(), server_default='0', nullable=False, comment='Total contract clauses parsed and evaluated'),
        sa.Column('flagged_clauses_count', sa.Integer(), server_default='0', nullable=False, comment='Count of non-standard or high-risk clauses identified'),
        sa.Column('summary', sa.Text(), nullable=True, comment='Executive legal/risk analysis summary'),
        sa.Column('summary_urdu', sa.Text(), nullable=True, comment='Urdu executive legal/risk analysis summary'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when analysis reached final completed state'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Record modification timestamp'),
        sa.CheckConstraint("status IN ('unprocessed', 'processing', 'completed', 'failed')", name='ck_contract_analyses_status'),
        sa.CheckConstraint('risk_score IS NULL OR (risk_score >= 0.00 AND risk_score <= 10.00)', name='ck_contract_analyses_risk_score'),
        sa.CheckConstraint("risk_category IS NULL OR risk_category IN ('Critical Risk', 'Moderate Risk', 'Low Risk')", name='ck_contract_analyses_risk_category'),
        sa.CheckConstraint('total_clauses_audited >= 0 AND flagged_clauses_count >= 0', name='ck_contract_analyses_clauses_non_negative'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_contract_analyses_document_id_documents'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_contract_analyses_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_contract_analyses_user_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contract_analyses')),
    )
    op.create_index('ix_contract_analyses_project_id', 'contract_analyses', ['project_id'], unique=False)
    op.create_index('ix_contract_analyses_user_id', 'contract_analyses', ['user_id'], unique=False)
    op.create_index('ix_contract_analyses_document_id', 'contract_analyses', ['document_id'], unique=False)

    # -----------------------------------------------------------------------
    # 4. Table: contract_risk_cards
    # -----------------------------------------------------------------------
    op.create_table(
        'contract_risk_cards',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Public-facing risk card code (e.g. RISK-001 or risk-delay). Unique per analysis.'),
        sa.Column('analysis_id', sa.Uuid(), nullable=False, comment='Parent contract analysis UUID'),
        sa.Column('clause_title', sa.String(length=255), nullable=False, comment="Subject title of clause (e.g. 'Extension of Time for Completion')"),
        sa.Column('clause_title_urdu', sa.String(length=255), nullable=True, comment='Urdu subject title of clause'),
        sa.Column('fidic_reference', sa.String(length=150), nullable=False, comment="Benchmark standard reference (e.g. 'FIDIC Clause 8.4', 'PEC Clause 44.1')"),
        sa.Column('page_number', sa.Integer(), nullable=True, comment='Exact page number in original uploaded contract file'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, comment='Risk level severity: high, medium, low'),
        sa.Column('risk_level_label', sa.String(length=100), nullable=False, comment="Display label (e.g. 'High Risk - Contractor Exposure')"),
        sa.Column('risk_level_label_urdu', sa.String(length=100), nullable=True, comment='Urdu display label'),
        sa.Column('explanation', sa.Text(), nullable=False, comment='Detailed explanation of legal ambiguity or commercial imbalance'),
        sa.Column('explanation_urdu', sa.Text(), nullable=True, comment='Urdu legal explanation'),
        sa.Column('recommendation', sa.Text(), nullable=False, comment='Practical mitigation or amendment recommendation'),
        sa.Column('recommendation_urdu', sa.Text(), nullable=True, comment='Urdu mitigation recommendation'),
        sa.Column('impact_metric', sa.String(length=150), nullable=True, comment="Quantifiable commercial exposure metric (e.g. 'Liquidated damages capped at 10%')"),
        sa.Column('raw_clause_snippet', sa.Text(), nullable=False, comment='Specific verbatim sentence / excerpt from the uploaded submittal document'),
        sa.Column('citation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Structured citation trace (e.g. char offsets, section numbering, OCR bbox)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Risk card creation timestamp'),
        sa.CheckConstraint("risk_level IN ('high', 'medium', 'low')", name='ck_contract_risk_cards_risk_level'),
        sa.CheckConstraint('page_number IS NULL OR page_number >= 1', name='ck_contract_risk_cards_page_number'),
        sa.ForeignKeyConstraint(['analysis_id'], ['contract_analyses.id'], name=op.f('fk_contract_risk_cards_analysis_id_contract_analyses'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contract_risk_cards')),
        sa.UniqueConstraint('analysis_id', 'code', name='uq_contract_risk_cards_analysis_code'),
    )
    op.create_index('ix_contract_risk_cards_code', 'contract_risk_cards', ['code'], unique=False)
    op.create_index('ix_contract_risk_cards_analysis_id', 'contract_risk_cards', ['analysis_id'], unique=False)
    op.create_index('ix_contract_risk_cards_risk_level', 'contract_risk_cards', ['risk_level'], unique=False)

    # -----------------------------------------------------------------------
    # 5. Table: material_rates
    # -----------------------------------------------------------------------
    op.create_table(
        'material_rates',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('city', sa.String(length=50), nullable=False, comment='Market jurisdiction: Lahore, Karachi, Islamabad, Peshawar, Quetta, Rawalpindi'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='Material category: steel, cement, bricks, aggregates, sand, tiles, labor, general'),
        sa.Column('name', sa.String(length=150), nullable=False, comment="Standard material name (e.g. 'Deformed Steel Bars Grade 60 1/2\"')"),
        sa.Column('name_urdu', sa.String(length=150), nullable=True, comment="Urdu material name (e.g. 'سٹیل سریا گریڈ 60')"),
        sa.Column('spec', sa.String(length=200), nullable=True, comment='Technical ASTM / PSQCA specification'),
        sa.Column('spec_urdu', sa.String(length=200), nullable=True, comment='Urdu specification summary'),
        sa.Column('unit', sa.String(length=50), nullable=False, comment='Standard measurement unit: ton, bag (50kg), 1000 bricks, cu ft, sq ft'),
        sa.Column('unit_urdu', sa.String(length=50), nullable=True, comment='Urdu measurement unit'),
        sa.Column('rate_pkr', sa.Numeric(precision=12, scale=2), nullable=False, comment='Authoritative observed price in Pakistani Rupees (PKR)'),
        sa.Column('change_pct', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False, comment='Percentage change relative to previous survey period'),
        sa.Column('trend', sa.String(length=20), server_default='neutral', nullable=False, comment='Price movement direction: up, down, neutral'),
        sa.Column('primary_brands', sa.String(length=255), nullable=True, comment="Representative market manufacturers (e.g. 'Mughal, Amreli, Bestway, Fauji')"),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False, comment='Exact timestamp when the market quote was collected'),
        sa.Column('source_name', sa.String(length=150), nullable=False, comment="Verifiable reporting agency (e.g. 'Pakistan Bureau of Statistics', 'C&W Dept')"),
        sa.Column('source_url', sa.String(length=500), nullable=True, comment='Official reference or published bulletin link'),
        sa.Column('verification_status', sa.String(length=50), server_default='unverified', nullable=False, comment='Verification condition: verified, unverified, stale'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Database insertion timestamp'),
        sa.CheckConstraint('rate_pkr >= 0', name='ck_material_rates_rate_pkr_non_negative'),
        sa.CheckConstraint("trend IN ('up', 'down', 'neutral')", name='ck_material_rates_trend'),
        sa.CheckConstraint("verification_status IN ('verified', 'unverified', 'stale')", name='ck_material_rates_verification_status'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_material_rates')),
    )
    op.create_index('ix_material_rates_city', 'material_rates', ['city'], unique=False)
    op.create_index('ix_material_rates_category', 'material_rates', ['category'], unique=False)
    op.create_index('ix_material_rates_observed_at', 'material_rates', ['observed_at'], unique=False)

    # -----------------------------------------------------------------------
    # 6. Table: boq_analyses
    # -----------------------------------------------------------------------
    op.create_table(
        'boq_analyses',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project workspace UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Initiating quantity surveyor UUID'),
        sa.Column('document_id', sa.Uuid(), nullable=True, comment='Source Excel / CSV BOQ schedule document UUID'),
        sa.Column('status', sa.String(length=50), server_default='unprocessed', nullable=False, comment='Analysis state: unprocessed, processing, completed, failed'),
        sa.Column('project_budget', sa.Numeric(precision=15, scale=2), nullable=True, comment='Baseline budgeted tender cost in PKR'),
        sa.Column('estimated_cost', sa.Numeric(precision=15, scale=2), nullable=True, comment='Estimated current execution cost in PKR based on verified quantities'),
        sa.Column('current_cost', sa.Numeric(precision=15, scale=2), nullable=True, comment='Real-time revised project cost taking into account commodity market trends'),
        sa.Column('cost_variance', sa.Numeric(precision=15, scale=2), nullable=True, comment='Absolute cost variance in PKR (positive represents cost overrun)'),
        sa.Column('variance_percentage', sa.Numeric(precision=6, scale=2), nullable=True, comment='Percentage variance relative to baseline budget'),
        sa.Column('risk_indicator', sa.String(length=20), server_default='Low', nullable=False, comment='Overall budget escalation risk indicator: Low, Medium, High'),
        sa.Column('summary', sa.Text(), nullable=True, comment='Executive cost analysis summary'),
        sa.Column('summary_urdu', sa.Text(), nullable=True, comment='Urdu executive cost analysis summary'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when schedule processing finished'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Modification timestamp'),
        sa.CheckConstraint("status IN ('unprocessed', 'processing', 'completed', 'failed')", name='ck_boq_analyses_status'),
        sa.CheckConstraint('project_budget IS NULL OR project_budget >= 0', name='ck_boq_analyses_project_budget_non_negative'),
        sa.CheckConstraint('estimated_cost IS NULL OR estimated_cost >= 0', name='ck_boq_analyses_estimated_cost_non_negative'),
        sa.CheckConstraint('current_cost IS NULL OR current_cost >= 0', name='ck_boq_analyses_current_cost_non_negative'),
        sa.CheckConstraint("risk_indicator IN ('Low', 'Medium', 'High')", name='ck_boq_analyses_risk_indicator'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_boq_analyses_document_id_documents'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_boq_analyses_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_boq_analyses_user_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_boq_analyses')),
    )
    op.create_index('ix_boq_analyses_project_id', 'boq_analyses', ['project_id'], unique=False)
    op.create_index('ix_boq_analyses_user_id', 'boq_analyses', ['user_id'], unique=False)
    op.create_index('ix_boq_analyses_document_id', 'boq_analyses', ['document_id'], unique=False)

    # -----------------------------------------------------------------------
    # 7. Table: boq_items
    # -----------------------------------------------------------------------
    op.create_table(
        'boq_items',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('analysis_id', sa.Uuid(), nullable=False, comment='Parent BOQ analysis UUID'),
        sa.Column('material_rate_id', sa.Uuid(), nullable=True, comment='Optional matched commodity market quote UUID'),
        sa.Column('phase', sa.String(length=100), nullable=False, comment='Project phase: Substructure, Superstructure, Finishing, MEP, External Works'),
        sa.Column('phase_urdu', sa.String(length=100), nullable=True, comment='Urdu construction phase name'),
        sa.Column('item_code', sa.String(length=50), nullable=True, comment="Schedule line identifier (e.g. '1.02', 'BOQ-STR-04')"),
        sa.Column('description', sa.Text(), nullable=False, comment='Full engineering description of works / materials'),
        sa.Column('description_urdu', sa.Text(), nullable=True, comment='Urdu engineering description'),
        sa.Column('spec', sa.String(length=200), nullable=True, comment="Material specification or strength class (e.g. '1:2:4 3000 PSI')"),
        sa.Column('unit', sa.String(length=50), nullable=False, comment='Unit of measurement: cu m, cu ft, ton, sq ft, bag'),
        sa.Column('unit_urdu', sa.String(length=50), nullable=True, comment='Urdu measurement unit'),
        sa.Column('quantity', sa.Numeric(precision=12, scale=3), server_default='0.000', nullable=False, comment='Physical quantity required'),
        sa.Column('boq_base_rate', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False, comment='Contract tender unit rate in PKR'),
        sa.Column('current_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False, comment='Current market unit rate in PKR'),
        sa.Column('budget_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='Authoritative baseline amount (quantity * boq_base_rate)'),
        sa.Column('estimated_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='Current execution cost amount (quantity * current_price)'),
        sa.Column('overrun_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='Projected cost overrun (estimated_amount - budget_amount)'),
        sa.Column('variance_pct', sa.Numeric(precision=6, scale=2), server_default='0.00', nullable=False, comment='Percentage escalation'),
        sa.Column('risk_level', sa.String(length=20), server_default='low', nullable=False, comment='Cost escalation risk level: low, medium, high'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Item creation timestamp'),
        sa.CheckConstraint('quantity >= 0', name='ck_boq_items_quantity_non_negative'),
        sa.CheckConstraint('boq_base_rate >= 0', name='ck_boq_items_boq_base_rate_non_negative'),
        sa.CheckConstraint('current_price >= 0', name='ck_boq_items_current_price_non_negative'),
        sa.CheckConstraint('budget_amount >= 0', name='ck_boq_items_budget_amount_non_negative'),
        sa.CheckConstraint('estimated_amount >= 0', name='ck_boq_items_estimated_amount_non_negative'),
        sa.CheckConstraint("risk_level IN ('low', 'medium', 'high')", name='ck_boq_items_risk_level'),
        sa.ForeignKeyConstraint(['analysis_id'], ['boq_analyses.id'], name=op.f('fk_boq_items_analysis_id_boq_analyses'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_rate_id'], ['material_rates.id'], name=op.f('fk_boq_items_material_rate_id_material_rates'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_boq_items')),
    )
    op.create_index('ix_boq_items_analysis_id', 'boq_items', ['analysis_id'], unique=False)
    op.create_index('ix_boq_items_material_rate_id', 'boq_items', ['material_rate_id'], unique=False)
    op.create_index('ix_boq_items_phase', 'boq_items', ['phase'], unique=False)

    # -----------------------------------------------------------------------
    # 8. Table: reports
    # -----------------------------------------------------------------------
    op.create_table(
        'reports',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Public-facing report code (e.g. RPT-001). Unique per project workspace.'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project workspace UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Author engineer user UUID'),
        sa.Column('compliance_audit_id', sa.Uuid(), nullable=True, comment='Referenced compliance audit UUID'),
        sa.Column('contract_analysis_id', sa.Uuid(), nullable=True, comment='Referenced contract analysis UUID'),
        sa.Column('boq_analysis_id', sa.Uuid(), nullable=True, comment='Referenced BOQ analysis UUID'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='Report domain: compliance, contract, cost, executive_comprehensive'),
        sa.Column('category_label', sa.String(length=100), nullable=False, comment="Human-readable domain label (e.g. 'Structural & Building Code Audit')"),
        sa.Column('title', sa.String(length=255), nullable=False, comment="Report title (e.g. 'Comprehensive Structural Compliance Dossier - Rev 2')"),
        sa.Column('title_urdu', sa.String(length=255), nullable=True, comment='Urdu report title'),
        sa.Column('status', sa.String(length=50), server_default='in_review', nullable=False, comment='Approval / verification state: certified, action_required, overrun_alert, in_review, approved'),
        sa.Column('status_label', sa.String(length=100), nullable=False, comment="Display status label (e.g. 'Action Required - Redesign Egress')"),
        sa.Column('status_label_urdu', sa.String(length=100), nullable=True, comment='Urdu display status label'),
        sa.Column('file_size', sa.String(length=50), server_default='0 MB', nullable=False, comment="Human-readable file size string (e.g. '4.2 MB')"),
        sa.Column('page_count', sa.Integer(), server_default='1', nullable=False, comment='Number of document pages in generated report'),
        sa.Column('author', sa.String(length=150), server_default='TameerAI Engineering Intelligence', nullable=False, comment='Publishing engineering entity or lead engineer name'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='Internal private storage key / path (never exposed directly publicly)'),
        sa.Column('executive_summary', sa.Text(), nullable=False, comment='Executive summary of engineering analysis'),
        sa.Column('executive_summary_urdu', sa.Text(), nullable=True, comment='Urdu executive summary'),
        sa.Column('key_metric', sa.String(length=150), nullable=False, comment="Headline metric (e.g. 'Score: 84% — 3 Critical Non-Compliances', '+18.4% Cost Escalation')"),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Safe structured report metadata (charts, parameter summaries, signature states)'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when report compilation finished'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Record modification timestamp'),
        sa.CheckConstraint("category IN ('compliance', 'contract', 'cost', 'executive_comprehensive')", name='ck_reports_category'),
        sa.CheckConstraint("status IN ('certified', 'action_required', 'overrun_alert', 'in_review', 'approved')", name='ck_reports_status'),
        sa.CheckConstraint('page_count >= 1', name='ck_reports_page_count'),
        sa.CheckConstraint("status NOT IN ('certified', 'approved') OR generated_at IS NOT NULL", name='ck_reports_generation_status'),
        sa.ForeignKeyConstraint(['boq_analysis_id'], ['boq_analyses.id'], name=op.f('fk_reports_boq_analysis_id_boq_analyses'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['compliance_audit_id'], ['compliance_audits.id'], name=op.f('fk_reports_compliance_audit_id_compliance_audits'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contract_analysis_id'], ['contract_analyses.id'], name=op.f('fk_reports_contract_analysis_id_contract_analyses'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_reports_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reports_user_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reports')),
        sa.UniqueConstraint('project_id', 'code', name='uq_reports_project_code'),
    )
    op.create_index('ix_reports_code', 'reports', ['code'], unique=False)
    op.create_index('ix_reports_project_id', 'reports', ['project_id'], unique=False)
    op.create_index('ix_reports_user_id', 'reports', ['user_id'], unique=False)
    op.create_index('ix_reports_compliance_audit_id', 'reports', ['compliance_audit_id'], unique=False)
    op.create_index('ix_reports_contract_analysis_id', 'reports', ['contract_analysis_id'], unique=False)
    op.create_index('ix_reports_boq_analysis_id', 'reports', ['boq_analysis_id'], unique=False)


def downgrade() -> None:
    # Drop tables in exact reverse dependency order
    op.drop_index('ix_reports_boq_analysis_id', table_name='reports')
    op.drop_index('ix_reports_contract_analysis_id', table_name='reports')
    op.drop_index('ix_reports_compliance_audit_id', table_name='reports')
    op.drop_index('ix_reports_user_id', table_name='reports')
    op.drop_index('ix_reports_project_id', table_name='reports')
    op.drop_index('ix_reports_code', table_name='reports')
    op.drop_table('reports')

    op.drop_index('ix_boq_items_phase', table_name='boq_items')
    op.drop_index('ix_boq_items_material_rate_id', table_name='boq_items')
    op.drop_index('ix_boq_items_analysis_id', table_name='boq_items')
    op.drop_table('boq_items')

    op.drop_index('ix_boq_analyses_document_id', table_name='boq_analyses')
    op.drop_index('ix_boq_analyses_user_id', table_name='boq_analyses')
    op.drop_index('ix_boq_analyses_project_id', table_name='boq_analyses')
    op.drop_table('boq_analyses')

    op.drop_index('ix_material_rates_observed_at', table_name='material_rates')
    op.drop_index('ix_material_rates_category', table_name='material_rates')
    op.drop_index('ix_material_rates_city', table_name='material_rates')
    op.drop_table('material_rates')

    op.drop_index('ix_contract_risk_cards_risk_level', table_name='contract_risk_cards')
    op.drop_index('ix_contract_risk_cards_analysis_id', table_name='contract_risk_cards')
    op.drop_index('ix_contract_risk_cards_code', table_name='contract_risk_cards')
    op.drop_table('contract_risk_cards')

    op.drop_index('ix_contract_analyses_document_id', table_name='contract_analyses')
    op.drop_index('ix_contract_analyses_user_id', table_name='contract_analyses')
    op.drop_index('ix_contract_analyses_project_id', table_name='contract_analyses')
    op.drop_table('contract_analyses')

    op.drop_index('ix_compliance_findings_status', table_name='compliance_findings')
    op.drop_index('ix_compliance_findings_category', table_name='compliance_findings')
    op.drop_index('ix_compliance_findings_document_id', table_name='compliance_findings')
    op.drop_index('ix_compliance_findings_project_id', table_name='compliance_findings')
    op.drop_index('ix_compliance_findings_audit_id', table_name='compliance_findings')
    op.drop_index('ix_compliance_findings_code', table_name='compliance_findings')
    op.drop_table('compliance_findings')

    op.drop_index('ix_compliance_audits_document_id', table_name='compliance_audits')
    op.drop_index('ix_compliance_audits_user_id', table_name='compliance_audits')
    op.drop_index('ix_compliance_audits_project_id', table_name='compliance_audits')
    op.drop_table('compliance_audits')

