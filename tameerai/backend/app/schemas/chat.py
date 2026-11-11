"""
TameerAI - Conversational AI Assistant Pydantic Schemas (Phase 01C.5)

Defines Pydantic v2 schemas for ChatSession and ChatMessage.
Ensures full compatibility with frontend TypeScript contracts (src/types/chat.ts),
supporting camelCase aliases, structured citation metadata, and engineering discrepancy warning cards.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums matching frontend chat contracts
# ---------------------------------------------------------------------------

class ChatSessionTypeEnum(str, Enum):
    CODE = "code"
    CONTRACT = "contract"
    COST = "cost"
    GENERAL = "general"


class ChatRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatLanguageEnum(str, Enum):
    EN = "en"
    UR = "ur"


class ChatMessageStatusEnum(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Citation & Warning Card Schemas
# ---------------------------------------------------------------------------

class ChatCitationSchema(BaseModel):
    """Structured citation referencing a regulatory clause or contract section."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(description="Document or standard code (e.g. 'PBC 2021', 'FIDIC-17')")
    clause: str = Field(description="Clause or section identifier (e.g. '4.3.2.1', '14.1')")
    doc_id: Optional[str] = Field(default=None, alias="docId", description="Referenced document UUID or code")
    page: Optional[int] = Field(default=None, description="Exact page number within source document")
    source_title: Optional[str] = Field(default=None, alias="sourceTitle", description="Official title of cited source")
    knowledge_source_id: Optional[str] = Field(default=None, alias="knowledgeSourceId", description="Referenced knowledge source UUID")
    chunk_id: Optional[str] = Field(default=None, alias="chunkId", description="Supporting chunk UUID")


class ChatWarningCardSchema(BaseModel):
    """Detailed engineering deficit card for non-compliance alerts."""
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(description="Warning card headline")
    title_urdu: Optional[str] = Field(default=None, alias="titleUrdu", description="Urdu headline")
    reference_code: str = Field(alias="referenceCode", description="Regulatory codex reference (e.g. 'PBC 2021')")
    reference_section: str = Field(alias="referenceSection", description="Section or rule clause")
    reference_page: Optional[int] = Field(default=None, alias="referencePage", description="Source page number")
    current_value: str = Field(alias="currentValue", description="Observed metric from drawing or schedule")
    required_value: str = Field(alias="requiredValue", description="Mandated metric from codex")
    deficit: str = Field(description="Quantified shortfall or deviation")
    recommendation: str = Field(description="Actionable remediation recommendation")
    recommendation_urdu: Optional[str] = Field(default=None, alias="recommendationUrdu", description="Urdu remediation recommendation")
    detailed_notes: List[str] = Field(default_factory=list, alias="detailedNotes", description="Supporting engineering observations")


# ---------------------------------------------------------------------------
# ChatMessage Schemas
# ---------------------------------------------------------------------------

class ChatMessageBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    role: ChatRoleEnum = Field(default=ChatRoleEnum.USER, description="Participant role: user, assistant, system, tool")
    content: str = Field(min_length=1, description="Message body in primary language")
    content_urdu: Optional[str] = Field(default=None, alias="contentUrdu", description="Urdu translation or native response content")
    language: ChatLanguageEnum = Field(default=ChatLanguageEnum.EN, description="Message language: en, ur")


class ChatMessageCreate(ChatMessageBase):
    code: Optional[str] = Field(default=None, description="Optional client-assigned message tracking identifier")
    warning_card: Optional[ChatWarningCardSchema] = Field(default=None, alias="warningCard", description="Optional structured warning card")
    citations: Optional[List[ChatCitationSchema]] = Field(default=None, description="Structured citation references")
    attachments: Optional[List[str]] = Field(default=None, description="Attached file or document identifiers")


class ChatMessageRead(ChatMessageBase):
    id: UUID
    session_id: UUID = Field(alias="sessionId")
    code: Optional[str] = None
    sequence_number: int = Field(alias="sequenceNumber")
    status: ChatMessageStatusEnum = ChatMessageStatusEnum.COMPLETED
    warning_card: Optional[Dict[str, Any]] = Field(default=None, alias="warningCard")
    citations: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[str]] = None
    created_at: datetime = Field(alias="createdAt")

    @property
    def timestamp(self) -> str:
        """Frontend timestamp compatibility property."""
        return self.created_at.isoformat()


# ---------------------------------------------------------------------------
# ChatSession Schemas
# ---------------------------------------------------------------------------

class ChatSessionBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    title: str = Field(min_length=1, max_length=255, description="Conversation session title")
    title_urdu: Optional[str] = Field(default=None, max_length=255, alias="titleUrdu", description="Urdu session title")
    session_type: ChatSessionTypeEnum = Field(
        default=ChatSessionTypeEnum.GENERAL,
        alias="type",
        description="Session domain: code, contract, cost, general",
    )
    language: ChatLanguageEnum = Field(default=ChatLanguageEnum.EN, description="Preferred language: en, ur")


class ChatSessionCreate(ChatSessionBase):
    code: Optional[str] = Field(default=None, description="Optional public session code (e.g. session-1)")
    project_id: Optional[UUID] = Field(default=None, alias="projectId", description="Optional parent project UUID")


class ChatSessionUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    title_urdu: Optional[str] = Field(default=None, max_length=255, alias="titleUrdu")
    session_type: Optional[ChatSessionTypeEnum] = Field(default=None, alias="type")
    language: Optional[ChatLanguageEnum] = None
    preview: Optional[str] = Field(default=None, max_length=255)
    preview_urdu: Optional[str] = Field(default=None, max_length=255, alias="previewUrdu")
    is_archived: Optional[bool] = Field(default=None, alias="isArchived")


class ChatSessionRead(ChatSessionBase):
    id: UUID
    code: Optional[str] = None
    user_id: UUID = Field(alias="userId")
    project_id: Optional[UUID] = Field(default=None, alias="projectId")
    preview: Optional[str] = None
    preview_urdu: Optional[str] = Field(default=None, alias="previewUrdu")
    is_archived: bool = Field(default=False, alias="isArchived")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @property
    def timestamp(self) -> str:
        """Frontend timestamp compatibility property."""
        return self.updated_at.isoformat()


# ---------------------------------------------------------------------------
# Integrated Conversational Turn Schemas (Phase 03E)
# ---------------------------------------------------------------------------

class ChatTurnResponse(BaseModel):
    """
    Integrated response from an executed conversational turn.
    Returns the persisted user message, the persisted assistant message,
    and the domain evaluation telemetry.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    user_message: ChatMessageRead = Field(alias="userMessage")
    assistant_message: ChatMessageRead = Field(alias="assistantMessage")
    domain_category: str = Field(alias="domainCategory")
    is_off_topic: bool = Field(alias="isOffTopic")
    is_grounded: bool = Field(alias="isGrounded")
    disclaimer: str
    latency_ms: float = Field(alias="latencyMs")
    telemetry: Dict[str, Any] = Field(default_factory=dict)


