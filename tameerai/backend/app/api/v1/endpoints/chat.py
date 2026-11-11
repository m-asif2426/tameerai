"""
TameerAI - Chat & Message History API Endpoints (Phase 02F)

Provides authenticated endpoints for:
- Chat session lifecycle management (POST, GET, PATCH)
- Dialogue turn message management (GET, POST)
- Concurrency-safe sequence number allocation
- Strict message role provenance (preventing assistant / system forging)
- Project workspace isolation and active collaborator access enforcement
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionRead,
    ChatSessionUpdate,
    ChatTurnResponse,
)
from app.services import chat_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------

@router.post(
    "/sessions",
    response_model=ChatSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Chat Session",
    description="Initiates a new conversation thread owned by the authenticated user. Optionally scoped to a project workspace.",
)
async def create_session(
    payload: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionRead:
    session = await chat_service.create_chat_session(
        db=db,
        user_id=current_user.id,
        data=payload,
    )
    return ChatSessionRead.model_validate(session)


@router.get(
    "/sessions",
    response_model=List[ChatSessionRead],
    status_code=status.HTTP_200_OK,
    summary="List Chat Sessions",
    description="Retrieves a paginated list of chat sessions owned by the authenticated user, ordered by recent activity.",
)
async def list_sessions(
    project_id: Optional[UUID] = Query(default=None, alias="projectId"),
    session_type: Optional[str] = Query(default=None, alias="type"),
    is_archived: Optional[bool] = Query(default=False, alias="isArchived"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatSessionRead]:
    sessions = await chat_service.list_chat_sessions(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        session_type=session_type,
        is_archived=is_archived,
        limit=limit,
        offset=offset,
    )
    return [ChatSessionRead.model_validate(s) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionRead,
    status_code=status.HTTP_200_OK,
    summary="Get Chat Session",
    description="Retrieves metadata for a specific conversation session owned by the caller.",
)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionRead:
    session = await chat_service.get_chat_session(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )
    return ChatSessionRead.model_validate(session)


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionRead,
    status_code=status.HTTP_200_OK,
    summary="Update Chat Session Metadata",
    description="Updates title, language, preview or archive status of an owned chat session. Project association and ownership are immutable.",
)
async def update_session(
    session_id: UUID,
    payload: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionRead:
    session = await chat_service.update_chat_session(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        data=payload,
    )
    return ChatSessionRead.model_validate(session)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_409_CONFLICT,
    summary="Delete Chat Session (Restricted)",
    description="Direct deletion of chat history is blocked under active compliance and retention requirements. Use archiving instead.",
)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Chat session deletion is prohibited under current data retention policies. Conversation threads may be archived via PATCH instead.",
    )


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------

@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[ChatMessageRead],
    status_code=status.HTTP_200_OK,
    summary="List Chat Messages",
    description="Retrieves messages for a conversation session in deterministic chronological sequence.",
)
async def list_messages(
    session_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatMessageRead]:
    messages = await chat_service.list_chat_messages(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        limit=limit,
        offset=offset,
        order=order,
    )
    return [ChatMessageRead.model_validate(m) for m in messages]


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Chat Message",
    description="Submits a new user dialogue turn into the session with concurrency-safe sequence allocation.",
)
async def create_message(
    session_id: UUID,
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageRead:
    message = await chat_service.create_chat_message(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        data=payload,
    )
    return ChatMessageRead.model_validate(message)


@router.post(
    "/sessions/{session_id}/turn",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Conversational Turn",
    description="Submits a user message and returns both the persisted user message and the generated assistant reply with citation auditing.",
)
async def execute_turn(
    session_id: UUID,
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatTurnResponse:
    user_msg, assistant_msg, workflow_resp = await chat_service.execute_chat_turn(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        data=payload,
    )
    return ChatTurnResponse(
        user_message=ChatMessageRead.model_validate(user_msg),
        assistant_message=ChatMessageRead.model_validate(assistant_msg),
        domain_category=str(workflow_resp.domain_category),
        is_off_topic=workflow_resp.is_off_topic,
        is_grounded=workflow_resp.is_grounded,
        disclaimer=workflow_resp.disclaimer,
        latency_ms=workflow_resp.latency_ms,
        telemetry=workflow_resp.telemetry,
    )


