"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ToggleGroupContextValue {
  value: string;
  onValueChange: (val: string) => void;
}

const ToggleGroupContext = React.createContext<ToggleGroupContextValue | null>(null);

export interface ToggleGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  onValueChange: (val: string) => void;
}

export function ToggleGroup({
  value,
  onValueChange,
  className,
  children,
  ...props
}: ToggleGroupProps) {
  return (
    <ToggleGroupContext.Provider value={{ value, onValueChange }}>
      <div
        role="group"
        className={cn(
          "inline-flex items-center rounded-md bg-[#0e141f] p-0.5 border border-[#1f293d]",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </ToggleGroupContext.Provider>
  );
}

export interface ToggleGroupItemProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

export function ToggleGroupItem({
  value,
  className,
  children,
  ...props
}: ToggleGroupItemProps) {
  const context = React.useContext(ToggleGroupContext);
  if (!context) throw new Error("ToggleGroupItem must be within ToggleGroup");

  const isSelected = context.value === value;

  return (
    <button
      type="button"
      aria-pressed={isSelected}
      onClick={() => context.onValueChange(value)}
      className={cn(
        "inline-flex items-center justify-center rounded px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer select-none",
        isSelected
          ? "bg-[#161f30] text-[#f8fafc] border border-[#2d3b55] shadow-xs"
          : "text-[#94a3b8] hover:text-[#f8fafc] hover:bg-[#161f30]/40",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
