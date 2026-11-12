"""Sample screens for the fund-month panel: objective code, fund name and extreme returns."""

import logging
from collections.abc import Collection

import pandas as pd

from src.config import schema

logger = logging.getLogger(__name__)

_ATTRIBUTES = [schema.D1B_ID, schema.D1B_DATE, "crsp_obj_cd", "fund_name"]


def attach_objective_and_name(returns: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """Add crsp_obj_cd and fund_name to each fund-month from the latest quarterly row on or
    before the month (never a later quarter). Months before a fund's first quarterly row get NaN.
    """
    attrs = summary[_ATTRIBUTES].dropna(subset=[schema.D1B_DATE]).sort_values(schema.D1B_DATE)
    attrs = attrs.rename(columns={schema.D1B_DATE: "attr_date"})
    left = returns.sort_values(schema.D1A_DATE)
    merged = pd.merge_asof(
        left,
        attrs,
        left_on=schema.D1A_DATE,
        right_on="attr_date",
        by=schema.D1A_ID,
        direction="backward",
    )
    return merged.drop(columns="attr_date").sort_values([schema.D1A_ID, schema.D1A_DATE])


def screen_active_us_equity(
    panel: pd.DataFrame, obj_codes: Collection[str], excluded_name_pattern: str
) -> pd.DataFrame:
    """Keep rows whose objective code is in obj_codes and whose name avoids the pattern."""
    keep_code = panel["crsp_obj_cd"].isin(obj_codes)
    excluded_name = panel["fund_name"].str.contains(excluded_name_pattern, case=False, na=False)
    out = panel[keep_code & ~excluded_name]
    logger.info(
        "screen: %d rows -> %d (%d by code, %d more by name)",
        len(panel),
        len(out),
        len(panel) - keep_code.sum(),
        (keep_code & excluded_name).sum(),
    )
    return out


def drop_extreme_returns(panel: pd.DataFrame, max_return: float) -> pd.DataFrame:
    """Remove fund-months with a raw return above max_return; log how many."""
    extreme = panel[schema.D1A_NUMERIC[0]] > max_return
    logger.info("dropped %d fund-months with mret > %s", extreme.sum(), max_return)
    return panel[~extreme]
