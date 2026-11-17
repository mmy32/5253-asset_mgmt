import numpy as np
import pandas as pd

from src.models.baseline import TARGET, portfolios, predict, training


def test_delayed_labels_and_future_rows_cannot_enter_training():
    frame = pd.DataFrame({'formation_date': pd.to_datetime(['2020-01-31','2020-02-29','2020-04-30']),
                          'target_assumed_available_at': pd.to_datetime(['2020-03-31','2020-04-30','2020-06-30']),
                          TARGET: [1., 2., 3.]})
    result = training(frame, pd.Timestamp('2020-03-31'))
    assert result.index.tolist() == [0]


def test_ridge_standardizes_using_training_only():
    train = pd.DataFrame({'flow': [1.,2.,3.,4.], 'momentum_12_2': [4.,1.,2.,3.], TARGET: [1.,2.,3.,4.]})
    one = train.iloc[:1]
    extreme = pd.concat([one, one.assign(flow=1e10)])
    assert predict(train, one, 1.)[0] == predict(train, extreme, 1.)[0]


def test_missing_outcome_preserves_weights_and_ties_are_deterministic():
    rows = pd.DataFrame({'fund_id': [str(i).zfill(2) for i in range(20)], 'score': np.zeros(20),
                         TARGET: np.full(20, .01), 'target_net_return': np.full(20, .02)})
    rows.loc[0, TARGET] = np.nan
    members, result = portfolios(rows.sample(frac=1, random_state=1))
    assert members.iloc[0].fund_id == '00'
    first = result.iloc[0]
    assert first.missing_weight_abnormal == .5
    assert np.isnan(first.abnormal)
    assert first.net_proxy == .02
    assert members.groupby('decile').weight.sum().eq(1).all()


def test_tuning_ignores_labels_not_available_by_selection_date():
    from src.models.baseline import tune

    months = pd.date_range('2018-01-31', periods=8, freq='ME')
    rows = []
    for month_index, month in enumerate(months):
        for fund in range(4):
            rows.append({'formation_date': month,
                         'target_assumed_available_at': month + pd.offsets.MonthEnd(2),
                         'flow': float(fund), 'momentum_12_2': float((fund + month_index) % 4),
                         TARGET: float(fund + month_index)})
    frame = pd.DataFrame(rows)
    decision = months[6]
    validation = [months[3], months[5]]  # The latter has not matured by decision.
    original = tune(frame, validation, decision, [0.01, 1.0])
    frame.loc[frame.target_assumed_available_at > decision, TARGET] = 1e9
    assert tune(frame, validation, decision, [0.01, 1.0]) == original
