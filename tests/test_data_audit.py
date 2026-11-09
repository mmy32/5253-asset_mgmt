"""Targeted checks for input integrity and source handling."""

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from openpyxl import Workbook

from src.data_loader.audit import audit_csv, audit_factors, audit_workbook, sha256
from src.data_loader.audit_cli import audit_source


class DataAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_csv_multiline_truncation_codes_and_duplicate_candidates(self):
        path = self.root / "input.csv"
        path.write_text(
            'id,day,value,note\n001,2020-01-31,R,"two\nlines"\n'
            '001,2020-01-31,2,ok\n002,2020-02-29,\n', encoding="utf-8"
        )
        spec = {"date": "day", "keys": ["id", "day"], "numeric": ["value"]}
        result = audit_csv(path, spec)
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["malformed_rows"], 1)
        self.assertEqual(result["malformed_examples"][0]["actual_fields"], 3)
        self.assertEqual(result["numeric"]["value"]["invalid"]["R"], 1)
        self.assertEqual(result["key_check"]["excess_rows_candidates"], 1)
        self.assertEqual(result["sha256"], sha256(path))
        self.assertEqual(result["dates"]["min"], "2020-01-31")

    def test_link_window_open_end_and_future_date(self):
        path = self.root / "link.csv"
        path.write_text("id,day,start,end\n1,2020-01-31,2010-01-01,E\n"
                        "2,2021-01-31,2010-01-01,2020-12-31\n", encoding="utf-8")
        result = audit_csv(path, {"date": "day", "link_start": "start", "link_end": "end",
                                  "documented_pull_date": "2020-12-01"})
        self.assertEqual(result["link_window"], {"outside": 1, "unknown": 0})
        self.assertEqual(result["after_documented_pull_date"], 1)

    def test_factor_monthly_only_and_zip_match(self):
        path = self.root / "factor.csv"
        content = b"header\n,Factor\n202001,1.2\n202002,2.0\nAnnual\n2020,3.2\n"
        path.write_bytes(content)
        archive = self.root / "factor.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("original.csv", content)
        result = audit_factors(path, archive)
        self.assertEqual(result["monthly_rows"], 2)
        self.assertTrue(result["archive_matches_csv"])
        path.write_bytes(content + b"changed\n")
        self.assertFalse(audit_factors(path, archive)["archive_matches_csv"])

    def test_workbook_coverage(self):
        path = self.root / "sentiment.xlsx"
        book = Workbook()
        book.active.title = "README"
        sheet = book.create_sheet("DATA")
        sheet.append(["yearmo", "SENT", "SENT_ORTH"])
        sheet.append([202001, 0.1, None])
        book.save(path)
        book.close()
        result = audit_workbook(path)
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["missing_by_column"]["SENT_ORTH"], 1)

    def test_cli_refuses_to_write_inside_raw_directory(self):
        raw = self.root / "raw"
        raw.mkdir()
        output = raw / "inventory.json"
        result = subprocess.run(
            [sys.executable, "-m", "src.data_loader.audit_cli", "--raw-dir", str(raw),
             "--output", str(output)], capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output must be outside", result.stderr)
        self.assertFalse(output.exists())

    def test_missing_input_is_blocked(self):
        result = audit_source(self.root, {"id": "D1", "path": "missing.csv", "kind": "csv",
                                          "availability": "unknown"})
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["blocking_issues"])
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
