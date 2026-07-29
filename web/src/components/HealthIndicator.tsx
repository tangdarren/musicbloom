import { useHealthQuery } from "../hooks/useHealth";

export function HealthIndicator() {
  const { data, isLoading, isError, isFetching } = useHealthQuery();

  if (isLoading) {
    return (
      <span className="health-indicator health-indicator--loading" role="status">
        Checking API…
      </span>
    );
  }

  if (isError || !data) {
    return (
      <span className="health-indicator health-indicator--offline" role="status">
        API offline
      </span>
    );
  }

  const isHealthy = data.status === "healthy";

  return (
    <span
      className={`health-indicator ${
        isHealthy
          ? "health-indicator--healthy"
          : "health-indicator--offline"
      }`}
      role="status"
      aria-live="polite"
      title={`${data.service}${isFetching ? " (refreshing)" : ""}`}
    >
      API {isHealthy ? "healthy" : data.status}
    </span>
  );
}
