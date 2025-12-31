from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import BASEBALL_API_URL
from .db import Base, SessionLocal, engine
from .models import Player, PlayerCareerBatting
from .schemas import ImportResult


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Baseball Importer API")


def _int_or_none(value: Any) -> int | None:
    if value in (None, "", "--"):
        return None
    return int(value)


def _to_player_and_stats(
    row: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    player = {
        "name": str(row["Player name"]).strip(),
        "primary_position": str(row["position"]).strip(),
    }
    stats = {
        "games": int(row["Games"]),
        "at_bats": int(row["At-bat"]),
        "runs": int(row["Runs"]),
        "hits": int(row["Hits"]),
        "doubles": int(row["Double (2B)"]),
        "triples": int(row["third baseman"]),
        "home_runs": int(row["home run"]),
        "rbi": int(row["run batted in"]),
        "walks": int(row["a walk"]),
        "strikeouts": int(row["Strikeouts"]),
        "stolen_bases": int(row["stolen base"]),
        "caught_stealing": _int_or_none(row.get("Caught stealing")),
        "avg": float(row["AVG"]),
        "obp": float(row["On-base Percentage"]),
        "slg": float(row["Slugging Percentage"]),
        "ops": float(row["On-base Plus Slugging"]),
        "updated_at": datetime.now(timezone.utc),
    }
    return player, stats


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
