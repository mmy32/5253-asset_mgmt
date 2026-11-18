import hashlib

import numpy as np
import pandas as pd
import pytest

from src.models import setup_a
from src.models.baseline import TARGET
from src.models.features import complete_cases, rank_normalize
from src.models.neural_net import NetConfig
from src.models.random_folds import fold_of, load_folds, validate_rotations

INPUTS = [f'x{i}' for i in range(9)]
ROTATIONS = [{'test': 0, 'train': 1, 'validation': 2},
             {'test': 1, 'train': 2, 'validation': 0},
             {'test': 2, 'train': 0, 'validation': 1}]


def synthetic(seed=0):
    rng = np.random.default_rng(seed)
    months = pd.date_range('2018-01-31', periods=60, freq='ME')
    rows = []
    for month in months:
        for fund in range(40):
            rows.append({'fund_id': f'F{fund:02d}', 'formation_date': month,
                         **{name: rng.normal() for name in INPUTS},
                         'target_assumed_available_at': month + pd.offsets.MonthEnd(2)})
    frame = pd.DataFrame(rows)
    frame[TARGET] = 0.5 * frame.x0 + rng.normal(size=len(frame))
    frame['target_net_return'] = frame[TARGET] * 0.9
    return frame, {m.strftime('%Y-%m'): i % 3 for i, m in enumerate(months)}


def test_rank_normalize_is_within_month_scaled_and_handles_ties():
    frame = pd.DataFrame({'formation_date': pd.to_datetime(['2020-01-31'] * 4 + ['2020-02-29'] * 2),
                          'a': [10., 20., 20., 40., 5., 6.]})
    ranked = rank_normalize(frame, ['a'])
    assert ranked.a.between(-1, 1).all()
    assert ranked.a[1] == ranked.a[2]
    other = rank_normalize(frame.assign(a=[10., 20., 20., 40., 1000., -5.]), ['a'])
    assert ranked.a[:4].tolist() == other.a[:4].tolist()  # another month cannot change this one


def test_complete_cases_drops_missing_and_infinite_and_rejects_unknown_columns():
    frame = pd.DataFrame({'a': [1., np.nan, 3., np.inf], 'b': [1., 2., 3., 4.]})
    assert complete_cases(frame, ['a', 'b']).index.tolist() == [0, 2]
    with pytest.raises(ValueError):
        complete_cases(frame, ['zzz'])


def test_folds_require_the_registered_file_and_valid_rotations(tmp_path):
    path = tmp_path / 'folds.csv'
    path.write_text('formation_month,fold\n2020-01,0\n2020-02,1\n')
    good = hashlib.sha256(path.read_bytes()).hexdigest()
    assert load_folds(path, good) == {'2020-01': 0, '2020-02': 1}
    with pytest.raises(ValueError):
        load_folds(path, 'bad')
    validate_rotations(ROTATIONS)
    with pytest.raises(ValueError):
        validate_rotations([{'test': 0, 'train': 0, 'validation': 1}] * 3)
    frame = pd.DataFrame({'formation_date': pd.to_datetime(['2020-01-31', '2030-01-31'])})
    assert fold_of(frame, {'2020-01': 2}).tolist() == [2, -1]


def test_test_months_never_enter_training_and_missing_outcomes_do_not_select_test_rows(monkeypatch):
    frame, folds = synthetic()
    frame.loc[frame.x1 > 1.5, [TARGET, 'target_net_return']] = np.nan  # outcomes missing in all folds
    seen = []

    def fake(train, val, test, column, spec, settings, grid):
        seen.append((train, val, test, column))
        return ({'nn': test.x0.to_numpy(), 'ridge': test.x1.to_numpy()},
                [{'model': 'nn', 'setting': 's', 'validation_loss': 1.0, 'chosen': True}])

    monkeypatch.setattr(setup_a, 'score_test', fake)
    spec = {'inputs': INPUTS, 'grid': {}, 'training': {'batch_size': 8, 'max_epochs': 1, 'patience': 1,
                                                       'ensemble_size': 1, 'seed': 1}}
    sample = {'evaluation_formation_start': '2020-01-31', 'evaluation_formation_end': '2022-12-31',
              'minimum_funds_per_month': 20}
    constituents, tuning = setup_a.run_setup_a(frame, folds, ROTATIONS, spec, sample, '2022-12-31',
                                               grid=[NetConfig((2,), 1.0, 0.01, 0.0, 0.0)])
    for train, val, test, column in seen:
        train_months, val_months, test_months = (set(d.formation_date) for d in (train, val, test))
        assert not (train_months & test_months) and not (val_months & test_months)
        assert not (train_months & val_months)
        assert np.isfinite(train[column]).all() and np.isfinite(val[column]).all()
        assert (train.target_assumed_available_at <= pd.Timestamp('2022-12-31')).all()
        assert test.formation_date.between('2020-01-31', '2022-12-31').all()
    assert test[column].isna().any()  # test rows are kept whether or not the outcome exists
    assert set(constituents.model) == {'nn_A_abnormal', 'ridge_A_abnormal', 'nn_A_net', 'ridge_A_net'}
    per_model = constituents.groupby('model').formation_date.nunique()
    assert (per_model == 36).all()  # each evaluation month is tested once per model
    assert set(tuning.target) == {'abnormal', 'net'}


def test_each_model_is_evaluated_only_on_its_own_target():
    table = pd.DataFrame({'model': ['nn_A_abnormal', 'nn_A_abnormal', 'ridge_A_net', 'ridge_A_net'],
                          'target': ['abnormal', 'net_proxy', 'abnormal', 'net_proxy']})
    kept = setup_a.matching_pairs(table)
    assert kept.target.tolist() == ['abnormal', 'net_proxy']
    assert kept.model.tolist() == ['nn_A_abnormal', 'ridge_A_net']
