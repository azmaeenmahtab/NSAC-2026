"""Unit tests for the D05 pure VIIRS-to-MODIS harmonization engine."""

from __future__ import annotations

import numpy as np
import pytest

from pyroscope_pipeline.harmonize import (
    apply_qm,
    apply_ratio,
    choose_method,
    circular_month_group,
    cv_by_year,
    fit_qm,
    fit_ratio,
    pool_month_mask,
)


def test_fixture_1_qm_exact_fit_and_extrapolation() -> None:
    """Fixture 1: QM exact fit, midpoint interpolation, and high/low ratio extrapolation."""
    m = [2, 4, 6, 8, 10]
    v = [6, 12, 18, 24, 30]
    knots = fit_qm(v, m)

    assert np.allclose(knots.knots_v, [6.0, 12.0, 18.0, 24.0, 30.0])
    assert np.allclose(knots.knots_m, [2.0, 4.0, 6.0, 8.0, 10.0])

    # Inside knot range
    assert apply_qm(knots, 18) == pytest.approx(6.0, abs=1e-12)
    assert apply_qm(knots, 15) == pytest.approx(5.0, abs=1e-12)

    # Above highest knot: constant-ratio extrapolation 36 * 10 / 30 = 12.0
    assert apply_qm(knots, 36) == pytest.approx(12.0, abs=1e-12)

    # Below lowest knot: 0 * (2 / 6) = 0.0; 3 * (2 / 6) = 1.0
    assert apply_qm(knots, 0) == pytest.approx(0.0, abs=1e-12)
    assert apply_qm(knots, 3) == pytest.approx(1.0, abs=1e-12)


def test_fixture_2_duplicates_isotonic_merging() -> None:
    """Fixture 2: Repeated VIIRS values merge duplicates by averaging paired MODIS values."""
    v = [0, 0, 6, 12]
    m = [0, 1, 2, 4]
    knots = fit_qm(v, m)

    assert np.allclose(knots.knots_v, [0.0, 6.0, 12.0])
    assert np.allclose(knots.knots_m, [0.5, 2.0, 4.0])

    assert apply_qm(knots, 0) == pytest.approx(0.5, abs=1e-12)
    assert apply_qm(knots, 3) == pytest.approx(1.25, abs=1e-12)


def test_fixture_3_ratio_fit_and_zero_guard() -> None:
    """Fixture 3: Ratio baseline fits sum(m) / sum(v) and guards against sum(v) == 0."""
    m = [2, 4, 6]
    v = [6, 12, 18]
    r = fit_ratio(v, m)
    assert r == pytest.approx(1.0 / 3.0, abs=1e-12)
    assert apply_ratio(r, 15) == pytest.approx(5.0, abs=1e-12)

    r_zero = fit_ratio([0, 0], [1, 2])
    assert r_zero == 0.0
    assert apply_ratio(r_zero, 10) == 0.0


def test_fixture_4_cv_exact_proportional_relation() -> None:
    """Fixture 4: CV on exact relation v = 3 * m over >=5 years & >=3 months/year has 0 error."""
    years: list[int] = []
    months: list[int] = []
    modis: list[float] = []
    viirs: list[float] = []

    # 6 overlap years, 4 months each (including higher held-out values to test extrapolation)
    for idx_y, y in enumerate(range(2015, 2021)):
        for m_cal in (2, 3, 4, 5):
            m_val = float((idx_y + 1) * m_cal * 2)
            years.append(y)
            months.append(m_cal)
            modis.append(m_val)
            viirs.append(3.0 * m_val)

    cv_qm = cv_by_year(modis, viirs, years, months, method="quantile_map")
    cv_r = cv_by_year(modis, viirs, years, months, method="ratio")

    assert cv_qm.rmse == pytest.approx(0.0, abs=1e-9)
    assert cv_qm.bias == pytest.approx(0.0, abs=1e-9)
    assert cv_qm.mae == pytest.approx(0.0, abs=1e-9)
    assert cv_qm.annual_total_rel_error == pytest.approx(0.0, abs=1e-9)
    assert cv_qm.spearman_rho == pytest.approx(1.0, abs=1e-9)

    assert cv_r.rmse == pytest.approx(0.0, abs=1e-9)
    assert cv_r.bias == pytest.approx(0.0, abs=1e-9)
    assert cv_r.mae == pytest.approx(0.0, abs=1e-9)
    assert cv_r.annual_total_rel_error == pytest.approx(0.0, abs=1e-9)
    assert cv_r.spearman_rho == pytest.approx(1.0, abs=1e-9)

    # Tie goes to ratio (simpler)
    assert choose_method(cv_qm, cv_r) == "ratio"


def test_fixture_5_cv_choice_convex_non_proportional() -> None:
    """Fixture 5: Convex non-proportional relation v = m + m^2 / 4 + 1 over >=12 years (>=36 pts)."""
    years: list[int] = []
    months: list[int] = []
    modis: list[float] = []
    viirs: list[float] = []

    # 12 overlap years x 3 spring fire-season months = 36 paired observations
    base_pattern = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]
    for y_idx, y in enumerate(range(2013, 2025)):
        for m_offset, cal_m in enumerate((3, 4, 5)):
            # Cycle across intensity levels so training distribution spans the domain
            m_val = base_pattern[(y_idx + m_offset * 4) % len(base_pattern)]
            v_val = m_val + (m_val**2) / 4.0 + 1.0
            years.append(y)
            months.append(cal_m)
            modis.append(m_val)
            viirs.append(v_val)

    cv_qm = cv_by_year(modis, viirs, years, months, method="quantile_map")
    cv_r = cv_by_year(modis, viirs, years, months, method="ratio")

    assert len(modis) >= 36
    assert cv_qm.n_years >= 12
    assert cv_qm.rmse < cv_r.rmse
    assert choose_method(cv_qm, cv_r) == "quantile_map"


def test_fixture_6_non_negativity_and_monotonicity_property() -> None:
    """Fixture 6: For random non-negative inputs, apply_qm is non-decreasing and >= 0."""
    rng = np.random.default_rng(20261114)
    x_grid = np.linspace(-5.0, 250.0, 500)

    for _ in range(50):
        n = int(rng.integers(5, 40))
        # Include zeros and duplicates as well as positive draws
        v_sample = np.maximum(0.0, rng.normal(loc=25.0, scale=20.0, size=n).round(0))
        m_sample = np.maximum(0.0, rng.normal(loc=8.0, scale=7.0, size=n).round(0))

        knots = fit_qm(v_sample, m_sample)
        y_grid = apply_qm(knots, x_grid)

        assert np.all(y_grid >= 0.0)
        # Non-decreasing for non-negative queries x >= 0
        non_neg_y = y_grid[x_grid >= 0.0]
        diffs = np.diff(non_neg_y)
        assert np.all(diffs >= -1e-12)


def test_circular_month_pooling_wraparound() -> None:
    """Verify circular calendar-month pooling wraps Jan (12, 1, 2) and Dec (11, 12, 1)."""
    assert circular_month_group(1, pool_width=1) == (12, 1, 2)
    assert circular_month_group(12, pool_width=1) == (11, 12, 1)
    assert circular_month_group(4, pool_width=1) == (3, 4, 5)
    assert circular_month_group(4, pool_width=0) == (4,)

    months = np.array([1, 2, 3, 11, 12])
    mask_jan = pool_month_mask(months, target_month=1, pool_width=1)
    assert np.array_equal(mask_jan, np.array([True, True, False, False, True]))
