import * as React from "react";
import { cn } from "@/lib/utils";

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[#1e293b]/80 border border-[#2d3b55]/40",
        className
      )}
      {...props}
    />
  );
}
