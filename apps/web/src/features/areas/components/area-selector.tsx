"use client";

import * as React from "react";
import { useAreas } from "../api/use-areas";
import type { AreaItem } from "../types";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export interface AreaSelectorProps {
  selectedId: string;
  onSelect: (areaId: string) => void;
  className?: string;
}

export function AreaSelector({
  selectedId,
  onSelect,
  className,
}: AreaSelectorProps) {
  const { data: areasResponse, isLoading } = useAreas();
  const [search, setSearch] = React.useState("");

  const filteredAreas = React.useMemo(() => {
    const areas = areasResponse?.data || [];
    if (!search.trim()) return areas;
    const query = search.toLowerCase().trim();
    return areas.filter((a) => {
      const matchName = a.name.toLowerCase().includes(query);
      const matchId = a.id.toLowerCase().includes(query);
      const matchAliases = a.aliases?.some((alias) =>
        alias.toLowerCase().includes(query)
      );
      return matchName || matchId || matchAliases;
    });
  }, [areasResponse?.data, search]);

  const presets = filteredAreas.filter((a) => a.level === "preset");
  const country = filteredAreas.filter((a) => a.level === "country");
  const divisions = filteredAreas.filter((a) => a.level === "adm1");
  const districts = filteredAreas.filter((a) => a.level === "adm2");

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <Input
        type="search"
        placeholder="Search area (e.g. CHT, Rangamati, Dhaka)..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="h-8 text-xs bg-[#080b10]"
        aria-label="Filter areas"
      />

      {isLoading ? (
        <div className="py-4 text-center text-xs text-[#64748b]">
          Loading regions...
        </div>
      ) : (
        <div className="max-h-60 overflow-y-auto space-y-3 pr-1 text-xs">
          {/* Presets */}
          {presets.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#ff6b00] mb-1 px-1">
                Featured Presets
              </div>
              <div className="space-y-0.5">
                {presets.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                  />
                ))}
              </div>
            </div>
          )}

          {/* National */}
          {country.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#94a3b8] mb-1 px-1">
                National Overview
              </div>
              <div className="space-y-0.5">
                {country.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Divisions */}
          {divisions.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#94a3b8] mb-1 px-1">
                Divisions (ADM1)
              </div>
              <div className="space-y-0.5">
                {divisions.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Districts */}
          {districts.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#94a3b8] mb-1 px-1">
                Districts (ADM2)
              </div>
              <div className="space-y-0.5">
                {districts.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                  />
                ))}
              </div>
            </div>
          )}

          {filteredAreas.length === 0 && (
            <div className="py-4 text-center text-xs text-[#64748b]">
              No matching regions found.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AreaRow({
  item,
  isSelected,
  onSelect,
}: {
  item: AreaItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(item.id)}
      className={cn(
        "flex w-full items-center justify-between rounded px-2 py-1.5 text-left transition-colors cursor-pointer",
        isSelected
          ? "bg-[#161f30] text-[#f8fafc] border border-[#ff6b00]/60 shadow-xs"
          : "text-[#94a3b8] hover:bg-[#161f30]/40 hover:text-[#f8fafc]"
      )}
    >
      <span className="font-medium truncate">{item.name}</span>
      <Badge
        variant={item.level === "preset" ? "accent" : "outline"}
        className="text-[10px] py-0 px-1.5 shrink-0"
      >
        {item.level}
      </Badge>
    </button>
  );
}
