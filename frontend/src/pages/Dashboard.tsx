import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import type { Project } from "../types";

export default function Dashboard() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.listProjects().then((p) => setProjects(p as Project[]));
  }, []);

  return (
    <div className="stack">
      <h2>Welcome back{user?.full_name ? `, ${user.full_name}` : ""}</h2>
      <div className="grid">
        <div className="card stat">
          <span className="muted">Credits</span>
          <strong className="big">{user?.credits ?? 0}</strong>
        </div>
        <div className="card stat">
          <span className="muted">Projects</span>
          <strong className="big">{projects.length}</strong>
        </div>
        <div className="card stat">
          <span className="muted">Plan</span>
          <strong className="big">{user?.subscription_tier}</strong>
        </div>
      </div>
      <Link className="btn primary" to="/projects">
        Start a new sketch
      </Link>
    </div>
  );
}
