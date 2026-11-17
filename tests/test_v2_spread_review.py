import json
from statistics import NormalDist

import numpy as np
import pandas as pd
import pytest

from src.models.calendar_inference import calendar_inference
from src.models.spread_report import ROOT, load_protocols, summarize


@pytest.mark.parametrize('changed', [0, 1])
def test_protocol_override_must_match_frozen_content(tmp_path, changed):
    paths = [ROOT / f'configs/research_protocol_v{v}.json' for v in (1, 2)]
    original = paths[changed].read_bytes()
    paths[changed] = tmp_path / 'protocol.json'
    paths[changed].write_bytes(original)
    base, v2 = load_protocols(*paths)
    assert base['inference']['seed'] == 5253
    assert v2['missing_outcome_estimand']['coverage_threshold'] == 0.90

    override = json.loads(original)
    key, setting, value = [('inference', 'seed', 9000),
                           ('missing_outcome_estimand', 'coverage_threshold', 0.85)][changed]
    override[key][setting] = value
    paths[changed].write_text(json.dumps(override))
    with pytest.raises(ValueError, match='Protocol differs'):
        load_protocols(*paths)


def test_calendar_inference_uses_actual_calendar_lags_and_all_passing_months():
    months = pd.DatetimeIndex(['2020-01-31', '2020-02-29', '2020-04-30'])
    result = calendar_inference(np.array([1., 3., 8.]), months, length=2)
    # Residuals (-3, -1, 4); only Jan/Feb are correlated, at 0.5.
    se = np.sqrt(9 + 1 + 16 + 3) / 3
    assert result is not None
    assert result.ci_low == pytest.approx(4 - NormalDist().inv_cdf(.975) * se)
    assert result.p_value == pytest.approx(NormalDist().cdf(-4 / se))


def test_spread_summary_preserves_old_inference_and_reports_same_mean_sensitivity():
    months = pd.date_range('2020-01-31', periods=12, freq='ME')
    months = months.append(pd.DatetimeIndex(['2021-01-31', '2022-01-31']))
    table = pd.DataFrame({
        'model': 'ridge_C', 'target': 'abnormal', 'formation_date': months,
        'both_pass': [True] * 12 + [False, True],
        'spread': [1.] * 12 + [np.nan, -6.], 'bound_lower': -2., 'bound_upper': 2.,
    })
    row = summarize(table, {'draws': 1000, 'seed': 5253}).iloc[0]
    assert row.months_passing == 13
    assert row.mean_spread == pytest.approx(6 / 13)
    assert row.ci_low == row.ci_high == 1
    assert row.calendar_ci_low < 0 < row.calendar_ci_high
    assert (row.calendar_ci_low + row.calendar_ci_high) / 2 == pytest.approx(row.mean_spread)


def test_calendar_inference_keeps_the_minimum_contiguous_run_gate():
    months = pd.date_range('2020-01-31', periods=11, freq='ME')
    months = months.append(pd.DatetimeIndex(['2022-01-31']))
    assert calendar_inference(np.arange(12.), months) is None
