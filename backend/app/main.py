from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from datetime import timezone
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .config import BASEBALL_API_URL, CORS_ORIGINS
from .db import Base, SessionLocal, engine
from .models import BaseballSnapshot, Player, PlayerCareerBatting
from .schemas import ImportResult, PlayerOut


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Beginner-friendly: create tables automatically.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Baseball Explorer API", lifespan=lifespan)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _int_or_none(value: Any) -> int | None:
    if value in (None, "", "--"):
        return None
    return int(value)


def _to_player_and_stats(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Convert the API's quirky keys into normalized fields.
    The API looks like career totals (not per-game logs).
    """
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
        "triples": int(row["third baseman"]),  # actually 3B (triples)
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not isinstance(payload, list):
        raise HTTPException(status_code=500, detail="Unexpected API shape: expected list")

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
            existing.career_batting = PlayerCareerBatting(player_id=existing.id, **stats_data)
            inserted += 1
        else:
            updated += 1
            existing.name = player_data["name"]
            existing.primary_position = player_data["primary_position"]

            if existing.career_batting is None:
                existing.career_batting = PlayerCareerBatting(player_id=existing.id, **stats_data)
            else:
                for k, v in stats_data.items():
                    setattr(existing.career_batting, k, v)

    db.commit()
    return ImportResult(inserted_players=inserted, updated_players=updated)


@app.get("/api/players", response_model=list[PlayerOut])
def list_players(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)) -> list[PlayerOut]:
    rows = (
        db.execute(
            select(Player)
            .options(joinedload(Player.career_batting))
            .order_by(Player.name.asc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return [
        PlayerOut(
            id=p.id,
            name=p.name,
            primary_position=p.primary_position,
            career_batting=(
                None
                if p.career_batting is None
                else {
                    "games": p.career_batting.games,
                    "at_bats": p.career_batting.at_bats,
                    "runs": p.career_batting.runs,
                    "hits": p.career_batting.hits,
                    "doubles": p.career_batting.doubles,
                    "triples": p.career_batting.triples,
                    "home_runs": p.career_batting.home_runs,
                    "rbi": p.career_batting.rbi,
                    "walks": p.career_batting.walks,
                    "strikeouts": p.career_batting.strikeouts,
                    "stolen_bases": p.career_batting.stolen_bases,
                    "caught_stealing": p.career_batting.caught_stealing,
                    "avg": float(p.career_batting.avg),
                    "obp": float(p.career_batting.obp),
                    "slg": float(p.career_batting.slg),
                    "ops": float(p.career_batting.ops),
                }
            ),
        )
        for p in rows
    ]


@app.post("/api/snapshots")
async def create_snapshot(db: Session = Depends(get_db)) -> dict[str, Any]:
    # Fetch then store in Postgres as JSONB
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(BASEBALL_API_URL)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snap = BaseballSnapshot(payload=data)
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return {"id": str(snap.id), "fetched_at": snap.fetched_at.isoformat()}


@app.get("/api/snapshots")
def list_snapshots(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.execute(select(BaseballSnapshot).order_by(BaseballSnapshot.fetched_at.desc())).scalars().all()
    return [{"id": str(r.id), "fetched_at": r.fetched_at.isoformat()} for r in rows]


@app.get("/api/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(BaseballSnapshot, snapshot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"id": str(row.id), "fetched_at": row.fetched_at.isoformat(), "payload": row.payload}
