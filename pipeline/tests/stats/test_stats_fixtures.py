"""Unit tests for D07 pure calendar statistics engines and hand-verified fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pyroscope_pipeline.common.paths import FIXTURES_DIR
from pyroscope_pipeline.stats import (
    compute_anomalies,
    compute_climatology,
    compute_month_climatology,
    compute_region_yearly_stats,
    compute_season_from_means,
    compute_seasons,
    compute_yearly,
    determine_complete_years,
    evaluate_month_anomaly,
)


def _make_yearly_series(
    region_id: str,
    year_month_values: dict[tuple[int, int], float],
    source_used: str = "modis_raw",
) -> pd.DataFrame:
    rows = [
        {
            "region_id": region_id,
            "year": y,
            "month": m,
            "raw_modis": val,
            "raw_viirs": np.nan,
            "harmonized": val,
            "source_used": source_used,
            "method": "none",
            "calibration_unit_id": region_id,
            "in_overlap": False,
        }
        for (y, m), val in sorted(year_month_values.items())
    ]
    return pd.DataFrame(rows)


def test_fixture_1_seasons_standard_window() -> None:
    """Hand-verified Fixture 1: [1,1,2,8,10,6,1,1,1,1,1,1] -> Apr-May-Jun (4, 5, 6)."""
    means = [1, 1, 2, 8, 10, 6, 1, 1, 1, 1, 1, 1]
    res = compute_season_from_means(means, share_threshold=0.7)

    assert res["start_month"] == 4
    assert res["peak_month"] == 5
    assert res["end_month"] == 6
    assert res["window_length"] == 3
    assert res["share_of_annual"] == pytest.approx(24.0 / 34.0, abs=1e-9)


def test_fixture_2_seasons_circular_wraparound() -> None:
    """Hand-verified Fixture 2: [8,1,1,1,1,1,1,1,1,1,6,10] -> Nov-Dec-Jan (11, 12, 1)."""
    means = [8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6, 10]
    res = compute_season_from_means(means, share_threshold=0.7)

    assert res["start_month"] == 11
    assert res["peak_month"] == 12
    assert res["end_month"] == 1
    assert res["window_length"] == 3
    assert res["share_of_annual"] == pytest.approx(24.0 / 33.0, abs=1e-9)


def test_fixture_3_percentiles_and_anomaly_classes() -> None:
    """Hand-verified Fixture 3: baseline [1..10] -> p90=9.1, p95=9.55, 9.5 elevated, 9.6 extreme, 3 normal."""
    baseline = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    n_yrs, mean_v, p50, p90, p95 = compute_month_climatology(baseline)
    assert n_yrs == 10
    assert mean_v == pytest.approx(5.5, abs=1e-12)
    assert p50 == pytest.approx(5.5, abs=1e-12)
    assert p90 == pytest.approx(9.1, abs=1e-12)
    assert p95 == pytest.approx(9.55, abs=1e-12)

    rank_elev, cls_elev = evaluate_month_anomaly(9.5, baseline)
    assert cls_elev == "elevated"
    assert rank_elev == pytest.approx(0.9, abs=1e-12)

    rank_ext, cls_ext = evaluate_month_anomaly(9.6, baseline)
    assert cls_ext == "extreme"
    assert rank_ext == pytest.approx(0.9, abs=1e-12)

    rank_norm, cls_norm = evaluate_month_anomaly(3.0, baseline)
    assert cls_norm == "normal"
    assert rank_norm == pytest.approx(0.3, abs=1e-12)


def test_fixture_4_baseline_excludes_evaluated_year_and_insufficient_data() -> None:
    """Hand-verified Fixture 4: 10 years -> baseline for year y has 9 values; <8 -> insufficient_data."""
    # Build 10 complete years (2010..2019), month 5 values = [1..9, 100.0]
    ym_vals: dict[tuple[int, int], float] = {}
    for idx, y in enumerate(range(2010, 2020)):
        for m in range(1, 13):
            if m == 5:
                ym_vals[(y, m)] = 100.0 if y == 2019 else float(idx + 1)
            else:
                ym_vals[(y, m)] = 1.0
    df = _make_yearly_series("REG-A", ym_vals)

    anomalies = compute_anomalies(df)
    may_2019 = anomalies[(anomalies["year"] == 2019) & (anomalies["month"] == 5)].iloc[0]
    # Baseline for 2019 is [1..9] (9 values, p95 = 8.6); 100.0 is NOT included in its own baseline
    assert may_2019["class"] == "extreme"
    assert may_2019["percentile_rank"] == pytest.approx(1.0, abs=1e-12)

    # Evaluating 2018 (value 9.0) excludes 2018 -> baseline [1..8, 100.0] (9 values, p90=26.4, rank=8/9)
    may_2018 = anomalies[(anomalies["year"] == 2018) & (anomalies["month"] == 5)].iloc[0]
    assert may_2018["class"] == "normal"
    assert may_2018["percentile_rank"] == pytest.approx(8.0 / 9.0, abs=1e-12)

    # Fewer than 8 baseline years (7 complete years -> 6 in LOO baseline) -> insufficient_data
    short_df = df[df["year"] <= 2016].copy()
    short_anom = compute_anomalies(short_df)
    assert (short_anom["class"] == "insufficient_data").all()
    assert short_anom["percentile_rank"].isna().all()


def test_fixture_5_yearly_ranks_and_vs_mean_pct() -> None:
    """Hand-verified Fixture 5: totals [10, 20, 30] -> ranks [3, 2, 1], vs_mean_pct [ -60, 0, 100 ]."""
    res = compute_region_yearly_stats(
        years=[2018, 2019, 2020],
        totals=[10.0, 20.0, 30.0],
        frp_sums=[100.0, 200.0, 300.0],
        peak_months=[3, 4, 5],
    )
    assert res["rank"].tolist() == [3, 2, 1]
    assert res["vs_mean_pct"].tolist() == pytest.approx([-60.0, 0.0, 100.0], abs=1e-12)


def test_partial_and_provisional_years_excluded_from_baseline_and_yearly() -> None:
    """Partial boundary years (2000, 2026) and provisional rows never enter baseline or yearly."""
    ym_vals: dict[tuple[int, int], float] = {
        (2000, 11): 5.0,
        (2000, 12): 5.0,
    }
    for y in range(2001, 2011):
        for m in range(1, 13):
            ym_vals[(y, m)] = 10.0 if m == 4 else 1.0
    for m in range(1, 11):
        ym_vals[(2026, m)] = 50.0 if m == 4 else 1.0

    df = _make_yearly_series("REG-P", ym_vals)
    comp_map = determine_complete_years(df)
    assert comp_map["REG-P"] == set(range(2001, 2011))

    clim = compute_climatology(df)
    assert (clim["n_years"] == 10).all()
    assert (clim["baseline_year_min"] == 2001).all()
    assert (clim["baseline_year_max"] == 2010).all()

    yearly = compute_yearly(df)
    assert set(yearly["year"].tolist()) == set(range(2001, 2011))

    # Partial years still appear in anomalies and evaluate against complete years
    anom = compute_anomalies(df)
    apr_2026 = anom[(anom["year"] == 2026) & (anom["month"] == 4)].iloc[0]
    assert apr_2026["class"] == "extreme"
    assert apr_2026["percentile_rank"] == pytest.approx(1.0, abs=1e-12)

    # Marking 2010 as having a provisional row removes 2010 from complete years
    df_prov = df.copy()
    df_prov["provisional"] = (df_prov["year"] == 2010) & (df_prov["month"] == 12)
    assert 2010 not in determine_complete_years(df_prov)["REG-P"]


def test_edge_cases_zero_season_ties_and_single_year_yearly() -> None:
    """Zero totals and ties remain finite, deterministic, and non-throwing."""
    zero_season = compute_season_from_means([0.0] * 12, share_threshold=0.7)
    assert zero_season == {
        "start_month": 1,
        "peak_month": 1,
        "end_month": 1,
        "share_of_annual": 0.0,
        "window_length": 1,
    }

    # Tie in window sum -> earliest start month wins (Jan-Feb vs Jul-Aug, both sum 0.8)
    tied_means = [0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0]
    # Sum is 1.6; 70% is 1.12 -> min length needed is 7 (Jan-Jul or Jul-Jan)
    # Wait: test length-2 tie directly with 0.5/0.5 vs 0.0:
    tied_means_2 = [0.35, 0.35, 0.0, 0.0, 0.0, 0.0, 0.35, 0.35, 0.0, 0.0, 0.0, 0.0]
    # Total 1.4; 70% is 0.98 -> length 7: Jan..Jul sums 1.05, Jul..Jan sums 1.05 -> start 1 wins
    tied_res = compute_season_from_means(tied_means_2, share_threshold=0.7)
    assert tied_res["start_month"] == 1

    # Single-year or all-zero yearly stats never divide by zero
    single = compute_region_yearly_stats([2020], [0.0], [0.0], [1])
    assert single["rank"].tolist() == [1]
    assert single["vs_mean_pct"].tolist() == [0.0]

    tied_yearly = compute_region_yearly_stats([2019, 2020], [0.0, 0.0], [0.0, 0.0], [1, 1])
    assert tied_yearly["rank"].tolist() == [1, 1]
    assert tied_yearly["vs_mean_pct"].tolist() == [0.0, 0.0]
    del tied_means


def test_consistency_against_s01_fixtures() -> None:
    """Verify pure stats engines on S01 harmonized_region match exact mathematical truths."""
    harm_reg = pd.read_parquet(FIXTURES_DIR / "harmonized_region.parquet")
    monthly_reg = pd.read_parquet(FIXTURES_DIR / "monthly_region.parquet")

    clim = compute_climatology(harm_reg)
    seasons = compute_seasons(clim, share_threshold=0.7)
    anomalies = compute_anomalies(harm_reg)
    yearly = compute_yearly(harm_reg)

    fix_clim = pd.read_parquet(FIXTURES_DIR / "climatology.parquet")
    fix_yearly = pd.read_parquet(FIXTURES_DIR / "yearly.parquet")

    # Alpha climatology matches fixture exactly (2020-05 = 200 vs 24 years of 100 -> mean 104)
    pd.testing.assert_frame_equal(
        clim[clim["region_id"] == "BGD-ADM2-alpha"].reset_index(drop=True),
        fix_clim[fix_clim["region_id"] == "BGD-ADM2-alpha"].reset_index(drop=True),
        check_dtype=False,
    )
    # Country BGD May mean = (24 * 150 + 300) / 25 = 156.0 (exact sum of alpha 104 + beta 52)
    bgd_may = clim[(clim["region_id"] == "BGD") & (clim["month"] == 5)].iloc[0]
    assert bgd_may["mean"] == pytest.approx(156.0, abs=1e-9)

    # All three regions have season Apr-May-Jun with share (80+104+60)/(344) = 244/344
    for _, srow in seasons.iterrows():
        assert srow["start_month"] == 4
        assert srow["peak_month"] == 5
        assert srow["end_month"] == 6
        assert srow["window_length"] == 3
        assert srow["share_of_annual"] == pytest.approx(244.0 / 344.0, abs=1e-9)

    # 2020-05 is extreme for alpha, beta, and BGD
    may20_alpha = anomalies[
        (anomalies["region_id"] == "BGD-ADM2-alpha")
        & (anomalies["year"] == 2020)
        & (anomalies["month"] == 5)
    ].iloc[0]
    assert may20_alpha["class"] == "extreme"
    assert may20_alpha["percentile_rank"] == pytest.approx(1.0, abs=1e-12)

    # Yearly totals, ranks, peak_month, and 2020 vs_mean_pct match fixture; non-2020 years
    # reflect 2020 included in other-years mean: (340 - 344.1667)/344.1667 * 100 = -1.210654
    merged_y = yearly.merge(fix_yearly, on=["region_id", "year"], suffixes=("_calc", "_fix"))
    sub_ab = merged_y[merged_y["region_id"].isin(["BGD-ADM2-alpha", "BGD"])]
    assert np.allclose(sub_ab["harmonized_total_calc"], sub_ab["harmonized_total_fix"])
    assert (sub_ab["rank_calc"] == sub_ab["rank_fix"]).all()
    assert (sub_ab["peak_month_calc"] == sub_ab["peak_month_fix"]).all()
    rows_2020 = sub_ab[sub_ab["year"] == 2020]
    assert np.allclose(rows_2020["vs_mean_pct_calc"], rows_2020["vs_mean_pct_fix"])
    rows_other = sub_ab[sub_ab["year"] != 2020]
    expected_other = (340.0 - (23 * 340.0 + 440.0) / 24.0) / ((23 * 340.0 + 440.0) / 24.0) * 100.0
    assert np.allclose(rows_other["vs_mean_pct_calc"], expected_other)

    # Verify FRP aggregation picks selected sensor (no MODIS+VIIRS double-counting)
    yearly_with_frp = compute_yearly(
        harm_reg,
        monthly_region_df=monthly_reg,
        region_constituents={"BGD": ["BGD-ADM2-alpha", "BGD-ADM2-beta"]},
    )
    bgd_2020 = yearly_with_frp[
        (yearly_with_frp["region_id"] == "BGD") & (yearly_with_frp["year"] == 2020)
    ].iloc[0]
    alpha_2020 = yearly_with_frp[
        (yearly_with_frp["region_id"] == "BGD-ADM2-alpha") & (yearly_with_frp["year"] == 2020)
    ].iloc[0]
    beta_2020 = yearly_with_frp[
        (yearly_with_frp["region_id"] == "BGD-ADM2-beta") & (yearly_with_frp["year"] == 2020)
    ].iloc[0]
    assert bgd_2020["frp_sum"] == pytest.approx(
        alpha_2020["frp_sum"] + beta_2020["frp_sum"], abs=1e-6
    )
