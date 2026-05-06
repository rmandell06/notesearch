import { createContext, useContext, useEffect, useState } from "react";
import { setAuthToken } from "./api";

const AuthContext = createContext(null);
const STORAGE_KEY = "ns.auth";

function readPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.token === "string" && parsed.token) {
      return parsed;
    }
  } catch (_) {
    // localStorage unavailable / corrupted → behave as if signed out.
  }
  return null;
}

export function AuthProvider({ children }) {
  // Initialize from localStorage so a refresh doesn't kick the user back
  // to /login. Initial state is computed lazily so the read happens once.
  const [auth, setAuth] = useState(() => {
    const persisted = readPersisted();
    if (persisted) setAuthToken(persisted.token);
    return persisted ?? { token: null, user: null };
  });

  // Mirror state back to localStorage on change.
  useEffect(() => {
    try {
      if (auth.token) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (_) {
      // Private mode etc. — token still works in this tab, just won't persist.
    }
  }, [auth]);

  function login(newToken, newUser) {
    setAuthToken(newToken);
    setAuth({ token: newToken, user: newUser });
  }

  function logout() {
    setAuthToken(null);
    setAuth({ token: null, user: null });
  }

  return (
    <AuthContext.Provider value={{ token: auth.token, user: auth.user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
