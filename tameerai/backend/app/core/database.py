import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

logger = logging.getLogger("tameerai.database")

# Global singleton engine and session factory references
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """
    Returns the singleton asynchronous SQLAlchemy engine.
    Initializes the engine on first call using settings.DATABASE_URL.
    Fails safely if DATABASE_URL is not configured.
    """
    global _engine
    if _engine is not None:
        return _engine

    if not settings.is_database_configured:
        masked_url = settings.get_masked_database_url()
        raise RuntimeError(
            f"Database connection error: DATABASE_URL is not configured. "
            f"Current value: '{masked_url}'. Please configure DATABASE_URL in .env."
        )

    connect_args = {
        "command_timeout": settings.DB_COMMAND_TIMEOUT,
    }

    # Configure SSL for Supabase remote connections if not explicitly specified in URL
    db_url = settings.DATABASE_URL
    if ("supabase.co" in db_url or "supabase.com" in db_url) and "ssl=" not in db_url:
        connect_args["ssl"] = "require"

    try:
        _engine = create_async_engine(
            db_url,
            echo=False,
            hide_parameters=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            connect_args=connect_args,
        )
        logger.info(
            "Initialized asynchronous SQLAlchemy engine for %s",
            settings.get_masked_database_url(),
        )
        return _engine
    except Exception as exc:
        masked = settings.get_masked_database_url()
        logger.error("Failed to initialize database engine for %s: %s", masked, str(exc))
        raise RuntimeError(f"Could not initialize database engine for {masked}: {exc}") from None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Returns the singleton async sessionmaker.
    """
    global _session_factory
    if _session_factory is not None:
        return _session_factory

    engine = get_engine()
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an asynchronous database session.
    Manages session lifecycle, ensures commit on success, rollback on error,
    and guaranteed closure upon request completion.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    """
    Closes all active database connections and disposes the engine.
    Called during application shutdown.
    """
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Disposing database engine connections.")
        await _engine.dispose()
        _engine = None
        _session_factory = None

