const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function getExternalBaseball() {
  const res = await fetch(`${baseUrl}/api/external/baseball`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createSnapshot() {
  const res = await fetch(`${baseUrl}/api/snapshots`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listSnapshots() {
  const res = await fetch(`${baseUrl}/api/snapshots`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getSnapshot(id) {
  const res = await fetch(`${baseUrl}/api/snapshots/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
