import pandas as pd
import pytest

from src.data_loader.sentiment import load_sentiment


def _book(path, rows):
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        pd.DataFrame({"x": [1]}).to_excel(w, sheet_name="README", index=False)
        pd.DataFrame(rows).to_excel(w, sheet_name="DATA", index=False)
    return path


def test_sentiment_indexed_by_month_with_blank_early_rows(tmp_path):
    f = _book(
        tmp_path / "bw.xlsx",
        {"yearmo": [195801, 195802], "SENT": [None, 0.5], "SENT_ORTH": [None, 0.4], "cpi": [1, 2]},
    )
    s = load_sentiment(f)
    assert list(s.columns) == ["SENT", "SENT_ORTH"]
    assert list(s.index) == [pd.Period("1958-01"), pd.Period("1958-02")]
    assert pd.isna(s.iloc[0, 0]) and s.iloc[1, 0] == 0.5


def test_sentiment_missing_column_raises(tmp_path):
    f = _book(tmp_path / "bw.xlsx", {"yearmo": [195801], "SENT": [1.0]})
    with pytest.raises(ValueError, match="lacks columns"):
        load_sentiment(f)
