import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { loginUser } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await loginUser(email, password);
      login(data.access_token ?? data.token, data.user ?? { email });
      navigate("/");
    } catch (err) {
      setError(err.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div
        className="w-full max-w-sm"
        style={{ background: "#0e0e1c", border: "1.5px solid #1a1a2e", borderRadius: 16, padding: 36 }}
      >
        <p className="mono text-xs mb-2" style={{ color: "#3a3a5a", letterSpacing: "0.15em" }}>
          notesearch.app
        </p>
        <h1 className="mono text-2xl font-bold mb-8 gradient-text">login</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="mono text-xs" style={{ color: "#3a3a5a" }}>email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
              style={{
                background: "#08080e",
                border: "1.5px solid #1e1e32",
                color: "#e2e2f0",
                caretColor: "#00e5ff",
              }}
              onFocus={(e) => {
                e.target.style.border = "1.5px solid #00e5ff";
                e.target.style.boxShadow = "0 0 0 3px rgba(0,229,255,0.08)";
              }}
              onBlur={(e) => {
                e.target.style.border = "1.5px solid #1e1e32";
                e.target.style.boxShadow = "none";
              }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="mono text-xs" style={{ color: "#3a3a5a" }}>password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
              style={{
                background: "#08080e",
                border: "1.5px solid #1e1e32",
                color: "#e2e2f0",
                caretColor: "#00e5ff",
              }}
              onFocus={(e) => {
                e.target.style.border = "1.5px solid #00e5ff";
                e.target.style.boxShadow = "0 0 0 3px rgba(0,229,255,0.08)";
              }}
              onBlur={(e) => {
                e.target.style.border = "1.5px solid #1e1e32";
                e.target.style.boxShadow = "none";
              }}
            />
          </div>

          {error && (
            <p
              className="mono text-xs rounded-lg px-3 py-2"
              role="alert"
              style={{ background: "rgba(255,45,85,0.07)", border: "1.5px solid rgba(255,45,85,0.2)", color: "#ff2d55" }}
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 py-2.5 mono text-xs font-bold rounded-lg transition-all"
            style={{
              background: "transparent",
              border: "1.5px solid #00e5ff",
              color: loading ? "#3a3a5a" : "#00e5ff",
              borderColor: loading ? "#1e1e32" : "#00e5ff",
              textShadow: loading ? "none" : "0 0 8px rgba(0,229,255,0.5)",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "logging in..." : "login_"}
          </button>
        </form>

        <p className="mt-6 text-xs text-center" style={{ color: "#3a3a5a" }}>
          don't have an account?{" "}
          <Link to="/signup" className="mono transition-colors" style={{ color: "#bf5af2" }}>
            sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
