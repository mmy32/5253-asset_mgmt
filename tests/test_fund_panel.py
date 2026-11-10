import calendar
import csv
import json
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

from src.data_processing.fund_panel import abnormal_returns, build_panel


def month_end(year, month):
    return date(year, month, calendar.monthrange(year, month)[1])


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_rolling_target_uses_only_prior_months_and_keeps_intercept():
    rng = np.random.default_rng(42)
    factors = rng.normal(0, .03, (45, 4))
    beta = np.array([.8, -.2, .4, .1])
    months = pd.date_range('2016-01-31', periods=45, freq='ME')
    frame = pd.DataFrame(factors, columns=['mkt', 'smb', 'hml', 'mom'])
    frame['fund_id'] = 'fund'
    frame['return_month'] = months
    frame['rf'] = .001
    frame['gross_return'] = .001 + .004 + factors @ beta
    result = abnormal_returns(frame)
    assert result.abnormal_return.iloc[:30].isna().all()
    assert result.abnormal_return.iloc[30] == pytest.approx(.004)
    assert result.beta_observations.iloc[36] == 36
    frame.loc[44, 'gross_return'] = 999
    assert abnormal_returns(frame).abnormal_return.iloc[35] == pytest.approx(.004)


def test_panel_preserves_missing_returns_and_respects_lags(tmp_path: Path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    factor_dir = raw / 'D2_Carhart_factors'
    factor_dir.mkdir()
    dates = pd.date_range('2017-01-31', periods=43, freq='ME')
    rng = np.random.default_rng(11)
    factors = rng.normal(0, .02, (43, 4))
    beta = np.array([.7, .2, -.3, .1])
    names = ['crsp_fundno', 'caldt', 'mtna', 'mret']
    returns = []
    for fund, tna in [('000001', 10), ('000002', 30), ('000003', 20)]:
        for i, dt in enumerate(dates):
            if fund == '000002' and i == 20:
                continue  # Missing future outcome must not remove the formation row.
            net = .001 + .005 + factors[i] @ beta - .001
            if i == 34:
                net = 2.0  # Paper's >100% fund-return cutoff should preserve the row.
            returns.append({'crsp_fundno': fund, 'caldt': pd.offsets.BMonthEnd().rollback(dt).date(), 'mtna': tna,
                            'mret': 'R' if fund == '000002' and i == 12 else net})
    write_csv(raw / 'D1a_CRSP_monthly_returns.csv', names, returns)
    columns = ['crsp_fundno', 'caldt', 'crsp_cl_grp', 'crsp_obj_cd', 'si_obj_cd',
               'lipper_class', 'lipper_obj_cd', 'wbrger_obj_cd', 'fund_name',
               'index_fund_flag', 'et_flag', 'mgmt_cd', 'exp_ratio', 'turn_ratio',
               'fiscal_yearend']
    attrs = [dict.fromkeys(columns, '') for _ in range(3)]
    for i, row in enumerate(attrs):
        row.update(crsp_fundno=f'{i+1:06}', caldt='2016-09-30', crsp_cl_grp='100',
                   crsp_obj_cd='EDYG', fund_name='Domestic Growth Fund', mgmt_cd='F1',
                   exp_ratio='.012', turn_ratio='.5', fiscal_yearend='2015-12-31')
    attrs[2]['et_flag'] = 'N'  # CRSP N denotes an ETN, not "no ETF".
    newer = attrs[0].copy()
    newer.update(caldt='2018-01-31', fiscal_yearend='2030-01-31', exp_ratio='.5')
    attrs.append(newer)
    for original in attrs[:2]:
        changed = original.copy()
        changed.update(caldt='2020-01-31', crsp_obj_cd='ICQY')
        attrs.append(changed)
    write_csv(raw / 'D1b_CRSP_fund_summary.csv', columns, attrs)
    with (factor_dir / 'D2_Carhart_factors_research.csv').open('w') as f:
        f.write('Factor file\n')
        for d, v in zip(dates, factors):
            f.write(f'{d:%Y%m},{v[0]*100},{v[1]*100},{v[2]*100},0.1\n')
    with (factor_dir / 'D2_Carhart_factors_momentum.csv').open('w') as f:
        for d, v in zip(dates, factors):
            f.write(f'{d:%Y%m},{v[3]*100}\n')
    config = json.loads(Path('configs/fund_panel.json').read_text())
    config.update(formation_start='2017-01-31', formation_end='2020-12-31',
                  summary_max_age_days=5000, fee_max_age_days=5000, memory_limit='256MB')
    output = tmp_path / 'output'
    build_panel(raw, output, config)
    db = duckdb.connect(str(output / 'fund_panel.duckdb'), read_only=True)
    try:
        assert db.execute("SELECT count(*) FROM classes WHERE universe_status='exchange_traded'").fetchone()[0] > 0
        row = db.execute("""SELECT share_classes, tna, net_return, expense_ratio, flow
            FROM panel WHERE return_month='2017-02-28'""").fetchone()
        expected = .001 + .005 + factors[1] @ beta - .001
        assert row == pytest.approx((2, 40, expected, .012, -expected))
        assert db.execute("SELECT min(known_excluded_classes) FROM panel").fetchone()[0] == 1
        missing = db.execute("""SELECT net_return, share_classes FROM panel
            WHERE return_month='2018-01-31'""").fetchone()
        assert missing == (None, 2)
        missing_outcome = db.execute("SELECT future_classes_missing, target_net_return FROM panel "
                                     "WHERE formation_date='2018-08-31'").fetchone()
        assert missing_outcome == (1, None)
        friday = db.execute("SELECT DISTINCT source_return_date, return_month FROM classes "
                            "WHERE return_month='2017-09-30'").fetchone()
        assert tuple(map(str, friday)) == ('2017-09-29', '2017-09-30')
        extreme = db.execute("SELECT net_return, return_above_cutoff, gross_return, flow FROM panel "
                             "WHERE return_month='2019-11-30'").fetchone()
        assert extreme == (2.0, True, None, None)
        target_extreme = db.execute("SELECT target_net_return, next_month_abnormal_return "
                                    "FROM panel WHERE formation_date='2019-10-31'").fetchone()
        assert target_extreme == (2.0, None)
        fee = db.execute("SELECT expense_ratio FROM panel WHERE return_month='2018-08-31'").fetchone()[0]
        assert fee == pytest.approx(.012)  # The newer .5 fee is not yet available.
        assert db.execute("SELECT count(*) FROM panel WHERE next_month_abnormal_return IS NOT NULL").fetchone()[0] > 0
        # A future objective change must not remove the outcome of the earlier selection.
        target = db.execute("SELECT next_month_abnormal_return FROM panel "
                            "WHERE formation_date='2020-03-31'").fetchone()[0]
        assert target == pytest.approx(.005)
        assert db.execute("SELECT count(*) FROM classes WHERE return_month='2020-04-30' "
                          "AND universe_status='other_objective'").fetchone()[0] == 2
        assert db.execute("SELECT max(abs(next_month_abnormal_return-.005)) FROM panel").fetchone()[0] < 1e-8
    finally:
        db.close()
    # Two records for one share class and economic month must fail, not double count.
    with (raw / 'D1a_CRSP_monthly_returns.csv').open('a', newline='') as f:
        csv.writer(f).writerow(['000001', '2017-02-27', '10', '.01'])
    with pytest.raises(ValueError, match='Duplicate share-class economic month'):
        build_panel(raw, tmp_path / 'duplicate_output', config)


def test_invalid_lags_and_raw_output_are_rejected(tmp_path: Path):
    config = json.loads(Path('configs/fund_panel.json').read_text())
    raw = tmp_path / 'raw'
    raw.mkdir()
    with pytest.raises(ValueError, match='outside the raw'):
        build_panel(raw, raw / 'output', config)
    config['summary_lag_days'] = -1
    with pytest.raises(ValueError, match='summary_lag_days'):
        build_panel(raw, tmp_path / 'output', config)
