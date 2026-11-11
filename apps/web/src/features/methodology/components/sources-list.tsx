import * as React from "react";
import { cn } from "@/lib/utils";

export interface SourcesListProps {
  dataVersion?: string;
  asOf?: string;
  attribution?: string;
  className?: string;
}

const PRIMARY_SOURCES = [
  {
    name: "NASA FIRMS Active Fire Data",
    provider: "NASA LANCE / EOSDIS",
    details: "MODIS Collection 6.1 (1km) & VIIRS S-NPP (375m) archive and NRT thermal anomalies.",
    license: "NASA Open Data Policy (Public Domain)",
    link: "https://firms.modaps.eosdis.nasa.gov/",
  },
  {
    name: "geoBoundaries Administrative Boundaries",
    provider: "William & Mary geoBoundaries Research Lab",
    details: "ADM0 (National) and ADM2 (64 Districts) standardized geographic polygons (v6.0.0).",
    license: "Creative Commons Attribution 3.0 IGO (CC BY 3.0 IGO)",
    link: "https://www.geoboundaries.org/",
  },
  {
    name: "CARTO Dark Matter & OpenStreetMap",
    provider: "CARTO / OpenStreetMap Contributors",
    details: "High-contrast dark cartographic basemap tiles for geospatial situational awareness.",
    license: "ODbL / CC BY 4.0",
    link: "https://carto.com/basemaps/",
  },
] as const;

export function SourcesList({
  dataVersion = "v0.1.0-fixtures",
  asOf = "2025-12-31",
  attribution,
  className,
}: SourcesListProps) {
  return (
    <div
      role="region"
      aria-label="Authoritative data sources and licensing attribution"
      data-testid="sources-list"
      className={cn(
        "rounded-xl border border-[#1f293d] bg-[#0e141f] p-4 text-xs text-[#f8fafc] shadow-sm space-y-4",
        className
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1f293d]/60 pb-2">
        <div>
          <h3 className="text-sm font-semibold text-[#f8fafc]">
            Authoritative Data Lineage & Sources
          </h3>
          <p className="text-[11px] text-[#94a3b8]">
            Complete attribution, sensor versions, and open-source geographic boundaries
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="rounded bg-[#161f30] px-2 py-0.5 text-[#ff6b00] border border-[#2d3b55]">
            Dataset {dataVersion}
          </span>
          <span className="text-[#64748b]">As of {asOf}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {PRIMARY_SOURCES.map((s) => (
          <div
            key={s.name}
            className="flex flex-col justify-between rounded-lg border border-[#1f293d] bg-[#080b10] p-3 text-xs space-y-2"
          >
            <div>
              <div className="font-semibold text-xs text-[#f8fafc] mb-0.5">
                {s.name}
              </div>
              <div className="text-[10px] font-mono text-[#ff8533]">{s.provider}</div>
              <p className="text-[11px] text-[#94a3b8] mt-1.5 leading-relaxed">
                {s.details}
              </p>
            </div>
            <div className="pt-2 border-t border-[#1f293d]/50 text-[10px] text-[#64748b]">
              License: <span className="text-[#94a3b8]">{s.license}</span>
            </div>
          </div>
        ))}
      </div>

      {attribution && (
        <div className="rounded border border-[#1f293d]/50 bg-[#161f30]/40 p-2 text-[10px] text-[#64748b] font-mono">
          Required Notice: {attribution}
        </div>
      )}
    </div>
  );
}
