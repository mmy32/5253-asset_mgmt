# 5253 Asset Mgmt

Estimates the true breadth N (effective number of independent bets) of a portfolio or signal set, and tests whether that breadth holds up under market stress.

## Quickstart

```bash
# 1. Clone
git clone <repo-url> && cd 5253-asset_mgmt

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# 3. Run tests
pytest
```

## Usage

```python
from src.data_loader import load_data

data = load_data("data/raw/example.csv")
```

## Architecture

data_loader -> data_processing -> feature_registry -> transformations -> breadth estimation (stress vs. normal regimes).
Breadth estimators and stress-regime definitions are not yet implemented; see TODO.md.

## Project Structure

```
data/{raw,interim,processed}   datasets (gitignored)
src/{config,models,data_loader,data_processing,feature_registry,transformations,utils}
tests/        mirrors src/
scripts/      standalone utilities
notebooks/    exploration only
research/     notes and literature
reports/      generated reports
```
