/** Application environment configuration loaded from Vite env variables. */

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";

export const env = {
  apiBaseUrl: configuredApiBaseUrl.replace(/\/$/, ""),
} as const;

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (!env.apiBaseUrl) {
    return normalizedPath;
  }

  return `${env.apiBaseUrl}${normalizedPath}`;
}
