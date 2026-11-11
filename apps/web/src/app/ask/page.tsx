import { AppShell } from "@/components/layout/app-shell";

export default function AskPage() {
  return (
    <AppShell activeTab="ask">
      <div className="flex h-full w-full items-center justify-center p-6 text-center">
        <div className="max-w-lg space-y-2 rounded-xl border border-[#1f293d] bg-[#0e141f] p-8">
          <h2 className="text-base font-semibold text-[#f8fafc]">
            Ask PyroScope Assistant
          </h2>
          <p className="text-xs text-[#94a3b8]">
            Natural-language queries backed by typed API tools load here in Chunk F07.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
