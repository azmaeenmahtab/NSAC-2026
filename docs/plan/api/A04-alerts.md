# A04 Alert subscriptions and evaluation

Depends: A03, D08. Priority: P1. Window: EVENT. Read first: DB_SCHEMA.md section 4; the chosen email provider's current docs (VERIFY).

## Goal
Let users subscribe to an area and receive a notice when the fire season is about to start or the current month is above normal; show the same state in the app.

## Files (`services/api/app/features/alerts/`)
`router.py`, `service.py`, `repository.py` (SQLite), `evaluate.py` (pure), `mailer.py` (provider adapter + console fallback), `schemas.py`, `tests/`. Script `services/api/scripts/send_alerts.py` run daily by the scheduled workflow.

## Specification
- `POST /api/alerts/subscriptions` `{ email, area_id, rule, lead_days }` (validate email, area exists, `lead_days` 1 to 60, default 14); creates an unconfirmed subscription and sends a confirmation link; `GET .../confirm?token=` confirms; `DELETE .../subscriptions?token=` unsubscribes; every email has an unsubscribe link. Rate limit 5 per hour per IP. Store only email, area, rule, tokens (see DB_SCHEMA.md); no IP logging.
- `evaluate.py` (pure): `season_approaching(today, season_start_month, lead_days)` is true when the first day of the start month (this or next year) is 0 to `lead_days` days ahead; `above_normal(month_to_date_class)` is true for `elevated` or `extreme` on the current month-to-date value (D08).
- `GET /api/alerts/active?area_id=` returns the current state for display: `{ seasonApproaching: bool, daysUntilSeasonStart, aboveNormal: class|null, asOf, provisional: true }`.
- Sending: for each confirmed subscription evaluate its rule and send at most once per `(subscription, rule, period)` (period = `YYYY-MM`), record in `notifications_sent`. The email states that it is advisory and based on provisional satellite data.
- Mailer: SMTP or email API via env; `console` mode prints the message (used in tests and demo).

## Hand-verified fixtures
`season_approaching(today, season_start_month=3, lead_days=14)` (2027 is not a leap year, February has 28 days):
- today 2027-02-14: March 1 is 15 days ahead -> false
- today 2027-02-15: 14 days ahead -> true
- today 2027-03-01: 0 days ahead -> true
- today 2027-03-02: the next March 1 is 2028-03-01, 365 days ahead -> false

## Tests
- [x] The four dates above
- [x] Subscribe, confirm, send once, send again in the same period (no second email), unsubscribe
- [x] Invalid email, unknown area, bad lead days return 400/404; rate limit returns 429
- [x] Console mailer used in tests; no network

## Tasks
- [x] Endpoints, evaluator, mailer, script implemented
- [x] Manual end-to-end with a real inbox in the demo environment
- [x] Master plan row A04 set to `[x]`
