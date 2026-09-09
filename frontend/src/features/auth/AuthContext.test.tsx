import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { AuthProvider } from "./AuthContext";
import { useAuth } from "./useAuth";

vi.mock("./api");

const demoUser = { id: 1, email: "demo@example.com", created_at: "2026-01-01T00:00:00Z" };

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
  });

  it("inicia sesión y guarda el usuario", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "abc123", token_type: "bearer" });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login({ email: demoUser.email, password: "secret123" });
    });

    await waitFor(() => expect(result.current.user?.email).toBe(demoUser.email));
    expect(localStorage.getItem("expensetrack_token")).toBe("abc123");
  });

  it("cierra sesión y limpia el token guardado", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "abc123", token_type: "bearer" });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login({ email: demoUser.email, password: "secret123" });
    });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    act(() => result.current.logout());

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("expensetrack_token")).toBeNull();
  });

  it("restaura la sesión a partir de un token guardado en localStorage", async () => {
    localStorage.setItem("expensetrack_token", "existing-token");
    vi.mocked(api.fetchCurrentUser).mockResolvedValue({
      id: 2,
      email: "restored@example.com",
      created_at: "2026-01-01T00:00:00Z",
    });

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.user?.email).toBe("restored@example.com"));
    expect(api.fetchCurrentUser).toHaveBeenCalledWith("existing-token");
  });

  it("descarta el token si ya no es válido", async () => {
    localStorage.setItem("expensetrack_token", "expired-token");
    vi.mocked(api.fetchCurrentUser).mockRejectedValue(new Error("401"));

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("expensetrack_token")).toBeNull();
  });

  it("loginWithTokens guarda access y refresh token (callback de login social)", async () => {
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.loginWithTokens("access-abc", "refresh-xyz"));

    await waitFor(() => expect(result.current.user?.email).toBe(demoUser.email));
    expect(localStorage.getItem("expensetrack_token")).toBe("access-abc");
    expect(localStorage.getItem("expensetrack_refresh_token")).toBe("refresh-xyz");
  });

  it("logout revoca el refresh token guardado en el backend", async () => {
    vi.mocked(api.login).mockResolvedValue({
      access_token: "abc123",
      token_type: "bearer",
      refresh_token: "refresh-1",
    });
    vi.mocked(api.fetchCurrentUser).mockResolvedValue(demoUser);
    vi.mocked(api.logoutRequest).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login({ email: demoUser.email, password: "secret123" });
    });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    act(() => result.current.logout());

    expect(api.logoutRequest).toHaveBeenCalledWith("refresh-1");
    expect(localStorage.getItem("expensetrack_refresh_token")).toBeNull();
  });
});
