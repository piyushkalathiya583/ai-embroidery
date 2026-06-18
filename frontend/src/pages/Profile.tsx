import { useAuth } from "../auth";

export default function Profile() {
  const { user } = useAuth();
  return (
    <div className="stack">
      <h2>Profile</h2>
      <div className="card">
        <p>
          <span className="muted">Name:</span> {user?.full_name ?? "—"}
        </p>
        <p>
          <span className="muted">Email:</span> {user?.email}
        </p>
        <p>
          <span className="muted">Plan:</span> {user?.subscription_tier}
        </p>
        <p>
          <span className="muted">Credits:</span> {user?.credits}
        </p>
      </div>
    </div>
  );
}
