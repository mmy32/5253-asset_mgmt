# TODO

Project: test fund-level predictability with an **availability-lagged chronological backtest** and evaluate long-only net performance. Strict historical-vintage point-in-time validation is a separate extension. Scope is Option A: fund and family predictors; holdings-based predictors are out of scope. The research protocol in `reports/2026-11-12-research-protocol-v1.md` describes the current protocol and review gates.

Stop after each major milestone for review.

## 1. Primary research protocol — recorded locally

- [X] Registered `configs/research_protocol_v1.json`, the deterministic month-fold calendar and `reports/2026-11-12-research-protocol-v1.md`. The primary study uses flow and momentum without sentiment; A–C distinguish random folds, chronology and conservative lags.
- [X] Recorded the proposed monthly dates, ridge grid, 12-month moving-block bootstrap, 10,000 draws, seed 5253, rebalancing, illustrative cost scenarios and working retail class-selection rule. No model or ranked portfolio has been evaluated.
- [X] Ran a read-only completeness and assumed-date check; record any design/data changes as a new protocol version before evaluation. The panel, data vintages and investor access remain to be validated.

## 2. Reconcile the canonical panel and diagnose missing targets

- [X] Reconciled the supplied class-month waterfall with the local lagged panel on aligned formation months. See `reports/2026-11-12-sample-reconciliation.md` for the screen overlap and first applicable exclusion reasons; these are not isolated causal effects.
- [X] Confirmed 13.0% of the retrospectively selected class-months lack a group on their latest as-of summary row. Full-file group mapping reproduces 1,060,735 but uses later-than-source-date information for 28 class-months (23 first appear after formation; all 28 miss the assumed 90-day cutoff); the last-nonblank as-of singleton sensitivity gives 1,060,747. The 668,821 observations lacking a usable objective are share-class months, not fund-months.
- [ ] Produce an ordered, mutually exclusive attribution of missing targets by year. Reconcile all 666,430 existing formation rows, with 297,858 nonmissing targets and 2,550 of those assumed available after 2025-12. Keep pre-formation mapping losses in a separate upstream waterfall; report overlaps and unresolved reasons.
- [ ] Compare included and excluded funds on information available at formation. Track selected portfolio weight with missing realized returns and specify treatment of closures and mergers. Do not drop formation rows on future outcomes, assign missing returns zero or silently renormalize.
- [ ] Evaluate whether last-nonblank group carry-forward is valid under publication and staleness rules; never use a group or objective first observed later. Choose canonical loaders, factor parser and universe rules. Validate the objective-code list and name exclusions, class-group changes and partial groups, fee/turnover lags, annual expense/12 gross approximation, rolling factors and target availability. Treat missing fund/family ages as unavailable until a historical source is verified.
- [ ] Verify information-date guards with trading-day month-ends, duplicate summaries, future data changes and delayed labels. Do not use pull-date `dead_flag`, `end_dt`, `delist_cd` or `first_offer_dt` to decide historical eligibility or as predictors.
- [ ] Explain the sample boundary in each output: the raw D1a–D3 observation overlap ends in 2025-12; the existing fund panel extends through 2026-09; the draft primary experiment also requires target availability by 2025-12-31. Confirm that the final evaluation dates are achievable.

## 3. Build and evaluate the baseline

- [ ] Implement a momentum ranking and a regularized linear model using flow and momentum. Produce month-end rankings, equal-weighted research deciles, constituent weights and realized outcome coverage, with chronological refits and prior-only tuning.
- [ ] Run matched experiments A–C, preserving fixed feature definitions, target and evaluation dates where feasible. Report paired monthly A–B and B–C differences, training-set sizes, each design's complete formation universe and the ex-post matched outcome sample.
- [ ] Evaluate the long-only portfolio separately using observed net share-class returns. Working investor: U.S. retail. Specify one-class-per-fund selection, open status, access, minimums, turnover, loads and redemption costs. If those cannot be established, label the result a net-return proxy rather than an investable portfolio.
- [ ] Compare long-only results with a suitable passive alternative and an equal-weighted eligible active-fund portfolio. Report missing realized weights, risk-adjusted returns, paired monthly uncertainty and effect sizes; do not subtract annual expenses twice.

## 4. Extensions and reporting

- [ ] Add broader available fund/family features and a paper-inspired 64-unit ReLU network after the baseline works. Compare the network with a linear sentiment-interaction model before attributing gains to nonlinear complexity. Prediction-strength weighting is secondary and requires a prespecified formula and tie/zero-weight rules.
- [ ] Run a limited, prespecified set of lag, mapping and return-cutoff sensitivities. Record WRDS release vintages if available. Optional: obtain CFNAI (D4) and the additional eight-factor inputs (D8), document vintages, then run those checks. Strict PIT is a separate extension if appropriate historical data become available.
- [ ] Write up the sample waterfall, common and full-universe coverage, comparisons, costs, missing outcomes, confidence intervals, specification count and limitations. The paper reports **+72% and −119% cumulative abnormal returns for the top and bottom legs**, respectively; those are not themselves a single decile-spread statistic and are not targets to force-match.

## Done and current limitations

- [X] Research proposal and project scaffold created; latest GitHub history fetched and merged locally. A previous push was rejected for lack of write permission; verify access before attempting another push.
- [X] Source audit and initial lagged fund-only panel implemented with tests. Reports: `reports/2026-11-09-data-audit.md` and `reports/2026-11-09-fund-panel.md`. The raw observation overlap is 1999-03 through 2025-12; the lagged panel begins in 1999-06.
- [X] D1a/D1b/D2/D3 loaders, a retrospective objective/name screen and the common-window calculation exist. The reported retrospective screen has 2,739,850 share-class months through 2025-12 after removing 16 share-class returns above 100%; this is a diagnostic, not the lagged fund-panel universe.
- [X] D5 is incomplete and blocked; D5, D6 and D7 are not needed for Option A. WRDS release vintages remain unrecorded. No predictive model has been evaluated.
