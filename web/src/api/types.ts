/** Typed API response models for the MusicBloom backend. */

export interface HealthResponse {
  status: string;
  service: string;
}

export interface RootResponse {
  name: string;
  tagline: string;
  version: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: string;

  constructor(message: string, status: number, body: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export class NetworkError extends Error {
  constructor(message = "Unable to reach the MusicBloom API.") {
    super(message);
    this.name = "NetworkError";
  }
}
