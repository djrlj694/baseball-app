# Baseball App (React + FastAPI + Postgres)

A beginner-friendly full-stack app that imports baseball player career batting stats from an
external REST API (i.e., the Fraction test API), stores them in Postgres, and lets you explore them
in a sortable React UI with generated player descriptions and inline editing.

- [Baseball App (React + FastAPI + Postgres)](#baseball-app-react--fastapi--postgres)
  - [Tech Stack](#tech-stack)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Quickstart (Docker)](#quickstart-docker)
  - [Running the App (Frontend, Backend, Database)](#running-the-app-frontend-backend-database)
  - [Usage](#usage)
  - [Configuration](#configuration)
  - [Development](#development)
  - [API Reference](#api-reference)
  - [Database](#database)
  - [Troubleshooting](#troubleshooting)
  - [License](#license)

## Tech Stack

**Frontend**
- React
- Vite
- TypeScript (recommended)

**Backend**
- Python 3.13
- FastAPI
- SQLAlchemy
- httpx

**Database**
- Postgres (Docker)

## Features

- Import players from https://api.hirefraction.com/api/test/baseball into Postgres (upsert).
- Sort roster by hits or home runs.
- Click a player to see an LLM-style generated profile.
- Edit player name/position/stats and persist to Postgres.
- Docker Compose for one-command local setup.



## Project Structure

```text
baseball-app/
  docker-compose.yml
  backend/
    Dockerfile
    requirements.txt
    app/
      config.py
      db.py
      main.py
      models.py
      schemas.py
    sql/
      schema.sql
  frontend/
    Dockerfile
    package.json
    tsconfig.json
    vite.config.js
    src/
      api.ts
      App.tsx
      main.tsx
      App.css
```

## Installation

Clone and install frontend deps:
```sh
git clone <repo> baseball-app
cd baseball-app/frontend
npm install
```
For backend local dev (optional):
```sh
cd ../backend
pip install -r requirements.txt
```

## Prerequisites
| Tool                   | Minimum version | Notes                                 |
| ---------------------- | --------------- | ------------------------------------- |
| Node.js                | 20.x            | Vite dev server and frontend builds   |
| npm                    | 10.x            | Ships with Node 20                    |
| Python                 | 3.13            | FastAPI backend                       |
| Docker                 | 24.x            | Containers for db/backend/frontend    |
| Docker Compose         | v2              | `docker compose ...`                  |
| Postgres client (psql) | 14+             | Optional: manual schema apply         |

## Quickstart (Docker)
From the repo root:
```sh
docker compose up --build
```
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Postgres: localhost:5433 (db/app/app)

Stop:
```sh
docker compose down
```

## Running the App (Frontend, Backend, Database)

### Prepare the Database

1. Make sure Docker is installed and running.
2. In the project root, start the database container:

  ```sh
  docker compose up -d db
  ```

  This will start the Postgres database container and map it to port 5433 on your host.

3. Create the database tables by running (note the port is 5433, not 5432):

  ```sh
  psql "postgresql://app:app@localhost:5433/baseball" -f backend/sql/schema.sql
  ```

  Or, you can run psql inside the running db container:

  ```sh
  docker compose exec db psql -U app -d baseball -f /var/lib/postgresql/data/../schema.sql
  ```

### Start All Services

1. Make sure Docker is installed and running.
2. In the project root, run:

  ```sh
  docker compose up --build
  ```

  This will build and start the database, backend, and frontend containers. The backend and frontend
  will wait for the database to be healthy before starting.

3. Access the frontend UI at [http://localhost:5173](http://localhost:5173)

  - The backend API will be available at [http://localhost:8000](http://localhost:8000)
  - The Postgres database will be running at port 5433 on your host (localhost:5433)

4. To run commands in a running container (for debugging or manual tasks):

  ```sh
  docker compose exec backend /bin/sh
  docker compose exec frontend /bin/sh
  docker compose exec db psql -U app -d baseball
  ```

### Stop All Services

In the project root, run:

```sh
docker compose down
```

This will stop and remove all containers, networks, and volumes created by Docker Compose. Your
database data will persist in the Docker volume unless you remove it with:

```sh
docker volume rm baseball-app_pgdata
```

## Usage
1) Click **Import latest** to pull the API and populate the DB.
2) Use the **Order players by** dropdown (hits or HR).
3) Click a table row to load the generated description.
4) Press **Edit player**, adjust fields, and **Save player** to persist changes.
5) **Refresh** repulls the ordered list (reflects edits).

## Configuration
Key env vars (see `docker-compose.yml`):
- Backend: `DATABASE_URL`, `BASEBALL_API_URL`, `CORS_ORIGINS` (default allows http://localhost:5173)
- Frontend: `VITE_API_BASE_URL` (default http://localhost:8000)
Quick start for local overrides: copy `backend/.env.example` to `.env` and `frontend/.env.example` to `.env` and adjust as needed.

## Development
Frontend (hot reload):
```sh
cd frontend
npm run dev
```
Backend (reload):
```sh
cd backend
DATABASE_URL="postgresql+psycopg://app:app@localhost:5433/baseball" uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Build frontend:
```sh
npm run build
```

## API Reference
- `POST /api/import/baseball` – import/upsert players.
- `GET /api/players?sort_by=hits|home_runs&limit=200&offset=0` – list players.
- `GET /api/players/{id}` – detail with generated description.
- `PUT /api/players/{id}` – update name/position/stats (partial allowed if stats already exist).

Example update payload:
```json
{
  "name": "Jane Doe",
  "primary_position": "RF",
  "career_batting": { "hits": 120, "home_runs": 18, "avg": 0.284 }
}
```

## Database
Schema lives in `backend/sql/schema.sql`. If running Postgres outside Docker:
```sh
psql "postgresql://app:app@localhost:5433/baseball" -f backend/sql/schema.sql
```

## Testing & Verification
- Frontend build check: `cd frontend && npm run build`
- Backend lint/tests: (add when available; e.g., `pytest`, `ruff`, `black` if configured)
- Manual API sanity: run `docker compose up --build`, then:
  - `curl -X POST http://localhost:8000/api/import/baseball`
  - `curl http://localhost:8000/api/players?sort_by=hits`

## Release / Build Notes
- Production bundle: `cd frontend && npm run build` (preview with `npm run preview`)
- Docker images: `docker compose build` to refresh; tag/push as needed for registries
- Ports in use: frontend 5173, backend 8000, Postgres 5433 (adjust compose/env if they collide)

## Troubleshooting
- Blank page: ensure `frontend/index.html` has `#root` and the dev server is running.
- CORS errors: set `CORS_ORIGINS` to match your frontend origin.
- DB connection issues: confirm Postgres is on port 5433 (per compose) and `DATABASE_URL` matches.
- Import fails: verify `BASEBALL_API_URL` is reachable and not blocked by network policy.
- Ports already in use: change mapped ports in `docker-compose.yml` or adjust Vite/uvicorn flags.
- Re-seed data: rerun import or drop the `pgdata` volume (`docker volume rm baseball-app_pgdata`).

## License
MIT (see LICENSE). Credits to the Fraction test API for sample data.
