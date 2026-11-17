"""Moving-block bootstrap for a monthly series with gaps (protocol v1 inference rules).

Blocks are overlapping runs of consecutive months and never cross a gap.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BootstrapResult:
    mean: float
    ci_low: float
    ci_high: float
    p_value: float
    draws: int
    blocks: int


def contiguous_runs(months: pd.DatetimeIndex) -> list[np.ndarray]:
    """Positions of consecutive calendar months; `months` must be sorted and unique."""
    periods = months.to_period('M').astype('int64').to_numpy()
    if len(periods) > 1 and (np.diff(periods) <= 0).any():
        raise ValueError('Months must be sorted and unique')
    breaks = np.flatnonzero(np.diff(periods) != 1) + 1
    return np.split(np.arange(len(periods)), breaks) if len(periods) else []


def block_means(values: np.ndarray, months: pd.DatetimeIndex, length: int) -> np.ndarray:
    means = []
    for run in contiguous_runs(months):
        for start in range(len(run) - length + 1):
            means.append(values[run[start:start + length]].mean())
    return np.asarray(means)


def moving_block_bootstrap(values: np.ndarray, months: pd.DatetimeIndex, length: int = 12,
                           draws: int = 10000, seed: int = 5253,
                           confidence: float = 0.95) -> BootstrapResult | None:
    """Percentile interval and one-sided null-centred p-value (null: mean <= 0).

    Returns None when no run of `length` contiguous months exists.
    """
    if len(values) != len(months):
        raise ValueError('values and months must align')
    pool = block_means(np.asarray(values, float), months, length)
    if pool.size == 0:
        return None
    observed = float(np.mean(values))
    per_draw = int(np.ceil(len(values) / length))
    rng = np.random.default_rng(seed)
    boot = pool[rng.integers(0, pool.size, size=(draws, per_draw))].mean(axis=1)
    tail = (1 - confidence) / 2
    low, high = np.quantile(boot, [tail, 1 - tail])
    centred = boot - boot.mean()
    p_value = (1 + int(np.sum(centred >= observed))) / (draws + 1)
    return BootstrapResult(observed, float(low), float(high), float(p_value), draws, int(pool.size))
