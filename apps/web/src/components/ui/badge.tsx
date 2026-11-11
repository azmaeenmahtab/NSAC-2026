import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors border select-none",
  {
    variants: {
      variant: {
        default:
          "border-[#2d3b55] bg-[#161f30] text-[#94a3b8]",
        accent:
          "border-[rgba(255,107,0,0.4)] bg-[rgba(255,107,0,0.12)] text-[#ff6b00]",
        normal:
          "border-[#065f46] bg-[#10b981]/15 text-[#10b981]",
        elevated:
          "border-[#d97706] border-dashed bg-[#f59e0b]/15 text-[#f59e0b]",
        extreme:
          "border-[#dc2626] bg-[#ef4444]/20 text-[#ef4444] animate-pulse",
        outline:
          "border-[#2d3b55] text-[#94a3b8] bg-transparent",
        provisional:
          "border-amber-500/50 bg-amber-500/10 text-amber-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
