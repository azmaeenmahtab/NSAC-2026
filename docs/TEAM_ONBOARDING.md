# Team onboarding (send this to the team)

## Lead only (do this once, today)
1. Create the GitHub repo and add all six teammates.
2. Unzip the pack at the repo root (you should see `AGENTS.md` and `docs/`), commit, push to `main`.
3. Start chunk **P00** yourself (rules check, accounts, keys) and **P01** (data requests): the FIRMS archive requests can take time to process, so they must go in today.
4. Assign the pre-event chunks (P02 to P05) and lanes from `docs/IMPLEMENTATION_PLAN.md`.
5. Share keys through a password manager, never in chat or git.

## Message for teammates

Hi team. This is how we work on PyroScope. Please follow it exactly so our AI agents do not clash.

**Setup (10 minutes)**: clone the repo; install Node LTS, pnpm, Python 3.12 and `uv`, git; open the repo in your AI coding tool.

**Start**: open `docs/CONTRIBUTOR_PROMPT.md`, copy the text between the two PASTE lines into your agent, fill in your handle and your chunk ID (or `auto`), and let it read the docs. Check that it understood the chunk, then say "go".

**What your agent does**: claims your chunk in `docs/IMPLEMENTATION_PLAN.md` (row becomes `[~]` with your name) and pushes; works on `feat/<ID>-<name>`; ticks the checkboxes in the chunk file; runs tests; opens a PR; reports.

**Rules for humans**
- One chunk at a time, only if its dependencies are `[x]` and its Window is open.
- Do not edit files that belong to another chunk.
- Pull `main` at least every two hours.
- No secrets, raw data or notebook outputs in git.
- Answer your agent's questions; do not let it guess about science or data.
- Review the report: tests pass, boxes ticked, numbers come from the data, then merge.

**Before the event (Nov 9 to 13)**: only `PRE` chunks (data requests, data exploration, region reference data, spikes, design). Do not write application code until the rules check (P00) says it is allowed or the hackathon starts on Nov 14 at 09:00.

**If something goes wrong**: merge conflict, pull `main` and ask your agent to resolve it carefully; plan looks wrong, tell the lead and log it in the Deviation Log; blocked, ask the lead for another unblocked chunk.
