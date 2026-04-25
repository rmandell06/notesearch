const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export function searchNotes(query) {
  return request(`/api/search?q=${encodeURIComponent(query)}`);
}

export function getRecentNotes() {
  return request("/api/notes?limit=10&sort=recent");
}

export function getNote(id) {
  return request(`/api/notes/${id}`);
}

export function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/api/notes/upload", { method: "POST", body: form });
}

export function getConnections() {
  return request("/api/connections/");
}
