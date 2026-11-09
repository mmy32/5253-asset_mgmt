# Point-in-time mutual fund research

This project tests whether mutual fund characteristics predict next-month risk-adjusted returns using information available at portfolio formation. The research proposal is in [reports/2026-10-22-research-proposal.md](reports/2026-10-22-research-proposal.md).

The first milestone is a read-only raw-data audit. Fund panel construction and models are not implemented yet.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Audit the supplied files

Keep the original files together under a raw-data directory, in the layout specified by [configs/data_sources.json](configs/data_sources.json). Run:

```bash
python -m src.data_loader.audit_cli --raw-dir /path/to/raw
```

The command streams the CSV files, records SHA-256 checksums, checks row widths and selected dates and keys, profiles configured fields, inspects the sentiment workbook, and compares each factor CSV to its ZIP member. The machine-readable inventory is written to `data/audit/data_inventory.json` by default. Use `--output` to choose another path **outside** the raw directory, or `--manifest` to provide a different source manifest. The `data/` directory is ignored by Git.

The command processes all configured sources and returns a nonzero exit code if a source is missing, malformed or fails a structural check. Duplicate-key counts are fingerprint-based candidates and require exact verification; they do not automatically establish that the data are invalid. A `profiled` status means structural checks passed, not that an input is point-in-time or cleared for modeling. Publication timing, historical revisions, security definitions and numerical anomalies still require review.

## Tests

```bash
python -m unittest discover -v
pytest
ruff check .
mypy src
```

## Layout

`configs/` contains source settings. `src/data_loader/` contains the audit, `tests/` its fixtures, and `reports/` research documents. `data/` is for ignored raw and derived data; source paths are configurable and raw inputs are never edited by the audit.
