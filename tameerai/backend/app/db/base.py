from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared SQLAlchemy Declarative Base.
    All future ORM models (users, projects, documents, etc.) will inherit from this base.
    Alembic migrations use Base.metadata as target_metadata.
    """
    pass

