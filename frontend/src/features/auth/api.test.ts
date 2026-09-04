import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchCurrentUser, login, register } from "./api";

function mockFetchOnce(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("auth api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("register envía email y password como JSON", async () => {
    const fetchMock = mockFetchOnce({ id: 1, email: "demo@example.com" });

    await register({ email: "demo@example.com", password: "secret123" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/auth/register");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ email: "demo@example.com", password: "secret123" });
  });

  it("login envía las credenciales como application/x-www-form-urlencoded", async () => {
    const fetchMock = mockFetchOnce({ access_token: "abc", token_type: "bearer" });

    await login({ email: "demo@example.com", password: "secret123" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/auth/login");
    expect(init.headers["Content-Type"]).toBe("application/x-www-form-urlencoded");
    expect(init.body).toBe("username=demo%40example.com&password=secret123");
  });

  it("fetchCurrentUser consulta /auth/me con el token", async () => {
    const fetchMock = mockFetchOnce({ id: 1, email: "demo@example.com" });

    await fetchCurrentUser("token-123");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/auth/me");
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });
});
