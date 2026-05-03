import { createContext, useContext, useState } from "react";
import { setAuthToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);

  function login(newToken, newUser) {
    setAuthToken(newToken);
    setToken(newToken);
    setUser(newUser);
  }

  function logout() {
    setAuthToken(null);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
