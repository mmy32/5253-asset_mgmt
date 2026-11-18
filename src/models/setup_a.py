"""Setup A: network and ridge under random three-fold evaluation (the paper's design).

One fold trains, one validates, one tests, then the roles rotate. Training may use
months after the test month, so results are a retrospective diagnostic, not a
real-time forecast. A model trained on a target is evaluated on that target only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from src.data_processing.target_diagnosis import sha256
from src.models.baseline import TARGET, portfolios
from src.models.family_features import add_family_inputs
from src.models.features import prepare_inputs
from src.models.linear_model import predict_ridge, tune_ridge
from src.models.missing_outcomes import validate_settings
from src.models.neural_net import NetConfig, TrainingSettings, build_grid, fit, predict_ensemble
from src.models.random_folds import fold_of, load_folds, validate_rotations
from src.models.spread_report import monthly_table, summarize

NET_TARGET = 'target_net_return'
EVALUATED_AS = {'abnormal': 'abnormal', 'net_proxy': 'net'}


def tune_network(x, y, x_val, y_val, grid: list[NetConfig], settings: TrainingSettings,
                 seed: int) -> tuple[NetConfig, list[dict[str, Any]]]:
    """One fit per setting; the lowest validation loss wins, ties go to the earlier setting."""
    log: list[dict[str, Any]] = []
    best: tuple[float, NetConfig] | None = None
    for config in grid:
        try:
            loss = fit(x, y, x_val, y_val, config, settings, seed).validation_loss
        except ValueError:  # a diverged fit (for example learning rate 0.1) is skipped
            loss = float('nan')
        log.append({'setting': repr(config), 'validation_loss': loss})
        if np.isfinite(loss) and (best is None or loss < best[0]):
            best = (loss, config)
    if best is None:
        raise ValueError('No network setting trained')
    return best[1], log


def score_test(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, column: str,
               spec: dict[str, Any], settings: TrainingSettings,
               grid: list[NetConfig]) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    inputs = spec['inputs']
    x, y = train[inputs].to_numpy(float), train[column].to_numpy(float)
    xv, yv = val[inputs].to_numpy(float), val[column].to_numpy(float)
    xt = test[inputs].to_numpy(float)
    seed = spec['training']['seed']
    config, log = tune_network(x, y, xv, yv, grid, settings, seed)
    models = [fit(x, y, xv, yv, config, settings, seed + k)
              for k in range(spec['training']['ensemble_size'])]
    ridge, alpha = tune_ridge(x, y, xv, yv, spec['ridge_alpha_grid'])
    log = [{'model': 'nn', **row, 'chosen': row['setting'] == repr(config)} for row in log]
    log.append({'model': 'ridge', 'setting': f'alpha={alpha}',
                'validation_loss': ridge.validation_loss, 'chosen': True})
    return {'nn': predict_ensemble(models, xt), 'ridge': predict_ridge(ridge, xt)}, log


def run_setup_a(frame: pd.DataFrame, folds: dict[str, int], rotations: list[dict[str, Any]],
                spec: dict[str, Any], sample: dict[str, Any], label_cutoff: str,
                grid: list[NetConfig] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return constituents (with deciles and weights) and the tuning log."""
    validate_rotations(rotations)
    settings = TrainingSettings(**{k: spec['training'][k] for k in ('batch_size', 'max_epochs', 'patience')})
    grid = build_grid(spec['grid']) if grid is None else grid
    targets = {'abnormal': TARGET, 'net': NET_TARGET}
    data = prepare_inputs(frame, spec['inputs'])
    data = data.assign(fold=fold_of(data, folds))
    data = data.loc[data.fold >= 0]
    in_window = ((data.formation_date >= sample['evaluation_formation_start'])
                 & (data.formation_date <= sample['evaluation_formation_end']))
    constituents, tuning = [], []
    for rotation in rotations:
        test = data.loc[(data.fold == rotation['test']) & in_window]
        for key, column in targets.items():
            labelled = data.loc[np.isfinite(data[column]) & (data.target_assumed_available_at <= pd.Timestamp(label_cutoff))]
            scores, log = score_test(labelled.loc[labelled.fold == rotation['train']],
                                     labelled.loc[labelled.fold == rotation['validation']],
                                     test, column, spec, settings, grid)
            tuning += [{'test_fold': rotation['test'], 'target': key, **row} for row in log]
            for name, score in scores.items():
                scored = test.assign(score=score)
                for month, rows in scored.groupby('formation_date'):
                    if len(rows) >= sample['minimum_funds_per_month']:
                        members, _ = portfolios(rows)
                        constituents.append(members.assign(model=f'{name}_A_{key}'))
    return pd.concat(constituents, ignore_index=True), pd.DataFrame(tuning)


def matching_pairs(table: pd.DataFrame) -> pd.DataFrame:
    """Keep each model only on the target it was trained for."""
    trained = table.model.str.rsplit('_', n=1).str[-1]
    return table.loc[trained == table.target.map(EVALUATED_AS)]


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('configs/neural_net_v2.json'))
    parser.add_argument('--base-protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v2.json'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.config.read_text())
    base = json.loads(args.base_protocol.read_text())
    protocol = json.loads(args.protocol.read_text())
    estimand = protocol['missing_outcome_estimand']
    low, high = estimand['bounds_percentiles']
    validate_settings(estimand['coverage_threshold'], low, high)
    if sha256(args.database) != protocol['provenance']['v2']['db_sha256']:
        raise ValueError('Panel hash differs from registered data')
    if args.output_dir.exists():
        raise FileExistsError('Choose a new output directory')
    experiment = base['experiments']['A']
    folds = load_folds(Path(experiment['fold_file']), experiment['fold_file_sha256'])
    with duckdb.connect(str(args.database), read_only=True) as db:
        frame = db.execute(f"SELECT {', '.join(spec['panel_columns'])} FROM panel").df()
    frame = add_family_inputs(frame)
    constituents, tuning = run_setup_a(frame, folds, experiment['rotations'], spec, base['sample'],
                                       experiment['label_cutoff'])
    table = matching_pairs(monthly_table(constituents, estimand['coverage_threshold'], low, high))
    summary = summarize(table, base['inference'])
    args.output_dir.mkdir(parents=True)
    constituents.to_csv(args.output_dir / 'constituents.csv', index=False)
    tuning.to_csv(args.output_dir / 'tuning_log.csv', index=False)
    table.to_csv(args.output_dir / 'spread_by_month.csv', index=False)
    summary.to_csv(args.output_dir / 'spread_summary.csv', index=False)
    code = [Path(__file__).parent / n for n in ('setup_a.py', 'neural_net.py', 'linear_model.py',
                                                'features.py', 'random_folds.py',
                                                'family_features.py')]
    manifest = {'panel_sha256': sha256(args.database), 'inputs': spec['inputs'],
                'hashes': file_hashes([args.config, Path(experiment['fold_file']), *code])}
    (args.output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(summary.T.to_string())


if __name__ == '__main__':
    main()
