"""Declarative base and common mixins.
Import concrete model classes here so Alembic autogenerate can discover them.
"""
from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Central SQLAlchemy 2.0 style declarative base."""
    pass

# Common timestamp columns
CreatedAt = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
]
UpdatedAt = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
]


class TimestampMixin:
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

__all__ = ["Base", "TimestampMixin"]

# Future model imports (uncomment as added):
# from app.models.user import User  # noqa: F401
# from app.models.property import Property  # noqa: F401

from .legacy_models import LegacySystem  # noqa: F401
