"""Run the registered v2 top-minus-bottom spread: coverage rule, bounds and bootstrap.

Settings come from `missing_outcome_estimand` and v1 `inference` in the protocol files.
Both targets are reported separately and never combined.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from src.data_processing.target_diagnosis import sha256
from src.models.baseline import run
from src.models.block_bootstrap import moving_block_bootstrap
from src.models.missing_outcomes import month_estimate, validate_settings
from src.models.overlap_report import COLUMNS, TARGETS, check_mechanics


def monthly_table(constituents: pd.DataFrame, threshold: float, low: float, high: float) -> pd.DataFrame:
    records = []
    for (model, month), rows in constituents.groupby(['model', 'formation_date']):
        for label, column in TARGETS.items():
            records.append({'model': model, 'target': label, 'formation_date': month,
                            **month_estimate(rows, column, threshold, low, high)})
    return pd.DataFrame(records)


def summarize(table: pd.DataFrame, inference: dict) -> pd.DataFrame:
    records = []
    for (model, target), group in table.groupby(['model', 'target']):
        group = group.sort_values('formation_date')
        passing = group[group.both_pass]
        record = {'model': model, 'target': target, 'months': len(group),
                  'months_passing': len(passing),
                  'mean_spread': passing.spread.mean(),
                  'mean_bound_lower_all_months': group.bound_lower.mean(),
                  'mean_bound_upper_all_months': group.bound_upper.mean(),
                  'months_bounds_above_zero': int((group.bound_lower > 0).sum()),
                  'months_bounds_below_zero': int((group.bound_upper < 0).sum()),
                  'months_bounds_include_zero': int(((group.bound_lower <= 0) & (group.bound_upper >= 0)).sum())}
        result = moving_block_bootstrap(
            passing.spread.to_numpy(float), pd.DatetimeIndex(passing.formation_date),
            draws=inference['draws'], seed=inference['seed'])
        record.update({'ci_low': result.ci_low, 'ci_high': result.ci_high, 'p_value_one_sided': result.p_value,
                       'bootstrap_blocks': result.blocks} if result else {'ci_low': None})
        records.append(record)
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--base-protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v2.json'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(args.base_protocol.read_text())
    protocol = json.loads(args.protocol.read_text())
    estimand = protocol['missing_outcome_estimand']
    low, high = estimand['bounds_percentiles']
    validate_settings(estimand['coverage_threshold'], low, high)
    if sha256(args.database) != protocol['provenance']['v2']['db_sha256']:
        raise ValueError('Panel hash differs from registered data')
    frozen = protocol['freeze']['code_sha256']
    for name, expected in frozen.items():
        if sha256(Path(name)) != expected:
            raise ValueError(f'Code changed since the freeze: {name}')
    if args.output_dir.exists():
        raise FileExistsError('Choose a new output directory')
    with duckdb.connect(str(args.database), read_only=True) as db:
        frame = db.execute(f"SELECT {', '.join(COLUMNS)} FROM panel").df()
    constituents, _, audit = run(frame, base)
    check_mechanics(constituents, audit)
    table = monthly_table(constituents, estimand['coverage_threshold'], low, high)
    summary = summarize(table, base['inference'])
    args.output_dir.mkdir(parents=True)
    table.to_csv(args.output_dir / 'spread_by_month.csv', index=False)
    summary.to_csv(args.output_dir / 'spread_summary.csv', index=False)
    print(summary.T.to_string())


if __name__ == '__main__':
    main()
