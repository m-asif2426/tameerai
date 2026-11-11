"""create project and document tables (projects, project_members, project_activities, documents)

Revision ID: 002_project_and_document_tables
Revises: 001_identity_tables
Create Date: 2026-11-03 16:45:00.000000

Phase 01C.3 - Project Workspace & Document Models Migration
Defines the relational schema for projects, collaborative membership, activity audit trail, and documents.
Financial representations use authoritative raw PKR (budget_raw, spent_raw NUMERIC(15, 2)) with non-negative checks.
Owner authority is strictly centralized in projects.user_id, with collaborative roles in project_members.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002_project_and_document_tables'
down_revision: Union[str, None] = '001_identity_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Table: projects
    # -----------------------------------------------------------------------
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Public-facing project code (e.g. PRJ-001). Unique per owner.'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Owner user UUID (RESTRICT prevents accidental deletion of active commercial projects)'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='English project name'),
        sa.Column('name_urdu', sa.String(length=200), nullable=True, comment='Urdu project name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Detailed engineering scope / description'),
        sa.Column('location', sa.String(length=255), nullable=False, comment='Site address or sector location'),
        sa.Column('location_urdu', sa.String(length=255), nullable=True, comment='Urdu site location'),
        sa.Column('city', sa.String(length=50), server_default='Lahore', nullable=False, comment='Pakistani city jurisdiction (Lahore, Karachi, Islamabad)'),
        sa.Column('city_urdu', sa.String(length=50), server_default='لاہور', nullable=True, comment='Urdu city label'),
        sa.Column('type', sa.String(length=100), server_default='Commercial', nullable=False, comment='Building typology (e.g. Commercial G+12, Residential Villa)'),
        sa.Column('type_urdu', sa.String(length=100), nullable=True, comment='Urdu building typology'),
        sa.Column('budget_raw', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='Authoritative raw budget in PKR (e.g. 120,000,000.00)'),
        sa.Column('spent_raw', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='Authoritative spent amount in raw PKR'),
        sa.Column('status', sa.String(length=50), server_default='Planning', nullable=False, comment='Lifecycle status: Under Analysis, Active, Planning, Completed'),
        sa.Column('status_urdu', sa.String(length=100), server_default='منصوبہ بندی (Planning)', nullable=True, comment='Urdu status display string'),
        sa.Column('risk', sa.String(length=20), server_default='Low', nullable=False, comment='Overall risk level: Low, Medium, High'),
        sa.Column('risk_urdu', sa.String(length=50), server_default='کم (Low)', nullable=True, comment='Urdu risk display string'),
        sa.Column('compliance_score', sa.Integer(), nullable=True, comment='Current building-code compliance score (0-100 or NULL if unassessed)'),
        sa.Column('floors', sa.Integer(), server_default='1', nullable=False, comment='Number of storeys/floors'),
        sa.Column('area_sqft', sa.String(length=50), server_default='N/A', nullable=False, comment="Total covered area (e.g. '45,000 sq ft')"),
        sa.Column('engineer', sa.String(length=150), nullable=True, comment='Lead engineer or contractor name'),
        sa.Column('governing_authority', sa.String(length=150), nullable=True, comment='Jurisdictional building authority (LDA, CDA, SBCA, etc.)'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='Site mobilization / construction start date'),
        sa.Column('expected_completion_date', sa.Date(), nullable=True, comment='Target handover / completion date'),
        sa.Column('handover_date', sa.String(length=50), nullable=True, comment="Display handover date string (e.g. 'December 2024')"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last modification timestamp'),
        sa.CheckConstraint('budget_raw >= 0', name='ck_projects_budget_raw_non_negative'),
        sa.CheckConstraint('spent_raw >= 0', name='ck_projects_spent_raw_non_negative'),
        sa.CheckConstraint('compliance_score IS NULL OR (compliance_score >= 0 AND compliance_score <= 100)', name='ck_projects_compliance_score_range'),
        sa.CheckConstraint("status IN ('Under Analysis', 'Active', 'Planning', 'Completed')", name='ck_projects_status'),
        sa.CheckConstraint("risk IN ('Low', 'Medium', 'High')", name='ck_projects_risk'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_projects_user_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
        sa.UniqueConstraint('user_id', 'code', name='uq_projects_user_code'),
    )
    op.create_index('ix_projects_code', 'projects', ['code'], unique=False)
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], unique=False)
    op.create_index('ix_projects_city', 'projects', ['city'], unique=False)
    op.create_index('ix_projects_status', 'projects', ['status'], unique=False)

    # -----------------------------------------------------------------------
    # 2. Table: project_members
    # -----------------------------------------------------------------------
    op.create_table(
        'project_members',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Membership record primary key'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Collaborating user UUID'),
        sa.Column('role', sa.String(length=50), server_default='viewer', nullable=False, comment='Workspace role: lead_engineer, architect, contractor, viewer'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Membership grant timestamp'),
        sa.CheckConstraint("role IN ('lead_engineer', 'architect', 'contractor', 'viewer')", name='ck_project_members_role'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_members_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_project_members_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_members')),
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_members_project_user'),
    )
    op.create_index('ix_project_members_project_id', 'project_members', ['project_id'], unique=False)
    op.create_index('ix_project_members_user_id', 'project_members', ['user_id'], unique=False)

    # -----------------------------------------------------------------------
    # 3. Table: project_activities
    # -----------------------------------------------------------------------
    op.create_table(
        'project_activities',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Activity event primary key'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=True, comment='Actor user UUID (SET NULL preserves audit history if user is deleted)'),
        sa.Column('actor_name', sa.String(length=150), nullable=True, comment="Cached actor display name at event occurrence (e.g. 'Engr. Tariq')"),
        sa.Column('action', sa.String(length=255), nullable=False, comment='English action description'),
        sa.Column('action_urdu', sa.String(length=255), nullable=True, comment='Urdu action description'),
        sa.Column('activity_type', sa.String(length=50), server_default='upload', nullable=False, comment='Category: compliance, contract, cost, upload, general'),
        sa.Column('detail', sa.Text(), nullable=True, comment='Detailed activity log or diff snippet'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Safe structured event parameters (never stores credentials or raw binaries)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Event occurrence timestamp'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_activities_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_project_activities_user_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_activities')),
    )
    op.create_index('ix_project_activities_project_id', 'project_activities', ['project_id'], unique=False)
    op.create_index('ix_project_activities_user_id', 'project_activities', ['user_id'], unique=False)

    # -----------------------------------------------------------------------
    # 4. Table: documents
    # -----------------------------------------------------------------------
    op.create_table(
        'documents',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Public document code (e.g. DOC-01). Unique per project workspace.'),
        sa.Column('project_id', sa.Uuid(), nullable=False, comment='Referenced project workspace UUID'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Uploader user UUID (RESTRICT prevents deleting user who authored legal submittals)'),
        sa.Column('name', sa.String(length=255), nullable=False, comment="Original filename (e.g. 'DHA-Plaza-Structural-Drawings-Rev4.dwg')"),
        sa.Column('file_type', sa.String(length=50), nullable=False, comment="Human-readable file type: 'CAD Drawing', 'Architectural Blueprint', 'Legal Contract', etc."),
        sa.Column('document_category', sa.String(length=50), server_default='general_project_document', nullable=False, comment='Standardized domain category: blueprint, building_code, contract, boq, general_project_document'),
        sa.Column('file_size_bytes', sa.BigInteger(), server_default='0', nullable=False, comment='Exact file size in bytes'),
        sa.Column('file_size_human', sa.String(length=30), server_default='0 KB', nullable=False, comment="Human-readable file size string (e.g. '42.5 MB')"),
        sa.Column('storage_path', sa.String(length=500), nullable=False, comment='Internal private storage key / path (never exposed publicly)'),
        sa.Column('mime_type', sa.String(length=100), nullable=True, comment="MIME content type (e.g. 'application/pdf', 'image/vnd.dwg')"),
        sa.Column('status', sa.String(length=50), server_default='Pending Analysis', nullable=False, comment="Review/verification status: 'Verified', 'Review Required', 'Pending Analysis'"),
        sa.Column('analysis_status', sa.String(length=50), server_default='unprocessed', nullable=False, comment="AI analysis pipeline state: 'unprocessed', 'processing', 'completed', 'failed'"),
        sa.Column('uploaded_by', sa.String(length=150), nullable=True, comment="Cached display name of uploader at time of upload (e.g. 'Engr. Tariq')"),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Safe document metadata (e.g. page counts, CAD layer names, sheet dimensions)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Upload creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last status update timestamp'),
        sa.CheckConstraint("document_category IN ('blueprint', 'building_code', 'contract', 'boq', 'general_project_document')", name='ck_documents_category'),
        sa.CheckConstraint("status IN ('Verified', 'Review Required', 'Pending Analysis')", name='ck_documents_status'),
        sa.CheckConstraint("analysis_status IN ('unprocessed', 'processing', 'completed', 'failed')", name='ck_documents_analysis_status'),
        sa.CheckConstraint('file_size_bytes >= 0', name='ck_documents_file_size_bytes'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_documents_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_documents_user_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_documents')),
        sa.UniqueConstraint('project_id', 'code', name='uq_documents_project_code'),
    )
    op.create_index('ix_documents_code', 'documents', ['code'], unique=False)
    op.create_index('ix_documents_project_id', 'documents', ['project_id'], unique=False)
    op.create_index('ix_documents_user_id', 'documents', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in exact reverse dependency order
    op.drop_index('ix_documents_user_id', table_name='documents')
    op.drop_index('ix_documents_project_id', table_name='documents')
    op.drop_index('ix_documents_code', table_name='documents')
    op.drop_table('documents')

    op.drop_index('ix_project_activities_user_id', table_name='project_activities')
    op.drop_index('ix_project_activities_project_id', table_name='project_activities')
    op.drop_table('project_activities')

    op.drop_index('ix_project_members_user_id', table_name='project_members')
    op.drop_index('ix_project_members_project_id', table_name='project_members')
    op.drop_table('project_members')

    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_city', table_name='projects')
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_index('ix_projects_code', table_name='projects')
    op.drop_table('projects')
