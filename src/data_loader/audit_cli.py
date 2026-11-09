"""Run the raw-data inventory without changing any source files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data_loader.audit import audit_csv, audit_factors, audit_workbook


def audit_source(raw_dir: Path, spec: dict[str, Any]) -> dict[str, Any]:
    path = raw_dir / spec["path"]
    result: dict[str, Any] = {"id": spec["id"], "path": spec["path"],
                              "kind": spec["kind"], "availability": spec["availability"]}
    for field in ("source", "pull_date", "vintage", "query"):
        result[field] = spec.get(field)
    try:
        result["size_bytes"] = path.stat().st_size
        if spec["kind"] == "csv":
            result.update(audit_csv(path, spec))
        elif spec["kind"] == "factor":
            result.update(audit_factors(path, raw_dir / spec["archive"]))
        elif spec["kind"] == "xlsx":
            result.update(audit_workbook(path))
        else:
            raise ValueError(f"unsupported input kind: {spec['kind']}")
        issues = []
        if result.get("malformed_rows", 0):
            issues.append("malformed CSV records")
        if result.get("dates", {}).get("invalid", 0):
            issues.append("invalid observation dates")
        if result.get("archive_matches_csv") is False:
            issues.append("factor CSV does not match ZIP member")
        if result.get("duplicate_months", 0):
            issues.append("duplicate factor or sentiment months")
        result["blocking_issues"] = issues
        result["status"] = "blocked" if issues else "profiled"
    except (OSError, ValueError, UnicodeError, KeyError, csv.Error, zipfile.BadZipFile) as exc:
        result["status"] = "blocked"
        result["blocking_issues"] = [f"{type(exc).__name__}: {exc}"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("configs/data_sources.json"))
    parser.add_argument("--output", type=Path, default=Path("data/audit/data_inventory.json"))
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.raw_dir.resolve()):
        parser.error("output must be outside the raw data directory")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = []
    for spec in manifest["sources"]:
        print(f"Auditing {spec['id']}...", flush=True)
        result = audit_source(args.raw_dir, spec)
        results.append(result)
        detail = ", ".join(result["blocking_issues"]) or "no structural errors"
        print(f"  {result['status']}: {detail}", flush=True)
    output = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "manifest": str(args.manifest), "sources": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(output, indent=2, ensure_ascii=False) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Inventory written to {args.output}", flush=True)
    return 1 if any(item["status"] == "blocked" for item in results) else 0


if __name__ == "__main__":
    sys.exit(main())
