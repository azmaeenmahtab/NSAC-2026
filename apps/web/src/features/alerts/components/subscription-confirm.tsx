"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiGetData } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { ConfirmResponse } from "../types";

interface SubscriptionConfirmProps {
  token: string | null;
}

export function SubscriptionConfirm({ token }: SubscriptionConfirmProps) {
  const [loading, setLoading] = useState(Boolean(token));
  const [confirmed, setConfirmed] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    token ? null : "No confirmation token was provided in the link."
  );

  useEffect(() => {
    if (!token) return;

    let isMounted = true;
    apiGetData<ConfirmResponse>("/alerts/subscriptions/confirm", { token })
      .then((res) => {
        if (isMounted) {
          setConfirmed(res.confirmed);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setLoading(false);
          setErrorMessage(
            err instanceof ApiError
              ? err.message
              : "This confirmation link has expired or is invalid."
          );
        }
      });

    return () => {
      isMounted = false;
    };
  }, [token]);

  return (
    <div
      data-testid="subscription-confirm-card"
      className="max-w-md mx-auto p-6 rounded-xl bg-[#0e1626] border border-[#1e293b] text-center space-y-4"
    >
      {loading && (
        <div className="py-8 space-y-2">
          <div className="text-2xl animate-spin">⏳</div>
          <p className="text-xs text-[#94a3b8] animate-pulse">
            Verifying your alert subscription token...
          </p>
        </div>
      )}

      {!loading && confirmed && (
        <div className="space-y-3">
          <div className="text-3xl">✅</div>
          <h2 className="text-base font-bold text-white">Subscription Confirmed</h2>
          <p className="text-xs text-emerald-300 leading-relaxed">
            Your alert subscription is now active! You will receive email notifications
            ahead of seasonal fire shifts and anomalous thermal detections.
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="inline-block px-4 py-2 rounded-lg bg-[#FF6B00] hover:bg-[#e05e00] text-white text-xs font-semibold transition-colors"
            >
              Return to PyroScope Map
            </Link>
          </div>
        </div>
      )}

      {!loading && !confirmed && (
        <div className="space-y-3">
          <div className="text-3xl">⚠️</div>
          <h2 className="text-base font-bold text-white">Confirmation Failed</h2>
          <p className="text-xs text-red-300 leading-relaxed">
            {errorMessage || "This subscription link has expired or is invalid."}
          </p>
          <p className="text-[11px] text-[#64748b]">
            Please return to the main dashboard to submit a new subscription request.
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="inline-block px-4 py-2 rounded-lg bg-[#162238] hover:bg-[#1e2e4a] text-[#cbd5e1] text-xs font-medium border border-[#233554] transition-colors"
            >
              Return to PyroScope Map
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
