import pandas as pd

from src.data_processing.sample_screen import (
    attach_objective_and_name,
    drop_extreme_returns,
    screen_active_us_equity,
)


def _returns():
    return pd.DataFrame(
        {
            "crsp_fundno": ["1", "1", "1", "2"],
            "caldt": pd.to_datetime(["1999-02-26", "1999-03-31", "1999-07-30", "1999-07-30"]),
            "mret": [0.01, 0.02, 0.03, 0.04],
        }
    )


def _summary():
    return pd.DataFrame(
        {
            "crsp_fundno": ["1", "1"],
            "caldt": pd.to_datetime(["1999-03-31", "1999-06-30"]),
            "crsp_obj_cd": ["EDCL", "EDYH"],
            "fund_name": ["Alpha Fund", "Alpha Fund"],
        }
    )


def test_attributes_use_latest_quarter_on_or_before_month_only():
    out = attach_objective_and_name(_returns(), _summary()).set_index(["crsp_fundno", "caldt"])
    assert pd.isna(out.loc[("1", pd.Timestamp("1999-02-26")), "crsp_obj_cd"])  # before first row
    assert out.loc[("1", pd.Timestamp("1999-03-31")), "crsp_obj_cd"] == "EDCL"  # exact match
    assert out.loc[("1", pd.Timestamp("1999-07-30")), "crsp_obj_cd"] == "EDYH"  # latest quarter
    assert pd.isna(out.loc[("2", pd.Timestamp("1999-07-30")), "crsp_obj_cd"])  # unknown fund


def test_screen_by_code_and_name():
    panel = pd.DataFrame(
        {
            "crsp_obj_cd": ["EDCL", "EDCL", "EDST", None],
            "fund_name": ["Growth Fund", "S&P 500 Index Fund", "Tech Fund", "Growth Fund"],
        }
    )
    out = screen_active_us_equity(panel, {"EDCL"}, r"index")
    assert out["fund_name"].tolist() == ["Growth Fund"]


def test_drop_extreme_returns_keeps_boundary_and_missing():
    panel = pd.DataFrame({"mret": [1.0, 1.01, float("nan"), -0.5]})
    out = drop_extreme_returns(panel, 1.0)
    assert out.index.tolist() == [0, 2, 3]
