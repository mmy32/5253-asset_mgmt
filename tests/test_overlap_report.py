import numpy as np
import pandas as pd
import pytest

from src.models.baseline import TARGET
from src.models.overlap_report import check_mechanics, coverage_table, summarize


def constituents(missing_top):
    rows = []
    for decile in (1, 10):
        y = np.arange(10, dtype=float)
        if decile == 10:
            y[:missing_top] = np.nan
        rows.append(pd.DataFrame({'model': 'm', 'formation_date': pd.Timestamp('2020-01-31'),
                                  'decile': decile, 'weight': 0.1, TARGET: y,
                                  'target_net_return': np.arange(10, dtype=float)}))
    return pd.concat(rows, ignore_index=True)


def test_coverage_table_flags_months_and_has_no_return_columns():
    table = coverage_table(constituents(missing_top=2), 0.9)
    by_target = table.set_index('target')
    assert not by_target.loc['abnormal', 'both_pass']
    assert by_target.loc['net_proxy', 'both_pass']
    assert {'spread', 'bound_lower', 'abnormal_return'}.isdisjoint(table.columns)


def test_summary_counts_passing_months():
    summary = summarize(coverage_table(constituents(missing_top=1), 0.9))
    assert summary.set_index('target').both_pass.eq(1).all()


def audit(label_date):
    return pd.DataFrame({'formation_date': [pd.Timestamp('2020-01-31')],
                         'latest_training_label_available': [pd.Timestamp(label_date)]})


def ten_deciles():
    return pd.DataFrame({'model': 'm', 'formation_date': pd.Timestamp('2020-01-31'),
                         'decile': np.repeat(np.arange(1, 11), 10), 'weight': 0.1})


def test_mechanics_pass_on_valid_weights_and_labels():
    check_mechanics(ten_deciles(), audit('2019-12-31'))


def test_mechanics_reject_future_training_label_and_bad_weights():
    with pytest.raises(ValueError):
        check_mechanics(ten_deciles(), audit('2020-02-29'))
    with pytest.raises(ValueError):
        check_mechanics(ten_deciles().assign(weight=0.2), audit('2019-12-31'))
