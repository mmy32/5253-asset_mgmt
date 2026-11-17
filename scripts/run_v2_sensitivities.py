"""Count coverage for the v2 panel and its three registered sensitivities.

Counts only: no model, ranking or return is computed.
Usage: python scripts/run_v2_sensitivities.py --panels-dir data/interim/panels --output out.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from src.data_processing.protocol_coverage import summarize
from src.data_processing.target_diagnosis import sha256

VARIANTS = {
    'v2': ('v2', ''),
    'v2_add_global': ('v2_global', ''),
    'v2_no_floor': ('v2_nofloor', ''),
    'v2_drop_flagged': ('v2', 'WHERE NOT coalesce(ungrouped_shares_portno, false)'),
}
FEATURES = 'flow IS NOT NULL AND isfinite(flow) AND momentum_12_2 IS NOT NULL AND isfinite(momentum_12_2)'


def count_variant(database: Path, where: str, protocol: dict) -> dict:
    sample = protocol['sample']
    db = duckdb.connect()
    try:
        db.execute(f"ATTACH '{database}' AS src (READ_ONLY)")
        db.execute(f'CREATE VIEW panel AS SELECT * FROM src.main.panel {where}')
        result = summarize(db, protocol)
        common = result['common_window']
        row = db.execute(f"""
          WITH e AS (SELECT * FROM panel WHERE formation_date BETWEEN ? AND ? AND {FEATURES})
          SELECT count(*), count(DISTINCT fund_id),
            count(*) FILTER (WHERE next_month_abnormal_return IS NULL),
            count(*) FILTER (WHERE target_net_return IS NULL),
            count(DISTINCT formation_date) FILTER (WHERE target_net_return IS NULL),
            count(DISTINCT formation_date) FILTER (WHERE next_month_abnormal_return IS NULL)
          FROM e""", [sample['evaluation_formation_start'], sample['evaluation_formation_end']]).fetchone()
        assert row is not None
        months = result['evaluation_monthly_feature_coverage']
    finally:
        db.close()
    return {'funds_common': common['funds'], 'fund_months_common': common['formation_rows'],
            'complete_features_common': common['complete_features'],
            'timely_targets_common': common['timely_targets'],
            'eval_feature_complete_rows': row[0], 'eval_funds': row[1],
            'eval_missing_abnormal': row[2], 'eval_missing_net': row[3],
            'eval_missing_abnormal_share': row[2] / row[0], 'eval_missing_net_share': row[3] / row[0],
            'months_with_missing_net': row[4], 'months_with_missing_abnormal': row[5],
            'eval_months': months['calendar_months'], 'min_eligible': months['min_eligible'],
            'max_eligible': months['max_eligible']}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panels-dir', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    rows = []
    for name, (folder, where) in VARIANTS.items():
        database = args.panels_dir / folder / 'fund_panel.duckdb'
        rows.append({'variant': name, 'panel_sha256': sha256(database),
                     **count_variant(database, where, protocol)})
    table = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)
    print(table.T.to_string())


if __name__ == '__main__':
    main()
