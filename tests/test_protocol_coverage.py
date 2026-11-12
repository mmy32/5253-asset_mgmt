import csv
import hashlib
import json
import shutil
from pathlib import Path

import duckdb
import pytest

from src.data_processing.protocol_coverage import check_folds, summarize


ROOT = Path(__file__).resolve().parents[1]


def protocol():
    return json.loads((ROOT / "configs/research_protocol_v1.json").read_text())


def test_coverage_uses_label_cutoff_without_return_statistics():
    db = duckdb.connect()
    try:
        db.execute("""
          CREATE TABLE panel (
            fund_id VARCHAR, formation_date DATE, return_month DATE,
            return_assumed_available_at DATE, latest_summary_available_at DATE,
            latest_fee_available_at DATE, expense_ratio DOUBLE, flow DOUBLE, momentum_12_2 DOUBLE,
            next_month_abnormal_return DOUBLE, target_assumed_available_at DATE
          )
        """)
        db.execute("""
          INSERT INTO panel VALUES
          ('a','2002-01-31','2001-12-31','2002-01-31','2002-01-01',NULL,NULL,
              0.1,0.02,12345,'2016-12-31'),
          ('b','2002-02-28','2002-01-31','2002-02-28','2002-02-01',NULL,NULL,
              0.1,0.02,23456,'2017-01-31'),
          ('c','2018-12-31','2018-11-30','2018-12-31','2018-12-01',NULL,NULL,
              0.1,0.02,34567,'2019-02-28'),
          ('d','2019-02-28','2019-01-31','2019-02-28','2019-02-01',NULL,NULL,
              0.1,0.02,NULL,NULL),
          ('e','2019-03-31','2019-02-28','2019-03-31','2019-03-01',NULL,NULL,
              NULL,0.02,45678,'2019-05-31')
        """)
        result = summarize(db, protocol())
        training = result["initial_training"]
        assert training["formation_rows"] == 2
        assert training["complete_features"] == 2
        assert training["nonmissing_targets"] == 2
        assert training["timely_targets"] == 1
        assert training["ex_post_complete_cases"] == 1
        assert result["initial_validation"]["timely_targets"] == 1  # Inclusive cutoff.
        assert result["evaluation"]["formation_rows"] == 2  # Missing target remains.
        assert result["evaluation"]["ex_post_complete_cases"] == 0
        assert result["evaluation_monthly_feature_coverage"]["calendar_months"] == 81
        assert not any(result["timing_violations"].values())
        assert not any(str(value) in json.dumps(result) for value in (12345, 23456, 34567, 45678))
        db.execute("UPDATE panel SET return_assumed_available_at='2002-03-31', "
                   "expense_ratio=0.01 WHERE fund_id='b'")
        timing = summarize(db, protocol())["timing_violations"]
        assert timing["monthly_return"] == 1
        assert timing["fee"] == 1  # Used expense without an availability date.
    finally:
        db.close()


def test_folds_are_registered_and_tampering_fails(tmp_path):
    spec = protocol()
    folds = check_folds(spec, ROOT)
    assert folds["month_count"] == 286
    assert folds["fold_months"] == {"0": 96, "1": 95, "2": 95}
    assert folds["evaluation_months"] == {"0": 25, "1": 26, "2": 30}
    source = ROOT / spec["experiments"]["A"]["fold_file"]
    with source.open(newline="") as stream:
        actual = {row["formation_month"]: int(row["fold"]) for row in csv.DictReader(stream)}
    ranked = sorted(actual, key=lambda month: (hashlib.sha256(f"5253|{month}".encode()).hexdigest(), month))
    expected = {month: (0 if i < 96 else 1 if i < 191 else 2) for i, month in enumerate(ranked)}
    assert actual == expected
    path = tmp_path / spec["experiments"]["A"]["fold_file"]
    path.parent.mkdir(parents=True)
    shutil.copy(ROOT / spec["experiments"]["A"]["fold_file"], path)
    with path.open("a") as stream:
        stream.write("2026-01,0\n")
    with pytest.raises(ValueError, match="hash"):
        check_folds(spec, tmp_path)
