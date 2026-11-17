"""Calendar-aware inference for the mean over all passing months."""
from __future__ import annotations

from dataclasses import dataclass
from math import erfc, sqrt
from statistics import NormalDist

import numpy as np
import pandas as pd

from src.models.block_bootstrap import contiguous_runs


@dataclass(frozen=True)
class CalendarInference:
    ci_low: float
    ci_high: float
    p_value: float


def calendar_inference(
    values: np.ndarray, months: pd.DatetimeIndex, length: int = 12, confidence: float = 0.95,
) -> CalendarInference | None:
    """Gaussian multiplier inference with Bartlett dependence in calendar time.

    Each passing month's centered contribution receives a unit-variance multiplier.
    Multipliers at lag k have correlation max(1 - k/length, 0). With Gaussian
    multipliers the conditional distribution is normal, so no simulation is needed.
    """
    if len(values) != len(months) or not np.isfinite(values).all() or months.hasnans:
        raise ValueError('Finite spreads must align with valid months')
    if length < 1 or not 0 < confidence < 1:
        raise ValueError('Require a positive dependence length and confidence in (0, 1)')
    if not any(len(run) >= length for run in contiguous_runs(months)):
        return None
    mean = float(np.mean(values))
    periods = months.to_period('M').astype('int64').to_numpy()
    offsets = periods - periods[0]
    # Gaps contribute no residual to the mean; they still separate calendar lags.
    residuals = np.zeros(offsets[-1] + 1)
    residuals[offsets] = values - mean
    sums = np.convolve(residuals, np.ones(length), mode='full')
    se = float(np.linalg.norm(sums)) / (sqrt(length) * len(values))
    if se == 0 or np.all(values == values[0]):
        return None
    margin = NormalDist().inv_cdf((1 + confidence) / 2) * se
    return CalendarInference(mean - margin, mean + margin, erfc(mean / (sqrt(2) * se)) / 2)
