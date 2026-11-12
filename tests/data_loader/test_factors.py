import pandas as pd
import pytest

from src.data_loader.factors import load_carhart_factors

RESEARCH = """notes line

,Mkt-RF,SMB,HML,RF
192607,   2.89,  -2.42,  -2.75,   0.22
192608,   2.64,  -1.44,   4.13,   0.25

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RF
  1927,  29.47,  -2.46,  -3.76,   3.12
"""
MOMENTUM = """notes

,Mom
192607,   1.00
192608, -99.99

 Annual Factors:
  1927,  5.0
"""


def test_monthly_section_only_decimals_and_missing_code(tmp_path):
    r, m = tmp_path / "r.csv", tmp_path / "m.csv"
    r.write_text(RESEARCH)
    m.write_text(MOMENTUM)
    f = load_carhart_factors(r, m)
    assert list(f.index) == [pd.Period("1926-07"), pd.Period("1926-08")]
    assert f.loc[pd.Period("1926-07"), "Mkt-RF"] == pytest.approx(0.0289)
    assert f.loc[pd.Period("1926-07"), "Mom"] == pytest.approx(0.01)
    assert pd.isna(f.loc[pd.Period("1926-08"), "Mom"])


def test_file_without_monthly_rows_raises(tmp_path):
    r = tmp_path / "r.csv"
    r.write_text("nothing here\n")
    with pytest.raises(ValueError, match="no monthly rows"):
        load_carhart_factors(r, r)
