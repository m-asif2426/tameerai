"""
TameerAI - Conversational AI Assistant Service Layer (Phase 02F)

Implements business logic for:
- Chat session lifecycle (creation, retrieval, update, listing, archiving)
- Tenant and project workspace RBAC enforcement
- Revoked project collaborator access termination
- Concurrency-safe message sequence allocation using SELECT FOR UPDATE
- Strict participant role enforcement (preventing client-side assistant/system forgery)
- Stable pagination and chronological ordering
- Retention preservation (no destructive public DELETE endpoints)
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.identifiers import is_valid_session_code
from app.core.security_redaction import sanitize_sensitive_details
from app.ai.contracts.provider import (
    AIConfigurationError,
    AIError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
)
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.models.knowledge import DocumentChunk
from app.models.project import Project, ProjectMember
from app.schemas.chat import (
    ChatLanguageEnum,
    ChatMessageCreate,
    ChatRoleEnum,
    ChatSessionCreate,
    ChatSessionTypeEnum,
    ChatSessionUpdate,
)
from app.services.project_service import get_user_project_role

logger = logging.getLogger("tameerai.chat_service")


# ---------------------------------------------------------------------------
# Project Access Helper
# ---------------------------------------------------------------------------

async def verify_project_chat_access(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    is_existing_session: bool = False,
) -> Project:
    """
    Verifies that the specified project exists and that the user is an active
    owner or collaborator. If the user was removed from an existing project session,
    HTTP 403 Access Revoked is returned. If an unauthorized user attempts to link
    to an unassociated project, HTTP 404 Not Found is returned (anti-enumeration).
    """
    project = await db.scalar(select(Project).where(Project.id == project_id))
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access.",
        )

    role = await get_user_project_role(db, project, user_id)
    if role is None:
        if is_existing_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access revoked. You are no longer an active member or owner of this project.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have access.",
        )

    return project


# ---------------------------------------------------------------------------
# Chat Session Management
# ---------------------------------------------------------------------------

async def list_chat_sessions(
    db: AsyncSession,
    user_id: UUID,
    project_id: Optional[UUID] = None,
    session_type: Optional[str] = None,
    is_archived: Optional[bool] = False,
    limit: int = 20,
    offset: int = 0,
) -> List[ChatSession]:
    """
    Lists conversation threads owned by the authenticated user.
    If filtered by project_id, verifies active project access first.
    Orders by recents (updated_at DESC, created_at DESC).
    """
    if project_id is not None:
        await verify_project_chat_access(db, project_id, user_id)

    stmt = select(ChatSession).where(ChatSession.user_id == user_id)

    if project_id is not None:
        stmt = stmt.where(ChatSession.project_id == project_id)
    else:
        # If project_id is not explicitly filtered, hide any project-linked sessions
        # where the user is no longer an active owner or member of that project.
        # Personal/general sessions (project_id IS NULL) remain fully accessible.
        active_projects_subquery = (
            select(Project.id).where(Project.user_id == user_id)
            .union(
                select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
            )
        )
        stmt = stmt.where(
            or_(
                ChatSession.project_id.is_(None),
                ChatSession.project_id.in_(active_projects_subquery),
            )
        )

    if session_type is not None:
        stmt = stmt.where(ChatSession.session_type == session_type)
    if is_archived is not None:
        stmt = stmt.where(ChatSession.is_archived == is_archived)

    stmt = stmt.order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc(), ChatSession.id.desc())
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_chat_session(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
) -> ChatSession:
    """
    Retrieves a single conversation thread owned by the authenticated user.
    Enforces tenant isolation and active project collaborator authorization.
    """
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    # If scoped to a project, confirm caller retains active project membership
    if session.project_id is not None:
        await verify_project_chat_access(db, session.project_id, user_id, is_existing_session=True)

    return session


async def create_chat_session(
    db: AsyncSession,
    user_id: UUID,
    data: ChatSessionCreate,
) -> ChatSession:
    """
    Creates a new conversation session owned by the authenticated user.
    Optionally scopes to a verified project workspace.
    """
    clean_title = data.title.strip() if data.title else ""
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Session title cannot be empty.",
        )

    # Validate project linkage if requested
    if data.project_id is not None:
        await verify_project_chat_access(db, data.project_id, user_id)

    # Validate custom code if supplied
    session_code = None
    if data.code:
        clean_code = data.code.strip()
        if not is_valid_session_code(clean_code):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid chat session code format '{data.code}'. Expected alphanumeric identifier.",
            )
        # Verify uniqueness per user
        existing = await db.scalar(
            select(ChatSession.id).where(
                ChatSession.user_id == user_id,
                ChatSession.code == clean_code,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Chat session with code '{clean_code}' already exists in your workspace.",
            )
        session_code = clean_code
    else:
        session_code = f"chat-{uuid.uuid4().hex[:10]}"

    session_type_val = (
        data.session_type.value
        if hasattr(data.session_type, "value")
        else str(data.session_type)
    )
    language_val = (
        data.language.value
        if hasattr(data.language, "value")
        else str(data.language)
    )

    session = ChatSession(
        user_id=user_id,
        project_id=data.project_id,
        title=clean_title,
        title_urdu=data.title_urdu.strip() if data.title_urdu else None,
        session_type=session_type_val,
        language=language_val,
        code=session_code,
        is_archived=False,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info("Created chat session %s for user %s (project: %s)", session.id, user_id, data.project_id)
    return session


async def update_chat_session(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    data: ChatSessionUpdate,
) -> ChatSession:
    """
    Updates editable chat session metadata.
    Prevents modifying user_id or project_id to prevent ownership bypass.
    """
    session = await get_chat_session(db, user_id, session_id)

    if data.title is not None:
        clean_title = data.title.strip()
        if not clean_title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Session title cannot be empty.",
            )
        session.title = clean_title

    if data.title_urdu is not None:
        session.title_urdu = data.title_urdu.strip() if data.title_urdu else None

    if data.session_type is not None:
        session.session_type = (
            data.session_type.value
            if hasattr(data.session_type, "value")
            else str(data.session_type)
        )

    if data.language is not None:
        session.language = (
            data.language.value
            if hasattr(data.language, "value")
            else str(data.language)
        )

    if data.preview is not None:
        session.preview = data.preview.strip()[:255] if data.preview else None

    if data.preview_urdu is not None:
        session.preview_urdu = data.preview_urdu.strip()[:255] if data.preview_urdu else None

    if data.is_archived is not None:
        session.is_archived = data.is_archived

    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    logger.info("Updated chat session %s metadata for user %s", session.id, user_id)
    return session


# ---------------------------------------------------------------------------
# Chat Message Management
# ---------------------------------------------------------------------------

async def list_chat_messages(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    limit: int = 50,
    offset: int = 0,
    order: str = "asc",
) -> List[ChatMessage]:
    """
    Lists messages within a session owned by the caller.
    Supports deterministic sequence ordering ('asc' or 'desc') and pagination.
    """
    # Enforces ownership and active project access
    await get_chat_session(db, user_id, session_id)

    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id)
    if order == "desc":
        stmt = stmt.order_by(ChatMessage.sequence_number.desc())
    else:
        stmt = stmt.order_by(ChatMessage.sequence_number.asc())

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _validate_citations_and_attachments(
    db: AsyncSession,
    project_id: Optional[UUID],
    citations: Optional[List[Any]],
    attachments: Optional[List[str]],
) -> None:
    """Enforces that referenced documents, chunks, and attachments belong to the session's project."""
    if citations:
        for cit in citations:
            if cit.doc_id:
                try:
                    doc_uuid = UUID(cit.doc_id.strip())
                    doc = await db.scalar(select(Document).where(Document.id == doc_uuid))
                    if doc is not None:
                        if project_id is None or doc.project_id != project_id:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Referenced document does not belong to this project or could not be found.",
                            )
                except ValueError:
                    pass
            if cit.chunk_id:
                try:
                    chunk_uuid = UUID(cit.chunk_id.strip())
                    chunk = await db.scalar(select(DocumentChunk).where(DocumentChunk.id == chunk_uuid))
                    if chunk is not None and chunk.project_id is not None:
                        if project_id is None or chunk.project_id != project_id:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Referenced document chunk does not belong to this project or could not be found.",
                            )
                except ValueError:
                    pass

    if attachments:
        for att in attachments:
            if att:
                try:
                    att_uuid = UUID(att.strip())
                    att_doc = await db.scalar(select(Document).where(Document.id == att_uuid))
                    if att_doc is not None:
                        if project_id is None or att_doc.project_id != project_id:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Referenced attachment does not belong to this project or could not be found.",
                            )
                except ValueError:
                    pass


async def _finalize_failed_assistant_message(
    db: AsyncSession,
    session_id: UUID,
    assistant_msg_id: UUID,
    error_content: str,
) -> None:
    """Updates a pending assistant message row to 'error' status with sanitized error description."""
    try:
        asst_stmt = select(ChatMessage).where(ChatMessage.id == assistant_msg_id).with_for_update()
        asst_res = await db.execute(asst_stmt)
        asst = asst_res.scalar_one_or_none()
        if asst is not None:
            asst.status = "error"
            asst.content = sanitize_sensitive_details(error_content)[:500]
            session = await db.scalar(select(ChatSession).where(ChatSession.id == session_id))
            if session:
                session.preview = f"Error: {asst.content[:80]}"
                session.updated_at = datetime.now(timezone.utc)
            await db.commit()
    except Exception as e:
        logger.warning("Failed to record error state for assistant message %s: %s", assistant_msg_id, e)
        await db.rollback()


async def create_chat_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    data: ChatMessageCreate,
) -> ChatMessage:
    """
    Persists a user dialogue turn with concurrency-safe sequence allocation.
    
    Security & Integrity Guarantees:
    1. Rejects forged assistant, system, and tool messages (only 'user' role permitted).
    2. Enforces non-empty content and length ceiling (10,000 characters).
    3. Blocks message submission to archived chat sessions.
    4. Handles client-supplied code for idempotent retries.
    5. Verifies active project collaborator authorization if session is project-scoped.
    6. Validates project document citation boundaries.
    7. Locks parent ChatSession row via SELECT FOR UPDATE to serialize concurrent writes.
    8. Monotonically assigns sequence_number (COALESCE(MAX, -1) + 1).
    9. Atomically updates session preview and updated_at timestamp.
    """
    # 1. Enforce participant role provenance
    req_role = data.role.value if hasattr(data.role, "value") else str(data.role)
    if req_role != ChatRoleEnum.USER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clients are only permitted to submit messages with role 'user'. Assistant, system, and tool roles cannot be forged.",
        )

    # 2. Content validation
    content = data.content.strip() if data.content else ""
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message content cannot be empty.",
        )
    if len(content) > 10000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message content exceeds allowable limit of 10,000 characters.",
        )

    # 3. Lock parent session row to serialize concurrent message insertion
    session_stmt = (
        select(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .with_for_update()
    )
    session_res = await db.execute(session_stmt)
    session = session_res.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    # Block submissions to archived sessions
    if session.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot submit messages to an archived chat session.",
        )

    # 4. Project access validation if session is project-scoped
    if session.project_id is not None:
        await verify_project_chat_access(db, session.project_id, user_id, is_existing_session=True)

    # Idempotency check: if code is provided and already exists, return existing message
    if data.code:
        clean_code = data.code.strip()
        existing = await db.scalar(
            select(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.code == clean_code,
            )
        )
        if existing is not None:
            logger.info("Idempotent replay for message code %s in session %s", clean_code, session_id)
            return existing

    # 5. Citation and attachment document boundaries
    await _validate_citations_and_attachments(db, session.project_id, data.citations, data.attachments)

    # 6. Read next sequence number under the parent row lock
    seq_stmt = (
        select(func.coalesce(func.max(ChatMessage.sequence_number), -1) + 1)
        .where(ChatMessage.session_id == session_id)
    )
    next_seq = (await db.execute(seq_stmt)).scalar_one()

    # 7. Prepare JSON structured components
    warning_card_dict = data.warning_card.model_dump(by_alias=True) if data.warning_card else None
    citations_list = [c.model_dump(by_alias=True) for c in data.citations] if data.citations else None

    language_val = (
        data.language.value
        if hasattr(data.language, "value")
        else str(data.language)
    )

    message = ChatMessage(
        session_id=session.id,
        sequence_number=next_seq,
        code=data.code or f"msg-{uuid.uuid4().hex[:12]}",
        role="user",
        content=content,
        content_urdu=data.content_urdu.strip() if data.content_urdu else None,
        language=language_val,
        status="completed",
        warning_card=warning_card_dict,
        citations=citations_list,
        attachments=data.attachments,
    )
    db.add(message)

    # 8. Atomically update parent session recents preview and timestamp
    session.preview = content[:250]
    if data.content_urdu:
        session.preview_urdu = data.content_urdu.strip()[:250]
    session.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(message)
    logger.info("Persisted user message %s (seq: %d) in chat session %s", message.id, next_seq, session_id)
    return message


# ---------------------------------------------------------------------------
# Integrated Conversational Turn Execution (Phase 03E Stage B1)
# ---------------------------------------------------------------------------

async def execute_chat_turn(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    data: ChatMessageCreate,
    ai_workflow: Optional[Any] = None,
    allow_synthetic: bool = False,
) -> tuple[ChatMessage, ChatMessage, Any]:
    """
    Executes an integrated conversational turn within an authenticated chat session.
    
    Two-Phase Short-Transaction Lifecycle:
    Phase 1 (Short Transaction):
      - Verifies production feature flags.
      - Checks session existence, ownership, and archive status.
      - Verifies active project authorization (anti-enumeration 404, revoked member 403).
      - Checks client-supplied code for duplicate idempotency.
      - Atomically row-locks session, allocates user sequence N and assistant sequence N+1.
      - Persists user message (status='completed') and placeholder assistant message (status='pending').
      - Commits Phase 1, releasing all DB row locks before external LLM call.
      
    Phase 2 (External LLM & Scoped Retrieval):
      - Retrieves recent conversation context without holding locks.
      - Invokes ConstructionChatWorkflow with ConstructionDomainGuard.
      - Zero database row locks are held during slow external LLM or retrieval queries.
      
    Phase 3 (Short Transaction):
      - Re-verifies session and project collaborator access.
      - If access revoked during generation, marks assistant message status='error' and raises 403.
      - On success: updates assistant message to status='completed' with answer, citations, telemetry.
      - On timeout/rate-limit/provider error: marks assistant message status='error' with friendly
        sanitized message and re-raises corresponding HTTP 504 / 429 / 502 exception.
      - On cancellation: marks assistant message status='error' and re-raises CancelledError.
      - Updates session preview and timestamp; commits Phase 3.
    """
    # 1. Feature Flag Protection
    if settings.ENVIRONMENT.lower() == "production" and not settings.ENABLE_AI_FEATURES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI conversational features are disabled in production by configuration.",
        )

    # 2. Content validation
    content = data.content.strip() if data.content else ""
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message content cannot be empty.",
        )
    if len(content) > 10000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Message content exceeds allowable limit of 10,000 characters.",
        )

    # 3. Phase 1 (Short Transaction): Row lock, validation, idempotency, and sequence pre-allocation
    session_stmt = (
        select(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .with_for_update()
    )
    session_res = await db.execute(session_stmt)
    session = session_res.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    if session.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot execute chat turns on an archived chat session.",
        )

    if session.project_id is not None:
        await verify_project_chat_access(db, session.project_id, user_id, is_existing_session=True)

    # Validate citations and attachments against project boundary
    await _validate_citations_and_attachments(db, session.project_id, data.citations, data.attachments)

    # Duplicate / Idempotency check on client-assigned code
    clean_code = data.code.strip() if data.code else None
    if clean_code:
        existing_user_msg = await db.scalar(
            select(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.code == clean_code,
                ChatMessage.role == "user",
            )
        )
        if existing_user_msg is not None:
            existing_asst_msg = await db.scalar(
                select(ChatMessage).where(
                    ChatMessage.session_id == session_id,
                    ChatMessage.sequence_number == existing_user_msg.sequence_number + 1,
                    ChatMessage.role == "assistant",
                )
            )
            if existing_asst_msg is not None and existing_asst_msg.status == "completed":
                from app.ai.workflow.construction_chat import ConstructionChatResponse
                from app.ai.guardrails.domain_guard import DomainCategory
                logger.info("Idempotent replay for completed turn code %s in session %s", clean_code, session_id)
                cached_resp = ConstructionChatResponse(
                    session_id=session_id,
                    query=existing_user_msg.content,
                    detected_language=existing_asst_msg.language or "en",
                    domain_category=DomainCategory.CONSTRUCTION_RELATED,
                    answer=existing_asst_msg.content,
                    answer_urdu=existing_asst_msg.content_urdu,
                    is_off_topic=False,
                    is_grounded=True,
                    citations=existing_asst_msg.citations or [],
                    disclaimer="TameerAI Advisory Output (Cached turn result).",
                    latency_ms=0.0,
                    telemetry={"idempotent_replay": True},
                )
                return existing_user_msg, existing_asst_msg, cached_resp

    # Monotonically allocate user and assistant sequence numbers under the row lock
    seq_stmt = (
        select(func.coalesce(func.max(ChatMessage.sequence_number), -1) + 1)
        .where(ChatMessage.session_id == session_id)
    )
    user_seq = (await db.execute(seq_stmt)).scalar_one()
    assistant_seq = user_seq + 1

    language_val = data.language.value if hasattr(data.language, "value") else str(data.language)
    citations_list = [c.model_dump(by_alias=True) for c in data.citations] if data.citations else None
    warning_card_dict = data.warning_card.model_dump(by_alias=True) if data.warning_card else None

    # Persist user message (status='completed')
    user_message = ChatMessage(
        session_id=session_id,
        sequence_number=user_seq,
        code=clean_code or f"msg-{uuid.uuid4().hex[:12]}",
        role="user",
        content=content,
        content_urdu=data.content_urdu.strip() if data.content_urdu else None,
        language=language_val,
        status="completed",
        warning_card=warning_card_dict,
        citations=citations_list,
        attachments=data.attachments,
    )
    db.add(user_message)

    # Persist placeholder assistant message (status='pending')
    asst_code = f"msg-{uuid.uuid4().hex[:12]}"
    assistant_message = ChatMessage(
        session_id=session_id,
        sequence_number=assistant_seq,
        code=asst_code,
        role="assistant",
        content="",
        content_urdu=None,
        language=session.language,
        status="pending",
        warning_card=None,
        citations=None,
        attachments=None,
    )
    db.add(assistant_message)

    session.preview = content[:250]
    session.updated_at = datetime.now(timezone.utc)

    # Commit Phase 1: RELEASES SESSION ROW LOCK BEFORE CALLING EXTERNAL AI WORKFLOW
    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    # 4. Gathers conversation context preceding this turn
    history_stmt = (
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.sequence_number < user_seq,
        )
        .order_by(ChatMessage.sequence_number.desc())
        .limit(6)
    )
    history_res = await db.execute(history_stmt)
    prior_messages = list(reversed(history_res.scalars().all()))
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
        if m.role in ("user", "assistant") and m.status == "completed" and m.content
    ]

    # Resolve AI workflow
    workflow = ai_workflow
    if workflow is None:
        from app.ai.providers.factory import get_ai_provider
        from app.ai.retrieval.service import ScopedRetrievalService
        from app.ai.workflow.construction_chat import ConstructionChatWorkflow

        retrieval_service = ScopedRetrievalService(session=db)
        ai_provider = get_ai_provider()
        workflow = ConstructionChatWorkflow(
            ai_provider=ai_provider,
            retrieval_service=retrieval_service,
        )

    # 5. Phase 2: Execute slow external LLM workflow (ZERO DATABASE LOCKS HELD)
    workflow_resp = None
    try:
        workflow_resp = await workflow.process_user_query(
            query=user_message.content,
            project_id=session.project_id,
            requesting_user_id=user_id,
            conversation_history=conversation_history,
        )
    except asyncio.CancelledError:
        logger.warning("Turn execution cancelled during generation for session %s", session_id)
        await _finalize_failed_assistant_message(
            db, session_id, assistant_message.id, "Request was cancelled during generation."
        )
        raise
    except AITimeoutError as e:
        sanitized_err = sanitize_sensitive_details(str(e))
        logger.error("AI provider timeout for session %s: %s", session_id, sanitized_err)
        await _finalize_failed_assistant_message(
            db, session_id, assistant_message.id, f"AI service timeout: {sanitized_err}"
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Gemini AI provider request timed out: {sanitized_err}",
        )
    except AIRateLimitError as e:
        sanitized_err = sanitize_sensitive_details(str(e))
        logger.warning("AI rate limit reached for session %s: %s", session_id, sanitized_err)
        await _finalize_failed_assistant_message(
            db, session_id, assistant_message.id, f"Rate limit reached: {sanitized_err}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Gemini AI rate limit reached: {sanitized_err}",
        )
    except Exception as e:
        sanitized_err = sanitize_sensitive_details(str(e))
        logger.error("AI workflow failed for session %s: %s", session_id, sanitized_err)
        await _finalize_failed_assistant_message(
            db, session_id, assistant_message.id, f"Service error: {sanitized_err}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {sanitized_err}",
        )

    # 6. Phase 3 (Short Transaction): Re-validate access, finalize assistant message to 'completed'
    session_stmt = (
        select(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .with_for_update()
    )
    locked_session_res = await db.execute(session_stmt)
    locked_session = locked_session_res.scalar_one_or_none()

    if locked_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session no longer exists.",
        )

    # Re-verify project membership: check if collaborator was revoked during generation
    if locked_session.project_id is not None:
        try:
            await verify_project_chat_access(db, locked_session.project_id, user_id, is_existing_session=True)
        except HTTPException:
            await _finalize_failed_assistant_message(
                db, session_id, assistant_message.id, "Access revoked during generation."
            )
            raise

    asst_stmt = select(ChatMessage).where(ChatMessage.id == assistant_message.id).with_for_update()
    asst_res = await db.execute(asst_stmt)
    asst_row = asst_res.scalar_one()

    asst_row.content = workflow_resp.answer
    asst_row.content_urdu = workflow_resp.answer_urdu
    asst_row.status = "completed"
    asst_row.citations = workflow_resp.citations if workflow_resp.citations else None

    locked_session.preview = workflow_resp.answer[:250]
    locked_session.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(asst_row)

    logger.info(
        "Persisted assistant reply %s (seq: %d) in chat session %s (grounded: %s)",
        asst_row.id,
        assistant_seq,
        session_id,
        workflow_resp.is_grounded,
    )

    return user_message, asst_row, workflow_resp


