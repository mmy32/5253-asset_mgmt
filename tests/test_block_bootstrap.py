import numpy as np
import pandas as pd
import pytest

from src.models.block_bootstrap import block_means, contiguous_runs, moving_block_bootstrap


def months(*spans):
    index = [pd.date_range(start, periods=n, freq='ME') for start, n in spans]
    return index[0].append(index[1:]) if len(index) > 1 else index[0]


def test_runs_split_at_gaps():
    runs = contiguous_runs(months(('2020-01-31', 3), ('2020-06-30', 2)))
    assert [len(r) for r in runs] == [3, 2]


def test_blocks_never_cross_a_gap():
    idx = months(('2020-01-31', 3), ('2020-06-30', 3))
    values = np.array([0., 0., 0., 100., 100., 100.])
    assert sorted(block_means(values, idx, 3)) == [0.0, 100.0]


def test_no_run_long_enough_means_no_inference():
    idx = months(('2020-01-31', 11))
    assert moving_block_bootstrap(np.ones(11), idx) is None


def test_constant_series_gives_degenerate_interval_and_is_deterministic():
    idx = months(('2020-01-31', 24))
    first = moving_block_bootstrap(np.full(24, 0.01), idx, draws=500)
    second = moving_block_bootstrap(np.full(24, 0.01), idx, draws=500)
    assert first == second
    assert first.ci_low == pytest.approx(0.01) and first.ci_high == pytest.approx(0.01)
    assert first.p_value == pytest.approx(1 / 501)


def test_zero_mean_series_is_not_significant():
    rng = np.random.default_rng(1)
    idx = months(('2015-01-31', 60))
    values = rng.normal(0, 1, 60)
    values -= values.mean()
    result = moving_block_bootstrap(values, idx, draws=2000)
    assert result.p_value > 0.4 and result.ci_low < 0 < result.ci_high


def test_unsorted_months_rejected():
    idx = pd.DatetimeIndex(['2020-02-29', '2020-01-31'])
    with pytest.raises(ValueError):
        contiguous_runs(idx)
