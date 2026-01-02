const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type SortBy = "hits" | "home_runs" | "hits_per_game";

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
  hits_per_game?: number | null;
};

export type Player = {
  id: string;
  name: string;
  primary_position: string;
  career_batting: CareerBatting | null;
};

export type PlayerDetail = Player & {
  description: string;
};

export type PlayerUpdateRequest = {
  name?: string;
  primary_position?: string;
  career_batting?: Partial<CareerBatting>;
};

export type ImportResult = {
  inserted_players: number;
  updated_players: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function importBaseball(): Promise<ImportResult> {
  return request<ImportResult>("/api/import/baseball", { method: "POST" });
}

export function listPlayers(sortBy: SortBy = "hits"): Promise<Player[]> {
  return request<Player[]>(`/api/players?sort_by=${sortBy}`);
}

export function fetchPlayerDetail(playerId: string): Promise<PlayerDetail> {
  return request<PlayerDetail>(`/api/players/${playerId}`);
}

export function updatePlayer(
  playerId: string,
  payload: PlayerUpdateRequest
): Promise<PlayerDetail> {
  return request<PlayerDetail>(`/api/players/${playerId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
