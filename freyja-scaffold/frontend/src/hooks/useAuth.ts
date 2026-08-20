import { useState, useCallback } from "react";

interface AuthState {
  isLoggedIn: boolean;
  tier: string;
  ageVerified: boolean;
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>({
    isLoggedIn: false,
    tier: "basic",
    ageVerified: false,
  });

  const login = useCallback(async (username: string, password: string) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error("Login failed");
    const data = await res.json();
    setAuth({ isLoggedIn: true, tier: data.tier, ageVerified: data.age_verified });
  }, []);

  const signup = useCallback(async (username: string, password: string) => {
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error("Signup failed");
    // Auto-login after signup
    await login(username, password);
  }, [login]);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    setAuth({ isLoggedIn: false, tier: "basic", ageVerified: false });
  }, []);

  return { ...auth, login, signup, logout };
}
