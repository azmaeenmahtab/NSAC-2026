/**
 * Build direct-dial `tel:` and pre-filled `mailto:` links for emergency station contact.
 */

export function buildTelHref(phoneOrHotline: string): string {
  const cleaned = phoneOrHotline.replace(/[^0-9+]/g, "");
  return `tel:${cleaned || "102"}`;
}

export function buildMailtoHref(
  email: string | null | undefined,
  subject: string,
  body: string
): string {
  const to = email ? email.trim() : "";
  const params = new URLSearchParams({
    subject,
    body,
  });
  return `mailto:${to}?${params.toString().replace(/\+/g, "%20")}`;
}

