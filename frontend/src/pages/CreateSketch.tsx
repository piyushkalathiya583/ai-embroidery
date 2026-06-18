import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, fileUrl } from "../api";
import { useAuth } from "../auth";
import Lightbox from "../components/Lightbox";
import {
  GARMENTS,
  PLACEMENTS,
  VARIATIONS,
  type Collection,
  type MeasurementResult,
  type PipelineResult,
  type Project,
  type ProjectState,
  type Sketch,
  type VisionResult,
} from "../types";

export default function CreateSketch() {
  const { id } = useParams();
  const projectId = Number(id);
  const { refresh } = useAuth();
  const nav = useNavigate();
  const [zoom, setZoom] = useState<string | null>(null);

  const [project, setProject] = useState<Project | null>(null);
  const [vision, setVision] = useState<VisionResult | null>(null);
  const [measurement, setMeasurement] = useState<MeasurementResult | null>(null);
  const [garment, setGarmentSel] = useState(GARMENTS[0]);
  const [placement, setPlacement] = useState(PLACEMENTS[0]);
  const [m, setM] = useState({ waist: 42, height: 44, margin: 0.5, kali: 12 });
  const [style, setStyle] = useState("photoreal");
  const [size, setSize] = useState("panel");
  const [sketches, setSketches] = useState<Sketch[]>([]);
  const [collection, setCollection] = useState<Collection | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) return;
    // Rehydrate all saved work so reopening a project resumes where you left off.
    api.getState(projectId).then((data) => {
      const s = data as ProjectState;
      setProject(s.project);
      if (s.project.garment) setGarmentSel(s.project.garment);
      if (s.project.placement) setPlacement(s.project.placement);
      if (s.vision) setVision(s.vision);
      if (s.measurement_input) setM(s.measurement_input);
      if (s.measurement_result) setMeasurement(s.measurement_result);
      if (s.sketches?.length) setSketches(s.sketches);
    });
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
        <h3>5 · Generate Designs</h3>
        <div className="row">
          <label className="field">
            Style
            <select value={style} onChange={(e) => setStyle(e.target.value)}>
              <option value="photoreal">Photorealistic embroidery</option>
              <option value="pencil">Pencil sketch</option>
            </select>
          </label>
          <label className="field">
            Resolution
            <select value={size} onChange={(e) => setSize(e.target.value)}>
              <option value="panel">Tall panel (1024×1536)</option>
              <option value="square">Square (1024×1024)</option>
            </select>
          </label>
          <button
            className="btn primary"
            disabled={busy === "gen"}
            onClick={guard("gen", async () => {
              const res = (await api.generate(
                projectId,
                2,
                style,
                size
              )) as PipelineResult;
              setSketches(res.output);
              await refresh();
            })}
          >
            {busy === "gen" ? "Generating…" : "Generate Designs"}
          </button>
        </div>
        <p className="muted small">
          Photorealistic mode renders visible threads & stitches for digitising.
          High-quality generation can take 30–60s.
        </p>
      </section>

      {/* Results + Phase 3 variations */}
      {sketches.length > 0 && (
        <section className="card">
          <h3>Results</h3>
          <div className="grid">
            {sketches.map((s) => (
              <div className="card sketch" key={s.id}>
                <img
                  className="thumb-img"
                  src={fileUrl(s.image_url)}
                  alt={`Sketch ${s.id}`}
                  onClick={() => setZoom(fileUrl(s.image_url))}
                />
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
                    nav("/collection");
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
                  src={fileUrl(it.image_url)}
                  alt={it.piece}
                  onClick={() => setZoom(fileUrl(it.image_url))}
                />
                <strong>{it.piece}</strong>
              </div>
            ))}
          </div>
        </section>
      )}

      <Lightbox src={zoom} onClose={() => setZoom(null)} />
    </div>
  );
}
