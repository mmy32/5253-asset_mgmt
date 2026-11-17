import numpy as np
import pandas as pd
import pytest

from src.models.missing_outcomes import (
    leg_bounds,
    month_coverage,
    month_estimate,
    observed_share,
    passes,
    rescaled_return,
    validate_settings,
)

W = np.full(10, 0.1)


def outcomes(missing=0):
    values = np.arange(10, dtype=float)
    values[:missing] = np.nan
    return values


def test_threshold_is_inclusive_at_ninety_percent():
    assert passes(observed_share(W, outcomes(1)), 0.9)
    assert not passes(observed_share(W, outcomes(2)), 0.9)


def test_rescaling_uses_observed_funds_only_and_never_zero_fills():
    # Fund 0 is missing; remaining outcomes 1..9 average 5, not 4.5 (zero fill).
    assert rescaled_return(W, outcomes(1)) == pytest.approx(5.0)
    assert np.isnan(rescaled_return(W, outcomes(10)))


def test_bounds_fill_missing_weight_with_low_and_high():
    lo, hi = leg_bounds(W, outcomes(2), low=-1.0, high=20.0)
    known = 0.1 * sum(range(2, 10))
    assert lo == pytest.approx(known + 0.2 * -1.0)
    assert hi == pytest.approx(known + 0.2 * 20.0)


def test_bounds_equal_when_nothing_is_missing():
    lo, hi = leg_bounds(W, outcomes(0), low=-5.0, high=50.0)
    assert lo == pytest.approx(hi)


def test_coverage_ignores_outcome_values():
    frame = pd.DataFrame({'weight': W, 'y': outcomes(1)})
    shifted = frame.assign(y=frame.y * 1000)
    assert month_coverage(frame, frame, 'y', 0.9) == month_coverage(shifted, shifted, 'y', 0.9)


def month_rows(top_missing, bottom_missing):
    rows = []
    for decile, missing in [(1, bottom_missing), (10, top_missing)]:
        y = outcomes(missing) + (100 if decile == 10 else 0)
        rows.append(pd.DataFrame({'decile': decile, 'weight': W, 'y': y}))
    return pd.concat(rows, ignore_index=True)


def test_month_estimate_spread_only_when_both_legs_pass():
    ok = month_estimate(month_rows(1, 0), 'y', 0.9, 5, 95)
    assert ok['both_pass'] and ok['spread'] == pytest.approx(105.0 - 4.5)
    failing = month_estimate(month_rows(3, 0), 'y', 0.9, 5, 95)
    assert not failing['both_pass'] and np.isnan(failing['spread'])


def test_bounds_bracket_the_spread_and_widen_with_missing_weight():
    few = month_estimate(month_rows(1, 1), 'y', 0.9, 5, 95)
    many = month_estimate(month_rows(4, 4), 'y', 0.9, 5, 95)
    assert few['bound_lower'] <= few['spread'] <= few['bound_upper']
    assert many['bound_upper'] - many['bound_lower'] > few['bound_upper'] - few['bound_lower']


def test_fill_values_come_from_the_same_months_observed_outcomes():
    result = month_estimate(month_rows(1, 1), 'y', 0.9, 5, 95)
    pool = month_rows(1, 1).y.dropna().to_numpy()
    assert result['fill_low'] == pytest.approx(np.percentile(pool, 5))
    assert result['fill_high'] == pytest.approx(np.percentile(pool, 95))


@pytest.mark.parametrize('args', [(0, 5, 95), (1.1, 5, 95), (0.9, 95, 5), (0.9, -1, 95)])
def test_invalid_settings_fail_fast(args):
    with pytest.raises(ValueError):
        validate_settings(*args)
