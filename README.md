# Baseball App (React + FastAPI + Postgres)

A beginner-friendly full-stack app that imports baseball player career batting stats from an
external API and stores them in a normalized Postgres schema. The UI displays the imported players
and key stats in a typed table.

- [Baseball App (React + FastAPI + Postgres)](#baseball-app-react--fastapi--postgres)
  - [Tech Stack](#tech-stack)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Running the App (Frontend, Backend, Database)](#running-the-app-frontend-backend-database)
    - [Prepare the Database](#prepare-the-database)
    - [Start All Services](#start-all-services)
    - [Stop All Services](#stop-all-services)

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
