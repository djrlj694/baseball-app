-- Enable UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- === Core dimension tables ===

CREATE TABLE IF NOT EXISTS teams (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  city text,
  abbreviation text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, city)
);

CREATE TABLE IF NOT EXISTS players (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  primary_position text NOT NULL,
  -- API doesn't provide a stable ID, so we key by (name, position)
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, primary_position)
);

-- === Games (for future expansion) ===

CREATE TABLE IF NOT EXISTS games (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  game_date date NOT NULL,
  venue text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS game_teams (
  game_id uuid NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  team_id uuid NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
  is_home boolean NOT NULL,
  runs integer,
  PRIMARY KEY (game_id, team_id),
  UNIQUE (game_id, is_home)
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

-- Future: per-game stats if you later ingest game logs
CREATE TABLE IF NOT EXISTS player_game_batting (
  game_id uuid NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  player_id uuid NOT NULL REFERENCES players(id) ON DELETE CASCADE,
  team_id uuid REFERENCES teams(id) ON DELETE SET NULL,

  at_bats integer,
  runs integer,
  hits integer,
  doubles integer,
  triples integer,
  home_runs integer,
  rbi integer,
  walks integer,
  strikeouts integer,
  stolen_bases integer,
  caught_stealing integer,

  PRIMARY KEY (game_id, player_id)
);

CREATE INDEX IF NOT EXISTS ix_players_name ON players (name);
CREATE INDEX IF NOT EXISTS ix_games_date ON games (game_date);
