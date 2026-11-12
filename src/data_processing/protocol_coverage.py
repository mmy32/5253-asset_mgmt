"""Report protocol date/feature/label coverage without computing outcome statistics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import duckdb


def summarize(db: duckdb.DuckDBPyConnection, protocol: dict[str, Any]) -> dict[str, Any]:
    """Count completeness only; a known future outcome never selects formation rows."""
    sample = protocol["sample"]
    periods = {
        "common_window": (sample["common_start"], sample["common_end"],
                          sample["label_available_by"]),
        "initial_training": (sample["model_formation_start"],
                             sample["initial_training_formation_end"],
                             sample["initial_training_label_available_by"]),
        "initial_validation": (sample["initial_validation_formation_start"],
                               sample["initial_validation_formation_end"],
                               sample["initial_validation_label_available_by"]),
        "evaluation": (sample["evaluation_formation_start"],
                       sample["evaluation_formation_end"], sample["label_available_by"]),
    }
    sql = """
      SELECT count(*) AS formation_rows, count(DISTINCT fund_id) AS funds,
        count(DISTINCT formation_date) AS months,
        count(*) FILTER (WHERE flow IS NOT NULL AND isfinite(flow)
          AND momentum_12_2 IS NOT NULL AND isfinite(momentum_12_2)) AS complete_features,
        count(*) FILTER (WHERE next_month_abnormal_return IS NOT NULL
          AND isfinite(next_month_abnormal_return)) AS nonmissing_targets,
        count(*) FILTER (WHERE next_month_abnormal_return IS NOT NULL
          AND isfinite(next_month_abnormal_return) AND target_assumed_available_at <= ?) AS timely_targets,
        count(*) FILTER (WHERE flow IS NOT NULL AND isfinite(flow)
          AND momentum_12_2 IS NOT NULL AND isfinite(momentum_12_2)
          AND next_month_abnormal_return IS NOT NULL AND isfinite(next_month_abnormal_return)
          AND target_assumed_available_at <= ?) AS ex_post_complete_cases
      FROM panel WHERE formation_date BETWEEN ? AND ?
    """
    results: dict[str, Any] = {}
    for name, (start, end, cutoff) in periods.items():
        row = db.execute(sql, [cutoff, cutoff, start, end])
        results[name] = dict(zip([col[0] for col in row.description], row.fetchone()))
    month_rows = db.execute("""
      WITH months AS (
        SELECT CAST(last_day(d) AS DATE) AS formation_date
        FROM generate_series(CAST(? AS DATE), CAST(? AS DATE), INTERVAL 1 MONTH) AS s(d)
      ), eligible AS (
        SELECT formation_date, count(*) AS n FROM panel
        WHERE formation_date BETWEEN ? AND ? AND flow IS NOT NULL AND isfinite(flow)
          AND momentum_12_2 IS NOT NULL AND isfinite(momentum_12_2)
        GROUP BY formation_date
      )
      SELECT count(*), min(coalesce(n,0)), max(coalesce(n,0)),
        count(*) FILTER (WHERE coalesce(n,0) < ?)
      FROM months LEFT JOIN eligible USING (formation_date)
    """, [sample["evaluation_formation_start"], sample["evaluation_formation_end"],
            sample["evaluation_formation_start"], sample["evaluation_formation_end"],
            sample["minimum_funds_per_month"]]).fetchone()
    results["evaluation_monthly_feature_coverage"] = dict(zip(
        ("calendar_months", "min_eligible", "max_eligible", "months_below_minimum"), month_rows
    ))
    results["duplicate_fund_month_keys"] = db.execute("""
      SELECT count(*) FROM (
        SELECT fund_id, formation_date FROM panel GROUP BY 1,2 HAVING count(*) > 1
      )
    """).fetchone()[0]
    timing = db.execute("""
      SELECT count(*) FILTER (WHERE return_month IS NULL OR formation_date IS NULL OR
          last_day(return_month + INTERVAL 1 MONTH) <> formation_date),
        count(*) FILTER (WHERE return_assumed_available_at IS NULL OR
          return_assumed_available_at > formation_date),
        count(*) FILTER (WHERE latest_summary_available_at IS NULL OR
          latest_summary_available_at > formation_date),
        count(*) FILTER (WHERE latest_fee_available_at > formation_date OR
          (expense_ratio IS NOT NULL AND latest_fee_available_at IS NULL)),
        count(*) FILTER (WHERE next_month_abnormal_return IS NOT NULL AND
          (target_assumed_available_at IS NULL OR target_assumed_available_at <= formation_date))
      FROM panel
    """).fetchone()
    results["timing_violations"] = dict(zip(
        ("month_alignment", "monthly_return", "summary", "fee", "target"), timing
    ))
    return results


def check_folds(protocol: dict[str, Any], root: Path) -> dict[str, Any]:
    spec = protocol["experiments"]["A"]
    path = root / spec["fold_file"]
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_hash != spec["fold_file_sha256"]:
        raise ValueError("Fold assignment hash does not match the registered protocol")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    months = [row["formation_month"] for row in rows]
    if len(months) != len(set(months)) or any(row["fold"] not in {"0", "1", "2"} for row in rows):
        raise ValueError("Duplicate month or invalid fold assignment")
    start = protocol["sample"]["evaluation_formation_start"][:7]
    end = protocol["sample"]["evaluation_formation_end"][:7]
    return {"month_count": len(rows), "fold_months": dict(Counter(r["fold"] for r in rows)),
            "evaluation_months": dict(Counter(r["fold"] for r in rows if start <= r["formation_month"] <= end)),
            "sha256": actual_hash}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/interim/fund_panel/fund_panel.duckdb"))
    parser.add_argument("--protocol", type=Path, default=Path("configs/research_protocol_v1.json"))
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[2]
    db = duckdb.connect(str(args.database), read_only=True)
    try:
        result = {"protocol_id": protocol["protocol_id"], "coverage": summarize(db, protocol),
                  "random_folds": check_folds(protocol, root),
                  "note": "Completeness counts only; no outcome values or model results."}
    finally:
        db.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
