import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { setSessionRefresher } from "../../api/client";
import { updatePreferences } from "../preferences/api";
import {
  fetchCurrentUser,
  login as apiLogin,
  logoutRequest,
  refreshRequest,
  register as apiRegister,
} from "./api";
import { AuthContext, type AuthContextValue } from "./context";
import type { Credentials, User } from "./types";

const TOKEN_STORAGE_KEY = "expensetrack_token";
const REFRESH_TOKEN_STORAGE_KEY = "expensetrack_refresh_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => token !== null);

  // Se registra en el primer render (no en un efecto) para que esté lista
  // antes de las primeras peticiones de las pantallas hijas, cuyos efectos
  // se ejecutan antes que los de este proveedor.
  useState(() => {
    setSessionRefresher(async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
      try {
        if (!refreshToken) throw new Error("Sin refresh token");
        const tokens = await refreshRequest(refreshToken);
        localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);
        if (tokens.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, tokens.refresh_token);
        }
        setToken(tokens.access_token);
        return tokens.access_token;
      } catch {
        // La sesión caducó del todo: se cierra en local y la app vuelve al login.
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
        setToken(null);
        setUser(null);
        return null;
      }
    });
  });

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
          localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
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

  const storeTokens = useCallback(
    (accessToken: string, refreshToken: string | null | undefined) => {
      localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken);
      }
      setToken(accessToken);
    },
    [],
  );

  const handleLogin = useCallback(
    async (credentials: Credentials) => {
      const tokens = await apiLogin(credentials);
      storeTokens(tokens.access_token, tokens.refresh_token);
    },
    [storeTokens],
  );

  const handleRegister = useCallback(
    async (credentials: Credentials, baseCurrency?: string) => {
      await apiRegister(credentials);
      const tokens = await apiLogin(credentials);
      storeTokens(tokens.access_token, tokens.refresh_token);
      if (baseCurrency) {
        try {
          await updatePreferences(tokens.access_token, { base_currency: baseCurrency });
        } catch {
          // no bloquear el registro si falla guardar la moneda elegida
        }
      }
    },
    [storeTokens],
  );

  const refreshUser = useCallback(async () => {
    if (!token) return;
    const fetchedUser = await fetchCurrentUser(token);
    setUser(fetchedUser);
  }, [token]);

  const loginWithTokens = useCallback(
    (accessToken: string, refreshToken: string | null) => {
      storeTokens(accessToken, refreshToken);
    },
    [storeTokens],
  );

  const logout = useCallback(() => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
    if (refreshToken) {
      void logoutRequest(refreshToken).catch(() => {
        // best-effort: si falla la revocación remota, igual cerramos sesión local
      });
    }
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      login: handleLogin,
      register: handleRegister,
      loginWithTokens,
      logout,
      refreshUser,
    }),
    [user, token, isLoading, handleLogin, handleRegister, loginWithTokens, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
