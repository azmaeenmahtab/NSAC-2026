# S02 Deployment and data shipping

Depends: A01, F01. Priority: P0. Window: EVENT. Read first: ARCHITECTURE.md sections 4, 10; the hosts' current docs (VERIFY).

## Goal
A public URL for the web app and the API, loaded with the real processed data, with a local fallback.

## Specification
- Web on Vercel (or any Node host), API on Render, Fly or Railway as a Docker service with a health check on `/api/health`. CORS allows only the web origin. Env variables per ARCHITECTURE.md section 10, set in each host (never in git).
- Data shipping: the API image includes `data/processed/<version>/` if it is under about 200 MB; otherwise the API downloads a release asset on start and verifies the manifest checksum. Keep a copy of the processed data as a GitHub release asset.
- Start with a draft deploy on Day 1 using fixtures, switch to real data when D07 completes.
- Local fallback: `docker compose up` (API + web) documented in the README; offline judging works with Ask in replay mode.
- Smoke test script `scripts/smoke.sh`: health, meta, one heatmap, one calendar, one ask (replay).

## Tasks
- [ ] Draft API and web deployed with fixture data (Day 1)
- [ ] Real data deployed; smoke script passes against production
- [ ] CORS, secrets and rate limits verified in production
- [ ] `docker compose up` works from a clean clone
- [ ] Rollback note: how to redeploy the previous data version
- [ ] Master plan row S02 set to `[x]`
