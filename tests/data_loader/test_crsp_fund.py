import pandas as pd
import pytest

from src.data_loader.crsp_fund import load_fund_summary, load_monthly_returns


def _write(path, text):
    path.write_text(text, encoding="latin-1")
    return path


def test_monthly_codes_become_nan_and_ids_keep_leading_zeros(tmp_path):
    f = _write(
        tmp_path / "d1a.csv",
        "caldt,crsp_fundno,mtna,mret,mnav\n"
        "1976-01-30,000123,10.5,0.01,5.0\n"
        "1976-02-27,000123,T,R,N\n"
        "1976-03-31,000123,,,\n",
    )
    df = load_monthly_returns(f)
    assert df["crsp_fundno"].tolist() == ["000123"] * 3
    assert df[["mtna", "mret", "mnav"]].iloc[1:].isna().all().all()
    assert df.loc[0, "mret"] == 0.01
    assert pd.api.types.is_datetime64_any_dtype(df["caldt"])


def test_monthly_unknown_text_raises(tmp_path):
    f = _write(tmp_path / "d1a.csv", "caldt,crsp_fundno,mtna,mret,mnav\n1976-01-30,1,1,oops,1\n")
    with pytest.raises(ValueError):
        load_monthly_returns(f)


def test_monthly_duplicates_raise(tmp_path):
    row = "1976-01-30,1,1,0.1,1\n"
    f = _write(tmp_path / "d1a.csv", "caldt,crsp_fundno,mtna,mret,mnav\n" + row + row)
    with pytest.raises(ValueError, match="duplicate"):
        load_monthly_returns(f)


def test_fund_summary_selects_columns_and_parses_types(tmp_path):
    header = (
        "crsp_fundno,crsp_cl_grp,crsp_obj_cd,fund_name,mgmt_cd,mgmt_name,dead_flag,"
        "summary_period2,caldt,first_offer_dt,end_dt,exp_ratio,turn_ratio,junk\n"
    )
    f = _write(
        tmp_path / "d1b.csv",
        header + "000123,7,EDCL,Caf\xe9 Fund,AB,Alpha,N,Q,1999-03-31,1990-01-01,,0.01,0.5,x\n",
    )
    df = load_fund_summary(f)
    assert "junk" not in df.columns
    assert df.loc[0, "crsp_fundno"] == "000123"
    assert df.loc[0, "fund_name"] == "Caf\xe9 Fund"
    assert pd.isna(df.loc[0, "end_dt"])
    assert df.loc[0, "exp_ratio"] == 0.01
