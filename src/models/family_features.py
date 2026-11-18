"""Family inputs over whichever sibling funds have a value (no all-siblings rule).

Built from the v2 panel at model time, so the frozen panel is unchanged. Siblings are
other funds with the same family_id in the same formation month. Funds below the panel's
size floor are not in the panel, so they do not count as siblings.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FAMILY_INPUTS = ('family_tna_any', 'family_flow_any', 'family_momentum_any')


def _sibling_sum(frame: pd.DataFrame, values: pd.Series) -> pd.Series:
    """Sum over the family-month excluding the fund itself; missing values count as zero."""
    filled = values.fillna(0.0)
    keys = [frame.formation_date, frame.family_id]
    return filled.groupby(keys).transform('sum') - filled


def _sibling_weighted_mean(frame: pd.DataFrame, column: str) -> pd.Series:
    """TNA-weighted mean of `column` over siblings that have both the value and TNA > 0."""
    usable = np.isfinite(frame[column]) & (frame.tna > 0)
    weight = frame.tna.where(usable)
    total = _sibling_sum(frame, weight)
    weighted = _sibling_sum(frame, (frame[column] * frame.tna).where(usable))
    return (weighted / total).where(total > 0)


def add_family_inputs(frame: pd.DataFrame) -> pd.DataFrame:
    """Add family size, flow and momentum; NaN when the fund has no usable sibling or family."""
    required = {'formation_date', 'family_id', 'tna', 'flow', 'momentum_12_2'}
    if not required <= set(frame.columns):
        raise ValueError(f'Missing columns: {sorted(required - set(frame.columns))}')
    result = frame.copy()
    has_family = result.family_id.notna()
    family = result.loc[has_family]
    tna = family.tna.where(family.tna > 0)
    result['family_tna_any'] = _sibling_sum(family, tna).reindex(result.index)
    result['family_flow_any'] = _sibling_weighted_mean(family, 'flow').reindex(result.index)
    result['family_momentum_any'] = _sibling_weighted_mean(family, 'momentum_12_2').reindex(result.index)
    return result
