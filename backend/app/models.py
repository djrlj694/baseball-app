from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class BaseballSnapshot(Base):
    __tablename__ = "baseball_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str | None] = mapped_column(Text)
    abbreviation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    primary_position: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    career_batting: Mapped["PlayerCareerBatting"] = relationship(
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_date: Mapped[date] = mapped_column(Date, nullable=False)
    venue: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class GameTeam(Base):
    __tablename__ = "game_teams"

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    is_home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    runs: Mapped[int | None] = mapped_column(Integer)


class PlayerCareerBatting(Base):
    __tablename__ = "player_career_batting"

    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    )

    games: Mapped[int] = mapped_column(Integer, nullable=False)
    at_bats: Mapped[int] = mapped_column(Integer, nullable=False)
    runs: Mapped[int] = mapped_column(Integer, nullable=False)
    hits: Mapped[int] = mapped_column(Integer, nullable=False)
    doubles: Mapped[int] = mapped_column(Integer, nullable=False)
    triples: Mapped[int] = mapped_column(Integer, nullable=False)
    home_runs: Mapped[int] = mapped_column(Integer, nullable=False)
    rbi: Mapped[int] = mapped_column(Integer, nullable=False)
    walks: Mapped[int] = mapped_column(Integer, nullable=False)
    strikeouts: Mapped[int] = mapped_column(Integer, nullable=False)
    stolen_bases: Mapped[int] = mapped_column(Integer, nullable=False)
    caught_stealing: Mapped[int | None] = mapped_column(Integer)

    avg: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    obp: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    slg: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    ops: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    player: Mapped[Player] = relationship(back_populates="career_batting")


class PlayerGameBatting(Base):
    __tablename__ = "player_game_batting"

    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
    )

    at_bats: Mapped[int | None] = mapped_column(Integer)
    runs: Mapped[int | None] = mapped_column(Integer)
    hits: Mapped[int | None] = mapped_column(Integer)
    doubles: Mapped[int | None] = mapped_column(Integer)
    triples: Mapped[int | None] = mapped_column(Integer)
    home_runs: Mapped[int | None] = mapped_column(Integer)
    rbi: Mapped[int | None] = mapped_column(Integer)
    walks: Mapped[int | None] = mapped_column(Integer)
    strikeouts: Mapped[int | None] = mapped_column(Integer)
    stolen_bases: Mapped[int | None] = mapped_column(Integer)
    caught_stealing: Mapped[int | None] = mapped_column(Integer)
