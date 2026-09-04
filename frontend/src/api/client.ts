export const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const API_ROOT_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ErrorBody {
  detail?: string | { msg?: string }[];
}

function extractErrorMessage(body: unknown, status: number): string {
  const errorBody = body as ErrorBody | null;
  if (typeof errorBody?.detail === "string") {
    return errorBody.detail;
  }
  if (Array.isArray(errorBody?.detail) && errorBody.detail[0]?.msg) {
    return errorBody.detail[0].msg;
  }
  return `La petición falló con estado ${status}`;
}

export async function apiFetch<T>(
  path: string,
  token?: string | null,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, extractErrorMessage(body, response.status));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export interface HealthStatus {
  status: string;
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_ROOT_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthStatus>;
}
