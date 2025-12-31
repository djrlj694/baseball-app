# Baseball App (React + FastAPI + Postgres)

A beginner-friendly full-stack app that imports baseball player career batting stats from an external API and stores them in a normalized Postgres schema. The UI displays the imported players and key stats in a typed table.

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

- Import baseball data from the external API into Postgres (upsert)
- Normalized schema with typed fields (players + career batting stats)
- Simple UI to trigger import and view results
- Docker Compose for one-command local setup

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
