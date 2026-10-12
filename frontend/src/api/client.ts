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

type SessionRefresher = () => Promise<string | null>;

let sessionRefresher: SessionRefresher | null = null;
let refreshInFlight: Promise<string | null> | null = null;

/** Registra cómo renovar la sesión (lo hace `AuthProvider`). Devuelve el
 * token de acceso nuevo, o `null` si no se pudo renovar. */
export function setSessionRefresher(refresher: SessionRefresher | null): void {
  sessionRefresher = refresher;
}

/** Una sola renovación a la vez: con refresh tokens rotativos, dos
 * renovaciones en paralelo con el mismo token harían fallar la segunda. */
function renewSession(): Promise<string | null> {
  if (!sessionRefresher) return Promise.resolve(null);
  refreshInFlight ??= sessionRefresher().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

/** `fetch` con `Authorization: Bearer`. Si responde 401 y había token,
 * renueva la sesión y repite la petición una sola vez con el token nuevo. */
export async function authorizedFetch(
  url: string,
  token: string | null | undefined,
  init: RequestInit = {},
): Promise<Response> {
  const send = (accessToken: string | null | undefined) =>
    fetch(url, {
      ...init,
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(init.headers as Record<string, string> | undefined),
      },
    });

  const response = await send(token);
  if (response.status !== 401 || !token) {
    return response;
  }
  const newToken = await renewSession();
  return newToken ? send(newToken) : response;
}

/** Lanza `ApiError` con el mensaje del backend si la respuesta falló. */
export async function throwIfNotOk(response: Response): Promise<void> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, extractErrorMessage(body, response.status));
  }
}

export async function apiFetch<T>(
  path: string,
  token?: string | null,
  init?: RequestInit,
): Promise<T> {
  const response = await authorizedFetch(`${API_BASE_URL}${path}`, token, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    },
  });

  await throwIfNotOk(response);

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
