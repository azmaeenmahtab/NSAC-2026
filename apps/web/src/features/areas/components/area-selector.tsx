"use client";

import * as React from "react";
import { useAreas } from "../api/use-areas";
import type { AreaItem } from "../types";
import { BANGLADESH_NAMES_BN } from "../lib/bangla-names";
import { useLanguage } from "@/lib/i18n";
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
  const { t, isBangla } = useLanguage();

  const filteredAreas = React.useMemo(() => {
    const areas = areasResponse?.data || [];
    if (!search.trim()) return areas;
    const query = search.toLowerCase().trim();
    return areas.filter((a) => {
      const matchName = a.name.toLowerCase().includes(query);
      const matchId = a.id.toLowerCase().includes(query);
      const bnName = BANGLADESH_NAMES_BN[a.name];
      const matchBn = bnName ? bnName.includes(query) : false;
      const matchAliases = a.aliases?.some((alias) =>
        alias.toLowerCase().includes(query)
      );
      return matchName || matchId || matchBn || matchAliases;
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
        placeholder={isBangla ? t.side_panel.search_placeholder : "Search area (e.g. CHT, Rangamati, Dhaka)..."}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="h-8 text-xs bg-[#080b10]"
        aria-label="Filter areas"
      />

      {isLoading ? (
        <div className="py-4 text-center text-xs text-[#64748b]">
          {isBangla ? "এলাকা লোড হচ্ছে..." : "Loading regions..."}
        </div>
      ) : (
        <div className="max-h-60 overflow-y-auto space-y-3 pr-1 text-xs">
          {/* Presets */}
          {presets.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#ff6b00] mb-1 px-1">
                {isBangla ? t.side_panel.presets : "Featured Presets"}
              </div>
              <div className="space-y-0.5">
                {presets.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                    isBangla={isBangla}
                  />
                ))}
              </div>
            </div>
          )}

          {/* National */}
          {country.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#94a3b8] mb-1 px-1">
                {isBangla ? t.side_panel.country : "National Overview"}
              </div>
              <div className="space-y-0.5">
                {country.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                    isBangla={isBangla}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Divisions */}
          {divisions.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#94a3b8] mb-1 px-1">
                {isBangla ? t.side_panel.divisions : "Divisions"}
              </div>
              <div className="space-y-0.5">
                {divisions.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                    isBangla={isBangla}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Districts */}
          {districts.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-[#94a3b8] mb-1 px-1">
                {isBangla ? t.side_panel.districts : "Districts"}
              </div>
              <div className="space-y-0.5">
                {districts.map((item) => (
                  <AreaRow
                    key={item.id}
                    item={item}
                    isSelected={selectedId === item.id}
                    onSelect={onSelect}
                    isBangla={isBangla}
                  />
                ))}
              </div>
            </div>
          )}

          {filteredAreas.length === 0 && (
            <div className="py-4 text-center text-xs text-[#64748b]">
              {isBangla ? "কোনো এলাকা পাওয়া যায়নি।" : "No matching regions found."}
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
  isBangla,
}: {
  item: AreaItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
  isBangla?: boolean;
}) {
  const bnName = BANGLADESH_NAMES_BN[item.name];

  const levelLabel =
    item.level === "adm1"
      ? isBangla
        ? "বিভাগ"
        : "Division"
      : item.level === "adm2"
        ? isBangla
          ? "জেলা"
          : "District"
        : item.level === "preset"
          ? isBangla
            ? "অঞ্চল"
            : "Region"
          : isBangla
            ? "জাতীয়"
            : "Country";

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
      <div className="flex items-center gap-1.5 truncate">
        <span className="font-medium truncate">{item.name}</span>
        {bnName && (
          <span className="text-[11px] text-[#ff8533] font-normal truncate">
            ({bnName})
          </span>
        )}
      </div>
      <Badge
        variant={item.level === "preset" ? "accent" : "outline"}
        className="text-[10px] py-0 px-1.5 shrink-0"
      >
        {levelLabel}
      </Badge>
    </button>
  );
}
