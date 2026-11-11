import { AppShell } from "@/components/layout/app-shell";

export default function HomePage() {
  return (
    <AppShell
      sidePanelTitle="Analytical Telemetry"
      sidePanelContent={
        <div className="space-y-4 text-xs text-[#94a3b8]">
          <div className="rounded border border-[#1f293d] bg-[#161f30] p-3">
            <h4 className="font-semibold text-sm text-[#f8fafc] mb-1">
              Mission Control
            </h4>
            <p>
              Select an administrative region, district, or preset area to
              inspect harmonized burning trends.
            </p>
          </div>
        </div>
      }
    >
      <div className="flex h-full w-full items-center justify-center p-6 text-center">
        <div className="max-w-md space-y-2 rounded-xl border border-[#1f293d] bg-[#0e141f]/80 p-8 backdrop-blur-md">
          <div className="text-2xl">🔥</div>
          <h2 className="text-base font-semibold text-[#f8fafc]">
            PyroScope Hex Map Viewport
          </h2>
          <p className="text-xs text-[#94a3b8]">
            Interactive MapLibre + deck.gl H3 layer initialises here in Chunk F02.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
