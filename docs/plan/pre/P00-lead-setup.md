# P00 Lead setup: rules check, accounts, keys, tools

Depends: none. Priority: P0. Window: PRE. Owner: the lead (human task, no code).

## Goal
Remove all organizational risk before the event: know the rules, have every account and key, and have every teammate's tools installed.

## Tasks
- [ ] **Rules.** Read the official challenge page for "Harmonization of MODIS and VIIRS Hot Spots", the Participant Terms, and (when released on Nov 13) the Project Submission Guide and the Judging and Awards Guide. Ask your Local Lead and record the answers in `docs/RULES_CHECK.md` (create it with these headings): (1) May we write application code before Nov 14 09:00, or only research, data download and planning? (2) Required submission fields, formats and limits (summary length, links, video yes/no and length, slides). (3) Required disclosure of AI tools used. (4) Local judging schedule, pitch length and whether a new video is needed. (5) Judging criteria wording. (6) Rules on using existing open-source code and data. (7) Final submission time zone and cutoff.
- [ ] Update `docs/PRODUCT_BRIEF.md` section 1 and the master plan schedule with the confirmed answers; log changes in the Deviation Log.
- [ ] **Team on the platform.** All 6 members registered, one team page, the challenge selected, team size at most 6.
- [ ] **Accounts and keys** (store in a password manager; never in git): GitHub repo, NASA Earthdata login, FIRMS MAP_KEY (request 2 or 3 keys under different team emails so downloads can run in parallel; each key allows 5,000 transactions per 10 minutes and multi-day requests count as several), Vercel, an API host (Render, Fly or Railway), an LLM key (Gemini or another, with a spending cap) and the model id to use (VERIFY current ids), an SMTP or email-API account for alerts (P1), a basemap style that needs no key or a free key (VERIFY terms).
- [ ] **Tool install checklist** confirmed by every teammate: Node LTS, pnpm, Python 3.12, uv, git, Docker (optional), an AI coding tool, Make.
- [ ] Shared drive folder for raw data (not git) with write access for lane 1 and read access for everyone.
- [ ] Create the GitHub repo from the pack, enable branch protection on `main` (PR required, CI required once S00 lands).
- [ ] Master plan row P00 set to `[x]`
