"""Loaders for the CRSP mutual fund pulls D1a (monthly) and D1b (fund summary)."""

from pathlib import Path

import pandas as pd

from src.config import schema


def load_monthly_returns(path: Path) -> pd.DataFrame:
    """D1a: one row per (crsp_fundno, caldt) with mret, mtna, mnav as floats (codes -> NaN).

    A column holding any value that is neither a number, blank nor its documented code raises.
    """
    df = pd.read_csv(
        path,
        usecols=[schema.D1A_ID, schema.D1A_DATE, *schema.D1A_NUMERIC],
        dtype={schema.D1A_ID: str, **{c: "float64" for c in schema.D1A_NUMERIC}},
        na_values={col: [code] for col, code in schema.D1A_MISSING_CODES.items()},
        parse_dates=[schema.D1A_DATE],
        date_format="%Y-%m-%d",
    )
    if df.duplicated([schema.D1A_ID, schema.D1A_DATE]).any():
        raise ValueError("D1a has duplicate (crsp_fundno, caldt) pairs")
    return df[[schema.D1A_ID, schema.D1A_DATE, *schema.D1A_NUMERIC]]


def load_fund_summary(path: Path) -> pd.DataFrame:
    """D1b: quarterly fund attributes, only the columns in schema.D1B_COLUMNS."""
    df = pd.read_csv(
        path,
        dtype=str,
        encoding=schema.D1B_ENCODING,
        usecols=list(schema.D1B_COLUMNS),
    )
    for col in schema.D1B_DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
    for col in schema.D1B_NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df[list(schema.D1B_COLUMNS)]
