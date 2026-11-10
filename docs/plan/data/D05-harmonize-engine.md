# D05 Harmonization engine (pure)

Depends: S00. Priority: P0. Window: EVENT. Read first: PRODUCT_BRIEF.md sections 5 to 7 (method and decisions D-01, D-09).

## Goal
Pure, tested functions that fit a VIIRS-to-MODIS transfer function by quantile mapping (and a ratio baseline) and evaluate them by leave-one-year-out cross-validation.

## Files (`pipeline/src/pyroscope_pipeline/harmonize/`)
`quantile_map.py`, `ratio.py`, `evaluate.py`, `pooling.py` (calendar-month groups), `types.py`, `__init__.py`; tests in `pipeline/tests/harmonize/`.

## Specification
- Inputs are paired monthly series for one calibration unit over the overlap: `modis[i]`, `viirs[i]` for the same months `i`, with `year[i]` and `month[i]`.
- **Pooling**: the month-group for month m is the set of overlap rows whose month is m-1, m or m+1 (circular, width from config). Fit one transfer function per m using its pooled rows.
- **Quantile mapping** `fit_qm(v, m) -> knots`: because both samples are paired and have equal size n, sort both ascending; if values repeat in `v`, merge duplicates by averaging the paired `m` values (isotonic grouping); the transfer function is the piecewise-linear interpolation through the knots `(v_sorted_unique, m_mean)`. `apply_qm(knots, x)`: inside the knot range, linear interpolation; below the lowest knot, the lowest knot's ratio scaling (`x * m0 / v0` if `v0 > 0`, else `m0`); above the highest knot, constant-ratio extrapolation `x * m_max / v_max`. Output is never negative.
- **Ratio** `fit_ratio(v, m) -> r = sum(m) / sum(v)` (if `sum(v) == 0` return `r = 0`); `apply_ratio(r, x) = r * x`.
- **Evaluate** `cv_by_year(modis, viirs, year, month, method) -> metrics`: for each overlap year y, fit on the other years, predict MODIS for year y from VIIRS, collect predictions; metrics: RMSE, MAE, bias (mean of prediction minus MODIS), Spearman rho of monthly values, and the relative error of annual totals. Provide `choose_method(cv_qm, cv_ratio)`: the lower RMSE wins; tie goes to ratio (simpler).
- All functions are deterministic and use NumPy only (no scikit-learn state).

## Hand-verified fixtures
1. QM exact fit: `m = [2, 4, 6, 8, 10]`, `v = [6, 12, 18, 24, 30]`. `apply_qm(18) = 6`; `apply_qm(15) = 5.0` (midway between knots (12, 4) and (18, 6)); `apply_qm(36) = 12.0` (constant-ratio extrapolation `36 * 10/30`); `apply_qm(0) = 0.0` (below the lowest knot: `0 * 2/6`).
2. Duplicates: `v = [0, 0, 6, 12]`, `m = [0, 1, 2, 4]`. Merged knots: `(0, 0.5), (6, 2), (12, 4)`. `apply_qm(0) = 0.5`; `apply_qm(3) = 1.25`.
3. Ratio: `m = [2, 4, 6]`, `v = [6, 12, 18]` gives `r = 12 / 36 = 1/3`; `apply_ratio(15) = 5.0`. With `v = [0, 0]` gives `r = 0`.
4. CV on an exact relation: `v = 3 * m` for 5 or more overlap years with at least 3 months each: RMSE and bias for both methods are 0 within 1e-9 (the extrapolation rule must make held-out years exact when the relation is exactly proportional).
5. CV choice: build a convex non-proportional relation (for example `v = m + m**2 / 4 + 1`) with at least 36 paired points over at least 12 years; assert QM RMSE is less than or equal to ratio RMSE and that `choose_method` returns `quantile_map`. If this fails, stop and ask: it signals a bug or a bad extrapolation rule, not a reason to change the test.
6. Non-negativity and monotonic: for random sorted inputs, `apply_qm` is non-decreasing in `x` and never negative (property test).

## Tasks
- [ ] Pooling, QM, ratio, evaluation implemented with docstrings stating units and assumptions
- [ ] All six fixtures pass
- [ ] Short note `docs/HARMONIZATION.md` (one page): the method in plain language, the equal-n simplification, the pooling, the extrapolation rule, and why it is not applied per cell (D-01)
- [ ] Master plan row D05 set to `[x]`
