import { useAuth } from "../auth";

const PLANS = [
  { name: "Free", credits: 10, price: "₹0" },
  { name: "Pro", credits: 200, price: "₹999/mo" },
  { name: "Studio", credits: 1000, price: "₹3999/mo" },
];

export default function Subscription() {
  const { user } = useAuth();
  return (
    <div className="stack">
      <h2>Subscription</h2>
      <p className="muted">Current plan: {user?.subscription_tier}</p>
      <div className="grid">
        {PLANS.map((p) => (
          <div className="card stat" key={p.name}>
            <strong className="big">{p.name}</strong>
            <span className="muted">{p.credits} credits</span>
            <span>{p.price}</span>
            <button className="btn primary" disabled>
              Choose
            </button>
          </div>
        ))}
      </div>
      <p className="muted small">
        Payment integration (Module 1 — Subscription/Credits) is not wired yet.
      </p>
    </div>
  );
}
