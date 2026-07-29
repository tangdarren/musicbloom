import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const defaultQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

interface QueryProviderProps {
  children: ReactNode;
  client?: QueryClient;
}

export function QueryProvider({
  children,
  client = defaultQueryClient,
}: QueryProviderProps) {
  return (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}
