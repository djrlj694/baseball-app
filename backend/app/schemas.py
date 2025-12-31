from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class CareerBattingOut(BaseModel):
    games: int
    at_bats: int
    runs: int
    hits: int
    doubles: int
    triples: int
    home_runs: int
    rbi: int
    walks: int
    strikeouts: int
    stolen_bases: int
    caught_stealing: int | None

    avg: float = Field(..., ge=0)
    obp: float = Field(..., ge=0)
    slg: float = Field(..., ge=0)
    ops: float = Field(..., ge=0)


class PlayerOut(BaseModel):
    id: UUID
    name: str
    primary_position: str
    career_batting: CareerBattingOut | None


class ImportResult(BaseModel):
    inserted_players: int
    updated_players: int
