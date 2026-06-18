import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Project } from "../types";

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [onlyFav, setOnlyFav] = useState(false);
  const nav = useNavigate();

  async function load() {
    const data = (await api.listProjects(
      onlyFav ? true : undefined
    )) as Project[];
    setProjects(data);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onlyFav]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    const p = (await api.createProject(name)) as Project;
    setName("");
    nav(`/projects/${p.id}`);
  }

  return (
    <div>
      <div className="page-head">
        <h2>My Projects</h2>
        <label className="muted">
          <input
            type="checkbox"
            checked={onlyFav}
            onChange={(e) => setOnlyFav(e.target.checked)}
          />{" "}
          Favourites only
        </label>
      </div>

      <form className="row" onSubmit={create}>
        <input
          placeholder="New project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="btn primary">New Project</button>
      </form>

      <div className="grid">
        {projects.map((p) => (
          <div className="card project" key={p.id}>
            <div className="row between">
              <strong>{p.name}</strong>
              <button
                className="star"
                title="Favourite"
                onClick={async () => {
                  await api.toggleFavourite(p.id);
                  load();
                }}
              >
                {p.is_favourite ? "★" : "☆"}
              </button>
            </div>
            <div className="muted small">
              {p.garment ?? "—"} · {p.status}
            </div>
            <div className="row">
              <button
                className="btn"
                onClick={() => nav(`/projects/${p.id}`)}
              >
                Open
              </button>
              <button
                className="btn danger"
                onClick={async () => {
                  await api.deleteProject(p.id);
                  load();
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {projects.length === 0 && <p className="muted">No projects yet.</p>}
      </div>
    </div>
  );
}
