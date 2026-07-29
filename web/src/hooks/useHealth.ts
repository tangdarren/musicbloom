import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";

export const healthQueryKey = ["health"] as const;

export function useHealthQuery() {
  return useQuery({
    queryKey: healthQueryKey,
    queryFn: () => apiClient.getHealth(),
    retry: 0,
    staleTime: 30_000,
  });
}
