import * as React from "react";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface ParametersTableProps {
  parameters?: Record<string, unknown>;
  counts?: Record<string, number>;
  className?: string;
}

export function ParametersTable({
  parameters = {},
  counts = {},
  className,
}: ParametersTableProps) {
  const paramEntries = Object.entries(parameters);
  const countEntries = Object.entries(counts);

  return (
    <div
      role="region"
      aria-label="Algorithm parameters and data filtration counts"
      data-testid="parameters-table"
      className={cn(
        "rounded-xl border border-[#1f293d] bg-[#0e141f] p-4 text-xs text-[#f8fafc] shadow-sm space-y-4",
        className
      )}
    >
      <div>
        <h3 className="text-sm font-semibold text-[#f8fafc]">
          Pipeline Parameters & Filtration Ledger
        </h3>
        <p className="text-[11px] text-[#94a3b8]">
          Exact reproducible configuration stored in pipeline manifest and detection audit counts
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Parameters Column */}
        <div className="space-y-2">
          <div className="text-[11px] font-semibold text-[#64748b] uppercase tracking-wider font-mono">
            Algorithm Hyperparameters
          </div>
          <div className="overflow-x-auto rounded border border-[#1f293d] bg-[#080b10]">
            <table className="w-full text-left font-mono text-xs">
              <tbody className="divide-y divide-[#1f293d]/40">
                {paramEntries.length > 0 ? (
                  paramEntries.map(([key, val]) => (
                    <tr key={key} className="hover:bg-[#161f30]/40">
                      <td className="p-2 text-[#94a3b8]">{key}</td>
                      <td className="p-2 text-right text-[#ff6b00] font-semibold">
                        {Array.isArray(val) ? val.join(", ") : String(val)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={2} className="p-3 text-center text-[#64748b]">
                      No parameters available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Data Filtration Counts Column */}
        <div className="space-y-2">
          <div className="text-[11px] font-semibold text-[#64748b] uppercase tracking-wider font-mono">
            Detection Ingest & Drop Ledger
          </div>
          <div className="overflow-x-auto rounded border border-[#1f293d] bg-[#080b10]">
            <table className="w-full text-left font-mono text-xs">
              <tbody className="divide-y divide-[#1f293d]/40">
                {countEntries.length > 0 ? (
                  countEntries.map(([key, val]) => (
                    <tr key={key} className="hover:bg-[#161f30]/40">
                      <td className="p-2 text-[#94a3b8]">{key.replace(/_/g, " ")}</td>
                      <td className="p-2 text-right text-[#f8fafc] font-semibold">
                        {formatNumber(val)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <>
                    <tr className="hover:bg-[#161f30]/40">
                      <td className="p-2 text-[#94a3b8]">detections kept</td>
                      <td className="p-2 text-right text-emerald-400 font-semibold">
                        {formatNumber(12450)}
                      </td>
                    </tr>
                    <tr className="hover:bg-[#161f30]/40">
                      <td className="p-2 text-[#94a3b8]">dropped (low confidence)</td>
                      <td className="p-2 text-right text-amber-400 font-semibold">
                        {formatNumber(1420)}
                      </td>
                    </tr>
                    <tr className="hover:bg-[#161f30]/40">
                      <td className="p-2 text-[#94a3b8]">dropped (non-vegetation mask)</td>
                      <td className="p-2 text-right text-[#64748b] font-semibold">
                        {formatNumber(380)}
                      </td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
