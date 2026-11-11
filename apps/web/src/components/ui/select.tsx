import * as React from "react";
import { cn } from "@/lib/utils";

export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className="relative inline-block w-full">
        <select
          ref={ref}
          className={cn(
            "flex h-9 w-full appearance-none rounded-md border border-[#2d3b55] bg-[#0e141f] px-3 py-1 pr-8 text-xs text-[#f8fafc] shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#ff6b00] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer",
            className
          )}
          {...props}
        >
          {children}
        </select>
        <span className="pointer-events-none absolute right-2.5 top-2.5 text-[#64748b]">
          ▼
        </span>
      </div>
    );
  }
);
Select.displayName = "Select";
