import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, authStorage } from "../api/client";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(authStorage.getUser());
  const [loading, setLoading] = useState(Boolean(authStorage.getToken()));

  const bootstrap = useCallback(async () => {
    if (!authStorage.getToken()) {
      setLoading(false);
      return;
    }
    try {
      const me = await api.me();
      setUser(me);
      localStorage.setItem("bama_user", JSON.stringify(me));
    } catch {
      authStorage.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (email: string, password: string) => {
    const auth = await api.login(email, password);
    authStorage.save(auth);
    setUser(auth.user);
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    const auth = await api.register(email, password, fullName);
    authStorage.save(auth);
    setUser(auth.user);
  }, []);

  const logout = useCallback(() => {
    authStorage.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
