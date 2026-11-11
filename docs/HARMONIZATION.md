# Harmonization Engine: Method & Design Reference (`D05`)

PyroScope bridges NASA's 2000–present **MODIS** (1 km) and 2012–present **VIIRS S-NPP** (375 m) active-fire records into one continuous **MODIS-equivalent fire event series**. Because VIIRS has finer spatial resolution and higher sensitivity to small fires, plotting raw counts across 2012 creates an artificial structural break ("the hidden jump"). Even after spatio-temporal clustering (`ST-DBSCAN`, `2.7 km / 24 h`) collapses multi-pixel detections of the same physical fire into single fire events, VIIRS still detects ~1.5x more physical fire events than MODIS over Bangladesh (`~860` vs `~560` events/year over the 2012-02 to 2026-10 overlap).

This document explains how `pyroscope_pipeline.harmonize` calibrates VIIRS monthly event counts to the historical MODIS scale.

---

## 1. The Method in Plain Language

During the **177-month overlap window** (`2012-02` through `2026-10`), both MODIS and VIIRS S-NPP observed Bangladesh simultaneously. For each geographic calibration unit and seasonal calendar-month group, we compare the empirical distribution of monthly VIIRS fire event counts ($V$) against the distribution of monthly MODIS fire event counts ($M$) over the same pooled months.

We fit two candidate transfer functions $f(v) \mapsto \hat{m}$:

1. **Empirical Quantile Mapping (`quantile_map`)**: Matches the empirical percentiles of VIIRS to MODIS so that a median, 90th-percentile, or extreme VIIRS month maps to the corresponding median, 90th-percentile, or extreme MODIS month. This captures non-linear sensitivity differences (e.g., when small agricultural clearing fires inflate low-to-moderate VIIRS counts more than large canopy fires).
2. **Proportional Ratio Baseline (`ratio`)**: Scales VIIRS counts by the ratio of total overlap events, $r = \sum M_i / \sum V_i$ (with $r = 0$ if $\sum V_i = 0$).

For each calibration unit, we evaluate both candidates using **leave-one-year-out cross-validation (LOYO-CV)** across all overlap years. The method with the lower cross-validated monthly Root Mean Squared Error (**RMSE**) is selected for that unit (ties go to the simpler `ratio` model).

---

## 2. The Equal-$n$ Simplification & Isotonic Duplicate Merging

In general quantile mapping, one estimates empirical cumulative distribution functions $\hat{F}_V$ and $\hat{F}_M^{-1}$ on a fixed quantile grid. Because our calibration inputs are **paired monthly observations over the exact same set of $n$ pooled overlap months**, both samples have identical size $n$:

1. Sort both samples ascending: $v_{(1)} \le v_{(2)} \le \dots \le v_{(n)}$ and $m_{(1)} \le m_{(2)} \le \dots \le m_{(n)}$. Each pair $(v_{(k)}, m_{(k)})$ corresponds to the exact same empirical rank $k / n$.
2. **Duplicate merging (isotonic grouping)**: Monthly fire event counts frequently contain ties (especially zeros in monsoon months). If a value $v^*$ repeats at indices $k \in S$, a function cannot map one input $v^*$ to multiple outputs. We merge duplicate $v^*$ values into a single knot by averaging their paired sorted MODIS values:
   $$\tilde{m}(v^*) = \frac{1}{|S|} \sum_{k \in S} m_{(k)}$$
3. Because $m_{(k)}$ is already sorted non-decreasingly, the resulting knot sequence $(v_0 < v_1 < \dots < v_{K-1},\; \tilde{m}_0 \le \tilde{m}_1 \le \dots \le \tilde{m}_{K-1})$ is guaranteed to be **monotonically non-decreasing** and passes through piecewise-linear interpolation (`np.interp`) inside $[v_0, v_{\max}]$.

---

## 3. Circular Calendar-Month Pooling

A single calendar month over ~14 overlap years provides only ~14 data points, which is noisy for tail quantiles. Moreover, fire weather in Bangladesh shifts by a few weeks from year to year (e.g., late February vs March in the Chittagong Hill Tracts).

To stabilize empirical quantiles while respecting seasonality, the transfer function for target calendar month $m \in \{1, \dots, 12\}$ is fit on the **circular 3-month pool** $(m - 1,\, m,\, m + 1)$ (controlled by `month_pool_width: 1` in `pipeline/config.yaml`, wrapping December $\leftrightarrow$ January). Over 14–15 overlap years, each monthly transfer function is anchored by ~42–45 paired observations from the same seasonal regime.

---

## 4. Tail Extrapolation Rules

When applying the fitted quantile map `apply_qm(knots, x)` to a held-out year or future NRT month, $x$ may fall outside the historical knot range $[v_0, v_{\max}]$:

- **Inside $[v_0, v_{\max}]$**: Piecewise-linear interpolation between adjacent knots.
- **Below the lowest knot ($x < v_0$)**: Proportional scaling anchored at the origin, $x \cdot (\tilde{m}_0 / v_0)$ if $v_0 > 0$, else $\tilde{m}_0$. This ensures $x = 0$ maps cleanly to $0$ whenever $v_0 > 0$.
- **Above the highest knot ($x > v_{\max}$)**: Constant-ratio extrapolation, $x \cdot (\tilde{m}_{\max} / v_{\max})$ if $v_{\max} > 0$, else $\tilde{m}_{\max}$. Flat clamping at $\tilde{m}_{\max}$ would artificially cap record-breaking fire seasons; constant-ratio extrapolation preserves proportional severity in unseen extreme months and guarantees exact zero CV error when the underlying relationship is strictly proportional ($V = c \cdot M$).
- **Non-negativity**: Output is clamped to $\ge 0$.

---

## 5. Why Harmonization Is Not Applied Per H3 Cell (`D-01`)

The initial challenge background suggested fitting quantile mapping per spatial grid cell and month. In practice (`docs/PRODUCT_BRIEF.md` Decision **D-01**):

1. **Extreme sparsity at cell level**: Bangladesh contains **26,683** H3 resolution-7 hexagons (~$5.72\text{ km}^2$ each). Even in active burning regions, an individual H3 cell experiences fire in only a few years; a single cell-month has ~14 overlap observations that are almost all zeros, making cell-level empirical CDFs degenerate and statistically unstable.
2. **Spatial aggregation consistency**: Fitting nonlinear quantile maps independently at cell, district, and country levels would cause the sum of cells to disagree with district and national totals.

Instead, PyroScope fits harmonization at the **district (`ADM2`) level** when the district has sufficient signal ($\text{mean monthly MODIS events} \ge 3$ over the overlap), falling back to the **parent division (`ADM1`)** for sparse districts. Division and national series are computed bottom-up as the exact sum of districts, and H3 cell values are obtained by **proportional downscaling** (`cell_harmonized = cell_raw_viirs * (district_harmonized / district_raw_viirs)`), conserving regional totals while preserving VIIRS's sharp 375 m spatial localization.
