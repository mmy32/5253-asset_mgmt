"""Count months where both the top and bottom decile pass the coverage rule.

Runs the registered chronological forecasts and reports only whether outcomes exist.
No return, spread or bound is computed or written.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.data_processing.target_diagnosis import sha256
from src.models.baseline import FEATURES, TARGET, run
from src.models.missing_outcomes import month_coverage, validate_settings

TARGETS = {'abnormal': TARGET, 'net_proxy': 'target_net_return'}
COLUMNS = ['fund_id', 'formation_date', *FEATURES, TARGET, 'target_net_return',
           'target_assumed_available_at']


def coverage_table(constituents: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """One row per model, target and formation month; reads only whether outcomes exist."""
    records = []
    for (model, month), rows in constituents.groupby(['model', 'formation_date']):
        top, bottom = rows[rows.decile == rows.decile.max()], rows[rows.decile == rows.decile.min()]
        for label, column in TARGETS.items():
            records.append({'model': model, 'formation_date': month, 'target': label,
                            **month_coverage(top, bottom, column, threshold)})
    return pd.DataFrame(records)


def check_mechanics(constituents: pd.DataFrame, audit: pd.DataFrame) -> None:
    """Fail fast on broken weights or a training label dated after its decision."""
    sums = constituents.groupby(['model', 'formation_date', 'decile']).weight.sum()
    if not np.allclose(sums, 1.0):
        raise ValueError('Decile weights do not sum to one')
    if constituents.groupby(['model', 'formation_date']).decile.nunique().ne(10).any():
        raise ValueError('A month does not have ten deciles')
    labelled = audit.dropna(subset=['latest_training_label_available'])
    if (labelled.latest_training_label_available > labelled.formation_date).any():
        raise ValueError('A training label became available after its decision date')


def summarize(table: pd.DataFrame) -> pd.DataFrame:
    grouped = table.groupby(['model', 'target'])
    return grouped.agg(months=('both_pass', 'size'), both_pass=('both_pass', 'sum'),
                       mean_top_observed=('top_observed', 'mean'),
                       mean_bottom_observed=('bottom_observed', 'mean')).reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--base-protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v2.json'))
    parser.add_argument('--panel-version', default='v2')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(args.base_protocol.read_text())
    protocol = json.loads(args.protocol.read_text())
    estimand = protocol['missing_outcome_estimand']
    low, high = estimand['bounds_percentiles']
    validate_settings(estimand['coverage_threshold'], low, high)
    registered = protocol['provenance'][args.panel_version]['db_sha256']
    if sha256(args.database) != registered:
        raise ValueError('Panel hash differs from registered data')
    if args.output_dir.exists():
        raise FileExistsError('Choose a new output directory')
    with duckdb.connect(str(args.database), read_only=True) as db:
        frame = db.execute(f"SELECT {', '.join(COLUMNS)} FROM panel").df()
    constituents, _, audit = run(frame, base)
    check_mechanics(constituents, audit)
    table = coverage_table(constituents, estimand['coverage_threshold'])
    summary = summarize(table)
    args.output_dir.mkdir(parents=True)
    table.to_csv(args.output_dir / 'coverage_by_month.csv', index=False)
    summary.to_csv(args.output_dir / 'coverage_summary.csv', index=False)
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
