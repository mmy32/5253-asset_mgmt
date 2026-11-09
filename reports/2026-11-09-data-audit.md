# Raw-data audit

Date: 2026-11-09

The first implementation milestone adds a configurable, read-only inventory. The complete machine-readable results from this run are in `data/audit/data_inventory.json` (ignored by Git). Run the command in `README.md` to reproduce the inventory. A structurally profiled file is not necessarily ready for a point-in-time analysis.

| Source | Records | Coverage | Audit finding |
|---|---:|---|---|
| D1a fund returns | 10,345,662 | 1976-01-30 to 2026-09-30 | No malformed rows or duplicate fund/date fingerprint candidates. Return codes `R` occur 94,191 times and returns are blank 255,841 times. The maximum recorded return is 12,012.418 and needs investigation. |
| D1b fund summary | 2,949,105 | 1999-03-31 to 2026-09-30 | Six duplicate fund/date fingerprint candidates. Class-group identifiers are populated in 2,466,254 records; portfolio identifiers in 2,297,416. |
| D2 research factors | 1,203 monthly rows | 1926-07 to 2026-09 | CSV matches the ZIP member. Factor values are percentages. |
| D2 momentum | 1,197 monthly rows | 1927-01 to 2026-09 | CSV matches the ZIP member. Factor values are percentages. |
| D3 sentiment | 816 monthly rows | 1958-01 to 2025-12 | `SENT` has 90 missing values and `SENT_ORTH` 91. The workbook is a revised March 2026 vintage, not a first-release history. |
| D5 holdings | 5,418,660 data records, including one malformed | Well-formed records: 2001-12-31 to 2026-08-31 | **Blocked:** the final record has 12 fields instead of 15. The file may be incomplete; re-export or reconcile it before use. |
| D6 stock returns | 4,523,123 | 1976-01-30 to 2026-09-30 | 41,230 duplicate security-month fingerprint candidate groups, with 52,927 candidate excess rows. Check the row grain and distribution events before deduplication. |
| D7 security/link data | 3,785,886 | 1976-06-30 to 2026-11-30 | 404 records have observation dates after the documented 2026-11-06 file timestamp. No observations fall outside recorded link windows in this check, treating `E` as open-ended; vendor semantics need confirmation. The file lacks accounting fundamentals. |

Duplicate-key counts in the streaming inventory use 64-bit fingerprints. Hash collisions are possible, so the counts are candidates, not exact verified duplicate counts. Invalid numeric codes, missingness, numeric ranges, annual row counts, source metadata and checksums are recorded in the inventory. The audit does not establish publication dates, first-release vintages, the meaning of holdings `eff_dt`, or the suitability of values for modeling.

The command returns a nonzero exit status for this run because D5 is malformed. It still audits the other sources and writes the inventory. D5's valid-looking rows and date range should not be treated as a complete holdings sample. D1b's limited start date prevents full replication of the proposal's 1980–2019 sample with these attributes.

Next milestone: define and construct the fund universe and fund-month panel, with explicit availability assumptions and coverage reporting. Do not use D5 until its export is repaired or reconciled.
