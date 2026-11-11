"""
TameerAI - Conversational AI Assistant Database Models (Phase 01C.5)

Defines:
- ChatSession: Conversation thread owned by a user, optionally scoped to a project workspace.
- ChatMessage: Individual dialogue turns with structured citation metadata and warning cards.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project


class ChatSession(Base):
    """
    Conversational AI Thread Model.
    Tracks user conversation sessions, optionally scoped to a project workspace context.
    Supports bilingual engineering consultations (English / Urdu) and topic categorization.
    """

    __tablename__ = "chat_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_chat_sessions_user_code"),
        CheckConstraint(
            "session_type IN ('code', 'contract', 'cost', 'general')",
            name="ck_chat_sessions_session_type",
        ),
        CheckConstraint(
            "language IN ('en', 'ur')",
            name="ck_chat_sessions_language",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Public-facing session identifier (e.g. session-1, chat-042). Unique per user.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user UUID who initiated the conversation",
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Referenced project workspace UUID (CASCADE purges confidential project chats on project deletion)",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Session title or headline query topic",
    )
    title_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu session title or headline query topic",
    )
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="general",
        server_default="general",
        comment="Consultation domain: code, contract, cost, general",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
        comment="Preferred consultation language: en (English), ur (Urdu)",
    )
    preview: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Short text preview of most recent message",
    )
    preview_urdu: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Urdu text preview of most recent message",
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
        comment="Flag indicating whether conversation thread is archived",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        comment="Session creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Last activity / message timestamp (for recents ordering)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_sessions",
    )
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="chat_sessions",
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.sequence_number",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "session_type" not in kwargs:
            kwargs["session_type"] = "general"
        if "language" not in kwargs:
            kwargs["language"] = "en"
        if "is_archived" not in kwargs:
            kwargs["is_archived"] = False
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title='{self.title[:30]}', type='{self.session_type}')>"


class ChatMessage(Base):
    """
    Conversational Message Model.
    Stores individual dialogue turns with support for structured citation references,
    advisory warning cards, attachments, and model provider telemetry.
    """

    __tablename__ = "chat_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_number", name="uq_chat_messages_session_sequence"),
        CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')",
            name="ck_chat_messages_role",
        ),
        CheckConstraint(
            "language IN ('en', 'ur')",
            name="ck_chat_messages_language",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'error')",
            name="ck_chat_messages_status",
        ),
        CheckConstraint(
            "sequence_number >= 0",
            name="ck_chat_messages_sequence_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        comment="Collision-free internal UUID primary key",
    )
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Public-facing message identifier (e.g. msg-171234)",
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent chat session UUID",
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Monotonic turn counter within session for deterministic pagination and ordering",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Message participant role: user, assistant, system, tool",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message body in primary language",
    )
    content_urdu: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Urdu translation or native response content",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        server_default="en",
        comment="Language of current message content: en (English), ur (Urdu)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed",
        server_default="completed",
        comment="Message generation status: pending, completed, error",
    )
    warning_card: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Structured engineering discrepancy / deficit alert card (matches frontend ChatWarningCard)",
    )
    citations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Structured regulatory / contract citations (source doc, clause, page, code)",
    )
    attachments: Mapped[Optional[List[str]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Uploaded reference attachment identifiers or file names",
    )
    model_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        comment="Safe telemetry metadata (model name, token usage, finish reason; strictly no API keys)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
        comment="Message creation timestamp",
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "role" not in kwargs:
            kwargs["role"] = "user"
        if "language" not in kwargs:
            kwargs["language"] = "en"
        if "status" not in kwargs:
            kwargs["status"] = "completed"
        if "sequence_number" not in kwargs:
            kwargs["sequence_number"] = 0
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}', seq={self.sequence_number})>"

