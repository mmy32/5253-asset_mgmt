from datetime import date

import duckdb
import pandas as pd

from src.data_processing.target_diagnosis import build_diagnosis


def test_missing_target_precedence_cutoff_and_reconciliation():
    db = duckdb.connect()
    db.execute("""CREATE TABLE panel (fund_id VARCHAR, formation_date DATE,
        next_month_abnormal_return DOUBLE, target_net_return DOUBLE,
        target_beta_observations INTEGER)""")
    db.execute("""INSERT INTO panel VALUES
      ('observed','2025-10-31',.01,.02,36),
      ('absent','2025-10-31',NULL,NULL,0),
      ('fee','2025-10-31',NULL,.02,0),
      ('history','2025-10-31',NULL,.02,29),
      ('rank','2025-10-31',NULL,.02,36),
      ('factor','2025-09-30',NULL,.02,36),
      ('late','2025-11-30',.01,.02,36),
      ('late_missing','2025-11-30',NULL,NULL,0)""")
    db.execute("""CREATE TABLE classes AS SELECT fund_id, fund_id crsp_fundno,
        formation_date, 'selected' universe_status, 'EDYG' crsp_obj_cd FROM panel""")
    db.execute("""CREATE TABLE class_returns AS SELECT fund_id crsp_fundno,
        CAST(last_day(formation_date + INTERVAL 1 MONTH) AS DATE) return_month,
        CAST(last_day(formation_date + INTERVAL 2 MONTH) AS DATE) formation_date,
        100.0 lag_tna, .02 net_return FROM panel WHERE fund_id <> 'absent'""")
    db.execute("""CREATE TABLE fees AS SELECT fund_id crsp_fundno,
        DATE '2025-01-01' fee_summary_date, DATE '2025-02-01' fee_available_at,
        .01 exp_ratio FROM panel WHERE fund_id <> 'fee'""")
    db.execute("""CREATE TABLE abnormal AS SELECT fund_id,
        CAST(last_day(formation_date + INTERVAL 1 MONTH) AS DATE) return_month,
        CASE WHEN fund_id='rank' THEN NULL ELSE 1.0 END beta_mkt,
        1.0 beta_smb, 1.0 beta_hml, 1.0 beta_mom FROM panel""")
    factors = pd.DataFrame([{'month': date(2025, 11, 30), 'mkt': .01, 'smb': .01,
                             'hml': .01, 'mom': .01, 'rf': .001}])
    build_diagnosis(db, factors, '2025-12-31')
    result = dict(db.execute('SELECT fund_id, reason FROM diagnosis').fetchall())
    assert result == {
        'observed': '00_observed_by_cutoff',
        'late': '01_observed_after_cutoff',
        'late_missing': '02_missing_after_cutoff',
        'absent': '03_future_class_absent',
        'fee': '07_missing_future_expense',
        'history': '08_insufficient_history',
        'factor': '09_missing_factors',
        'rank': '10_failed_or_rank_deficient_loadings',
    }
    db.close()
