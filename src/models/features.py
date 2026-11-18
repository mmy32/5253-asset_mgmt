"""Model inputs: complete cases only, ranked within each month. No imputation."""
from __future__ import annotations

import numpy as np
import pandas as pd


def complete_cases(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise ValueError(f'Missing input columns: {missing}')
    values = frame[columns].to_numpy(float)
    return frame.loc[np.isfinite(values).all(axis=1)].copy()


def rank_normalize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Replace each input with its within-month rank scaled to [-1, 1].

    Uses only same-month cross-section, so nothing is fitted on other months.
    Ties get the average rank.
    """
    result = frame.copy()
    for column in columns:
        ranks = result.groupby('formation_date')[column].rank(method='average')
        counts = result.groupby('formation_date')[column].transform('size')
        result[column] = 2 * (ranks - 0.5) / counts - 1
    return result


def prepare_inputs(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return rank_normalize(complete_cases(frame, columns), columns)
