"""Diagnose frozen extreme-decile coverage without calculating new performance."""
import argparse
import json
from pathlib import Path

import duckdb

from src.data_processing.fund_panel import read_factors
from src.data_processing.target_diagnosis import build_diagnosis, sha256, write_query


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, required=True)
    parser.add_argument('--baseline-dir', type=Path, default=Path('data/interim/baseline_review'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads((args.baseline_dir / 'protocol.json').read_text())
    database = Path('data/interim/fund_panel/fund_panel.duckdb')
    if sha256(database) != protocol['provenance']['fund_panel_db_sha256']:
        raise ValueError('Panel hash differs from frozen baseline')
    if args.output_dir.resolve().is_relative_to(args.raw_dir.resolve()):
        raise ValueError('Output must be outside raw data')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    directory = args.raw_dir / 'D2_Carhart_factors'
    research = directory / 'D2_Carhart_factors_research.csv'
    momentum = directory / 'D2_Carhart_factors_momentum.csv'
    for path, key in [(research, 'D2_research'), (momentum, 'D2_momentum')]:
        if sha256(path) != protocol['provenance']['inputs_sha256'][key]:
            raise ValueError(f'Factor hash mismatch: {path}')
    factors = read_factors(research).merge(read_factors(momentum, True), on='month', validate='one_to_one')
    with duckdb.connect(str(database), read_only=True) as db:
        db.execute("SET memory_limit='1GB'")
        db.execute('SET threads=2')
        build_diagnosis(db, factors, protocol['sample']['label_available_by'])
        db.execute("""CREATE TEMP TABLE selected AS
            SELECT c.model, c.decile, c.weight, d.* FROM read_csv(?,
              types={'fund_id':'VARCHAR','formation_date':'DATE'}) c
            JOIN diagnosis d USING(fund_id,formation_date) WHERE c.decile IN (1,10)""",
                   [str(args.baseline_dir / 'constituents.csv')])
        db.execute("""CREATE TEMP TABLE source_trace AS
          WITH spans AS (
            SELECT crsp_fundno, min(return_month) first_return, max(return_month) last_return
            FROM class_returns GROUP BY 1
          )
          SELECT s.model, s.decile, s.fund_id, s.formation_date, s.weight,
            c.crsp_fundno, r.crsp_fundno IS NULL absent_return,
            last_day(s.formation_date + INTERVAL 1 MONTH) target_month,
            r.formation_date target_available_at, r.lag_tna, r.net_return,
            spans.first_return, spans.last_return,
            f.fee_summary_date, f.fee_available_at, f.exp_ratio,
            CASE WHEN r.crsp_fundno IS NULL THEN
              CASE WHEN spans.last_return < last_day(s.formation_date + INTERVAL 1 MONTH)
                THEN 'terminal_in_export' ELSE 'internal_gap' END
              WHEN r.lag_tna IS NULL THEN 'missing_lag_tna'
              WHEN r.lag_tna>0 AND (r.net_return IS NULL OR r.net_return < -1)
                THEN 'missing_or_invalid_return' ELSE 'observed' END return_issue,
            CASE WHEN r.lag_tna>0 THEN
              CASE WHEN f.crsp_fundno IS NULL THEN 'no_available_fee_record'
                WHEN date_diff('day', f.fee_summary_date, r.formation_date)>730 THEN 'stale_fee'
                WHEN f.exp_ratio IS NULL THEN 'blank_expense'
                WHEN f.exp_ratio<0 THEN 'negative_expense'
                ELSE 'usable' END ELSE 'no_positive_observed_weight' END fee_issue
          FROM selected s JOIN classes c ON s.fund_id=c.fund_id
            AND s.formation_date=c.formation_date AND c.universe_status='selected'
          LEFT JOIN class_returns r ON c.crsp_fundno=r.crsp_fundno
            AND r.return_month=last_day(s.formation_date + INTERVAL 1 MONTH)
          LEFT JOIN spans ON c.crsp_fundno=spans.crsp_fundno
          ASOF LEFT JOIN fees f ON r.crsp_fundno=f.crsp_fundno
            AND r.formation_date>=f.fee_available_at
        """)
        queries = {
            'source_return_issues.csv': """SELECT model,decile,return_issue,
                count(*) class_months,count(DISTINCT crsp_fundno) classes
                FROM source_trace WHERE return_issue<>'observed'
                GROUP BY 1,2,3 ORDER BY 1,2,3""",
            'source_fee_issues.csv': """SELECT model,decile,fee_issue,
                count(*) class_months,count(DISTINCT crsp_fundno) classes
                FROM source_trace WHERE fee_issue NOT IN ('usable','no_positive_observed_weight')
                GROUP BY 1,2,3 ORDER BY 1,2,3""",
            'source_repair_requests.csv': """SELECT DISTINCT crsp_fundno,target_month,
                return_issue,fee_issue,first_return,last_return,fee_summary_date,
                fee_available_at FROM source_trace
                WHERE return_issue<>'observed' OR fee_issue NOT IN ('usable','no_positive_observed_weight')
                ORDER BY 1,2""",
            'latest_expense_timing.csv': """WITH problems AS (
                SELECT DISTINCT crsp_fundno,target_month,target_available_at
                FROM source_trace WHERE fee_issue NOT IN ('usable','no_positive_observed_weight')
              ), ranked AS (
                SELECT p.*,s.caldt,s.fiscal_yearend,s.available_at,
                  row_number() OVER(PARTITION BY p.crsp_fundno,p.target_month ORDER BY s.caldt DESC) rn
                FROM problems p LEFT JOIN summary s ON p.crsp_fundno=s.crsp_fundno
                  AND s.caldt<=p.target_month AND s.exp_ratio>=0 AND s.same_date_rows=1
              ) SELECT CASE WHEN caldt IS NULL THEN 'no_historical_expense'
                WHEN date_diff('day',caldt,target_available_at)>730 THEN 'stale_latest_expense'
                WHEN greatest(available_at,fiscal_yearend+INTERVAL 180 DAY)>target_available_at
                  THEN 'latest_expense_not_yet_available' ELSE 'other' END reason,
                count(*) class_months FROM ranked WHERE rn=1 GROUP BY 1 ORDER BY 1""",
            'expense_source_evidence.csv': """WITH problems AS (
                SELECT DISTINCT crsp_fundno,target_month,target_available_at
                FROM source_trace WHERE fee_issue NOT IN ('usable','no_positive_observed_weight')
              ), evidence AS (
                SELECT p.crsp_fundno,p.target_month,
                  count(*) FILTER(WHERE s.exp_ratio>=0 AND s.same_date_rows=1
                    AND s.fiscal_yearend IS NOT NULL
                    AND greatest(s.available_at,s.fiscal_yearend + INTERVAL 180 DAY)<=p.target_available_at
                    AND date_diff('day',s.caldt,p.target_available_at)<=730) timely_valid_records,
                  count(*) FILTER(WHERE s.exp_ratio>=0 AND s.same_date_rows=1
                    AND s.caldt<=p.target_month) historical_nonnegative_records,
                  count(*) FILTER(WHERE s.exp_ratio>=0 AND s.same_date_rows=1
                    AND s.caldt<=p.target_month AND s.fiscal_yearend IS NULL) undated_fiscal_records
                FROM problems p LEFT JOIN summary s USING(crsp_fundno) GROUP BY 1,2
              ) SELECT count(*) unique_class_months,
                count(*) FILTER(WHERE timely_valid_records>0) with_timely_valid_record,
                count(*) FILTER(WHERE historical_nonnegative_records>0) with_historical_expense,
                count(*) FILTER(WHERE undated_fiscal_records>0) with_missing_fiscal_date
                FROM evidence""",
            'monthly_reasons.csv': """SELECT model, formation_date, decile, reason,
                count(*) holdings, sum(weight) original_weight FROM selected
                GROUP BY 1,2,3,4 ORDER BY 1,2,3,4""",
            'reason_totals.csv': """SELECT model, decile, reason, count(*) holdings,
                sum(weight)/(SELECT count(DISTINCT formation_date) FROM selected) mean_monthly_weight FROM selected GROUP BY 1,2,3 ORDER BY 1,2,3""",
            'overlaps.csv': """SELECT model, decile, count(*) holdings,
                count(*) FILTER(WHERE absent_class>0) absent_class,
                count(*) FILTER(WHERE missing_weight>0) missing_weight,
                count(*) FILTER(WHERE bad_return>0) bad_return,
                count(*) FILTER(WHERE missing_fee>0) missing_fee,
                count(*) FILTER(WHERE target_beta_observations<30) short_history
                FROM selected GROUP BY 1,2 ORDER BY 1,2""",
            'formation_comparison.csv': """SELECT model, decile,
                next_month_abnormal_return IS NULL missing_target, count(*) holdings,
                median(tna) median_tna, count(tna) observed_tna,
                avg(expense_ratio) mean_expense, count(expense_ratio) observed_expense
                FROM selected GROUP BY 1,2,3 ORDER BY 1,2,3""",
            'fee_recovery_candidates.csv': """WITH old_expense AS (
                SELECT * FROM fees WHERE exp_ratio>=0
              ), rows AS (
                SELECT s.model,s.decile,s.fund_id,s.formation_date,s.weight,s.missing_fee,
                  c.crsp_fundno,r.lag_tna,
                  CASE WHEN f.exp_ratio>=0 AND date_diff('day',f.fee_summary_date,r.formation_date)<=730
                    THEN f.exp_ratio END current_expense,
                  CASE WHEN e.exp_ratio>=0 AND date_diff('day',e.fee_summary_date,r.formation_date)<=730
                    THEN e.exp_ratio END previous_expense
                FROM selected s JOIN classes c ON s.fund_id=c.fund_id
                  AND s.formation_date=c.formation_date AND c.universe_status='selected'
                LEFT JOIN class_returns r ON c.crsp_fundno=r.crsp_fundno
                  AND r.return_month=last_day(s.formation_date+INTERVAL 1 MONTH)
                ASOF LEFT JOIN fees f ON r.crsp_fundno=f.crsp_fundno AND r.formation_date>=f.fee_available_at
                ASOF LEFT JOIN old_expense e ON r.crsp_fundno=e.crsp_fundno AND r.formation_date>=e.fee_available_at
              ) SELECT model,decile,count(*) FILTER(WHERE lag_tna>0 AND current_expense IS NULL) missing_class_expenses,
                count(*) FILTER(WHERE lag_tna>0 AND current_expense IS NULL AND previous_expense IS NOT NULL) recoverable_class_expenses
                FROM rows GROUP BY 1,2 ORDER BY 1,2""",
        }
        for name, query in queries.items():
            write_query(db, query, args.output_dir / name)
    manifest = {'panel_sha256': sha256(database),
                'constituents_sha256': sha256(args.baseline_dir / 'constituents.csv'),
                'code_sha256': sha256(Path(__file__)), 'note': 'Coverage only; no new performance.'}
    (args.output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
