-- Enable UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- === Core dimension tables ===

CREATE TABLE IF NOT EXISTS players (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  primary_position text NOT NULL,
  -- API doesn't provide a stable ID, so we key by (name, position)
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, primary_position)
);

-- === Player stats ===
-- What your API provides today: career totals (not per-game).
CREATE TABLE IF NOT EXISTS player_career_batting (
  player_id uuid PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,

  games integer NOT NULL,
  at_bats integer NOT NULL,
  runs integer NOT NULL,
  hits integer NOT NULL,
  doubles integer NOT NULL,
  triples integer NOT NULL,
  home_runs integer NOT NULL,
  rbi integer NOT NULL,
  walks integer NOT NULL,
  strikeouts integer NOT NULL,
  stolen_bases integer NOT NULL,
  caught_stealing integer,

  avg numeric(5,3) NOT NULL,
  obp numeric(5,3) NOT NULL,
  slg numeric(5,3) NOT NULL,
  ops numeric(5,3) NOT NULL,

  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_players_name ON players (name);
