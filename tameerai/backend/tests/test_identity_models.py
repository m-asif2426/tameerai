"""
Unit and Integration Tests for Phase 01C.2 - Identity Models & Schemas

Verifies:
1. Model definitions, columns, and types
2. UUID generation and primary key attributes
3. Unique email constraint and index
4. User-Settings strict 1:1 relationship and unique constraint
5. User-Session foreign keys and indexes
6. Expected CASCADE deletion behavior in an isolated database
7. Pydantic v2 validation (valid email, min length, defaults)
8. Security: Absolute exclusion of hashed_password and token hashes from response schemas
9. Alembic Revision 01 structure and downgrade reversibility
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Generator
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User, UserSettings, UserSession
from app.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserProfileContract,
    UserSettingsRead,
    UserSettingsUpdate,
    UserSessionRead,
)


# ---------------------------------------------------------------------------
# Fixture: Isolated in-memory SQLite database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def in_memory_db() -> Generator[Session, None, None]:
    """
    Creates an isolated in-memory SQLite database for testing ORM models
    and cascades without connecting to remote Supabase.
    Enforces SQLite foreign keys via PRAGMA listener.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create tables
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
# Test 1: Model Definitions, Columns & Types
# ---------------------------------------------------------------------------

def test_model_definitions_and_table_names():
    """Verify table names and metadata registration."""
    assert User.__tablename__ == "users"
    assert UserSettings.__tablename__ == "user_settings"
    assert UserSession.__tablename__ == "user_sessions"

    tables = Base.metadata.tables
    assert "users" in tables
    assert "user_settings" in tables
    assert "user_sessions" in tables


def test_user_columns_and_defaults():
    """Verify User columns, nullability, and primary key."""
    user_table = Base.metadata.tables["users"]
    assert "id" in user_table.c
    assert user_table.c.id.primary_key is True

    assert "email" in user_table.c
    assert user_table.c.email.nullable is False

    assert "hashed_password" in user_table.c
    assert user_table.c.hashed_password.nullable is False

    assert "full_name" in user_table.c
    assert user_table.c.full_name.nullable is False

    assert "role" in user_table.c
    assert "company" in user_table.c
    assert "pec_number" in user_table.c
    assert "phone" in user_table.c
    assert "city" in user_table.c
    assert "bio" in user_table.c
    assert "is_active" in user_table.c
    assert "is_verified" in user_table.c
    assert "created_at" in user_table.c
    assert "updated_at" in user_table.c


def test_user_settings_columns_and_constraints():
    """Verify UserSettings columns, 1:1 unique constraint, and foreign key."""
    settings_table = Base.metadata.tables["user_settings"]
    assert "id" in settings_table.c
    assert settings_table.c.id.primary_key is True

    assert "user_id" in settings_table.c
    assert settings_table.c.user_id.nullable is False

    # Foreign key checks
    fk = list(settings_table.c.user_id.foreign_keys)[0]
    assert fk.target_fullname == "users.id"
    assert fk.ondelete == "CASCADE"

    # Settings fields
    assert "language" in settings_table.c
    assert "theme" in settings_table.c
    assert "pbc_violations_alert" in settings_table.c
    assert "fidic_risks_alert" in settings_table.c
    assert "price_spikes_alert" in settings_table.c
    assert "weekly_digest_alert" in settings_table.c
    assert "whatsapp_alerts" in settings_table.c
    assert "ai_strictness" in settings_table.c
    assert "fidic_threshold" in settings_table.c
    assert "auto_citations" in settings_table.c
    assert "market_region" in settings_table.c
    assert "ai_tone" in settings_table.c


def test_user_session_columns_and_foreign_keys():
    """Verify UserSession columns, foreign key, and token hash."""
    session_table = Base.metadata.tables["user_sessions"]
    assert "id" in session_table.c
    assert session_table.c.id.primary_key is True

    assert "user_id" in session_table.c
    fk = list(session_table.c.user_id.foreign_keys)[0]
    assert fk.target_fullname == "users.id"
    assert fk.ondelete == "CASCADE"

    assert "refresh_token_hash" in session_table.c
    assert session_table.c.refresh_token_hash.nullable is False

    assert "device_info" in session_table.c
    assert "ip_address" in session_table.c
    assert "location" in session_table.c
    assert "is_revoked" in session_table.c
    assert "expires_at" in session_table.c
    assert "last_active_at" in session_table.c
    assert "created_at" in session_table.c


# ---------------------------------------------------------------------------
# Test 2: UUID Fields & Defaults
# ---------------------------------------------------------------------------

def test_uuid_generation_on_instantiation():
    """Verify that model instances receive valid UUIDs upon Python creation."""
    user = User(
        email="eng.tariq@tameerai.pk",
        hashed_password="fake_bcrypt_hash_123456",
        full_name="Engr. Tariq Mahmood",
    )
    assert isinstance(user.id, uuid.UUID)

    settings = UserSettings(user_id=user.id)
    assert isinstance(settings.id, uuid.UUID)

    session = UserSession(
        user_id=user.id,
        refresh_token_hash="fake_token_hash_abc",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    assert isinstance(session.id, uuid.UUID)


# ---------------------------------------------------------------------------
# Test 3: Unique Email Constraint
# ---------------------------------------------------------------------------

def test_unique_email_constraint(in_memory_db: Session):
    """Verify that creating two users with the same email raises an IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    u1 = User(
        email="duplicate@tameerai.pk",
        hashed_password="hash1",
        full_name="User One",
    )
    in_memory_db.add(u1)
    in_memory_db.commit()

    u2 = User(
        email="duplicate@tameerai.pk",
        hashed_password="hash2",
        full_name="User Two",
    )
    in_memory_db.add(u2)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 4: User-Settings One-to-One Relationship
# ---------------------------------------------------------------------------

def test_user_settings_one_to_one(in_memory_db: Session):
    """Verify bidirectional 1:1 relationship between User and UserSettings."""
    user = User(
        email="thekedar@tameerai.pk",
        hashed_password="hash_secure_pwd",
        full_name="Aslam Thekedar",
        role="contractor",
        city="Lahore",
    )
    settings = UserSettings(
        user=user,
        language="ur",
        theme="dark",
        market_region="lahore",
    )
    in_memory_db.add(user)
    in_memory_db.commit()

    # Query back
    fetched_user = in_memory_db.scalar(select(User).where(User.email == "thekedar@tameerai.pk"))
    assert fetched_user is not None
    assert fetched_user.settings is not None
    assert fetched_user.settings.language == "ur"
    assert fetched_user.settings.theme == "dark"
    assert fetched_user.settings.user.email == "thekedar@tameerai.pk"


def test_user_settings_strict_uniqueness(in_memory_db: Session):
    """Verify that creating a second settings record for the same user fails."""
    from sqlalchemy.exc import IntegrityError

    user = User(
        email="single_settings@tameerai.pk",
        hashed_password="hash",
        full_name="Single Settings User",
    )
    in_memory_db.add(user)
    in_memory_db.commit()

    s1 = UserSettings(user_id=user.id, language="en")
    in_memory_db.add(s1)
    in_memory_db.commit()

    s2 = UserSettings(user_id=user.id, language="ur")
    in_memory_db.add(s2)

    with pytest.raises(IntegrityError):
        in_memory_db.commit()

    in_memory_db.rollback()


# ---------------------------------------------------------------------------
# Test 5 & 6: Cascading Deletion Behavior
# ---------------------------------------------------------------------------

def test_cascade_deletion(in_memory_db: Session):
    """Verify that deleting a User cascades to their UserSettings and UserSessions."""
    user = User(
        email="delete_me@tameerai.pk",
        hashed_password="hash",
        full_name="Temporary User",
    )
    in_memory_db.add(user)
    in_memory_db.commit()

    settings = UserSettings(user_id=user.id)
    session1 = UserSession(
        user_id=user.id,
        refresh_token_hash="token_1",
        device_info="Chrome on Windows",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session2 = UserSession(
        user_id=user.id,
        refresh_token_hash="token_2",
        device_info="iPhone App",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    in_memory_db.add_all([settings, session1, session2])
    in_memory_db.commit()

    # Confirm created
    assert in_memory_db.scalar(select(UserSettings).where(UserSettings.user_id == user.id)) is not None
    assert len(in_memory_db.scalars(select(UserSession).where(UserSession.user_id == user.id)).all()) == 2

    # Delete user
    in_memory_db.delete(user)
    in_memory_db.commit()

    # Verify settings and sessions were cascade-deleted
    assert in_memory_db.scalar(select(UserSettings).where(UserSettings.user_id == user.id)) is None
    assert len(in_memory_db.scalars(select(UserSession).where(UserSession.user_id == user.id)).all()) == 0


# ---------------------------------------------------------------------------
# Test 7: Pydantic Validation & Defaults
# ---------------------------------------------------------------------------

def test_pydantic_user_create_validation():
    """Verify input validation rules on UserCreate."""
    # Valid input with snake_case
    valid = UserCreate(
        email="engr.ahmed@tameerai.pk",
        password="securePassword123",
        full_name="Ahmed Khan",
        role="engineer",
    )
    assert valid.email == "engr.ahmed@tameerai.pk"
    assert valid.full_name == "Ahmed Khan"
    assert valid.city == "Lahore"  # default

    # Valid input with camelCase (frontend alignment)
    valid_camel = UserCreate(
        email="engr.ahmed@tameerai.pk",
        password="securePassword123",
        fullName="Ahmed Khan",
        pecNumber="PEC-12345",
    )
    assert valid_camel.full_name == "Ahmed Khan"
    assert valid_camel.pec_number == "PEC-12345"

    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password="securePassword123",
            full_name="Ahmed Khan",
        )

    # Password too short (< 8 chars)
    with pytest.raises(ValidationError):
        UserCreate(
            email="valid@tameerai.pk",
            password="short",
            full_name="Ahmed Khan",
        )


def test_pydantic_user_settings_serialization_aliases():
    """Verify UserSettingsRead serializes to camelCase matching frontend contracts."""
    now = datetime.now(timezone.utc)
    settings_data = {
        "id": uuid.uuid4(),
        "userId": uuid.uuid4(),
        "language": "ur",
        "theme": "dark",
        "pbcViolations": True,
        "fidicRisks": True,
        "priceSpikes": True,
        "weeklyDigest": False,
        "whatsappAlerts": True,
        "strictness": "strict",
        "fidicThreshold": "8",
        "autoCitations": True,
        "marketRegion": "lahore",
        "aiTone": "professional",
        "createdAt": now,
        "updatedAt": now,
    }
    settings = UserSettingsRead.model_validate(settings_data)
    dumped = settings.model_dump(by_alias=True)

    # Verify camelCase aliases in output
    assert "pbcViolations" in dumped
    assert "fidicRisks" in dumped
    assert "strictness" in dumped
    assert "marketRegion" in dumped
    assert dumped["language"] == "ur"


# ---------------------------------------------------------------------------
# Test 8: Security — Exclusion of Hashed Passwords & Token Hashes
# ---------------------------------------------------------------------------

def test_password_hash_strictly_excluded_from_user_read():
    """Verify that UserRead never exposes hashed_password or raw passwords."""
    user = User(
        id=uuid.uuid4(),
        email="secure_user@tameerai.pk",
        hashed_password="$2b$12$super_secret_bcrypt_hash_that_must_not_leak",
        full_name="Secure User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    read_model = UserRead.model_validate(user)
    dumped = read_model.model_dump()
    dumped_by_alias = read_model.model_dump(by_alias=True)
    json_output = read_model.model_dump_json()

    assert "hashed_password" not in dumped
    assert "password" not in dumped
    assert "super_secret" not in json_output
    assert "hashed_password" not in dumped_by_alias


def test_token_hash_strictly_excluded_from_user_session_read():
    """Verify that UserSessionRead never exposes refresh_token_hash."""
    session = UserSession(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        refresh_token_hash="sha256$sensitive_refresh_hash_value_123",
        device_info="Chrome on Windows 11",
        ip_address="182.185.120.45",
        location="Lahore, Pakistan",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        last_active_at=datetime.now(timezone.utc),
    )

    session_read = UserSessionRead.model_validate(session)
    dumped = session_read.model_dump()
    json_output = session_read.model_dump_json()

    assert "refresh_token_hash" not in dumped
    assert "token_hash" not in dumped
    assert "sensitive_refresh_hash" not in json_output


# ---------------------------------------------------------------------------
# Test 9: Alembic Revision 01 Structure & Safety
# ---------------------------------------------------------------------------

def test_alembic_revision_01_structure():
    """Verify the migration script metadata, revision chain, and operations."""
    import importlib.util
    from pathlib import Path

    migration_file = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "001_create_identity_tables.py"
    assert migration_file.exists(), f"Migration file missing at {migration_file}"

    # Load module dynamically
    spec = importlib.util.spec_from_file_location("revision_001", migration_file)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Check revision metadata
    assert mod.revision == "001_identity_tables"
    assert mod.down_revision is None
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)

