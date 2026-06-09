import type {
  BackendHealthResponse,
  WeatherInsightFromSearchResponse,
  WeatherSearchRecord,
  WeatherSearchResponse,
} from "./types";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1";
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? DEFAULT_BASE_URL;

export class ApiError extends Error {
  status: number;
  code: string | null;
  details: unknown;

  constructor(message: string, status: number, code: string | null = null, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

function extractErrorMessage(payload: unknown, fallback: string): { message: string; code: string | null; details: unknown } {
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    if ("error" in record && record.error && typeof record.error === "object") {
      const error = record.error as Record<string, unknown>;
      return {
        message:
          typeof error.message === "string"
            ? error.message
            : typeof error.detail === "string"
              ? error.detail
              : fallback,
        code: typeof error.code === "string" ? error.code : null,
        details: "details" in error ? error.details : payload,
      };
    }

    return {
      message:
        typeof record.message === "string"
          ? record.message
          : typeof record.detail === "string"
            ? record.detail
            : fallback,
      code: typeof record.code === "string" ? record.code : null,
      details: "details" in record ? record.details : payload,
    };
  }

  if (typeof payload === "string" && payload.trim()) {
    return { message: payload, code: null, details: payload };
  }

  return { message: fallback, code: null, details: payload };
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Accept", "application/json");

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(buildUrl(path), {
    ...init,
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const rawText = await response.text();
  let payload: unknown = null;

  if (rawText) {
    try {
      payload = JSON.parse(rawText);
    } catch {
      payload = rawText;
    }
  }

  if (!response.ok) {
    const extracted = extractErrorMessage(payload, response.statusText || "Request failed");
    throw new ApiError(extracted.message, response.status, extracted.code, extracted.details);
  }

  return payload as T;
}

export function getBackendHealth(): Promise<BackendHealthResponse> {
  return requestJson<BackendHealthResponse>("/health");
}

export function searchWeather(query: string): Promise<WeatherSearchResponse> {
  return requestJson<WeatherSearchResponse>(`/weather/search?q=${encodeURIComponent(query)}`);
}

export function listSearches(): Promise<WeatherSearchRecord[]> {
  return requestJson<WeatherSearchRecord[]>("/searches");
}

export function getSearchById(searchId: number): Promise<WeatherSearchRecord> {
  return requestJson<WeatherSearchRecord>(`/searches/${searchId}`);
}

export function updateSearchNotes(searchId: number, notes: string | null): Promise<WeatherSearchRecord> {
  return requestJson<WeatherSearchRecord>(`/searches/${searchId}`, {
    method: "PUT",
    body: JSON.stringify({
      notes,
    }),
  });
}

export function deleteSearch(searchId: number): Promise<void> {
  return requestJson<void>(`/searches/${searchId}`, {
    method: "DELETE",
  });
}

export function generateInsightFromSearch(searchId: number): Promise<WeatherInsightFromSearchResponse> {
  return requestJson<WeatherInsightFromSearchResponse>(`/ai/insight/${searchId}`, {
    method: "POST",
  });
}
