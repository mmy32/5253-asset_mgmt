"""Registered chronological ridge baseline; outcomes never select forecast rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.data_processing.target_diagnosis import sha256

FEATURES = ['flow', 'momentum_12_2']
TARGET = 'next_month_abnormal_return'


def training(frame, decision):
    return frame.loc[(frame.formation_date < decision)
                     & (frame.target_assumed_available_at <= decision)
                     & np.isfinite(frame[TARGET])]


def ridge_system(train):
    x = train[FEATURES].to_numpy(float)
    y = train[TARGET].to_numpy(float)
    if len(y) < 3:
        raise ValueError('Insufficient training data or constant feature')
    mean, scale = x.mean(axis=0), x.std(axis=0)
    if np.any(scale == 0):
        raise ValueError('Insufficient training data or constant feature')
    z = (x - mean) / scale
    return mean, scale, y.mean(), z.T @ z, z.T @ (y - y.mean())


def ridge_predict(system, test, alpha):
    mean, scale, intercept, gram, cross = system
    beta = np.linalg.solve(gram + alpha * np.eye(len(FEATURES)), cross)
    return intercept + ((test[FEATURES].to_numpy(float) - mean) / scale) @ beta


def predict(train, test, alpha):
    return ridge_predict(ridge_system(train), test, alpha)


def tune(frame, months, decision, grid):
    losses = {a: [] for a in sorted(grid)}
    for month in months:
        valid = frame.loc[(frame.formation_date == month)
                          & (frame.target_assumed_available_at <= decision)
                          & np.isfinite(frame[TARGET])]
        if valid.empty:
            continue
        system = ridge_system(training(frame, month))
        for alpha in losses:
            error = ridge_predict(system, valid, alpha) - valid[TARGET].to_numpy()
            losses[alpha].append(float(np.mean(error ** 2)))
    if not all(losses.values()):
        raise ValueError('No usable validation months')
    scores = {a: float(np.mean(v)) for a, v in losses.items()}
    return min(scores, key=lambda a: (scores[a], a)), scores


def portfolios(rows):
    rows = rows.sort_values(['score', 'fund_id']).copy()
    rows['decile'] = np.floor(10 * np.arange(len(rows)) / len(rows)).astype(int) + 1
    rows['weight'] = 1 / rows.groupby('decile').fund_id.transform('size')
    records = []
    for decile, group in rows.groupby('decile'):
        record = {'decile': decile, 'funds': len(group)}
        for source, label in [(TARGET, 'abnormal'), ('target_net_return', 'net_proxy')]:
            missing = ~np.isfinite(group[source])
            record['missing_weight_' + label] = float(group.loc[missing, 'weight'].sum())
            record[label] = np.nan if missing.any() else float((group[source] * group.weight).sum())
        records.append(record)
    return rows, pd.DataFrame(records)


def run(frame, protocol):
    sample, model = protocol['sample'], protocol['model']
    frame = frame.loc[(frame.formation_date >= sample['model_formation_start'])
                      & np.isfinite(frame[FEATURES]).all(axis=1)].copy()
    predictions, returns, audit = [], [], []
    alpha = None
    months = pd.date_range(sample['evaluation_formation_start'],
                           sample['evaluation_formation_end'], freq='ME')
    for decision in months:
        if alpha is None:
            validation = pd.date_range(sample['initial_validation_formation_start'],
                                       sample['initial_validation_formation_end'], freq='ME')
        elif decision.month == 1:
            # A month-t label matures at t+2; select 24 fully matured calendar months.
            end = decision - pd.offsets.MonthEnd(2)
            validation = pd.date_range(end=end, periods=24, freq='ME')
        else:
            validation = None
        scores = {}
        if validation is not None:
            alpha, scores = tune(frame, validation, decision, model['alpha_grid'])
        train = training(frame, decision)
        test = frame.loc[frame.formation_date == decision].copy()
        audit.append({'formation_date': decision, 'train_rows': len(train),
                      'latest_training_label_available': train.target_assumed_available_at.max(),
                      'alpha': alpha, 'validation_scores': json.dumps(scores), 'forecast_rows': len(test)})
        if len(test) < sample['minimum_funds_per_month']:
            continue
        for name, score in [('ridge_C', predict(train, test, alpha)),
                            ('momentum', test.momentum_12_2.to_numpy())]:
            selected = test.assign(score=score)
            constituents, result = portfolios(selected)
            predictions.append(constituents.assign(model=name))
            returns.append(result.assign(model=name, formation_date=decision))
    return pd.concat(predictions, ignore_index=True), pd.concat(returns, ignore_index=True), pd.DataFrame(audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path('data/interim/fund_panel/fund_panel.duckdb'))
    parser.add_argument('--protocol', type=Path, default=Path('configs/research_protocol_v1.json'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    if sha256(args.database) != protocol['provenance']['fund_panel_db_sha256']:
        raise ValueError('Panel hash differs from registered data')
    if args.output_dir.exists():
        raise FileExistsError('Choose a new output directory')
    with duckdb.connect(str(args.database), read_only=True) as db:
        frame = db.execute('SELECT fund_id, formation_date, flow, momentum_12_2, '
                           'next_month_abnormal_return, target_net_return, target_assumed_available_at FROM panel').df()
    forecasts, returns, audit = run(frame, protocol)
    args.output_dir.mkdir(parents=True)
    forecasts.to_csv(args.output_dir / 'constituents.csv', index=False)
    returns.to_csv(args.output_dir / 'portfolio_months.csv', index=False)
    audit.to_csv(args.output_dir / 'training_audit.csv', index=False)
    (args.output_dir / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    (args.output_dir / 'code_sha256.txt').write_text(sha256(Path(__file__)) + '\n')
    print(returns.groupby('model')[['abnormal', 'net_proxy']].count().to_string())


if __name__ == '__main__':
    main()
