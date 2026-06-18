// Thin fetch wrapper around the FastAPI backend.

const TOKEN_KEY = "ai_embroidery_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`/api${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  register: (body: { email: string; password: string; full_name?: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () => request("/auth/me"),

  // Projects
  listProjects: (favourite?: boolean) =>
    request(
      `/projects${favourite !== undefined ? `?favourite=${favourite}` : ""}`
    ),
  createProject: (name: string) =>
    request("/projects", { method: "POST", body: JSON.stringify({ name }) }),
  getProject: (id: number) => request(`/projects/${id}`),
  getState: (id: number) => request(`/projects/${id}/state`),
  toggleFavourite: (id: number) =>
    request(`/projects/${id}/favourite`, { method: "PATCH" }),
  deleteProject: (id: number) =>
    request(`/projects/${id}`, { method: "DELETE" }),
  setGarment: (id: number, garment: string, placement: string) =>
    request(`/projects/${id}/garment`, {
      method: "PUT",
      body: JSON.stringify({ garment, placement }),
    }),

  // Upload + Vision
  uploadReference: (id: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request(`/projects/${id}/reference`, { method: "POST", body: fd });
  },
  analyze: (id: number) =>
    request(`/projects/${id}/analyze`, { method: "POST" }),

  // Measurements
  setMeasurements: (id: number, body: Record<string, number>) =>
    request(`/projects/${id}/measurements`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // Pipeline + Variations
  generate: (
    id: number,
    n_variants = 2,
    style = "photoreal",
    size = "panel"
  ) =>
    request(`/projects/${id}/generate`, {
      method: "POST",
      body: JSON.stringify({ n_variants, style, size }),
    }),
  variation: (id: number, base_sketch_id: number, variation: string) =>
    request(`/projects/${id}/variations`, {
      method: "POST",
      body: JSON.stringify({ base_sketch_id, variation, n_variants: 2 }),
    }),

  // Phase 4 — Collection Builder
  buildCollection: (id: number, base_sketch_id: number) =>
    request(`/projects/${id}/collection`, {
      method: "POST",
      body: JSON.stringify({ base_sketch_id }),
    }),
  getCollections: () => request(`/collections`),
};
