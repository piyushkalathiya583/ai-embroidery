import { Link } from "react-router-dom";

export default function Collection() {
  return (
    <div className="stack">
      <h2>Collection Builder</h2>
      <p className="muted">
        Phase 4 — from one generated sketch, build a matching set: Blouse,
        Dupatta, Border, Kurti and Panel, all sharing the same style and motifs.
      </p>
      <div className="card">
        <p>
          To build a collection, open a project, generate sketches, then click{" "}
          <strong>Build Collection</strong> on any result sketch.
        </p>
        <Link className="btn primary" to="/projects">
          Go to Projects
        </Link>
      </div>
      <div className="grid">
        {["Blouse", "Dupatta", "Border", "Kurti", "Panel"].map((x) => (
          <div className="card stat" key={x}>
            <span className="muted">Matching</span>
            <strong className="big">{x}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
