from __future__ import annotations

from dataclasses import field

from datetime import datetime, timezone
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

from app.services.spotify.types import SpotifySong


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    songs: Mapped[list[SpotifySong]] = mapped_column(JSON, default=field(default_factory=list))
    contract_count: Mapped[int] = mapped_column(default=0)