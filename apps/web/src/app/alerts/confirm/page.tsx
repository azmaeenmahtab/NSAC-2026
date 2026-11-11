"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { SubscriptionConfirm } from "@/features/alerts";

function ConfirmContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  return <SubscriptionConfirm token={token} />;
}

export default function ConfirmPage() {
  return (
    <div className="min-h-screen bg-[#080b10] flex items-center justify-center p-4">
      <Suspense
        fallback={
          <div className="text-xs text-[#94a3b8] text-center animate-pulse">
            Loading confirmation...
          </div>
        }
      >
        <ConfirmContent />
      </Suspense>
    </div>
  );
}

