import pandas as pd
import pytest

from src.data_processing.coverage import common_window, restrict_to_window


def _inputs(sent_values=(None, 0.1, 0.2, 0.3, 0.4)):
    returns = pd.DataFrame({"caldt": pd.to_datetime(["1976-01-30", "2026-09-30"])})
    summary = pd.DataFrame({"caldt": pd.to_datetime(["1999-03-31", "2026-09-30"])})
    factors = pd.DataFrame(index=pd.period_range("1927-01", "2026-09", freq="M"))
    sentiment = pd.DataFrame(
        {"SENT": list(sent_values)}, index=pd.period_range("1998-12", periods=len(sent_values), freq="M")
    )
    return returns, summary, factors, sentiment


def test_window_is_latest_start_and_earliest_end_ignoring_blank_sentiment():
    start, end = common_window(*_inputs())
    assert start == pd.Timestamp("1999-03-31")  # D1b start; sentiment's blank first month ignored
    assert end == pd.Timestamp("1999-04-30")  # sentiment last valid month


def test_no_overlap_raises():
    returns, summary, factors, _ = _inputs()
    sentiment = pd.DataFrame({"SENT": [0.1]}, index=pd.period_range("1990-01", periods=1, freq="M"))
    with pytest.raises(ValueError, match="do not overlap"):
        common_window(returns, summary, factors, sentiment)


def test_restrict_is_inclusive():
    panel = pd.DataFrame({"caldt": pd.to_datetime(["1999-02-26", "1999-03-31", "1999-04-30"])})
    out = restrict_to_window(panel, pd.Timestamp("1999-03-31"), pd.Timestamp("1999-03-31"))
    assert len(out) == 1
