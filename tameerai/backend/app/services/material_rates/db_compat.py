"""
TameerAI - Session Compatibility Layer for Material Rate Intelligence Services

Provides unified asynchronous-first database helpers that transparently handle both:
1. SQLAlchemy 2.0 AsyncSession (used by FastAPI routes, async workers, asyncpg)
2. SQLAlchemy 2.0 Session (used by test suites, CLI tools, SQLite sync fixtures)
"""

from typing import Any, List, Optional, Sequence, TypeVar
from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

T = TypeVar("T")


async def db_execute(session: Any, stmt: Any) -> Result:
    """Executes a SQLAlchemy statement against either an AsyncSession or Session."""
    if isinstance(session, AsyncSession):
        return await session.execute(stmt)
    return session.execute(stmt)


async def db_scalar(session: Any, stmt: Any) -> Any:
    """Executes a statement and returns a single scalar result or None."""
    res = await db_execute(session, stmt)
    return res.scalar_one_or_none()


async def db_scalars(session: Any, stmt: Any) -> Sequence[Any]:
    """Executes a statement and returns all matching scalar results."""
    res = await db_execute(session, stmt)
    return res.scalars().all()


async def db_commit(session: Any) -> None:
    """Commits the transaction for either AsyncSession or Session."""
    if isinstance(session, AsyncSession):
        await session.commit()
    else:
        session.commit()


async def db_rollback(session: Any) -> None:
    """Rolls back the transaction for either AsyncSession or Session."""
    if isinstance(session, AsyncSession):
        await session.rollback()
    else:
        session.rollback()


async def db_refresh(session: Any, obj: Any) -> None:
    """Refreshes an object from the database for either AsyncSession or Session."""
    if isinstance(session, AsyncSession):
        await session.refresh(obj)
    else:
        session.refresh(obj)

