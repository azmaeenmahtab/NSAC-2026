"use client";

import * as React from "react";
import { useAreas } from "../api/use-areas";
import { parseBBox } from "../lib/bbox";
import { cn } from "@/lib/utils";

export interface AreaBreadcrumbProps {
  currentAreaId: string;
  onAreaChange?: (areaId: string) => void;
  className?: string;
}

export function AreaBreadcrumb({
  currentAreaId,
  onAreaChange,
  className,
}: AreaBreadcrumbProps) {
  const { data: areasResponse } = useAreas();

  const areaMap = React.useMemo(() => {
    const areas = areasResponse?.data || [];
    const map = new Map<string, (typeof areas)[0]>();
    for (const a of areas) {
      map.set(a.id, a);
    }
    return map;
  }, [areasResponse?.data]);

  const items = React.useMemo(() => {
    if (currentAreaId.startsWith("bbox:")) {
      const bbox = parseBBox(currentAreaId);
      if (bbox) {
        const [w, s, e, n] = bbox;
        return [
          { id: "BGD", label: "Bangladesh" },
          {
            id: currentAreaId,
            label: `BBox [${w.toFixed(1)}°E, ${s.toFixed(1)}°N to ${e.toFixed(1)}°E, ${n.toFixed(1)}°N]`,
          },
        ];
      }
      return [{ id: currentAreaId, label: "Custom Area" }];
    }

    const current = areaMap.get(currentAreaId);
    if (!current) {
      return [{ id: currentAreaId, label: currentAreaId }];
    }

    if (current.level === "preset") {
      return [
        { id: "BGD", label: "National" },
        { id: current.id, label: current.name },
      ];
    }

    if (current.level === "country") {
      return [{ id: current.id, label: current.name }];
    }

    if (current.level === "adm1") {
      return [
        { id: "BGD", label: "Bangladesh" },
        { id: current.id, label: current.name },
      ];
    }

    if (current.level === "adm2") {
      const parent = current.parent_id ? areaMap.get(current.parent_id) : null;
      return [
        { id: "BGD", label: "Bangladesh" },
        ...(parent ? [{ id: parent.id, label: parent.name }] : []),
        { id: current.id, label: current.name },
      ];
    }

    return [{ id: current.id, label: current.name }];
  }, [currentAreaId, areaMap]);

  return (
    <nav
      aria-label="Area hierarchy breadcrumb"
      className={cn("flex items-center gap-1.5 text-xs text-[#94a3b8]", className)}
    >
      {items.map((crumb, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <React.Fragment key={crumb.id}>
            {idx > 0 && <span className="text-[#64748b]">/</span>}
            {isLast || !onAreaChange ? (
              <span className="font-semibold text-[#f8fafc] truncate max-w-[180px]">
                {crumb.label}
              </span>
            ) : (
              <button
                type="button"
                onClick={() => onAreaChange(crumb.id)}
                className="hover:text-[#ff6b00] hover:underline transition-colors cursor-pointer truncate max-w-[140px]"
              >
                {crumb.label}
              </button>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
