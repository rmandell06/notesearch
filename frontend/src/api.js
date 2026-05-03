const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

let _token = null;

export function setAuthToken(token) {
  _token = token;
}

async function request(path, options = {}) {
  const headers = { ...options.headers };
  if (_token) headers["Authorization"] = `Bearer ${_token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export function loginUser(email, password) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function signupUser(email, password) {
  return request("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function logoutUser() {
  return request("/auth/logout", { method: "POST" });
}

export function searchNotes(query) {
  return request(`/search?q=${encodeURIComponent(query)}`);
}

export function getRecentNotes() {
  return request("/notes?limit=10&sort=recent");
}

export function getNote(id) {
  return request(`/notes/${id}`);
}

export function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/notes/upload", { method: "POST", body: form });
}

export function getConnections() {
  return request("/connections/");
}
