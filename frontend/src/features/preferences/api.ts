import { apiFetch } from "../../api/client";
import type { UserPreferences, UserPreferencesUpdate } from "./types";

export function getPreferences(token: string): Promise<UserPreferences> {
  return apiFetch<UserPreferences>("/users/me/preferences/", token);
}

export function updatePreferences(
  token: string,
  payload: UserPreferencesUpdate,
): Promise<UserPreferences> {
  return apiFetch<UserPreferences>("/users/me/preferences/", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
