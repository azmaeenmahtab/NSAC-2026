# D07 Climatology, anomalies, seasons, yearly stats

Depends: D06. Priority: P0. Window: EVENT. Read first: DB_SCHEMA.md `climatology`, `anomalies`, `seasons`, `yearly`; PRODUCT_BRIEF.md section 5.

## Goal
Pure statistics that turn the harmonized record into the calendar: normal levels, anomaly classes, fire season, and yearly summaries, then assemble the final processed dataset with its manifest.

## Files (`pipeline/src/pyroscope_pipeline/stats/`)
`climatology.py`, `anomalies.py`, `seasons.py`, `yearly.py`, `run.py` (also assembles `data/processed/<version>/` and `current`), tests in `pipeline/tests/stats/`.

## Specification
- **Climatology** per region and calendar month over baseline years = all complete years in the harmonized record (2001 onward; the first partial year 2000 is excluded). Output `n_years, mean, p50, p90, p95` using numpy percentile with linear interpolation. For an evaluated year y the baseline excludes y (see anomalies).
- **Anomalies** per region-year-month: baseline = values of the same calendar month in all other complete years. `percentile_rank` = share of baseline values less than or equal to the value. Class: `extreme` if value > baseline p95, `elevated` if value > baseline p90 (and not extreme), else `normal`. If the baseline has fewer than 8 years, class `normal` with a null rank is NOT acceptable: set `class = insufficient_data`.
- **Seasons**: for each region take the climatology mean per month (12 values); find the smallest window length L (circular consecutive months) such that some window holds at least `season_share` (0.7) of the annual sum; among windows of that length choose the one with the largest sum (ties: earliest start). `start_month` is the window start, `end_month` its end, `peak_month` the month with the largest mean inside it, `share_of_annual` the window share.
- **Yearly**: `harmonized_total` (sum of months), `frp_sum` (from region-level FRP), `rank` (1 = highest total), `vs_mean_pct` = (total - mean of other years) / mean of other years x 100, `peak_month`.
- **Assemble** `data/processed/<version>/` with all tables of DB_SCHEMA.md, `manifest.json` (counts, parameters, git commit, as_of_date), and update the `current` pointer. `data_version` = `v<YYYY-MM-DD>-<short content hash>`.

## Hand-verified fixtures
1. Seasons: climatology means by month 1 to 12 = `[1, 1, 2, 8, 10, 6, 1, 1, 1, 1, 1, 1]` (sum 34). 70% of 34 is 23.8. Windows of length 2 have a max sum of 18 (April-May). Length 3 April-May-June sums to 24 (70.6%). Expected: `start=4, peak=5, end=6, share=24/34=0.70588`.
2. Circular: means `[8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 10]` (sum 33, 70% is 23.1): the window November-December-January sums to 6 + 10 + 8 = 24 and wins: `start=11, peak=12, end=1`.
3. Percentiles: baseline `[1,2,3,4,5,6,7,8,9,10]` gives `p90 = 9.1`, `p95 = 9.55`. Value 9.5: class `elevated`, percentile rank 0.9. Value 9.6: `extreme`. Value 3: `normal`, rank 0.3.
4. Baseline excludes the evaluated year: with 10 yearly values for a month, the baseline for year y has 9 values.
5. Yearly: totals `[10, 20, 30]` for 3 years: ranks `[3, 2, 1]`; `vs_mean_pct` for the year with 30 = (30 - 15) / 15 x 100 = 100.

## Tasks
- [ ] Climatology, anomalies, seasons, yearly implemented as pure functions
- [ ] All five fixtures pass
- [ ] Stage assembles the processed folder; `manifest.json` complete; `current` updated; API can read it (check with the A01 loader)
- [ ] Human review of results for the CHT preset: season months, which years are extreme; write the findings in `docs/DATA_FINDINGS.md` (do not force the expected March-May result; report what the data says)
- [ ] Master plan row D07 set to `[x]`
