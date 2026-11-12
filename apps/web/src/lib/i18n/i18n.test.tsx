import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LanguageProvider, useLanguage } from "./language-context";
import { EN_TRANSLATIONS, BN_TRANSLATIONS } from "./translations";

function TestComponent() {
  const { language, setLanguage, toggleLanguage, isBangla, t } = useLanguage();

  return (
    <div>
      <div data-testid="current-lang">{language}</div>
      <div data-testid="is-bangla">{isBangla ? "yes" : "no"}</div>
      <div data-testid="nav-label">{t.header.nav_map_calendar}</div>
      <div data-testid="planner-title">{t.planner.title}</div>
      <div data-testid="emergency-rule">{t.planner.rule_4}</div>
      <button onClick={() => setLanguage("bn")}>Set Bangla</button>
      <button onClick={() => setLanguage("en")}>Set English</button>
      <button onClick={toggleLanguage}>Toggle Lang</button>
    </div>
  );
}

describe("i18n Bilingual Context & Translations", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("defaults to English with comprehensive dictionary keys", () => {
    render(
      <LanguageProvider>
        <TestComponent />
      </LanguageProvider>
    );

    expect(screen.getByTestId("current-lang").textContent).toBe("en");
    expect(screen.getByTestId("is-bangla").textContent).toBe("no");
    expect(screen.getByTestId("nav-label").textContent).toBe("Map & Calendar");
    expect(screen.getByTestId("planner-title").textContent).toBe(
      "Wildland & Farm Fire Action Planner"
    );
    expect(screen.getByTestId("emergency-rule").textContent).toContain("999 or 102");
  });

  it("switches to Bangla and updates translations across all components", () => {
    render(
      <LanguageProvider>
        <TestComponent />
      </LanguageProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "Set Bangla" }));

    expect(screen.getByTestId("current-lang").textContent).toBe("bn");
    expect(screen.getByTestId("is-bangla").textContent).toBe("yes");
    expect(screen.getByTestId("nav-label").textContent).toBe("মানচিত্র ও দিনপঞ্জি");
    expect(screen.getByTestId("planner-title").textContent).toBe(
      "গ্রাম ও কৃষিজমি আগুন সুরক্ষা গাইড"
    );
    expect(screen.getByTestId("emergency-rule").textContent).toContain("৯৯৯ বা ১০২");
  });

  it("toggles between English and Bangla seamlessly", () => {
    render(
      <LanguageProvider>
        <TestComponent />
      </LanguageProvider>
    );

    const toggleBtn = screen.getByRole("button", { name: "Toggle Lang" });

    // Toggle to bn
    fireEvent.click(toggleBtn);
    expect(screen.getByTestId("current-lang").textContent).toBe("bn");

    // Toggle back to en
    fireEvent.click(toggleBtn);
    expect(screen.getByTestId("current-lang").textContent).toBe("en");
  });

  it("has matching translation keys between English and Bengali dictionaries", () => {
    expect(Object.keys(EN_TRANSLATIONS)).toEqual(Object.keys(BN_TRANSLATIONS));
    for (const section of Object.keys(EN_TRANSLATIONS) as (keyof typeof EN_TRANSLATIONS)[]) {
      expect(Object.keys(EN_TRANSLATIONS[section])).toEqual(
        Object.keys(BN_TRANSLATIONS[section])
      );
    }
  });
});
