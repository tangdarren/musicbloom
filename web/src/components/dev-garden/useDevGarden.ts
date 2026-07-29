import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import { isDevGardenDataStale } from "./devGardenState";

function useCurrentTime(intervalMs: number): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setNow(Date.now());
    }, intervalMs);

    return () => window.clearInterval(intervalId);
  }, [intervalMs]);

  return now;
}

export function useDevGarden() {
  const now = useCurrentTime(5_000);

  const statusQuery = useQuery({
    queryKey: ["devops", "status"],
    queryFn: () => apiClient.getDevOpsStatus(),
    refetchInterval: 30_000,
  });

  const runsQuery = useQuery({
    queryKey: ["devops", "runs"],
    queryFn: () => apiClient.getDevOpsRuns(),
    refetchInterval: 30_000,
  });

  const lastUpdatedAt = Math.max(
    statusQuery.dataUpdatedAt,
    runsQuery.dataUpdatedAt,
  );

  const isStale = isDevGardenDataStale(lastUpdatedAt, now);

  const refresh = async () => {
    await Promise.all([statusQuery.refetch(), runsQuery.refetch()]);
  };

  return {
    status: statusQuery.data,
    runs: runsQuery.data,
    isLoading: statusQuery.isLoading || runsQuery.isLoading,
    isFetching: statusQuery.isFetching || runsQuery.isFetching,
    isError: statusQuery.isError || runsQuery.isError,
    errorMessage:
      statusQuery.error instanceof Error
        ? statusQuery.error.message
        : runsQuery.error instanceof Error
          ? runsQuery.error.message
          : "Unable to load Dev Garden pipeline data.",
    isStale,
    lastUpdatedAt,
    refresh,
  };
}
