"""Loader for the Ken French Carhart factors (D2)."""

import re
from pathlib import Path

import pandas as pd

from src.config import schema

_MONTHLY_ROW = re.compile(r"^\s*(\d{6})\s*,")


def _read_monthly_section(path: Path, columns: tuple[str, ...]) -> pd.DataFrame:
    """Parse only the rows keyed by YYYYMM; the annual section and notes are skipped."""
    rows = []
    for line in path.read_text(encoding="latin-1").splitlines():
        match = _MONTHLY_ROW.match(line)
        if match:
            values = [float(v) for v in line.split(",")[1:]]
            if len(values) != len(columns):
                raise ValueError(f"{path}: expected {len(columns)} values, got {line!r}")
            rows.append((match.group(1), *values))
    if not rows:
        raise ValueError(f"{path}: no monthly rows found")
    df = pd.DataFrame(rows, columns=["yyyymm", *columns])
    df.index = pd.PeriodIndex(df.pop("yyyymm"), freq="M", name="month")
    return df


def load_carhart_factors(research_path: Path, momentum_path: Path) -> pd.DataFrame:
    """Monthly Mkt-RF, SMB, HML, RF, Mom as decimals, indexed by month; missing codes -> NaN."""
    research = _read_monthly_section(research_path, schema.D2_FACTOR_COLUMNS)
    momentum = _read_monthly_section(momentum_path, (schema.D2_MOMENTUM_COLUMN,))
    factors = research.join(momentum, how="inner")
    if factors.index.duplicated().any():
        raise ValueError("duplicate months in factor files")
    factors = factors.where(~factors.isin(schema.D2_MISSING_VALUES))
    return factors / schema.D2_PERCENT_DIVISOR
