"""Loader for the Baker-Wurgler sentiment index (D3)."""

from pathlib import Path

import pandas as pd

from src.config import schema


def load_sentiment(path: Path) -> pd.DataFrame:
    """Monthly SENT and SENT_ORTH indexed by month. Early rows are blank (NaN)."""
    df = pd.read_excel(path, sheet_name=schema.D3_SHEET, engine="openpyxl")
    missing = {schema.D3_DATE, *schema.D3_SENTIMENT_COLUMNS} - set(df.columns)
    if missing:
        raise ValueError(f"{path} lacks columns {sorted(missing)}")
    df.index = pd.PeriodIndex(df[schema.D3_DATE].astype(str), freq="M", name="month")
    if df.index.duplicated().any():
        raise ValueError("duplicate months in sentiment file")
    return df[list(schema.D3_SENTIMENT_COLUMNS)].astype("float64")
