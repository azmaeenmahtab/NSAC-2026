"use client";

import React, { useState } from "react";
import { useSubscribe } from "../api/use-subscribe";
import type { AlertRule, SubscriberType } from "../types";
import { ApiError } from "@/lib/api/errors";

interface SubscribeFormProps {
  areaId: string;
  areaName?: string;
  onSuccess?: () => void;
}

export function SubscribeForm({ areaId, areaName, onSuccess }: SubscribeFormProps) {
  const [email, setEmail] = useState("");
  const [subscriberType, setSubscriberType] = useState<SubscriberType>("public");
  const [stationName, setStationName] = useState("");
  const [phone, setPhone] = useState("");
  const [rule, setRule] = useState<AlertRule>("both");
  const [leadDays, setLeadDays] = useState(14);
  const [consent, setConsent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const subscribeMutation = useSubscribe();

  function validate(): boolean {
    setFormError(null);
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFormError("Please provide a valid email address.");
      return false;
    }
    if (leadDays < 1 || leadDays > 60 || isNaN(leadDays)) {
      setFormError("Advance notice must be between 1 and 60 days.");
      return false;
    }
    if (!consent) {
      setFormError("You must agree to the data consent terms to receive alerts.");
      return false;
    }
    return true;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    try {
      await subscribeMutation.mutateAsync({
        email: email.trim(),
        area_id: areaId,
        rule,
        lead_days: leadDays,
        subscriber_type: subscriberType,
        station_name:
          subscriberType === "fire_station" && stationName.trim()
            ? stationName.trim()
            : undefined,
        phone:
          subscriberType === "fire_station" && phone.trim() ? phone.trim() : undefined,
      });
      setIsSubmitted(true);
      if (onSuccess) onSuccess();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setFormError(
            "Subscription rate limit reached: maximum 5 requests per hour. Please wait before retrying."
          );
        } else if (err.status === 404) {
          setFormError("Area not found. Please select a valid monitoring region.");
        } else {
          setFormError(err.message || "Failed to submit subscription request.");
        }
      } else {
        setFormError("An unexpected network error occurred. Please try again.");
      }
    }
  }

  if (isSubmitted) {
    return (
      <div
        data-testid="subscribe-success"
        className="rounded-xl border border-emerald-500/40 bg-emerald-950/20 p-5 text-center space-y-2 text-xs"
      >
        <span className="text-2xl" aria-hidden="true">✉️</span>
        <h3 className="font-semibold text-white text-sm">Check your email</h3>
        <p className="text-emerald-300 leading-relaxed max-w-sm mx-auto">
          We sent a verification link to <strong className="text-white">{email}</strong>.
          Please click the link to confirm and activate your alert notifications for{" "}
          <strong className="text-white">{areaName || areaId}</strong>.
        </p>
      </div>
    );
  }

  return (
    <form
      data-testid="subscribe-form"
      onSubmit={handleSubmit}
      className="space-y-4 text-xs bg-[#0e1626] border border-[#1e293b] rounded-xl p-5"
    >
      <div>
        <h3 className="text-sm font-semibold text-white">Subscribe to Alerts</h3>
        <p className="text-[#94a3b8] text-[11px] mt-0.5">
          Get email notifications for seasonal shifts and fire anomalies in{" "}
          <span className="text-[#FF6B00] font-medium">{areaName || areaId}</span>.
        </p>
      </div>

      {formError && (
        <div
          role="alert"
          data-testid="form-error"
          className="p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-xs leading-snug"
        >
          {formError}
        </div>
      )}

      <div className="space-y-1.5">
        <span className="block font-medium text-[#cbd5e1]">I am subscribing as</span>
        <div className="grid grid-cols-2 gap-1.5">
          <button
            type="button"
            onClick={() => setSubscriberType("public")}
            className={`px-2.5 py-1.5 rounded-lg border text-[11px] font-medium cursor-pointer ${
              subscriberType === "public"
                ? "bg-[#ff6b00]/20 border-[#ff6b00] text-white"
                : "bg-[#141e30] border-[#233554] text-[#94a3b8]"
            }`}
          >
            Citizen / Researcher
          </button>
          <button
            type="button"
            onClick={() => setSubscriberType("fire_station")}
            className={`px-2.5 py-1.5 rounded-lg border text-[11px] font-medium cursor-pointer ${
              subscriberType === "fire_station"
                ? "bg-[#ff6b00]/20 border-[#ff6b00] text-white"
                : "bg-[#141e30] border-[#233554] text-[#94a3b8]"
            }`}
          >
            Fire Station
          </button>
        </div>
        {subscriberType === "fire_station" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1.5">
            <input
              type="text"
              value={stationName}
              onChange={(e) => setStationName(e.target.value)}
              placeholder="Station Name (e.g. Rangamati)"
              aria-label="Fire Station Name"
              className="w-full px-3 py-1.5 rounded-lg bg-[#141e30] border border-[#233554] text-white placeholder-[#64748b] focus:border-[#FF6B00] focus:outline-none"
            />
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="Station Phone (optional)"
              aria-label="Fire Station Phone"
              className="w-full px-3 py-1.5 rounded-lg bg-[#141e30] border border-[#233554] text-white placeholder-[#64748b] focus:border-[#FF6B00] focus:outline-none"
            />
          </div>
        )}
      </div>

      <div className="space-y-1.5">
        <label htmlFor="sub-email" className="block font-medium text-[#cbd5e1]">
          Email Address <span className="text-[#ef4444]">*</span>
        </label>
        <input
          id="sub-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="forester@forest.gov.bd"
          required
          className="w-full px-3 py-2 rounded-lg bg-[#141e30] border border-[#233554] text-white placeholder-[#64748b] focus:border-[#FF6B00] focus:outline-none"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="sub-rule" className="block font-medium text-[#cbd5e1]">
          Alert Conditions
        </label>
        <select
          id="sub-rule"
          value={rule}
          onChange={(e) => setRule(e.target.value as AlertRule)}
          className="w-full px-3 py-2 rounded-lg bg-[#141e30] border border-[#233554] text-white focus:border-[#FF6B00] focus:outline-none"
        >
          <option value="both">Both (Season Approaching & Elevated Anomalies)</option>
          <option value="season_approaching">Season Approaching Only</option>
          <option value="above_normal">Elevated / Extreme Anomalies Only</option>
        </select>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="sub-lead-days" className="block font-medium text-[#cbd5e1]">
          Lead Notice Window (Days before season onset)
        </label>
        <input
          id="sub-lead-days"
          type="number"
          min={1}
          max={60}
          value={leadDays}
          onChange={(e) => setLeadDays(parseInt(e.target.value, 10))}
          className="w-full px-3 py-2 rounded-lg bg-[#141e30] border border-[#233554] text-white focus:border-[#FF6B00] focus:outline-none"
        />
        <span className="text-[10px] text-[#64748b]">Between 1 and 60 days (default: 14)</span>
      </div>

      <div className="pt-2 border-t border-[#1e293b] space-y-2">
        <label className="flex items-start gap-2.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            required
            className="mt-0.5 h-4 w-4 rounded border-[#334155] bg-[#141e30] text-[#FF6B00] focus:ring-[#FF6B00]"
          />
          <span className="text-[11px] text-[#94a3b8] leading-tight">
            I consent to receiving email notifications. Only email and chosen region ID
            are stored. No commercial tracking. You can{" "}
            <span className="text-[#38bdf8] underline">unsubscribe at any time</span> via the link in any notification.
          </span>
        </label>
      </div>

      <button
        type="submit"
        disabled={subscribeMutation.isPending}
        className="w-full py-2.5 px-4 rounded-lg bg-[#FF6B00] hover:bg-[#e05e00] text-white font-semibold transition-colors disabled:opacity-50 cursor-pointer shadow-xs"
      >
        {subscribeMutation.isPending ? "Subscribing..." : "Subscribe to Alerts"}
      </button>
    </form>
  );
}

