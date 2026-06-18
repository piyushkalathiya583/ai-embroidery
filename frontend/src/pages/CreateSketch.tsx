import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import {
  GARMENTS,
  PLACEMENTS,
  VARIATIONS,
  type Collection,
  type MeasurementResult,
  type PipelineResult,
  type Project,
  type Sketch,
  type VisionResult,
} from "../types";

export default function CreateSketch() {
  const { id } = useParams();
  const projectId = Number(id);
  const { refresh } = useAuth();

  const [project, setProject] = useState<Project | null>(null);
  const [vision, setVision] = useState<VisionResult | null>(null);
  const [measurement, setMeasurement] = useState<MeasurementResult | null>(null);
  const [garment, setGarmentSel] = useState(GARMENTS[0]);
  const [placement, setPlacement] = useState(PLACEMENTS[0]);
  const [m, setM] = useState({ waist: 42, height: 44, margin: 0.5, kali: 12 });
  const [sketches, setSketches] = useState<Sketch[]>([]);
  const [collection, setCollection] = useState<Collection | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (projectId) api.getProject(projectId).then((p) => setProject(p as Project));
  }, [projectId]);

  function guard<T>(label: string, fn: () => Promise<T>) {
    return async () => {
      setError("");
      setBusy(label);
      try {
        await fn();
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setBusy("");
      }
    };
  }

  if (!projectId) {
    return (
      <div>
        <h2>Create Sketch</h2>
        <p className="muted">
          Open a project from the Projects page to start, or create one there.
        </p>
      </div>
    );
  }

  return (
    <div className="stack">
      <h2>{project?.name ?? "Create Sketch"}</h2>
      {error && <div className="error">{error}</div>}

      {/* Step 1: Upload reference */}
      <section className="card">
        <h3>1 · Reference Image</h3>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) guard("upload", () => api.uploadReference(projectId, f))();
          }}
        />
        {busy === "upload" && <span className="muted"> uploading…</span>}
      </section>

      {/* Step 2: Vision analysis */}
      <section className="card">
        <h3>2 · Vision Analysis</h3>
        <button
          className="btn"
          disabled={busy === "analyze"}
          onClick={guard("analyze", async () =>
            setVision((await api.analyze(projectId)) as VisionResult)
          )}
        >
          {busy === "analyze" ? "Analysing…" : "Analyse Image"}
        </button>
        {vision && <pre className="json">{JSON.stringify(vision, null, 2)}</pre>}
      </section>

      {/* Step 3: Garment + Placement */}
      <section className="card">
        <h3>3 · Garment & Placement</h3>
        <div className="row">
          <select value={garment} onChange={(e) => setGarmentSel(e.target.value)}>
            {GARMENTS.map((g) => (
              <option key={g}>{g}</option>
            ))}
          </select>
          <select value={placement} onChange={(e) => setPlacement(e.target.value)}>
            {PLACEMENTS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
          <button
            className="btn"
            onClick={guard("garment", () =>
              api.setGarment(projectId, garment, placement)
            )}
          >
            Save
          </button>
        </div>
      </section>

      {/* Step 4: Measurements */}
      <section className="card">
        <h3>4 · Measurements</h3>
        <div className="row">
          {(["waist", "height", "margin", "kali"] as const).map((k) => (
            <label key={k} className="field">
              {k}
              <input
                type="number"
                step="0.1"
                value={m[k]}
                onChange={(e) => setM({ ...m, [k]: Number(e.target.value) })}
              />
            </label>
          ))}
          <button
            className="btn"
            onClick={guard("meas", async () =>
              setMeasurement(
                (await api.setMeasurements(projectId, m)) as MeasurementResult
              )
            )}
          >
            Compute
          </button>
        </div>
        {measurement && (
          <pre className="json">{JSON.stringify(measurement, null, 2)}</pre>
        )}
      </section>

      {/* Step 5: Generate */}
      <section className="card">
        <h3>5 · Generate Sketches</h3>
        <button
          className="btn primary"
          disabled={busy === "gen"}
          onClick={guard("gen", async () => {
            const res = (await api.generate(projectId, 2)) as PipelineResult;
            setSketches(res.output);
            await refresh();
          })}
        >
          {busy === "gen" ? "Generating…" : "Generate Sketches"}
        </button>
      </section>

      {/* Results + Phase 3 variations */}
      {sketches.length > 0 && (
        <section className="card">
          <h3>Results</h3>
          <div className="grid">
            {sketches.map((s) => (
              <div className="card sketch" key={s.id}>
                <img className="thumb-img" src={s.image_url} alt={`Sketch ${s.id}`} />
                <div className="variations">
                  {VARIATIONS.map((v) => (
                    <button
                      key={v}
                      className="chip"
                      disabled={busy !== ""}
                      onClick={guard(`var-${s.id}-${v}`, async () => {
                        const res = (await api.variation(
                          projectId,
                          s.id,
                          v
                        )) as PipelineResult;
                        setSketches(res.output);
                        await refresh();
                      })}
                    >
                      {v}
                    </button>
                  ))}
                </div>
                <button
                  className="btn"
                  style={{ marginTop: 8 }}
                  disabled={busy !== ""}
                  onClick={guard(`coll-${s.id}`, async () => {
                    const c = (await api.buildCollection(
                      projectId,
                      s.id
                    )) as Collection;
                    setCollection(c);
                    await refresh();
                  })}
                >
                  {busy === `coll-${s.id}` ? "Building…" : "Build Collection"}
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Phase 4 — Collection Builder results */}
      {collection && (
        <section className="card">
          <h3>Matching Collection (from sketch #{collection.base_sketch_id})</h3>
          <div className="grid">
            {collection.items.map((it) => (
              <div className="card sketch" key={it.id}>
                <img
                  className="thumb-img"
                  src={it.image_url}
                  alt={it.piece}
                />
                <strong>{it.piece}</strong>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
