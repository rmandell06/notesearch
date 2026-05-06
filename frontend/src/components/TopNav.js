import { Link, useLocation, useNavigate } from "react-router-dom";
import { logoutUser } from "../api";
import { useAuth } from "../AuthContext";
import ThemeToggle from "./ThemeToggle";

export default function TopNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, token, user } = useAuth() ?? {};

  function handleLogout() {
    logoutUser().catch(() => {});
    logout?.();
    navigate("/login");
  }

  function isActive(path) {
    if (path === "/") return location.pathname === "/" || location.pathname.startsWith("/note/");
    return location.pathname.startsWith(path);
  }

  if (!token) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 50,
        width: "min(640px, calc(100% - 32px))",
      }}
    >
      <div
        className="glass-2 row between"
        style={{
          borderRadius: "var(--r-pill)",
          padding: "6px 8px 6px 16px",
        }}
      >
        <Link to="/" className="row gap-2" style={{ padding: "6px 4px" }}>
          <span style={{ width: 6, height: 6, borderRadius: "999px", background: "var(--accent)" }} />
          <span className="serif" style={{ fontWeight: 600, fontSize: 15, letterSpacing: "-0.02em" }}>
            notesearch
          </span>
        </Link>

        <nav className="row gap-1">
          <NavLink active={isActive("/")} to="/" label="Notes" navigate={navigate} />
          <NavLink active={isActive("/connections")} to="/connections" label="Connections" navigate={navigate} />
        </nav>

        <div className="row gap-1">
          <ThemeToggle />
          <button
          onClick={handleLogout}
          className="row gap-2"
          title={user?.email ?? "Sign out"}
          style={{
            padding: "5px 12px 5px 6px",
            borderRadius: "var(--r-pill)",
            color: "var(--ink-muted)",
            fontSize: 12,
          }}
        >
          <span
            style={{
              width: 22, height: 22, borderRadius: "999px",
              background: "var(--accent)", color: "var(--paper)",
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              fontSize: 10, fontWeight: 600,
            }}
          >
            {(user?.email?.[0] ?? "u").toUpperCase()}
          </span>
          <span>Sign out</span>
        </button>
        </div>
      </div>
    </div>
  );
}

function NavLink({ active, to, label, navigate }) {
  return (
    <button
      onClick={() => navigate(to)}
      style={{
        padding: "7px 14px",
        borderRadius: "999px",
        color: active ? "var(--ink)" : "var(--ink-muted)",
        fontWeight: active ? 500 : 400,
        fontSize: 13,
        background: active ? "rgba(20,17,13,0.05)" : "transparent",
        transition: "all 150ms ease",
      }}
    >
      {label}
    </button>
  );
}
