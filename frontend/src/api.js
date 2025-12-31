const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type CareerBatting = {
  games: number;
  at_bats: number;
  runs: number;
  hits: number;
  doubles: number;
  triples: number;
  home_runs: number;
  rbi: number;
  walks: number;
  strikeouts: number;
  stolen_bases: number;
  caught_stealing: number | null;
  avg: number;
  obp: number;
  slg: number;
  ops: number;
};

export type Player = {
  id: string;
  name: string;
  primary_position: string;
  career_batting: CareerBatting | null;
};

export type ImportResult = {
  inserted_players: number;
  updated_players: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, init);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export function importBaseball(): Promise<ImportResult> {
  return request<ImportResult>("/api/import/baseball", { method: "POST" });
}

export function listPlayers(limit = 200, offset = 0): Promise<Player[]> {
  return request<Player[]>(`/api/players?limit=${limit}&offset=${offset}`);
}
