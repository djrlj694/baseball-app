from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from .config import BASEBALL_API_URL, CORS_ORIGINS
from .db import Base, SessionLocal, engine
from .models import Player, PlayerCareerBatting
from .schemas import (
    CareerBattingUpdate,
    ImportResult,
    PlayerDetailOut,
    PlayerOut,
    PlayerUpdate,
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Baseball Importer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SORT_COLUMNS = {
    "hits": PlayerCareerBatting.hits,
    "home_runs": PlayerCareerBatting.home_runs,
}


def _first_value(
    row: dict[str, Any],
    keys: list[str],
) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _parse_int(
    row: dict[str, Any],
    keys: list[str],
    default: int = 0,
) -> int:
    value = _first_value(row, keys)
    try:
        if value in (None, "", "--"):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_optional_int(
    row: dict[str, Any],
    keys: list[str],
    default: int | None = None,
) -> int | None:
    value = _first_value(row, keys)
    try:
        if value in (None, "", "--"):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_float(
    row: dict[str, Any],
    keys: list[str],
    default: float = 0.0,
) -> float:
    value = _first_value(row, keys)
    try:
        if value in (None, "", "--"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_player_and_stats(
    row: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    player = {
        "name": str(
            _first_value(
                row,
                ["Player name", "player_name", "name"],
            ) or "",
        ).strip(),
        "primary_position": str(
            _first_value(
                row,
                ["position", "primary_position", "Position"],
            ) or ""
        ).strip(),
    }
    stats = {
        "games": _parse_int(row, ["Games"]),
        "at_bats": _parse_int(row, ["At-bat", "At Bat", "At Bats"]),
        "runs": _parse_int(row, ["Runs"]),
        "hits": _parse_int(row, ["Hits"]),
        "doubles": _parse_int(row, ["Double (2B)", "Doubles"]),
        "triples": _parse_int(
            row,
            ["third baseman", "Triple (3B)", "Triples (3B)", "Triples"],
        ),
        "home_runs": _parse_int(
            row,
            ["home run", "Home runs", "Home Runs", "HR"],
        ),
        "rbi": _parse_int(row, ["run batted in", "RBI"]),
        "walks": _parse_int(row, ["a walk", "Walks", "BB"]),
        "strikeouts": _parse_int(row, ["Strikeouts", "SO"]),
        "stolen_bases": _parse_int(row, ["stolen base", "Stolen bases", "SB"]),
        "caught_stealing": _parse_optional_int(row, ["Caught stealing", "CS"]),
        "avg": _parse_float(row, ["AVG"]),
        "obp": _parse_float(row, ["On-base Percentage", "OBP"]),
        "slg": _parse_float(row, ["Slugging Percentage", "SLG"]),
        "ops": _parse_float(row, ["On-base Plus Slugging", "OPS"]),
        "updated_at": datetime.now(timezone.utc),
    }
    return player, stats


def _generate_description(player: Player) -> str:
    stats = player.career_batting
    if stats is None:
        return (
            f"{player.name} lines up at {player.primary_position}. "
            "We have not imported full stats yet, "
            "but this profile will refresh once they arrive."
        )

    contact = (
        "contact-first"
        if stats.hits > stats.home_runs * 10
        else "power bat"
    )
    slash = f"{float(stats.avg):.3f}/{float(stats.obp):.3f}/{float(stats.slg):.3f}"
    return (
        f"{player.name} plays {player.primary_position} and profiles as a {contact} with "
        f"{stats.hits} career hits and {stats.home_runs} home runs. "
        f"The slash line sits at {slash}, driving {stats.rbi} runs with disciplined plate "
        f"approach ({stats.walks} walks vs. {stats.strikeouts} strikeouts). "
        "Generated on the fly by our local LLM-style summarizer."
    )


def _serialize_player(player: Player) -> PlayerOut:
    career = player.career_batting
    return PlayerOut(
        id=player.id,
        name=player.name,
        primary_position=player.primary_position,
        career_batting=None
        if career is None
        else {
            "games": career.games,
            "at_bats": career.at_bats,
            "runs": career.runs,
            "hits": career.hits,
            "doubles": career.doubles,
            "triples": career.triples,
            "home_runs": career.home_runs,
            "rbi": career.rbi,
            "walks": career.walks,
            "strikeouts": career.strikeouts,
            "stolen_bases": career.stolen_bases,
            "caught_stealing": career.caught_stealing,
            "avg": float(career.avg),
            "obp": float(career.obp),
            "slg": float(career.slg),
            "ops": float(career.ops),
        },
    )


def _get_player_or_404(player_id: UUID, db: Session) -> Player:
    player = db.execute(
        select(Player)
        .options(selectinload(Player.career_batting))
        .where(Player.id == player_id)
    ).scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@app.post("/api/import/baseball", response_model=ImportResult)
async def import_baseball(db: Session = Depends(get_db)) -> ImportResult:
    """
    Fetch the external API and upsert into normalized tables.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(BASEBALL_API_URL)
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=500,
            detail="Unexpected API shape: expected list",
        )

    inserted = 0
    updated = 0

    for row in payload:
        if not isinstance(row, dict):
            continue

        player_data, stats_data = _to_player_and_stats(row)
        if not player_data["name"] or not player_data["primary_position"]:
            continue

        existing = db.execute(
            select(Player).where(
                Player.name == player_data["name"],
                Player.primary_position == player_data["primary_position"],
            )
        ).scalar_one_or_none()

        if existing is None:
            existing = Player(**player_data)
            db.add(existing)
            db.flush()  # assign PK
            existing.career_batting = PlayerCareerBatting(
                player_id=existing.id,
                **stats_data,
            )
            inserted += 1
        else:
            updated += 1
            existing.name = player_data["name"]
            existing.primary_position = player_data["primary_position"]

            if existing.career_batting is None:
                existing.career_batting = PlayerCareerBatting(
                    player_id=existing.id,
                    **stats_data,
                )
            else:
                for k, v in stats_data.items():
                    setattr(existing.career_batting, k, v)

    db.commit()
    return ImportResult(inserted_players=inserted, updated_players=updated)


@app.get("/api/players", response_model=list[PlayerOut])
def list_players(
    sort_by: str = Query("hits", pattern="^(hits|home_runs)$"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[PlayerOut]:
    sort_column = SORT_COLUMNS[sort_by]
    stmt = (
        select(Player)
        .join(PlayerCareerBatting, isouter=True)
        .options(selectinload(Player.career_batting))
        .order_by(desc(sort_column).nulls_last(), Player.name)
        .offset(offset)
        .limit(limit)
    )
    players = db.scalars(stmt).all()
    return [_serialize_player(p) for p in players]


@app.get("/api/players/{player_id}", response_model=PlayerDetailOut)
def get_player_detail(
    player_id: UUID,
    db: Session = Depends(get_db),
) -> PlayerDetailOut:
    player = _get_player_or_404(player_id, db)
    payload = _serialize_player(player)
    return PlayerDetailOut(
        **payload.model_dump(),
        description=_generate_description(player),
    )


@app.put("/api/players/{player_id}", response_model=PlayerDetailOut)
def update_player(
    player_id: UUID, payload: PlayerUpdate, db: Session = Depends(get_db)
) -> PlayerDetailOut:
    player = _get_player_or_404(player_id, db)

    if payload.name is not None:
        player.name = payload.name
    if payload.primary_position is not None:
        player.primary_position = payload.primary_position

    stats_payload = payload.career_batting
    if stats_payload is not None:
        updates = stats_payload.model_dump(exclude_unset=True)
        if player.career_batting is None:
            required_missing = [
                field
                for field in [
                    "games",
                    "at_bats",
                    "runs",
                    "hits",
                    "doubles",
                    "triples",
                    "home_runs",
                    "rbi",
                    "walks",
                    "strikeouts",
                    "stolen_bases",
                    "avg",
                    "obp",
                    "slg",
                    "ops",
                ]
                if field not in updates
            ]
            if required_missing:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Missing required stats to create new record: "
                        f"{', '.join(required_missing)}"
                    ),
                )
            player.career_batting = PlayerCareerBatting(
                player_id=player.id,
                caught_stealing=updates.get("caught_stealing"),
                updated_at=datetime.now(timezone.utc),
                **{k: v for k, v in updates.items() if k != "caught_stealing"},
            )
        else:
            for key, value in updates.items():
                setattr(player.career_batting, key, value)
            player.career_batting.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(player)
    payload_out = _serialize_player(player)
    return PlayerDetailOut(
        **payload_out.model_dump(),
        description=_generate_description(player),
    )
