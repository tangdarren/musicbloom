import type { HealthResponse } from "./types";

import { buildApiUrl } from "../config/env";
import { ApiError, NetworkError, type RootResponse } from "./types";

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const bodyText = await response.text();

  if (!response.ok) {
    throw new ApiError(
      `Request failed with status ${response.status}`,
      response.status,
      bodyText,
    );
  }

  if (!bodyText) {
    throw new ApiError("Empty response body", response.status, bodyText);
  }

  return JSON.parse(bodyText) as T;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const url = buildApiUrl(path);

  try {
    const response = await fetch(url, {
      ...init,
      method: "GET",
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });

    return parseJsonResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new NetworkError();
  }
}

export const apiClient = {
  getHealth: () => apiGet<HealthResponse>("/api/health"),
  getRoot: () => apiGet<RootResponse>("/"),
};
