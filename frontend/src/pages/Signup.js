import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { signupUser } from "../api";
import { useAuth } from "../AuthContext";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      const data = await signupUser(email, password);
      login(data.access_token ?? data.token, data.user ?? { email });
      navigate("/");
    } catch (err) {
      setError(err.message || "Could not create account");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}>
      <div style={{ width: "100%", maxWidth: 400 }}>
        <div className="text-center mb-8 rise">
          <Link to="/" className="row gap-2 center" style={{ display: "inline-flex" }}>
            <span style={{ width: 8, height: 8, borderRadius: 999, background: "var(--accent)" }} />
            <span className="serif" style={{ fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em" }}>notesearch</span>
          </Link>
        </div>

        <div className="glass-2 r-xl rise delay-1" style={{ padding: 32 }}>
          <p className="eyebrow mb-3">Get started</p>
          <h1 className="display mb-6" style={{ fontSize: 40 }}>
            Create{" "}
            <span className="serif italic" style={{ color: "var(--accent)", fontWeight: 500 }}>account.</span>
          </h1>

          <form onSubmit={handleSubmit} className="col gap-4">
            <div className="col gap-2">
              <label className="muted" style={{ fontSize: 12, fontWeight: 500 }}>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com" required autoFocus className="input-glass" />
            </div>
            <div className="col gap-2">
              <label className="muted" style={{ fontSize: 12, fontWeight: 500 }}>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters" required minLength={8} className="input-glass" />
            </div>
            {error && (
              <p style={{
                fontSize: 12, padding: "8px 12px", borderRadius: 6,
                background: "rgba(194,65,12,0.08)",
                border: "1px solid rgba(194,65,12,0.2)", color: "var(--error)",
              }} role="alert">
                {error}
              </p>
            )}
            <button type="submit" disabled={loading} className="btn-primary mt-2 w-full" style={{ padding: "12px 20px" }}>
              {loading ? "creating…" : "Create account"}
            </button>
          </form>
        </div>

        <p className="muted text-center mt-6 fade delay-2" style={{ fontSize: 13 }}>
          Have an account?{" "}
          <Link to="/login" className="serif italic" style={{ color: "var(--accent)" }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
