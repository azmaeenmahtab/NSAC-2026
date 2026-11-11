# A06 Guidance and Wildland Action Planner

Depends: A03. Priority: P1. Window: EVENT. Read first: DB_SCHEMA.md `guidance.json`; PRODUCT_BRIEF.md section 7.

## Goal
Rule-based, sourced prevention and mitigation checklists tied to the area's calendar state. No generated advice.

## Files (`services/api/app/features/guidance/`)
`router.py`, `service.py`, `rules.py` (pure), `repository.py` (loads `data/reference/guidance.json`), `schemas.py`, `tests/`. The content file `data/reference/guidance.json` is created by a human.

## Specification
- Stages from the calendar: `pre_season` (season starts within 30 days), `in_season` (current month inside the season window), `post_season` (month after the window end), `extreme` (current or latest month class is `extreme`), otherwise `off_season`. Pure `stage_for(month, season, latest_class)`.
- Content: 10 to 20 short items, each with stage(s), audience (`community`, `land_manager`, `responder`), text, `source_title`, `source_url`, and `verified` (true only if a person checked the item against the source). Sources must be real public documents (for example fire management guidance from FAO or the Bangladesh Forest Department; VERIFY each link). Unverified items are shown with a visible "not yet verified" label.
- Wildland Action Planner: `GET /api/guidance?area_id=&month=` returns the stage, a checklist (items for that stage grouped by audience), and the disclaimer: advisory, not an official directive; follow local authorities.
- No LLM involvement.

## Hand-verified fixtures
Season start 3, end 5: month 2 -> `pre_season` (March 1 is within 30 days of mid-February; define "within 30 days" as the month before the start month); month 4 -> `in_season`; month 6 -> `post_season`; month 9 with latest class `extreme` -> `extreme`; month 9 normal -> `off_season`.

## Tasks
- [x] Content file with sourced items and `verified` flags
- [x] Rules, service, endpoint and tests (the five fixtures)
- [x] Master plan row A06 set to `[x]`
