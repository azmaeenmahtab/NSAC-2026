# F06 Alerts UI

Depends: F03. Priority: P1. Window: EVENT. Read first: API_REFERENCE.md `/api/alerts/*`; A04.

## Goal
Show the current alert state for the selected area and let a user subscribe by email.

## Files (`apps/web/src/features/alerts/`)
`components/{alert-banner.tsx,subscribe-form.tsx,subscription-confirm.tsx,alert-state-card.tsx}`, `api/{use-active-alerts.ts,use-subscribe.ts}`, `types.ts`, `index.ts`; page `app/alerts/confirm/page.tsx` (reads `token`).

## Specification
- Banner at the top of the main screen when `seasonApproaching` is true or `aboveNormal` is `elevated` or `extreme`: states the area, the reason, days until the season start, the "provisional data as of <date>" and the advisory text.
- Subscribe form (React Hook Form + Zod): email, rule (season approaching, above normal, both), lead days (1 to 60, default 14), a required consent checkbox with a plain statement of what is stored (email and area only) and a link to unsubscribe; on success show "check your email". Handle 400, 404 and 429 with clear messages.
- Confirmation page calls the confirm endpoint and shows success or an expired-link message.
- Optional: browser Notification permission request for the banner state (P2).

## Tasks
- [x] Banner, subscribe form with validation, confirmation page
- [x] RTL tests: validation messages, 429 message, banner conditions
- [x] Master plan row F06 set to `[x]`
