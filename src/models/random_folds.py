"""Setup A's random three-fold month assignment (registered in protocol v1)."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

import pandas as pd


def load_folds(path: Path, expected_sha256: str) -> dict[str, int]:
    """Map 'YYYY-MM' to fold 0, 1 or 2; refuses a file that differs from the registered one."""
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('Fold file differs from the registered protocol')
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    folds = {row['formation_month']: int(row['fold']) for row in rows}
    if len(folds) != len(rows) or not set(folds.values()) <= {0, 1, 2}:
        raise ValueError('Duplicate month or invalid fold')
    return folds


def validate_rotations(rotations: list[dict[str, Any]]) -> None:
    """Each rotation must use three distinct folds, and every fold must be tested once."""
    if any(sorted((r['test'], r['train'], r['validation'])) != [0, 1, 2] for r in rotations):
        raise ValueError('A rotation must use three distinct folds')
    if sorted(r['test'] for r in rotations) != [0, 1, 2]:
        raise ValueError('Every fold must be tested exactly once')


def fold_of(frame: pd.DataFrame, folds: dict[str, int]) -> pd.Series:
    """Fold per row; months outside the registered fold file get -1."""
    months = frame.formation_date.dt.strftime('%Y-%m')
    return months.map(folds).fillna(-1).astype(int)
