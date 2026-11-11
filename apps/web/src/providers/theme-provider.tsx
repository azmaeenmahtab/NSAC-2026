"use client";

import React, { useEffect } from "react";

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  useEffect(() => {
    // Enforce dark mode at root level
    document.documentElement.classList.add("dark");
  }, []);

  return <>{children}</>;
}
