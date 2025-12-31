import { useEffect, useMemo, useState } from "react";
import "./App.css";
import {
  createSnapshot,
  getExternalBaseball,
  getSnapshot,
  listSnapshots,
} from "./api";

export default function App() {
  const [liveData, setLiveData] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [error, setError] = useState("");

  const liveJson = useMemo(
    () => (liveData ? JSON.stringify(liveData, null, 2) : ""),
    [liveData]
  );

  const snapshotJson = useMemo(
    () => (selectedSnapshot ? JSON.stringify(selectedSnapshot.payload, null, 2) : ""),
    [selectedSnapshot]
  );

  async function refreshSnapshots() {
    const rows = await listSnapshots();
    setSnapshots(rows);
  }

  async function onFetchLive() {
    setError("");
    try {
      const data = await getExternalBaseball();
      setLiveData(data);
    } catch (e) {
      setError(String(e));
    }
  }

  async function onSaveSnapshot() {
    setError("");
    try {
      await createSnapshot();
      await refreshSnapshots();
    } catch (e) {
      setError(String(e));
    }
  }

  async function onSelectSnapshot(id) {
    setError("");
    try {
      const snap = await getSnapshot(id);
      setSelectedSnapshot(snap);
    } catch (e) {
      setError(String(e));
    }
  }

  useEffect(() => {
    refreshSnapshots().catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>Snapshots</h2>
        <button onClick={refreshSnapshots}>Reload list</button>

        <div className="snapshotList">
          {snapshots.map((s) => (
            <button
              key={s.id}
              className="snapshotItem"
              onClick={() => onSelectSnapshot(s.id)}
              title={s.id}
            >
              {new Date(s.fetched_at).toLocaleString()}
            </button>
          ))}
        </div>
      </aside>

      <main className="main">
        <h1>Baseball Explorer</h1>

        <div className="actions">
          <button onClick={onFetchLive}>Fetch live API data</button>
          <button onClick={onSaveSnapshot}>Save snapshot to Postgres</button>
        </div>

        {error && <div className="error">Error: {error}</div>}

        <section className="panel">
          <h3>Live API response</h3>
          <pre>{liveJson || "Click “Fetch live API data”"}</pre>
        </section>

        <section className="panel">
          <h3>Selected snapshot</h3>
          <pre>{snapshotJson || "Select a snapshot on the left"}</pre>
        </section>
      </main>
    </div>
  );
}
