import numpy as np
import pandas as pd
import pytest

from src.models.family_features import add_family_inputs


def frame():
    return pd.DataFrame({
        'formation_date': pd.to_datetime(['2020-01-31'] * 4 + ['2020-02-29'] * 2),
        'family_id': ['A', 'A', 'A', None, 'A', 'B'],
        'tna': [10., 30., 60., 5., 10., 20.],
        'flow': [0.1, np.nan, 0.4, 0.2, 0.3, 0.5],
        'momentum_12_2': [0.01, 0.02, np.nan, 0.03, 0.04, 0.05],
    })


def test_siblings_with_missing_values_are_skipped_not_disqualifying():
    out = add_family_inputs(frame())
    # Fund 0's siblings: fund 1 (flow missing) and fund 2 (flow 0.4); only fund 2 counts.
    assert out.family_flow_any[0] == pytest.approx(0.4)
    # Fund 0's momentum siblings: fund 1 only (fund 2 missing).
    assert out.family_momentum_any[0] == pytest.approx(0.02)
    # Fund 1: flow from funds 0 and 2, weighted by TNA 10 and 60.
    assert out.family_flow_any[1] == pytest.approx((0.1 * 10 + 0.4 * 60) / 70)
    assert out.family_tna_any[0] == pytest.approx(90.0)


def test_no_family_or_no_usable_sibling_gives_missing():
    out = add_family_inputs(frame())
    assert np.isnan(out.family_flow_any[3]) and np.isnan(out.family_tna_any[3])
    assert not np.isnan(out.family_momentum_any[2])  # fund 2 has siblings with momentum
    assert np.isnan(out.family_flow_any[4]) and out.family_tna_any[4] == 0.0  # alone that month


def test_months_and_families_do_not_mix():
    base = add_family_inputs(frame())
    changed = frame()
    changed.loc[5, 'flow'] = 99.0  # different family and month
    assert add_family_inputs(changed).family_flow_any[:5].equals(base.family_flow_any[:5])


def test_missing_columns_fail_fast():
    with pytest.raises(ValueError):
        add_family_inputs(frame().drop(columns='tna'))
