"""Missing-outcome rules from protocol v2: coverage threshold and best/worst-case bounds.

Weights are never set to zero or silently reassigned. Coverage functions read only
whether an outcome exists, never its value.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TOLERANCE = 1e-12


def validate_settings(threshold: float, low_pct: float, high_pct: float) -> None:
    if not 0 < threshold <= 1:
        raise ValueError('threshold must be in (0, 1]')
    if not 0 <= low_pct < high_pct <= 100:
        raise ValueError('percentiles must satisfy 0 <= low < high <= 100')


def observed_share(weights: np.ndarray, outcomes: np.ndarray) -> float:
    """Share of a leg's weight whose outcome exists."""
    total = float(np.sum(weights))
    if total <= 0:
        raise ValueError('Leg weights must sum to a positive number')
    return float(np.sum(weights[np.isfinite(outcomes)]) / total)


def passes(share: float, threshold: float) -> bool:
    return share >= threshold - TOLERANCE


def rescaled_return(weights: np.ndarray, outcomes: np.ndarray) -> float:
    """Weighted mean over observed funds only; weights rescaled to sum to one."""
    seen = np.isfinite(outcomes)
    if not seen.any():
        return float('nan')
    return float(np.sum(weights[seen] * outcomes[seen]) / np.sum(weights[seen]))


def leg_bounds(weights: np.ndarray, outcomes: np.ndarray, low: float, high: float) -> tuple[float, float]:
    """Leg return if every missing weight earned `low`, and if it earned `high`."""
    seen = np.isfinite(outcomes)
    total = float(np.sum(weights))
    known = float(np.sum(weights[seen] * outcomes[seen]))
    missing = float(np.sum(weights[~seen]))
    return (known + missing * low) / total, (known + missing * high) / total


def month_coverage(top: pd.DataFrame, bottom: pd.DataFrame, target: str, threshold: float) -> dict:
    """Coverage only: no outcome value is used."""
    top_share = observed_share(top.weight.to_numpy(float), top[target].to_numpy(float))
    bottom_share = observed_share(bottom.weight.to_numpy(float), bottom[target].to_numpy(float))
    return {'top_observed': top_share, 'bottom_observed': bottom_share,
            'both_pass': passes(top_share, threshold) and passes(bottom_share, threshold)}


def month_estimate(rows: pd.DataFrame, target: str, threshold: float,
                   low_pct: float, high_pct: float) -> dict:
    """Spread (top decile minus bottom decile) by threshold rule and by bounds.

    `rows` holds one month and one model with columns decile, weight and `target`.
    The low and high fill values are percentiles of that month's observed outcomes
    across all funds, so no later information is used.
    """
    validate_settings(threshold, low_pct, high_pct)
    pool = rows[target].to_numpy(float)
    pool = pool[np.isfinite(pool)]
    if pool.size == 0:
        raise ValueError('No observed outcomes in the month')
    low, high = np.percentile(pool, [low_pct, high_pct])
    top, bottom = rows[rows.decile == rows.decile.max()], rows[rows.decile == rows.decile.min()]
    coverage = month_coverage(top, bottom, target, threshold)
    tw, to = top.weight.to_numpy(float), top[target].to_numpy(float)
    bw, bo = bottom.weight.to_numpy(float), bottom[target].to_numpy(float)
    top_lo, top_hi = leg_bounds(tw, to, low, high)
    bottom_lo, bottom_hi = leg_bounds(bw, bo, low, high)
    spread = rescaled_return(tw, to) - rescaled_return(bw, bo) if coverage['both_pass'] else float('nan')
    return {**coverage, 'spread': spread, 'bound_lower': top_lo - bottom_hi,
            'bound_upper': top_hi - bottom_lo, 'fill_low': float(low), 'fill_high': float(high)}
