import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { importBaseball, listPlayers, type Player } from "./api";

export default function App() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [error, setError] = useState<string>("");
  const [status, setStatus] = useState<string>("");

  async function refresh() {
    setError("");
    const rows = await listPlayers();
    setPlayers(rows);
  }

  async function onImport() {
    setError("");
    setStatus("Importing...");
    try {
      const r = await importBaseball();
      setStatus(`Imported. inserted=${r.inserted_players}, updated=${r.updated_players}`);
      await refresh();
    } catch (e) {
      setStatus("");
      setError(String(e));
    }
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
  }, []);

  const rows = useMemo(() => players, [players]);

  return (
    <div className="main">
      <h1>Baseball Explorer</h1>

      <div className="actions">
        <button onClick={onImport}>Import from API</button>
        <button onClick={() => refresh()}>Refresh</button>
      </div>

      {status && <div className="status">{status}</div>}
      {error && <div className="error">Error: {error}</div>}

      <div className="panel">
        <h3>Players</h3>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Pos</th>
                <th>G</th>
                <th>AB</th>
                <th>H</th>
                <th>HR</th>
                <th>RBI</th>
                <th>BB</th>
                <th>SO</th>
                <th>AVG</th>
                <th>OBP</th>
                <th>SLG</th>
                <th>OPS</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => {
                const s = p.career_batting;
                return (
                  <tr key={p.id}>
                    <td>{p.name}</td>
                    <td>{p.primary_position}</td>
                    <td>{s?.games ?? "-"}</td>
                    <td>{s?.at_bats ?? "-"}</td>
                    <td>{s?.hits ?? "-"}</td>
                    <td>{s?.home_runs ?? "-"}</td>
                    <td>{s?.rbi ?? "-"}</td>
                    <td>{s?.walks ?? "-"}</td>
                    <td>{s?.strikeouts ?? "-"}</td>
                    <td>{s ? s.avg.toFixed(3) : "-"}</td>
                    <td>{s ? s.obp.toFixed(3) : "-"}</td>
                    <td>{s ? s.slg.toFixed(3) : "-"}</td>
                    <td>{s ? s.ops.toFixed(3) : "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
