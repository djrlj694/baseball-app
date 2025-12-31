
import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import "./App.css";
import {
  fetchPlayerDetail,
  importBaseball,
  listPlayers,
  updatePlayer,
  type CareerBatting,
  type Player,
  type PlayerDetail,
  type PlayerUpdateRequest,
  type SortBy,
} from "./api";

type StatKey = keyof CareerBatting;

const numberCell = (value: number | null | undefined) =>
  value === null || value === undefined ? "–" : value.toLocaleString();

const slashCell = (value: number | null | undefined) =>
  value === null || value === undefined ? "–" : value.toFixed(3);

export default function App() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [sortBy, setSortBy] = useState<SortBy>("hits");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<PlayerDetail | null>(null);
  const [editDraft, setEditDraft] = useState<PlayerUpdateRequest | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingImport, setLoadingImport] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);

  const refreshPlayers = async () => {
    setLoadingList(true);
    setError(null);
    try {
      const data = await listPlayers(sortBy);
      setPlayers(data);
      if (!data.length) {
        setSelectedId(null);
        setSelected(null);
        setEditDraft(null);
        setEditing(false);
        return;
      }
      if (data.length && (!selectedId || !data.some((p) => p.id === selectedId))) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load players");
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    void refreshPlayers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy]);

  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      return;
    }
    const loadDetail = async () => {
      setLoadingDetail(true);
      setError(null);
      try {
        const detail = await fetchPlayerDetail(selectedId);
        setSelected(detail);
        setEditDraft({
          name: detail.name,
          primary_position: detail.primary_position,
          career_batting: detail.career_batting ? { ...detail.career_batting } : undefined,
        });
        setEditing(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load player");
      } finally {
        setLoadingDetail(false);
      }
    };
    void loadDetail();
  }, [selectedId]);

  const handleImport = async () => {
    setLoadingImport(true);
    setStatus("Importing from source API…");
    setError(null);
    try {
      const result = await importBaseball();
      setStatus(
        `Imported ${result.inserted_players} new players, updated ${result.updated_players}.`
      );
      await refreshPlayers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoadingImport(false);
    }
  };

  const handleSave = async (evt: FormEvent<HTMLFormElement>) => {
    evt.preventDefault();
    if (!selectedId || !editDraft) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updatePlayer(selectedId, editDraft);
      setSelected(updated);
      setPlayers((prev) =>
        prev.map((p) =>
          p.id === updated.id
            ? { ...p, name: updated.name, primary_position: updated.primary_position, career_batting: updated.career_batting }
            : p
        )
      );
      setStatus(`Saved changes for ${updated.name}.`);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save changes");
    } finally {
      setSaving(false);
    }
  };

  const updateDraftStat = (key: StatKey, raw: string) => {
    setEditDraft((prev) => {
      const next = prev ?? {};
      const currentStats =
        next.career_batting ??
        (selected?.career_batting ? { ...selected.career_batting } : {});
      const parsed = raw === "" ? undefined : Number(raw);
      return {
        ...next,
        career_batting: {
          ...currentStats,
          [key]: Number.isNaN(parsed) ? undefined : parsed,
        },
      };
    });
  };

  const updateDraftField = (key: "name" | "primary_position", value: string) => {
    setEditDraft((prev) => ({
      ...(prev ?? {}),
      [key]: value,
    }));
  };

  const detailStats = useMemo(() => selected?.career_batting ?? null, [selected]);

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Baseball data explorer</p>
          <h1>Diamond Digest</h1>
          <p className="lede">
            Import players from the Fraction test API, sort by production, inspect an LLM-style
            player profile, and edit a player&apos;s record inline.
          </p>
        </div>
        <div className="actions">
          <button className="ghost" onClick={() => void refreshPlayers()} disabled={loadingList}>
            {loadingList ? "Refreshing…" : "Refresh"}
          </button>
          <button onClick={handleImport} disabled={loadingImport || loadingList}>
            {loadingImport ? "Importing…" : "Import latest"}
          </button>
        </div>
      </header>

      <div className="toolbar">
        <div className="control">
          <label htmlFor="sort">Order players by</label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            disabled={loadingList}
          >
            <option value="hits">Hits (desc)</option>
            <option value="home_runs">Home runs (desc)</option>
          </select>
        </div>
        {status && <div className="status">{status}</div>}
        {error && <div className="error">Error: {error}</div>}
      </div>

      <div className="content">
        <section className="panel list">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">Players</p>
              <h3>{players.length ? `${players.length} loaded` : "No players yet"}</h3>
            </div>
            {loadingList && <span className="muted">Loading roster…</span>}
          </div>
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Pos</th>
                  <th title="Games">G</th>
                  <th title="At-bats">AB</th>
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
                {players.map((p) => {
                  const isSelected = p.id === selectedId;
                  const s = p.career_batting;
                  return (
                    <tr
                      key={p.id}
                      className={isSelected ? "selected" : ""}
                      onClick={() => setSelectedId(p.id)}
                    >
                      <td>{p.name}</td>
                      <td>{p.primary_position}</td>
                      <td>{numberCell(s?.games)}</td>
                      <td>{numberCell(s?.at_bats)}</td>
                      <td>{numberCell(s?.hits)}</td>
                      <td>{numberCell(s?.home_runs)}</td>
                      <td>{numberCell(s?.rbi)}</td>
                      <td>{numberCell(s?.walks)}</td>
                      <td>{numberCell(s?.strikeouts)}</td>
                      <td>{slashCell(s?.avg)}</td>
                      <td>{slashCell(s?.obp)}</td>
                      <td>{slashCell(s?.slg)}</td>
                      <td>{slashCell(s?.ops)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel detail">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">Player profile</p>
              <h3>{selected ? selected.name : "Select a player"}</h3>
            </div>
            <div className="panelActions">
              {selected && (
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setEditing(true)}
                  disabled={saving || loadingDetail}
                >
                  {editing ? "Editing enabled" : "Edit player"}
                </button>
              )}
              {loadingDetail && <span className="muted">Loading detail…</span>}
            </div>
          </div>
          {!selected ? (
            <p className="muted">Choose a player from the table to see their generated summary.</p>
          ) : (
            <>
              <div className="description">{selected.description}</div>
              <form className="editForm" onSubmit={handleSave}>
                <div className="grid two">
                  <label>
                    <span className="label">Name</span>
                    <input
                      type="text"
                      value={editDraft?.name ?? ""}
                      onChange={(e) => updateDraftField("name", e.target.value)}
                      disabled={!editing || saving || loadingDetail}
                    />
                  </label>
                  <label>
                    <span className="label">Primary position</span>
                    <input
                      type="text"
                      value={editDraft?.primary_position ?? ""}
                      onChange={(e) => updateDraftField("primary_position", e.target.value)}
                      disabled={!editing || saving || loadingDetail}
                    />
                  </label>
                </div>

                <div className="grid four">
                  {([
                    ["games", "Games"],
                    ["at_bats", "At-bats"],
                    ["runs", "Runs"],
                    ["hits", "Hits"],
                    ["doubles", "Doubles"],
                    ["triples", "Triples"],
                    ["home_runs", "Home runs"],
                    ["rbi", "RBI"],
                    ["walks", "Walks"],
                    ["strikeouts", "Strikeouts"],
                    ["stolen_bases", "Stolen bases"],
                    ["caught_stealing", "Caught stealing"],
                  ] as Array<[StatKey, string]>).map(([key, labelText]) => (
                    <label key={key}>
                      <span className="label">{labelText}</span>
                      <input
                        type="number"
                        value={
                          editDraft?.career_batting?.[key] ?? detailStats?.[key] ?? ""
                        }
                        onChange={(e) => updateDraftStat(key, e.target.value)}
                        disabled={!editing || saving || loadingDetail}
                      />
                    </label>
                  ))}
                </div>

                <div className="grid four">
                  {([
                    ["avg", "AVG"],
                    ["obp", "OBP"],
                    ["slg", "SLG"],
                    ["ops", "OPS"],
                  ] as Array<[StatKey, string]>).map(([key, labelText]) => (
                    <label key={key}>
                      <span className="label">{labelText}</span>
                      <input
                        type="number"
                        step="0.001"
                        value={
                          editDraft?.career_batting?.[key] ?? detailStats?.[key] ?? ""
                        }
                        onChange={(e) => updateDraftStat(key, e.target.value)}
                        disabled={!editing || saving || loadingDetail}
                      />
                    </label>
                  ))}
                </div>

                <div className="formActions">
                  <button type="submit" disabled={!editing || saving || loadingDetail}>
                    {saving ? "Saving…" : "Save player"}
                  </button>
                  <span className="muted small">
                    Updates persist to Postgres and refresh the list ordering.
                  </span>
                </div>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
