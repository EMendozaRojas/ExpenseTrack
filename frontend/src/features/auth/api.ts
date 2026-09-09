import { apiFetch } from "../../api/client";
import type { AuthTokens, Credentials, User } from "./types";

export function register(credentials: Credentials): Promise<User> {
  return apiFetch<User>("/auth/register", null, {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function login(credentials: Credentials): Promise<AuthTokens> {
  const body = new URLSearchParams({
    username: credentials.email,
    password: credentials.password,
  });

  return apiFetch<AuthTokens>("/auth/login", null, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
}

export function fetchCurrentUser(token: string): Promise<User> {
  return apiFetch<User>("/auth/me", token);
}

export function logoutRequest(refreshToken: string): Promise<void> {
  return apiFetch<void>("/auth/logout", null, {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function googleLoginUrl(apiBaseUrl: string): string {
  return `${apiBaseUrl}/auth/oauth/google/start`;
}
