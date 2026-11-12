"""File locations for raw data. Single source of truth for paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

D1A_MONTHLY_RETURNS = RAW_DIR / "D1a_CRSP_monthly_returns.csv"
D1B_FUND_SUMMARY = RAW_DIR / "D1b_CRSP_fund_summary.csv"
D2_FACTORS_RESEARCH = RAW_DIR / "D2_Carhart_factors" / "D2_Carhart_factors_research.csv"
D2_FACTORS_MOMENTUM = RAW_DIR / "D2_Carhart_factors" / "D2_Carhart_factors_momentum.csv"
D3_SENTIMENT = RAW_DIR / "D3_Baker_Wurgler_sentiment.xlsx"
