import { API_BASE_URL, ApiError, apiFetch, authorizedFetch, throwIfNotOk } from "../../api/client";
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

  const response = await authorizedFetch(`${API_BASE_URL}/users/me/avatar`, token, {
    method: "POST",
    body: formData,
  });

  await throwIfNotOk(response);

  return response.json() as Promise<User>;
}

export function deleteAvatar(token: string): Promise<void> {
  return apiFetch<void>("/users/me/avatar", token, { method: "DELETE" });
}

export async function fetchAvatarBlob(token: string): Promise<Blob> {
  const response = await authorizedFetch(`${API_BASE_URL}/users/me/avatar`, token);
  if (!response.ok) {
    throw new ApiError(response.status, "No se pudo cargar la foto de perfil");
  }
  return response.blob();
}
