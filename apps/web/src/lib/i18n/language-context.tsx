"use client";

import React, { createContext, useContext, useState, useMemo, useCallback } from "react";
import type { Language, TranslationDictionary } from "./types";
import { EN_TRANSLATIONS, BN_TRANSLATIONS } from "./translations";

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  isBangla: boolean;
  t: TranslationDictionary;
}

const STORAGE_KEY = "pyroscope_lang";

const LanguageContext = createContext<LanguageContextValue>({
  language: "en",
  setLanguage: () => {},
  toggleLanguage: () => {},
  isBangla: false,
  t: EN_TRANSLATIONS,
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem(STORAGE_KEY) as Language | null;
        if (saved === "bn" || saved === "en") {
          return saved;
        }
      } catch {
        // Storage access may fail in restricted iframe contexts
      }
    }
    return "en";
  });

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // Ignore storage errors
    }
  }, []);

  const toggleLanguage = useCallback(() => {
    setLanguageState((prev) => {
      const nextLang: Language = prev === "en" ? "bn" : "en";
      try {
        localStorage.setItem(STORAGE_KEY, nextLang);
      } catch {
        // Ignore storage errors
      }
      return nextLang;
    });
  }, []);

  const value = useMemo<LanguageContextValue>(() => {
    const dict = language === "bn" ? BN_TRANSLATIONS : EN_TRANSLATIONS;
    return {
      language,
      setLanguage,
      toggleLanguage,
      isBangla: language === "bn",
      t: dict,
    };
  }, [language, setLanguage, toggleLanguage]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  return useContext(LanguageContext);
}
