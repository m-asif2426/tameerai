"""create identity tables (users, user_settings, user_sessions)

Revision ID: 001_identity_tables
Revises: 
Create Date: 2026-11-03 15:55:00.000000

Phase 01C.2 - Identity Models Migration
Defines the relational schema for users, user_settings (strict 1:1), and user_sessions.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_identity_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Table: users
    # -----------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Collision-free UUID primary key'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Unique user login email'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='Bcrypt-hashed password string. Never plaintext.'),
        sa.Column('full_name', sa.String(length=150), nullable=False, comment='Full name of user (matches frontend Profile)'),
        sa.Column('role', sa.String(length=50), server_default='engineer', nullable=False, comment='Professional persona: engineer, contractor, architect, company'),
        sa.Column('company', sa.String(length=150), nullable=True, comment='Company / Engineering consultancy firm name'),
        sa.Column('pec_number', sa.String(length=100), nullable=True, comment='Pakistan Engineering Council (PEC) registration number'),
        sa.Column('phone', sa.String(length=50), nullable=True, comment='Contact phone number (e.g. +92 300 1234567)'),
        sa.Column('city', sa.String(length=100), server_default='Lahore', nullable=False, comment='Primary operating city / municipal jurisdiction'),
        sa.Column('bio', sa.Text(), nullable=True, comment='Professional biographical overview'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Account activation status'),
        sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Email / PEC credentials verification status'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Account creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last profile modification timestamp'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    # Note: In PostgreSQL, uq_users_email automatically provides the unique B-tree index.
    # No redundant create_index on email is needed.

    # -----------------------------------------------------------------------
    # 2. Table: user_settings (Strict 1:1 with users)
    # -----------------------------------------------------------------------
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Primary key'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Foreign key referencing users.id (Strict 1:1)'),
        sa.Column('language', sa.String(length=10), server_default='en', nullable=False, comment="Preferred UI language: 'en' or 'ur'"),
        sa.Column('theme', sa.String(length=10), server_default='system', nullable=False, comment="Preferred UI theme: 'light', 'dark', 'system'"),
        sa.Column('pbc_violations_alert', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Alert on Pakistan Building Code violations'),
        sa.Column('fidic_risks_alert', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Alert on FIDIC contractual liabilities'),
        sa.Column('price_spikes_alert', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Alert on construction material price fluctuations'),
        sa.Column('weekly_digest_alert', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Receive weekly compliance summary digest'),
        sa.Column('whatsapp_alerts', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Receive critical site alerts via WhatsApp'),
        sa.Column('ai_strictness', sa.String(length=20), server_default='strict', nullable=False, comment="AI compliance strictness: 'strict' or 'consultative'"),
        sa.Column('fidic_threshold', sa.String(length=5), server_default='8', nullable=False, comment="FIDIC risk scoring threshold: '6', '8', '9'"),
        sa.Column('auto_citations', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='Automatically attach legal/code citations in AI answers'),
        sa.Column('market_region', sa.String(length=50), server_default='lahore', nullable=False, comment="Commodity price reference market: 'lahore', 'karachi', 'islamabad'"),
        sa.Column('ai_tone', sa.String(length=30), server_default='professional', nullable=False, comment="AI response tone: 'professional', 'practical', 'legal'"),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Settings record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Settings modification timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_settings_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_settings')),
        sa.UniqueConstraint('user_id', name='uq_user_settings_user_id'),
    )
    # Note: In PostgreSQL, uq_user_settings_user_id automatically provides the unique B-tree index.
    # No redundant create_index on user_id is needed.

    # -----------------------------------------------------------------------
    # 3. Table: user_sessions (Active logins & hashed token identifiers)
    # -----------------------------------------------------------------------
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False, comment='Session UUID primary key'),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Foreign key referencing users.id'),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=False, comment='Cryptographic hash of refresh token. Raw token is never stored.'),
        sa.Column('device_info', sa.String(length=255), nullable=True, comment="Client device / browser string (e.g. 'Chrome 128 on Windows 11')"),
        sa.Column('ip_address', sa.String(length=50), nullable=True, comment='Client IP address at session initiation'),
        sa.Column('location', sa.String(length=100), nullable=True, comment="Estimated geographic location (e.g. 'Lahore, Pakistan')"),
        sa.Column('is_revoked', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='Revocation flag for instant logout / session invalidation'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Refresh token expiration timestamp'),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Timestamp of latest activity'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Session creation timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_sessions')),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'], unique=False)
    op.create_index('ix_user_sessions_refresh_token_hash', 'user_sessions', ['refresh_token_hash'], unique=False)


def downgrade() -> None:
    # Drop tables in exact reverse dependency order
    op.drop_index('ix_user_sessions_refresh_token_hash', table_name='user_sessions')
    op.drop_index('ix_user_sessions_user_id', table_name='user_sessions')
    op.drop_table('user_sessions')

    op.drop_table('user_settings')
    op.drop_table('users')
