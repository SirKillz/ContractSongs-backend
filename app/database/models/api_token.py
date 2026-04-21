from __future__ import annotations

from datetime import datetime, UTC
from typing import TYPE_CHECKING

# SQLAlchemy Common Column Types
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Float,
    Numeric,
    Text,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session_factory import Base


class SpotifyApiTokens(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_token: Mapped[str] = mapped_column(Text)
    token_type: Mapped[str] = mapped_column(String(20))
    scope: Mapped[str] = mapped_column(String(255))
    access_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_token: Mapped[str] = mapped_column(Text)