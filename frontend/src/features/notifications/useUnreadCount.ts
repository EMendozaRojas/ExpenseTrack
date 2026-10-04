import { useQuery } from "@tanstack/react-query";

import { getUnreadCount } from "./api";

const POLL_INTERVAL_MS = 60 * 1000;

export function useUnreadCount(token: string | null): number {
  const query = useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: () => getUnreadCount(token as string),
    enabled: token !== null,
    refetchInterval: POLL_INTERVAL_MS,
  });

  return query.data?.count ?? 0;
}
