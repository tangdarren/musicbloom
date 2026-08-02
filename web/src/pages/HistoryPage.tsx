import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient, resolveMediaPath } from "../api/client";
import type { ListeningStatus, RecentBloomItem } from "../api/types";
import { LoadingState } from "../components/LoadingState";
import { PageCard } from "../components/PageCard";

const RECENT_BLOOMS_KEY = ["history", "recent"] as const;

function statusLabel(status: ListeningStatus): string {
  switch (status) {
    case "completed":
      return "Completed";
    case "skipped":
      return "Skipped";
    default:
      return "Played";
  }
}

function formatDayHeading(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  const sameDay = (left: Date, right: Date) =>
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate();

  if (sameDay(date, today)) {
    return "Today";
  }
  if (sameDay(date, yesterday)) {
    return "Yesterday";
  }
  return date.toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function dayKey(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

function groupByDate(items: RecentBloomItem[]): Array<{
  key: string;
  heading: string;
  items: RecentBloomItem[];
}> {
  const groups = new Map<string, { heading: string; items: RecentBloomItem[] }>();

  for (const item of items) {
    const key = dayKey(item.occurred_at);
    const existing = groups.get(key);
    if (existing) {
      existing.items.push(item);
      continue;
    }
    groups.set(key, {
      heading: formatDayHeading(item.occurred_at),
      items: [item],
    });
  }

  return [...groups.entries()].map(([key, group]) => ({
    key,
    heading: group.heading,
    items: group.items,
  }));
}

function BloomHistoryItem({ item }: { item: RecentBloomItem }) {
  const artworkSrc = resolveMediaPath(item.artwork);

  return (
    <li className="recent-blooms__item">
      <div className="recent-blooms__artwork" aria-hidden="true">
        {artworkSrc ? (
          <img src={artworkSrc} alt="" />
        ) : (
          <span>{item.title.slice(0, 1)}</span>
        )}
      </div>
      <div className="recent-blooms__meta">
        <strong className="recent-blooms__title">{item.title}</strong>
        <span className="muted">{item.artist_name}</span>
      </div>
      <div className="recent-blooms__status-block">
        <span
          className={`recent-blooms__status recent-blooms__status--${item.listening_status}`}
        >
          {statusLabel(item.listening_status)}
        </span>
        <time className="muted" dateTime={item.occurred_at}>
          {formatTime(item.occurred_at)}
        </time>
      </div>
    </li>
  );
}

export function HistoryPage() {
  const historyQuery = useQuery({
    queryKey: RECENT_BLOOMS_KEY,
    queryFn: () => apiClient.getRecentBlooms(),
  });

  const groups = useMemo(
    () => groupByDate(historyQuery.data?.items ?? []),
    [historyQuery.data?.items],
  );

  return (
    <PageCard
      eyebrow="Recent Blooms"
      title="Listening history"
      lede="Tracks you have played, completed, or skipped in the garden, newest blooms first."
    >
      {historyQuery.isLoading ? (
        <LoadingState label="Gathering recent blooms" />
      ) : null}

      {historyQuery.isError ? (
        <div className="player-alert" role="alert">
          Unable to load listening history. Please try again in a moment.
        </div>
      ) : null}

      {historyQuery.isSuccess && groups.length === 0 ? (
        <p className="muted" role="status">
          No blooms yet. Play a demo track in the visual player to grow your
          listening history.
        </p>
      ) : null}

      {historyQuery.isSuccess && groups.length > 0 ? (
        <div className="recent-blooms">
          {groups.map((group) => (
            <section key={group.key} className="recent-blooms__day">
              <h2 className="recent-blooms__day-heading">{group.heading}</h2>
              <ul className="recent-blooms__list">
                {group.items.map((item) => (
                  <BloomHistoryItem key={item.id} item={item} />
                ))}
              </ul>
            </section>
          ))}
        </div>
      ) : null}
    </PageCard>
  );
}
