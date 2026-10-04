import { API_BASE_URL, ApiError, apiFetch } from "../../api/client";
import type { User } from "../auth/types";

export function updateProfile(token: string, fullName: string): Promise<User> {
  return apiFetch<User>("/users/me/", token, {
    method: "PATCH",
    body: JSON.stringify({ full_name: fullName }),
  });
}

export async function uploadAvatar(token: string, file: File): Promise<User> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/users/me/avatar`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail =
      typeof body?.detail === "string" ? body.detail : `La petición falló con estado ${response.status}`;
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<User>;
}

export function deleteAvatar(token: string): Promise<void> {
  return apiFetch<void>("/users/me/avatar", token, { method: "DELETE" });
}

export async function fetchAvatarBlob(token: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/users/me/avatar`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new ApiError(response.status, "No se pudo cargar la foto de perfil");
  }
  return response.blob();
}
