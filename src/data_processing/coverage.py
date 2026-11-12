"""Date window in which every input has data."""

import pandas as pd

from src.config import schema


def _month_end(period: pd.Period) -> pd.Timestamp:
    return period.to_timestamp(how="end").normalize()


def common_window(
    returns: pd.DataFrame,
    summary: pd.DataFrame,
    factors: pd.DataFrame,
    sentiment: pd.DataFrame,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """First and last month-end at which D1a, D1b, D2 and D3 all have data.

    Sentiment counts only months where SENT is present. Raises if the inputs do not overlap.
    """
    sent = sentiment["SENT"].dropna().index
    windows = [
        (returns[schema.D1A_DATE].min(), returns[schema.D1A_DATE].max()),
        (summary[schema.D1B_DATE].min(), summary[schema.D1B_DATE].max()),
        (_month_end(factors.index.min()), _month_end(factors.index.max())),
        (_month_end(sent.min()), _month_end(sent.max())),
    ]
    start = max(w[0] for w in windows)
    end = min(w[1] for w in windows)
    if start > end:
        raise ValueError(f"inputs do not overlap: start {start.date()} is after end {end.date()}")
    return start, end


def restrict_to_window(
    panel: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    """Keep fund-months with start <= caldt <= end."""
    return panel[(panel[schema.D1A_DATE] >= start) & (panel[schema.D1A_DATE] <= end)]
