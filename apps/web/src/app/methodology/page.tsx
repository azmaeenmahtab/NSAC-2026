"use client";

import React, { Suspense } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { QueryBoundary } from "@/components/feedback/query-boundary";
import { useMeta } from "@/features/shell";
import {
  useMethodology,
  MethodSteps,
  ValidationSummary,
  QQChart,
  JumpMetrics,
  ParametersTable,
  SourcesList,
  Limitations,
} from "@/features/methodology";

function MethodologyContent() {
  const {
    data: methodEnvelope,
    isLoading: isMethodLoading,
    isError: isMethodError,
    error: methodError,
    refetch: refetchMethod,
  } = useMethodology();

  const { data: metaEnvelope } = useMeta();

  const methodData = methodEnvelope?.data;
  const metaData = metaEnvelope?.data;

  return (
    <QueryBoundary
      isLoading={isMethodLoading}
      isError={isMethodError}
      error={methodError}
      data={methodData}
      onRetry={refetchMethod}
    >
      <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-8">
        {/* Page Hero */}
        <div className="space-y-1.5 border-b border-[#1f293d] pb-4">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-[#ff6b00]" />
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-[#ff6b00]">
              NASA Space Apps 2026 • Challenge Track
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-[#f8fafc]">
            Harmonization of MODIS and VIIRS Hot Spots
          </h1>
          <p className="text-xs md:text-sm text-[#94a3b8] leading-relaxed max-w-3xl">
            A scientifically honest, fully reproducible framework for bridging the structural
            gap between NASA 1km MODIS and 375m VIIRS active-fire observations into a continuous
            25-year Burning Activity Calendar.
          </p>
        </div>

        {/* 1. Step-by-Step Flow */}
        <MethodSteps />

        {/* 2. Jump Metrics Diagnostic */}
        <JumpMetrics metrics={methodData?.jump_metrics} />

        {/* 3. Cross-Validation & Unit Breakdown */}
        <ValidationSummary
          metrics={methodData?.jump_metrics}
          units={methodData?.calibration_summary}
        />

        {/* 4. Empirical Q-Q Distribution Plot */}
        <QQChart data={methodData?.qq_data} />

        {/* 5. Hyperparameters & Ingest Counts */}
        <ParametersTable
          parameters={methodData?.parameters}
          counts={metaData?.counts}
        />

        {/* 6. Authoritative Sources */}
        <SourcesList
          dataVersion={metaData?.dataVersion || methodEnvelope?.meta.dataVersion}
          asOf={metaData?.asOf || methodEnvelope?.meta.asOf}
          attribution={metaData?.attribution}
        />

        {/* 7. Known Scientific Limitations */}
        <Limitations limitations={methodData?.limitations} />
      </div>
    </QueryBoundary>
  );
}

export default function MethodologyPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#080b10] text-[#f8fafc]">
          Loading PyroScope Methodology...
        </div>
      }
    >
      <AppShell activeTab="methodology">
        <div className="flex-1 overflow-y-auto bg-[#080b10]">
          <MethodologyContent />
        </div>
      </AppShell>
    </Suspense>
  );
}
