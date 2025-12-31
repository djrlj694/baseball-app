from __future__ import annotations

import os


def getenv(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


DATABASE_URL = getenv("DATABASE_URL")
BASEBALL_API_URL = getenv(
    "BASEBALL_API_URL",
    "https://api.hirefraction.com/api/test/baseball",
)
CORS_ORIGINS = [o.strip() for o in getenv("CORS_ORIGINS", "").split(",") if o.strip()]
