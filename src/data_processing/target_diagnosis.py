"""Reconcile target availability without evaluating returns or predictive performance."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import duckdb

from src.data_processing.fund_panel import read_factors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def build_diagnosis(db: duckdb.DuckDBPyConnection, factors, cutoff: str,
                    start: str = '1999-03-01', end: str = '2025-12-31',
                    fee_max_age_days: int = 730, max_return: float = 1.0) -> None:
    """Create temporary diagnostics; categories have precedence, not causal exclusivity."""
    db.register('diagnostic_factors', factors)
    db.execute("""
      CREATE TEMP TABLE future_inputs AS
      WITH rows AS (
        SELECT c.fund_id, c.formation_date, c.crsp_obj_cd,
          r.crsp_fundno AS observed_class, r.lag_tna, r.net_return,
          CASE WHEN date_diff('day', f.fee_summary_date, r.formation_date) <= ?
               AND f.exp_ratio >= 0 THEN f.exp_ratio END AS expense_ratio
        FROM classes c LEFT JOIN class_returns r
          ON c.crsp_fundno=r.crsp_fundno
          AND r.return_month=last_day(c.formation_date + INTERVAL 1 MONTH)
        ASOF LEFT JOIN fees f
          ON r.crsp_fundno=f.crsp_fundno AND r.formation_date>=f.fee_available_at
        WHERE c.universe_status='selected'
      )
      SELECT fund_id, formation_date,
        count(*) FILTER (WHERE observed_class IS NULL) AS absent_class,
        count(*) FILTER (WHERE observed_class IS NOT NULL AND lag_tna IS NULL) AS missing_weight,
        sum(lag_tna) AS total_weight,
        count(*) FILTER (WHERE lag_tna>0 AND (net_return IS NULL OR net_return < -1)) AS bad_return,
        count(*) FILTER (WHERE lag_tna>0 AND expense_ratio IS NULL) AS missing_fee,
        CASE WHEN count(DISTINCT coalesce(nullif(trim(crsp_obj_cd), ''), 'fallback'))=1
          THEN min(coalesce(nullif(trim(crsp_obj_cd), ''), 'fallback')) ELSE 'mixed' END AS objective
      FROM rows GROUP BY 1,2
    """, [fee_max_age_days])
    db.execute("""
      CREATE TEMP TABLE diagnosis AS
      WITH facts AS (
        SELECT p.*, i.absent_class, i.missing_weight, i.total_weight, i.bad_return,
          i.missing_fee, i.objective,
          (k.month IS NULL OR k.mkt IS NULL OR k.smb IS NULL OR k.hml IS NULL
           OR k.mom IS NULL OR k.rf IS NULL) AS missing_factors,
          (b.beta_mkt IS NULL OR b.beta_smb IS NULL OR b.beta_hml IS NULL
           OR b.beta_mom IS NULL) AS missing_loadings,
          last_day(p.formation_date + INTERVAL 2 MONTH) > CAST(? AS DATE) AS after_cutoff
        FROM panel p JOIN future_inputs i USING (fund_id, formation_date)
        LEFT JOIN abnormal b ON b.fund_id=p.fund_id
          AND b.return_month=last_day(p.formation_date + INTERVAL 1 MONTH)
        LEFT JOIN diagnostic_factors k ON k.month=last_day(p.formation_date + INTERVAL 1 MONTH)
        WHERE p.formation_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
      )
      SELECT *, CASE
        WHEN after_cutoff AND next_month_abnormal_return IS NOT NULL THEN '01_observed_after_cutoff'
        WHEN after_cutoff THEN '02_missing_after_cutoff'
        WHEN next_month_abnormal_return IS NOT NULL THEN '00_observed_by_cutoff'
        WHEN absent_class>0 THEN '03_future_class_absent'
        WHEN missing_weight>0 OR total_weight IS NULL OR total_weight<=0 THEN '04_missing_future_weight'
        WHEN bad_return>0 THEN '05_missing_invalid_future_return'
        WHEN target_net_return>? THEN '06_return_above_cutoff'
        WHEN missing_fee>0 THEN '07_missing_future_expense'
        WHEN target_beta_observations IS NULL OR target_beta_observations<30 THEN '08_insufficient_history'
        WHEN missing_factors THEN '09_missing_factors'
        WHEN missing_loadings THEN '10_failed_or_rank_deficient_loadings'
        ELSE '11_unresolved' END AS reason
      FROM facts
    """, [cutoff, start, end, max_return])
    n_panel_row = db.execute("SELECT count(*) FROM panel WHERE formation_date BETWEEN ? AND ?", [start, end]).fetchone()
    n_diagnosis_row = db.execute('SELECT count(*) FROM diagnosis').fetchone()
    if n_panel_row is None or n_diagnosis_row is None:
        raise ValueError('Could not count formation rows')
    n_panel, n_diagnosis = n_panel_row[0], n_diagnosis_row[0]
    if n_panel != n_diagnosis:
        raise ValueError(f'Formation rows did not reconcile: {n_panel} versus {n_diagnosis}')


def write_query(db, query: str, path: Path) -> None:
    cursor = db.execute(query)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow([c[0] for c in cursor.description])
        writer.writerows(cursor.fetchall())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path('data/interim/fund_panel/fund_panel.duckdb'))
    parser.add_argument('--raw-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    args = parser.parse_args()
    root = args.raw_dir.resolve()
    output = args.output_dir.resolve()
    if output.is_relative_to(root):
        raise ValueError('Output must be outside the raw directory')
    protocol = json.loads(args.protocol.read_text())
    config_path = Path('configs/fund_panel.json')
    config = json.loads(config_path.read_text())
    sources = [root / 'D2_Carhart_factors/D2_Carhart_factors_research.csv',
               root / 'D2_Carhart_factors/D2_Carhart_factors_momentum.csv']
    checks = [(args.database, protocol['provenance']['fund_panel_db_sha256']),
              (config_path, protocol['provenance']['fund_panel_config_sha256']),
              (sources[0], protocol['provenance']['inputs_sha256']['D2_research']),
              (sources[1], protocol['provenance']['inputs_sha256']['D2_momentum'])]
    for path, expected in checks:
        if sha256(path) != expected:
            raise ValueError(f'Input hash differs from registered protocol: {path}')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'Output directory is not empty: {output}')
    output.mkdir(parents=True, exist_ok=True)
    factors = read_factors(sources[0]).merge(read_factors(sources[1], momentum=True),
                                            on='month', how='inner', validate='one_to_one')
    db = duckdb.connect(str(args.database), read_only=True)
    try:
        db.execute("SET memory_limit='1GB'")
        db.execute('SET threads=2')
        sample = protocol['sample']
        build_diagnosis(db, factors, sample['label_available_by'], sample['common_start'],
                        sample['common_end'], config['fee_max_age_days'], config['max_fund_return'])
        queries = {
            'reasons_by_year.csv': "SELECT year(formation_date) AS formation_year, reason, count(*) fund_months FROM diagnosis GROUP BY 1,2 ORDER BY 1,2",
            'reasons_total.csv': "SELECT reason, count(*) fund_months FROM diagnosis GROUP BY 1 ORDER BY 1",
            'coverage_by_year_type.csv': "SELECT year(formation_date) AS formation_year, objective, count(*) fund_months, count(*) FILTER (WHERE reason='00_observed_by_cutoff') timely FROM diagnosis GROUP BY 1,2 ORDER BY 1,2",
            'formation_comparison.csv': """SELECT CASE WHEN reason='00_observed_by_cutoff' THEN 'timely_target' ELSE 'other' END cohort,
                count(*) fund_months, count(DISTINCT fund_id) funds,
                avg(tna) mean_tna, median(tna) median_tna, count(tna) tna_count,
                avg(expense_ratio) mean_expense, count(expense_ratio) expense_count,
                avg(flow) mean_flow, count(flow) flow_count,
                count(momentum_12_2) momentum_count, avg(share_classes) mean_classes,
                count(*) FILTER (WHERE known_excluded_classes>0) partial_groups,
                count(*) FILTER (WHERE flow IS NOT NULL AND momentum_12_2 IS NOT NULL) complete_features
                FROM diagnosis GROUP BY 1 ORDER BY 1""",
            'evaluation_eligible.csv': f"""WITH eligible AS (
                SELECT * FROM diagnosis WHERE formation_date BETWEEN
                  DATE '{sample['evaluation_formation_start']}' AND DATE '{sample['evaluation_formation_end']}'
                  AND flow IS NOT NULL AND isfinite(flow) AND momentum_12_2 IS NOT NULL
                  AND isfinite(momentum_12_2)
              ) SELECT formation_date, count(*) funds,
                count(*) FILTER (WHERE target_net_return IS NULL) missing_net,
                count(*) FILTER (WHERE next_month_abnormal_return IS NULL) missing_abnormal
                FROM eligible GROUP BY 1 ORDER BY 1""",
            'evaluation_comparison.csv': f"""SELECT CASE WHEN next_month_abnormal_return IS NULL
                THEN 'missing' ELSE 'observed' END cohort, count(*) fund_months,
                median(tna) median_tna, count(tna) tna_count, avg(expense_ratio) mean_expense,
                count(expense_ratio) expense_count, avg(share_classes) mean_classes,
                count(*) FILTER (WHERE known_excluded_classes>0) partial_groups
                FROM diagnosis WHERE formation_date BETWEEN DATE '{sample['evaluation_formation_start']}'
                AND DATE '{sample['evaluation_formation_end']}' AND flow IS NOT NULL AND isfinite(flow)
                AND momentum_12_2 IS NOT NULL AND isfinite(momentum_12_2) GROUP BY 1 ORDER BY 1""",
            'mapping_sensitivity.csv': f"""WITH groups AS (
              SELECT crsp_fundno, caldt, available_at, crsp_cl_grp FROM summary
              WHERE crsp_cl_grp IS NOT NULL AND trim(crsp_cl_grp)<>'' AND same_date_rows=1
            ), missing AS (
              SELECT * FROM classes WHERE universe_status='missing_class_group'
              AND formation_date BETWEEN DATE '{sample['common_start']}' AND DATE '{sample['common_end']}'
            ), candidate AS (
              SELECT m.*, g.caldt group_source_date, g.crsp_cl_grp previous_group
              FROM missing m ASOF LEFT JOIN groups g
              ON m.crsp_fundno=g.crsp_fundno AND m.formation_date>=g.available_at
            ) SELECT count(*) class_months_without_group,
              count(*) FILTER (WHERE previous_group IS NOT NULL
                AND date_diff('day',group_source_date,formation_date)<={config['summary_max_age_days']}) carry_forward_within_age,
              count(DISTINCT crsp_fundno) FILTER (WHERE previous_group IS NOT NULL
                AND date_diff('day',group_source_date,formation_date)<={config['summary_max_age_days']}) distinct_classes,
              count(*) FILTER (WHERE previous_group IS NOT NULL) carry_forward_any_age FROM candidate""",
            'fee_sensitivity.csv': f"""WITH fee_exp AS (SELECT * FROM fees WHERE exp_ratio>=0),
              base AS (SELECT * FROM classes WHERE universe_status='selected' AND formation_date
                BETWEEN DATE '{sample['common_start']}' AND DATE '{sample['common_end']}'),
              joined AS (SELECT c.expense_ratio, c.formation_date, e.fee_summary_date, e.exp_ratio
                FROM base c ASOF LEFT JOIN fee_exp e ON c.crsp_fundno=e.crsp_fundno
                AND c.formation_date>=e.fee_available_at)
              SELECT count(*) FILTER (WHERE expense_ratio IS NULL) no_current_expense,
                count(*) FILTER (WHERE expense_ratio IS NULL AND exp_ratio IS NOT NULL
                  AND date_diff('day',fee_summary_date,formation_date)<={config['fee_max_age_days']})
                  older_valid_expense FROM joined""",
            'upstream_waterfall.csv': f"""SELECT universe_status, count(*) class_months FROM classes
                WHERE formation_date BETWEEN DATE '{sample['common_start']}' AND DATE '{sample['common_end']}'
                GROUP BY 1 ORDER BY 2 DESC""",
            'overlaps.csv': """SELECT count(*) AS formation_rows, count(*) FILTER (WHERE next_month_abnormal_return IS NULL) missing_target,
                count(*) FILTER (WHERE absent_class>0) absent_class,
                count(*) FILTER (WHERE missing_weight>0 OR total_weight IS NULL OR total_weight<=0) missing_weight,
                count(*) FILTER (WHERE bad_return>0) bad_return,
                count(*) FILTER (WHERE missing_fee>0) missing_fee,
                count(*) FILTER (WHERE target_beta_observations IS NULL OR target_beta_observations<30) insufficient_history,
                count(*) FILTER (WHERE missing_factors) missing_factors,
                count(*) FILTER (WHERE known_excluded_classes>0) partial_groups,
                count(*) FILTER (WHERE known_excluded_classes>0 AND next_month_abnormal_return IS NULL) partial_and_missing
                FROM diagnosis""",
        }
        for name, query in queries.items():
            write_query(db, query, output / name)
        unresolved = db.execute("SELECT count(*) FROM diagnosis WHERE reason='11_unresolved'").fetchone()
        if unresolved is None:
            raise ValueError('Could not count unresolved targets')
        if unresolved[0]:
            print('Warning: unresolved missing targets; see reasons_total.csv')
    finally:
        db.close()
    print(f'Wrote target diagnosis to {output}')


if __name__ == '__main__':
    main()
