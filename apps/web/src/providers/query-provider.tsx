"use client";

import React, { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { env } from "@/lib/env";

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  const [isMockReady, setIsMockReady] = useState(!env.useMocks);

  useEffect(() => {
    if (env.useMocks && typeof window !== "undefined") {
      import("@/mocks/browser")
        .then(({ worker }) => {
          if (worker) {
            return worker.start({ quiet: true });
          }
        })
        .then(() => setIsMockReady(true))
        .catch((err) => {
          console.error("Failed to start MSW worker:", err);
          setIsMockReady(true);
        });
    }
  }, []);

  if (!isMockReady) {
    return null;
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
