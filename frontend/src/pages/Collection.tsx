import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import Lightbox from "../components/Lightbox";
import type { Collection as Coll } from "../types";

export default function Collection() {
  const [collections, setCollections] = useState<Coll[]>([]);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState<string | null>(null);

  useEffect(() => {
    api
      .getCollections()
      .then((c) => setCollections(c as Coll[]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="stack">
      <h2>Collection Builder</h2>
      <p className="muted">
        Matching sets built from a sketch — Blouse, Dupatta, Border, Kurti,
        Panel. Build one from any sketch via <strong>Build Collection</strong>;
        saved sets appear here permanently.
      </p>

      {loading && <p className="muted">Loading…</p>}

      {!loading && collections.length === 0 && (
        <div className="card">
          <p>No collections yet.</p>
          <Link className="btn primary" to="/projects">
            Go to Projects
          </Link>
        </div>
      )}

      {collections.map((c) => (
        <section className="card" key={c.id}>
          <div className="row between">
            <strong>{c.title ?? `Collection #${c.id}`}</strong>
            <span className="muted small">
              #{c.id} · {new Date(c.created_at).toLocaleString()}
            </span>
          </div>
          <div className="grid">
            {c.items.map((it) => (
              <div className="card sketch" key={it.id}>
                <img
                  className="thumb-img"
                  src={it.image_url}
                  alt={it.piece}
                  onClick={() => setZoom(it.image_url)}
                />
                <strong>{it.piece}</strong>
              </div>
            ))}
          </div>
        </section>
      ))}

      <Lightbox src={zoom} onClose={() => setZoom(null)} />
    </div>
  );
}
