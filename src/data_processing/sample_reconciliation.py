"""Reconcile retrospective share-class attrition with the lagged fund panel.

The full-file class mapping is a look-ahead diagnostic only, not a model input.
No holdings data or outcome performance are read.
"""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path
from typing import Any

import duckdb

from src.config.sample import ACTIVE_US_EQUITY_OBJ_CODES, EXCLUDED_NAME_PATTERN, MAX_RAW_RETURN
from src.data_loader.audit import sha256


def reconcile(db: duckdb.DuckDBPyConnection, start: str, end: str,
              aligned_start: str, aligned_end: str, summary_lag_days: int = 90) -> dict[str, Any]:
    """Compute class-level screens and mapping sensitivities from the read-only panel snapshot."""
    codes = ",".join("'" + value.replace("'", "''") + "'"
                     for value in sorted(ACTIVE_US_EQUITY_OBJ_CODES))
    db.execute(f"""
      CREATE TEMP TABLE retro AS
      WITH attached AS (
        SELECT r.crsp_fundno, r.source_return_date, r.return_month, r.formation_date,
          r.net_return, s.crsp_obj_cd, s.fund_name, s.crsp_cl_grp,
          s.caldt AS retro_summary_date, s.same_date_rows,
          l.universe_status AS lag_status, l.summary_date AS lag_summary_date
        FROM (SELECT * FROM class_returns WHERE source_return_date BETWEEN ? AND ?) r
        ASOF LEFT JOIN summary s
          ON r.crsp_fundno=s.crsp_fundno AND r.source_return_date>=s.caldt
        LEFT JOIN classes l
          ON r.crsp_fundno=l.crsp_fundno AND r.return_month=l.return_month
      )
      SELECT *, CASE
        WHEN crsp_obj_cd IS NULL OR trim(crsp_obj_cd)='' THEN 'unknown_objective'
        WHEN crsp_obj_cd NOT IN ({codes}) THEN 'other_objective'
        WHEN regexp_matches(lower(coalesce(fund_name,'')), ?) THEN 'excluded_name'
        WHEN net_return > ? THEN 'extreme_return'
        ELSE 'selected' END AS retro_status
      FROM attached
    """, [start, end, EXCLUDED_NAME_PATTERN, MAX_RAW_RETURN])
    db.execute("""
      CREATE TEMP TABLE mapping AS
      WITH valid_groups AS (
        SELECT crsp_fundno, caldt, crsp_cl_grp FROM summary
        WHERE crsp_cl_grp IS NOT NULL AND trim(crsp_cl_grp)<>''
      ), static_groups AS (
        SELECT crsp_fundno, crsp_cl_grp,
          min(caldt) OVER (PARTITION BY crsp_fundno, crsp_cl_grp) AS first_group_date,
          row_number() OVER (PARTITION BY crsp_fundno ORDER BY caldt DESC) AS n
        FROM valid_groups
      )
      SELECT r.*, g.crsp_cl_grp AS last_nonblank_group,
        g.caldt AS last_nonblank_date, z.crsp_cl_grp AS full_file_group,
        z.first_group_date
      FROM (SELECT * FROM retro WHERE retro_status='selected') r
      ASOF LEFT JOIN valid_groups g
        ON r.crsp_fundno=g.crsp_fundno AND r.source_return_date>=g.caldt
      LEFT JOIN static_groups z ON r.crsp_fundno=z.crsp_fundno AND z.n=1
    """)
    waterfall = db.execute("""
      SELECT count(*) AS in_window,
        count(*) FILTER (WHERE retro_status<>'unknown_objective') AS objective_known,
        count(*) FILTER (WHERE retro_status IN ('excluded_name','extreme_return','selected'))
          AS active_objective,
        count(*) FILTER (WHERE retro_status IN ('extreme_return','selected')) AS passed_name,
        count(*) FILTER (WHERE retro_status='selected') AS passed_return,
        count(*) FILTER (WHERE retro_status='selected' AND net_return IS NULL)
          AS selected_missing_return,
        count(*) FILTER (WHERE retro_summary_date IS NULL) AS no_summary_rows,
        count(*) FILTER (WHERE retro_summary_date IS NOT NULL AND
          (crsp_obj_cd IS NULL OR trim(crsp_obj_cd)='')) AS summary_without_objective,
        count(*) FILTER (WHERE retro_status='selected' AND
          (fund_name IS NULL OR trim(fund_name)='')) AS selected_missing_name,
        count(*) FILTER (WHERE same_date_rows>1) AS ambiguous_summary_rows,
        count(*) FILTER (WHERE same_date_rows>1 AND retro_status='selected')
          AS selected_ambiguous_summary_rows
      FROM retro
    """)
    waterfall_dict = dict(zip([x[0] for x in waterfall.description], waterfall.fetchone()))
    waterfall_dict["source_rows"] = db.execute("SELECT count(*) FROM class_returns").fetchone()[0]
    mapping = db.execute("""
      SELECT count(*) AS selected_class_months,
        count(*) FILTER (WHERE crsp_cl_grp IS NULL OR trim(crsp_cl_grp)='') AS latest_missing,
        count(DISTINCT (return_month,crsp_cl_grp))
          FILTER (WHERE crsp_cl_grp IS NOT NULL AND trim(crsp_cl_grp)<>'') AS strict_mapped,
        count(DISTINCT (return_month,CASE WHEN crsp_cl_grp IS NULL OR trim(crsp_cl_grp)=''
          THEN 'S:'||crsp_fundno ELSE 'G:'||crsp_cl_grp END)) AS latest_singleton,
        count(*) FILTER (WHERE last_nonblank_group IS NULL) AS last_nonblank_missing,
        count(DISTINCT (return_month,last_nonblank_group))
          FILTER (WHERE last_nonblank_group IS NOT NULL) AS last_nonblank_strict,
        count(DISTINCT (return_month,CASE WHEN last_nonblank_group IS NULL
          THEN 'S:'||crsp_fundno ELSE 'G:'||last_nonblank_group END)) AS last_nonblank_singleton,
        count(*) FILTER (WHERE full_file_group IS NULL) AS full_file_missing,
        count(DISTINCT (return_month,full_file_group))
          FILTER (WHERE full_file_group IS NOT NULL) AS full_file_strict,
        count(DISTINCT (return_month,CASE WHEN full_file_group IS NULL
          THEN 'S:'||crsp_fundno ELSE 'G:'||full_file_group END)) AS full_file_singleton,
        count(*) FILTER (WHERE last_nonblank_group IS NULL AND full_file_group IS NOT NULL)
          AS future_only_class_months,
        count(DISTINCT crsp_fundno) FILTER (WHERE last_nonblank_group IS NULL
          AND full_file_group IS NOT NULL) AS future_only_classes,
        count(*) FILTER (WHERE last_nonblank_group IS NULL AND full_file_group IS NOT NULL
          AND first_group_date > formation_date) AS first_group_after_formation,
        count(*) FILTER (WHERE last_nonblank_group IS NULL AND full_file_group IS NOT NULL
          AND first_group_date + ? * INTERVAL 1 DAY > formation_date) AS first_group_unavailable_at_lag,
        count(*) FILTER (WHERE last_nonblank_group IS NOT NULL AND full_file_group IS NOT NULL
          AND last_nonblank_group<>full_file_group) AS nonblank_mapping_changes,
        min(source_return_date) FILTER (WHERE last_nonblank_group IS NULL
          AND full_file_group IS NOT NULL) AS first_future_only_date,
        max(source_return_date) FILTER (WHERE last_nonblank_group IS NULL
          AND full_file_group IS NOT NULL) AS last_future_only_date
      FROM mapping
    """, [summary_lag_days])
    mapping_dict = dict(zip([x[0] for x in mapping.description], mapping.fetchone()))
    db.execute("""
      CREATE TEMP TABLE aligned AS
      SELECT *, coalesce(lag_status,'missing_local_row') AS local_status
      FROM retro WHERE formation_date BETWEEN ? AND ?
    """, [aligned_start, aligned_end])
    matrix = db.execute("""
      SELECT CASE WHEN retro_status='selected' THEN 'selected' ELSE 'not_selected' END AS retro,
        CASE WHEN local_status='selected' THEN 'selected' ELSE 'not_selected' END AS lagged,
        count(*) AS class_months FROM aligned GROUP BY 1,2 ORDER BY 1,2
    """)
    matrix_list = [dict(zip([x[0] for x in matrix.description], row)) for row in matrix.fetchall()]
    local_reasons = db.execute("""
      SELECT local_status, count(*) AS class_months FROM aligned
      WHERE retro_status='selected' AND local_status<>'selected'
      GROUP BY 1 ORDER BY 2 DESC,1
    """).fetchall()
    retro_reasons = db.execute("""
      SELECT retro_status, count(*) AS class_months FROM aligned
      WHERE local_status='selected' AND retro_status<>'selected'
      GROUP BY 1 ORDER BY 2 DESC,1
    """).fetchall()
    lag_dates = db.execute("""
      SELECT count(*) AS aligned_class_months,
        count(*) FILTER (WHERE retro_summary_date IS NULL) AS no_retro_summary,
        count(*) FILTER (WHERE lag_summary_date IS NULL) AS no_lagged_summary,
        count(*) FILTER (WHERE lag_summary_date IS NOT NULL AND
          retro_summary_date=lag_summary_date) AS same_summary_date,
        count(*) FILTER (WHERE lag_summary_date IS NOT NULL AND
          retro_summary_date>lag_summary_date) AS retrospective_later,
        count(*) FILTER (WHERE lag_summary_date IS NOT NULL AND
          retro_summary_date<lag_summary_date) AS lagged_later
      FROM aligned
    """)
    date_dict = dict(zip([x[0] for x in lag_dates.description], lag_dates.fetchone()))
    yearly = db.execute("""
      SELECT year(formation_date) AS year, count(*) AS total,
        count(*) FILTER (WHERE retro_status='selected' AND local_status='selected') AS both,
        count(*) FILTER (WHERE retro_status='selected' AND local_status<>'selected') AS retro_only,
        count(*) FILTER (WHERE retro_status<>'selected' AND local_status='selected') AS lagged_only,
        count(*) FILTER (WHERE retro_status<>'selected' AND local_status<>'selected') AS neither
      FROM aligned GROUP BY 1 ORDER BY 1
    """)
    annual = [dict(zip([x[0] for x in yearly.description], row)) for row in yearly.fetchall()]
    stages = [waterfall_dict[key] for key in (
        "source_rows", "in_window", "objective_known", "active_objective", "passed_name",
        "passed_return"
    )]
    if any(a < b for a, b in zip(stages, stages[1:])):
        raise ValueError("Retrospective screen counts do not reconcile")
    for missing, mapped, singleton in (("latest_missing", "strict_mapped", "latest_singleton"),
                                      ("last_nonblank_missing", "last_nonblank_strict",
                                       "last_nonblank_singleton"),
                                      ("full_file_missing", "full_file_strict", "full_file_singleton")):
        if mapping_dict[missing] + mapping_dict[mapped] != mapping_dict[singleton]:
            raise ValueError(f"Mapping sensitivity does not reconcile: {singleton}")
    if sum(row["class_months"] for row in matrix_list) != date_dict["aligned_class_months"]:
        raise ValueError("Aligned selection matrix does not reconcile")
    if sum(row["total"] for row in annual) != date_dict["aligned_class_months"]:
        raise ValueError("Annual coverage does not reconcile")
    return {"waterfall": waterfall_dict, "mapping": mapping_dict, "aligned_matrix": matrix_list,
            "retrospective_only_local_first_reason": dict(local_reasons),
            "lagged_only_retrospective_first_reason": dict(retro_reasons),
            "summary_date_comparison": date_dict, "annual_alignment": annual}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path('data/interim/fund_panel/fund_panel.duckdb'))
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    parser.add_argument('--output-dir', type=Path, default=Path('data/interim/sample_reconciliation'))
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding='utf-8'))
    actual_hash = sha256(args.database)
    if actual_hash != protocol['provenance']['fund_panel_db_sha256']:
        raise ValueError('Panel database hash differs from the registered protocol snapshot')
    if args.output_dir.resolve().is_relative_to(args.database.resolve().parent):
        raise ValueError('Output must be outside the input panel directory')
    names = ['summary.json', 'annual_alignment.csv', 'waterfall.csv', 'mapping_sensitivity.csv']
    if any((args.output_dir / name).exists() for name in names):
        raise FileExistsError('Reconciliation output exists; choose a new output directory')
    with tempfile.TemporaryDirectory(prefix='sample-reconciliation-') as temp:
        db = duckdb.connect(str(args.database), read_only=True)
        try:
            db.execute("SET memory_limit='1GB'")
            db.execute('SET threads=2')
            db.execute('SET temp_directory=?', [temp])
            result = reconcile(db, '1999-03-31', '2025-12-31', '1999-04-30', '2025-12-31',
                               protocol['availability']['summary_lag_days'])
        finally:
            db.close()
    result['provenance'] = {'panel_db_sha256': actual_hash, 'protocol_id': protocol['protocol_id'],
                            'summary_lag_days': protocol['availability']['summary_lag_days'],
                            'window': '1999-03-31 to 2025-12-31 source return date',
                            'aligned_formation_window': '1999-04-30 to 2025-12-31',
                            'note': 'Snapshot summary has one arbitrary row for six duplicate keys; '
                                    'full-file group mapping is a look-ahead sensitivity only.'}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'summary.json').write_text(json.dumps(result, indent=2, default=str)+'\n')
    with (args.output_dir / 'annual_alignment.csv').open('w', newline='') as stream:
        annual_writer = csv.DictWriter(stream, fieldnames=['year','total','both','retro_only','lagged_only','neither'])
        annual_writer.writeheader()
        annual_writer.writerows(result['annual_alignment'])
    w = result['waterfall']
    with (args.output_dir / 'waterfall.csv').open('w', newline='') as stream:
        waterfall_writer = csv.writer(stream)
        waterfall_writer.writerow(['stage','class_months_remaining'])
        for key in ['source_rows','in_window','objective_known','active_objective','passed_name','passed_return']:
            waterfall_writer.writerow([key,w[key]])
    m = result['mapping']
    with (args.output_dir / 'mapping_sensitivity.csv').open('w', newline='') as stream:
        mapping_writer = csv.writer(stream)
        mapping_writer.writerow(['mapping','missing_class_months','mapped_fund_months','fund_months_with_singletons'])
        mapping_writer.writerow(['latest_summary_asof',m['latest_missing'],m['strict_mapped'],m['latest_singleton']])
        mapping_writer.writerow(['last_nonblank_asof',m['last_nonblank_missing'],m['last_nonblank_strict'],m['last_nonblank_singleton']])
        mapping_writer.writerow(['full_file_LOOKAHEAD',m['full_file_missing'],m['full_file_strict'],m['full_file_singleton']])
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
