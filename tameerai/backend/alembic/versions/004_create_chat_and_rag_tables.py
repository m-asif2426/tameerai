"""create chat history and rag knowledgebase tables (chat_sessions, chat_messages, knowledge_sources, document_chunks)

Revision ID: 004_chat_rag_foundation
Revises: 003_engineering_intelligence_tables
Create Date: 2026-11-03 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '004_chat_rag_foundation'
down_revision: Union[str, None] = '003_engineering_intelligence_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Table: chat_sessions
    # -----------------------------------------------------------------------
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=True, comment='Public-facing session identifier (e.g. session-1, chat-042). Unique per user.'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Owner user UUID who initiated the conversation'),
        sa.Column('project_id', sa.Uuid(), nullable=True, comment='Referenced project workspace UUID (CASCADE purges confidential project chats on project deletion)'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='Session title or headline query topic'),
        sa.Column('title_urdu', sa.String(length=255), nullable=True, comment='Urdu session title or headline query topic'),
        sa.Column('session_type', sa.String(length=50), server_default='general', nullable=False, comment='Consultation domain: code, contract, cost, general'),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False, comment='Preferred consultation language: en (English), ur (Urdu)'),
        sa.Column('preview', sa.String(length=255), nullable=True, comment='Short text preview of most recent message'),
        sa.Column('preview_urdu', sa.String(length=255), nullable=True, comment='Urdu text preview of most recent message'),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Flag indicating whether conversation thread is archived'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Session creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last activity / message timestamp (for recents ordering)'),
        sa.CheckConstraint("session_type IN ('code', 'contract', 'cost', 'general')", name='ck_chat_sessions_session_type'),
        sa.CheckConstraint("language IN ('en', 'ur')", name='ck_chat_sessions_language'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_chat_sessions_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_chat_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_sessions')),
        sa.UniqueConstraint('user_id', 'code', name='uq_chat_sessions_user_code'),
    )
    op.create_index('ix_chat_sessions_code', 'chat_sessions', ['code'], unique=False)
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'], unique=False)
    op.create_index('ix_chat_sessions_project_id', 'chat_sessions', ['project_id'], unique=False)
    op.create_index('ix_chat_sessions_updated_at', 'chat_sessions', ['updated_at'], unique=False)

    # -----------------------------------------------------------------------
    # 2. Table: chat_messages
    # -----------------------------------------------------------------------
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('code', sa.String(length=50), nullable=True, comment='Public-facing message identifier (e.g. msg-171234)'),
        sa.Column('session_id', sa.Uuid(), nullable=False, comment='Parent chat session UUID'),
        sa.Column('sequence_number', sa.Integer(), server_default='0', nullable=False, comment='Monotonic turn counter within session for deterministic pagination and ordering'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='Message participant role: user, assistant, system, tool'),
        sa.Column('content', sa.Text(), nullable=False, comment='Message body in primary language'),
        sa.Column('content_urdu', sa.Text(), nullable=True, comment='Urdu translation or native response content'),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False, comment='Language of current message content: en (English), ur (Urdu)'),
        sa.Column('status', sa.String(length=20), server_default='completed', nullable=False, comment='Message generation status: pending, completed, error'),
        sa.Column('warning_card', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Structured engineering discrepancy / deficit alert card (matches frontend ChatWarningCard)'),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Structured regulatory / contract citations (source doc, clause, page, code)'),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Uploaded reference attachment identifiers or file names'),
        sa.Column('model_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Safe telemetry metadata (model name, token usage, finish reason; strictly no API keys)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Message creation timestamp'),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name='ck_chat_messages_role'),
        sa.CheckConstraint("language IN ('en', 'ur')", name='ck_chat_messages_language'),
        sa.CheckConstraint("status IN ('pending', 'completed', 'error')", name='ck_chat_messages_status'),
        sa.CheckConstraint('sequence_number >= 0', name='ck_chat_messages_sequence_non_negative'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], name=op.f('fk_chat_messages_session_id_chat_sessions'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_messages')),
        sa.UniqueConstraint('session_id', 'sequence_number', name='uq_chat_messages_session_sequence'),
    )
    op.create_index('ix_chat_messages_code', 'chat_messages', ['code'], unique=False)
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'], unique=False)
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'], unique=False)

    # -----------------------------------------------------------------------
    # 3. Table: knowledge_sources
    # -----------------------------------------------------------------------
    op.create_table(
        'knowledge_sources',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='Official title of regulatory codex or engineering standard'),
        sa.Column('title_urdu', sa.String(length=255), nullable=True, comment='Urdu title of regulatory codex or standard'),
        sa.Column('short_code', sa.String(length=50), nullable=False, comment='Unique identifier code (e.g. PBC_2021, LDA_2020, SBCA_2020, FIDIC_RED_2017)'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='Domain category: building_code, planning_regulation, construction_contract_standard, engineering_guideline, other_authorized_reference'),
        sa.Column('authority', sa.String(length=150), nullable=False, comment="Promulgating body (e.g. 'Pakistan Engineering Council', 'Lahore Development Authority', 'SBCA')"),
        sa.Column('edition_year', sa.Integer(), nullable=True, comment='Publication or gazette notification year (e.g. 2021)'),
        sa.Column('version', sa.String(length=50), server_default='1.0', nullable=False, comment='Standard edition version identifier'),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False, comment='Geographic jurisdiction: Federal - Pakistan, Punjab, Sindh, KPK, Balochistan, International'),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False, comment='Primary codex language: en (English), ur (Urdu), mixed'),
        sa.Column('source_url', sa.String(length=500), nullable=True, comment='Official publication URL or regulatory repository link'),
        sa.Column('storage_path', sa.String(length=500), nullable=True, comment='Internal cloud/server storage key for full text PDF'),
        sa.Column('total_pages', sa.Integer(), server_default='0', nullable=False, comment='Total documented pages in source volume'),
        sa.Column('effective_date', sa.Date(), nullable=True, comment='Date when regulation came into legal force'),
        sa.Column('provenance', sa.Text(), nullable=True, comment='Full legal provenance: gazette notification number, publisher details, copyright clearance'),
        sa.Column('is_official_regulatory', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Whether this is an officially approved/promulgated standard (default false until verified)'),
        sa.Column('verification_status', sa.String(length=30), server_default='unverified', nullable=False, comment='Editorial verification state: unverified, verified, deprecated'),
        sa.Column('ingestion_status', sa.String(length=30), server_default='pending', nullable=False, comment='Document parsing & chunking state: pending, processing, completed, failed'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Structured metadata (table of contents, chapter map, amendment history)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Source registration timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Source last modification timestamp'),
        sa.CheckConstraint("category IN ('building_code', 'planning_regulation', 'construction_contract_standard', 'engineering_guideline', 'other_authorized_reference')", name='ck_knowledge_sources_category'),
        sa.CheckConstraint("verification_status IN ('unverified', 'verified', 'deprecated')", name='ck_knowledge_sources_verification_status'),
        sa.CheckConstraint("ingestion_status IN ('pending', 'processing', 'completed', 'failed')", name='ck_knowledge_sources_ingestion_status'),
        sa.CheckConstraint("language IN ('en', 'ur', 'mixed')", name='ck_knowledge_sources_language'),
        sa.CheckConstraint('total_pages >= 0', name='ck_knowledge_sources_total_pages_non_negative'),
        sa.CheckConstraint('edition_year IS NULL OR (edition_year >= 1900 AND edition_year <= 2100)', name='ck_knowledge_sources_edition_year'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_knowledge_sources')),
        sa.UniqueConstraint('short_code', name='uq_knowledge_sources_short_code'),
    )
    op.create_index('ix_knowledge_sources_short_code', 'knowledge_sources', ['short_code'], unique=False)
    op.create_index('ix_knowledge_sources_category', 'knowledge_sources', ['category'], unique=False)
    op.create_index('ix_knowledge_sources_jurisdiction', 'knowledge_sources', ['jurisdiction'], unique=False)
    op.create_index('ix_knowledge_sources_verification_status', 'knowledge_sources', ['verification_status'], unique=False)

    # -----------------------------------------------------------------------
    # 4. Table: document_chunks
    # -----------------------------------------------------------------------
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free internal UUID primary key'),
        sa.Column('knowledge_source_id', sa.Uuid(), nullable=True, comment='Referenced global regulatory source UUID (populated ONLY for public regulatory chunks)'),
        sa.Column('project_id', sa.Uuid(), nullable=True, comment='Referenced private project UUID (populated ONLY for private tenant documents)'),
        sa.Column('document_id', sa.Uuid(), nullable=True, comment='Referenced private document UUID (populated ONLY for private tenant documents)'),
        sa.Column('chunk_index', sa.Integer(), server_default='0', nullable=False, comment='Ordinal position of this chunk within the parent source/document'),
        sa.Column('content', sa.Text(), nullable=False, comment='Passage text extracted for contextual embedding and prompt synthesis'),
        sa.Column('content_urdu', sa.Text(), nullable=True, comment='Urdu translation or native passage text'),
        sa.Column('chapter', sa.String(length=150), nullable=True, comment="Parent chapter name or heading (e.g. 'Chapter 4: Means of Egress')"),
        sa.Column('section', sa.String(length=150), nullable=True, comment="Specific clause or section identifier (e.g. 'Section 4.3.2.1', 'Clause 14.1')"),
        sa.Column('page_number', sa.Integer(), nullable=True, comment='Exact page number in original published volume / PDF document'),
        sa.Column('token_count', sa.Integer(), server_default='0', nullable=False, comment='Computed token count of chunk text'),
        sa.Column('content_hash', sa.String(length=64), nullable=True, comment='SHA-256 hash of chunk content for deduplication and update tracking'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Structured chunk metadata (bounding box coordinates, headings, table cells)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Chunk generation timestamp'),
        sa.CheckConstraint(
            "(knowledge_source_id IS NOT NULL AND project_id IS NULL AND document_id IS NULL) "
            "OR (knowledge_source_id IS NULL AND project_id IS NOT NULL AND document_id IS NOT NULL)",
            name='ck_document_chunks_scope',
        ),
        sa.CheckConstraint('chunk_index >= 0', name='ck_document_chunks_chunk_index_non_negative'),
        sa.CheckConstraint('page_number IS NULL OR page_number >= 1', name='ck_document_chunks_page_number_positive'),
        sa.CheckConstraint('token_count >= 0', name='ck_document_chunks_token_count_non_negative'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document_chunks_document_id_documents'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_source_id'], ['knowledge_sources.id'], name=op.f('fk_document_chunks_knowledge_source_id_knowledge_sources'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_document_chunks_project_id_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document_chunks')),
    )
    op.create_index('ix_document_chunks_knowledge_source_id', 'document_chunks', ['knowledge_source_id'], unique=False)
    op.create_index('ix_document_chunks_project_id', 'document_chunks', ['project_id'], unique=False)
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'], unique=False)
    op.create_index('ix_document_chunks_section', 'document_chunks', ['section'], unique=False)
    op.create_index('ix_document_chunks_content_hash', 'document_chunks', ['content_hash'], unique=False)


def downgrade() -> None:
    # Drop tables in exact reverse dependency order
    op.drop_index('ix_document_chunks_content_hash', table_name='document_chunks')
    op.drop_index('ix_document_chunks_section', table_name='document_chunks')
    op.drop_index('ix_document_chunks_document_id', table_name='document_chunks')
    op.drop_index('ix_document_chunks_project_id', table_name='document_chunks')
    op.drop_index('ix_document_chunks_knowledge_source_id', table_name='document_chunks')
    op.drop_table('document_chunks')

    op.drop_index('ix_knowledge_sources_verification_status', table_name='knowledge_sources')
    op.drop_index('ix_knowledge_sources_jurisdiction', table_name='knowledge_sources')
    op.drop_index('ix_knowledge_sources_category', table_name='knowledge_sources')
    op.drop_index('ix_knowledge_sources_short_code', table_name='knowledge_sources')
    op.drop_table('knowledge_sources')

    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_index('ix_chat_messages_code', table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('ix_chat_sessions_updated_at', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_project_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_code', table_name='chat_sessions')
    op.drop_table('chat_sessions')

