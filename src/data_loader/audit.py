"""Streaming, read-only inventory of the raw research inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import zipfile
from array import array
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
from openpyxl import load_workbook


class HashingLines:
    """Decode complete lines for csv.reader while hashing their original bytes."""

    def __init__(self, stream: Any, encoding: str) -> None:
        self.stream = stream
        self.encoding = encoding
        self.digest = hashlib.sha256()

    def __iter__(self) -> "HashingLines":
        return self

    def __next__(self) -> str:
        line = next(self.stream)
        self.digest.update(line)
        return line.decode(self.encoding)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def numeric_stats() -> dict[str, Any]:
    return {"missing": 0, "invalid": Counter(), "min": None, "max": None}


def update_numeric(stats: dict[str, Any], value: str) -> None:
    if not value:
        stats["missing"] += 1
        return
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite")
    except ValueError:
        stats["invalid"][value] += 1
        return
    stats["min"] = number if stats["min"] is None else min(stats["min"], number)
    stats["max"] = number if stats["max"] is None else max(stats["max"], number)


def audit_csv(path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Validate row widths and profile configured columns in a single streaming pass.

    Duplicate-key counts use 64-bit fingerprints; these are candidates rather than
    verified exact duplicate counts because distinct keys can theoretically collide.
    """
    result: dict[str, Any] = {
        "rows": 0, "malformed_rows": 0, "malformed_examples": [],
        "dates": {"min": None, "max": None, "missing": 0, "invalid": 0},
        "rows_by_year": Counter(), "numeric": {}, "coverage": {},
        "source_codes": spec.get("codes", {}),
    }
    fingerprints = array("Q")
    keys = spec.get("keys", [])
    with path.open("rb") as stream:
        lines = HashingLines(stream, spec.get("encoding", "utf-8"))
        reader = csv.reader(lines, strict=True)
        try:
            header = next(reader)
            if len(set(header)) != len(header):
                raise ValueError("duplicate column names")
            wanted = ([spec["date"]] + keys + spec.get("numeric", [])
                      + spec.get("coverage", []))
            wanted += [spec[field] for field in ("link_start", "link_end") if field in spec]
            missing = sorted(set(wanted) - set(header))
            if missing:
                raise ValueError(f"missing required columns: {missing}")
            indexes = {name: header.index(name) for name in set(wanted)}
            result["columns"] = header
            result["numeric"] = {name: numeric_stats() for name in spec.get("numeric", [])}
            result["coverage"] = {name: 0 for name in spec.get("coverage", [])}
            if "link_start" in spec:
                result["link_window"] = {"outside": 0, "unknown": 0}
            if "documented_pull_date" in spec:
                result["after_documented_pull_date"] = 0
            for row in reader:
                result["rows"] += 1
                if len(row) != len(header):
                    result["malformed_rows"] += 1
                    if len(result["malformed_examples"]) < 5:
                        result["malformed_examples"].append({
                            "line_end": reader.line_num, "expected_fields": len(header),
                            "actual_fields": len(row),
                        })
                    continue
                observation = row[indexes[spec["date"]]].strip()
                if not observation:
                    result["dates"]["missing"] += 1
                    date_ok = False
                elif not valid_date(observation):
                    result["dates"]["invalid"] += 1
                    date_ok = False
                else:
                    date_ok = True
                    dates = result["dates"]
                    dates["min"] = min(dates["min"] or observation, observation)
                    dates["max"] = max(dates["max"] or observation, observation)
                    result["rows_by_year"][observation[:4]] += 1
                    if ("documented_pull_date" in spec
                            and observation > spec["documented_pull_date"]):
                        result["after_documented_pull_date"] += 1
                for name, stats in result["numeric"].items():
                    update_numeric(stats, row[indexes[name]].strip())
                for name in result["coverage"]:
                    result["coverage"][name] += bool(row[indexes[name]].strip())
                if keys:
                    values = [row[indexes[name]].strip() for name in keys]
                    if all(values):
                        encoded = json.dumps(values, ensure_ascii=True, separators=(",", ":"))
                        digest = hashlib.blake2b(encoded.encode("ascii"), digest_size=8).digest()
                        fingerprints.append(int.from_bytes(digest, "little"))
                    else:
                        result["missing_key_rows"] = result.get("missing_key_rows", 0) + 1
                if "link_start" in spec:
                    start = row[indexes[spec["link_start"]]].strip()
                    end = row[indexes[spec["link_end"]]].strip()
                    if not date_ok or not valid_date(start) or (end != "E" and not valid_date(end)):
                        result["link_window"]["unknown"] += 1
                    elif observation < start or (end != "E" and observation > end):
                        result["link_window"]["outside"] += 1
        finally:
            # Exhaust unread bytes even on an error so a reported digest is complete.
            for _ in lines:
                pass
            result["sha256"] = lines.digest.hexdigest()
    if keys:
        fingerprint_values = np.frombuffer(fingerprints, dtype=np.uint64)
        _, counts = np.unique(fingerprint_values, return_counts=True)
        duplicates = counts[counts > 1]
        result["key_check"] = {
            "columns": keys, "method": "64-bit fingerprint candidates; collisions possible",
            "duplicate_groups_candidates": int(duplicates.size),
            "excess_rows_candidates": int((duplicates - 1).sum()),
        }
    return result


def audit_factors(path: Path, archive: Path) -> dict[str, Any]:
    months = []
    numeric: dict[str, Any] = {}
    missing_codes: Counter[str] = Counter()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream):
            if row and re.fullmatch(r"\d{6}", row[0].strip()):
                month = row[0].strip()
                if not 1 <= int(month[4:]) <= 12:
                    raise ValueError(f"invalid factor month: {month}")
                months.append(month)
                for index, raw in enumerate(row[1:], start=1):
                    value = raw.strip()
                    name = f"column_{index}"
                    numeric.setdefault(name, numeric_stats())
                    if value in {"-99.99", "-999", "-999.0", "-999.00"}:
                        missing_codes[value] += 1
                        numeric[name]["missing"] += 1
                    else:
                        update_numeric(numeric[name], value)
    with zipfile.ZipFile(archive) as zipped:
        names = [name for name in zipped.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise ValueError("expected exactly one factor file in ZIP")
        matches = hashlib.sha256(zipped.read(names[0])).hexdigest() == sha256(path)
    return {"sha256": sha256(path), "archive_sha256": sha256(archive),
            "archive_member": names[0], "archive_matches_csv": matches,
            "monthly_rows": len(months), "min_month": min(months) if months else None,
            "max_month": max(months) if months else None,
            "duplicate_months": len(months) - len(set(months)),
            "numeric": numeric, "missing_codes": missing_codes,
            "units": "percent; convert to decimals before joining returns"}


def audit_workbook(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook["DATA"]
        rows = sheet.iter_rows(values_only=True)
        header = list(next(rows))
        if not {"yearmo", "SENT", "SENT_ORTH"}.issubset(header):
            raise ValueError("sentiment sheet missing required columns")
        missing: Counter[str] = Counter()
        months = []
        row_count = 0
        for row in rows:
            row_count += 1
            for name, value in zip(header, row):
                if value is None:
                    missing[name] += 1
            if row[0] is not None:
                months.append(str(row[0]))
        return {"sha256": sha256(path), "sheets": workbook.sheetnames,
                "columns": header, "rows": row_count,
                "min_month": min(months) if months else None,
                "max_month": max(months) if months else None,
                "missing_by_column": dict(missing),
                "duplicate_months": len(months) - len(set(months))}
    finally:
        workbook.close()
