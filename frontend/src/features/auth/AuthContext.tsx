import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchCurrentUser, login as apiLogin, register as apiRegister } from "./api";
import { AuthContext, type AuthContextValue } from "./context";
import type { Credentials, User } from "./types";

const TOKEN_STORAGE_KEY = "expensetrack_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => token !== null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    fetchCurrentUser(token)
      .then((fetchedUser) => {
        if (!cancelled) setUser(fetchedUser);
      })
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          setToken(null);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleLogin = useCallback(async (credentials: Credentials) => {
    const tokens = await apiLogin(credentials);
    localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);
    setToken(tokens.access_token);
  }, []);

  const handleRegister = useCallback(
    async (credentials: Credentials) => {
      await apiRegister(credentials);
      await handleLogin(credentials);
    },
    [handleLogin],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, isLoading, login: handleLogin, register: handleRegister, logout }),
    [user, token, isLoading, handleLogin, handleRegister, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
