# Milestone 3: chronological baseline

Date: 2026-11-16. The registered v1 panel was hash-verified before running the momentum reference and two-input ridge model. Both use the same feature-complete formation universe. No retrospective A/B experiments, sentiment or holdings are included. No v1 setting or panel value was changed.

Run `python -m src.models.baseline --output-dir data/interim/baseline-new`. Outputs are constituent forecasts, deciles and original equal weights, portfolio-month returns and missing weights, the training audit, the protocol snapshot and source-code hash. The output directory must not exist. Source data and the panel are read-only. Local results are in `data/interim/baseline_v1/`.

## Construction and verification

Training uses only earlier formation rows with finite outcomes whose assumed label date is no later than the decision. Initial tuning walks forward over 2017–2018; each validation forecast fits only then-available prior labels. Annual retuning uses the latest 24 calendar formation months whose two-month label lag has matured, averages validation MSE equally across available months, and breaks alpha ties toward the smaller value. Monthly final refits use all eligible matured labels. Standardization uses training means and population standard deviations; the intercept is unpenalized. Momentum uses the registered feature directly. Score ties use fund ID; deciles use the registered integer-rank formula.

Tests check delayed-label exclusion, training-only standardization, stable ties and preservation of missing constituent weight, alongside the panel's future-source and availability tests. All 32 tests passed; Ruff and mypy passed. The full run found no training-label availability later than the forecast date. The reported net outcome is the existing selected-class aggregated fund return, explicitly a net-return proxy, not a verified purchasable retail class or an after-transaction-cost investor return.

## Results and coverage

Both models produced rankings for every one of the 81 evaluation months, 2019-02 through 2025-10, covering 82,539 fund-months each. Monthly eligible counts range from 789 to 1,168. Training-row counts range from 172,048 to 250,907. Ridge chose alpha 0.01 for 59 forecasts and 100 for 22 forecasts. These choices reflect prior-only validation; there was no evaluation-outcome-based selection.

| Coverage | Momentum | Ridge C |
|---|---:|---:|
| All decile-month records | 810 | 810 |
| Decile-months with complete abnormal returns | 104 | 105 |
| Decile-months with complete net-return proxies | 251 | 253 |
| Top-decile months with complete abnormal returns | 9 | 9 |
| Top-decile months with complete net-return proxies | 34 | 34 |
| Months with both top and bottom abnormal returns | **0** | **0** |
| Mean monthly top-decile missing abnormal weight | 2.15% | 2.14% |
| Mean monthly top-decile missing net-proxy weight | 0.96% | 0.95% |

A portfolio-month return is missing if any positive-weight constituent lacks that outcome; missing weights are never reassigned or treated as a zero return. Consequently **the primary top-minus-bottom spread cannot be estimated under this panel and v1 missingness rule**. There are no observations on which to compute its mean, confidence interval or bootstrap p-value. This is a coverage failure, not evidence for or against predictability. Complete months of the top leg alone are selected observations and do not establish overall investor performance. No relaxed complete-case spread is substituted.

## Review gate

Milestone 3's chronological forecasting and portfolio-accounting implementation is complete. Stop here. Milestone 4 remains the matched A–C comparison and economic evaluation, including retail class/access evidence, passive benchmark and costs. Before further evaluation, review the coverage failure. Any source repair, changed aggregation or alternative missing-outcome estimand requires a documented new protocol and data hashes before examining its performance; v1 results must remain visible. Revised vintages and assumed disclosure lags still prevent strict point-in-time claims.
