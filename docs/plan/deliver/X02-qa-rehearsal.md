# X02 Final QA, demo rehearsal, offline fallback

Depends: all P0. Priority: P0. Window: EVENT.

## Tasks
- [ ] Clean-clone test by someone who did not write the setup: `make setup`, `make test`, `docker compose up`, open the app, run the demo path
- [ ] Production smoke test (`scripts/smoke.sh`) passes; check CORS, rate limits, secrets not exposed in the client bundle
- [ ] Demo script with timings (240 seconds) in `docs/DEMO_SCRIPT.md`: steps, URLs (use `?demo=1`), who speaks, what to click; rehearsed at least twice with a timer
- [ ] Offline fallback: recorded video of the full demo; static screenshots; Ask in replay mode works with no internet; local `docker compose` instance ready on one laptop
- [ ] Failure plan: if the API is down, if the LLM key fails (switch to replay and say so), if the basemap fails (blank base with hexes still working), if WiFi fails (local instance)
- [ ] Accessibility and mobile spot check; browser check in Chrome and Firefox
- [ ] Numbers check: every number spoken in the pitch matches the app and `docs/CLAIMS_AUDIT.md`
- [ ] Master plan row X02 set to `[x]`
