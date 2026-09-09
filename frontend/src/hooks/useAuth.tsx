import { createContext, useContext, useState, ReactNode } from "react";
import { api } from "../services/api";

type Role = "manager" | "staff" | "guest";
interface AuthUser {
  email: string;
  name: string;
  role: Role;
}
interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem("resortiq_user");
    return raw ? JSON.parse(raw) : null;
  });

  async function login(email: string, password: string) {
    const res = await api.login(email, password);
    localStorage.setItem("resortiq_token", res.access_token);
    const u: AuthUser = { email: res.email, name: res.name, role: res.role };
    localStorage.setItem("resortiq_user", JSON.stringify(u));
    setUser(u);
    return u;
  }

  function logout() {
    localStorage.removeItem("resortiq_token");
    localStorage.removeItem("resortiq_user");
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
