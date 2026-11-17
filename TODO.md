# TODO

Project: test fund-level predictability with an **availability-lagged chronological backtest** and evaluate long-only net performance. Strict historical-vintage point-in-time validation is a separate extension. Scope is Option A: fund and family predictors; holdings-based predictors are out of scope. The research protocol in `reports/2026-11-12-research-protocol-v1.md` describes the current protocol and review gates.

Stop after each major milestone for review.

## 1. Primary research protocol — recorded locally

- [X] Registered `configs/research_protocol_v1.json`, the deterministic month-fold calendar and `reports/2026-11-12-research-protocol-v1.md`. The primary study uses flow and momentum without sentiment; A–C distinguish random folds, chronology and conservative lags.
- [X] Recorded the proposed monthly dates, ridge grid, 12-month moving-block bootstrap, 10,000 draws, seed 5253, rebalancing, illustrative cost scenarios and working retail class-selection rule. The chronological baseline has been run; its registered spread is unestimable because of missing outcomes.
- [X] Ran a read-only completeness and assumed-date check; record any design/data changes as a new protocol version before evaluation. Panel validation is documented in Milestone 2; historical vintages and investor access remain unverified.

## 2. Canonical panel and missing-target diagnosis — complete for review

- [X] Reconciled the class-level sample and fund mappings. The working panel uses the latest available group on the latest eligible summary, never future mapping or an unsupported singleton. Prior available group carry-forward is a documented sensitivity.
- [X] Reconciled all 666,430 common-window formation rows by mutually exclusive target status and year; 295,308 targets are timely and 2,550 observed targets are late. The separate class-level upstream waterfall and overlapping risks are reported in [panel validation](reports/2026-11-16-panel-validation.md).
- [X] Compared observable formation characteristics and coverage by year and objective. Specified missing-weight, merger and closure treatment; selected-portfolio missing weights are reported in the Milestone 3 baseline.
- [X] Chose the working fund panel and factor parser; verified the factor parsers agree on the supplied files and tested timing, aggregation, duplicate returns and future-source changes. Existing panel hashes and v1 rules remain unchanged.
- [X] Recorded the proposed 81 evaluation months, 82,539 feature-complete rows, 2,268 of those with missing targets and 1,441 with missing net returns. No month has fewer than 20 feature-complete funds. A missing net return occurs in every evaluation month among the eligible universe.
- [ ] Review the remaining limitations before evaluation. Register a new protocol version before evaluation if changing the v1 panel or rules. Sub-items:
  - [ ] Unverified historical data vintages and availability: data may have been revised after the dates we assume they were public.
  - [ ] Incomplete class groups: some share classes lack group assignments.
  - [ ] Imperfect objective/name screens: name-based fund-objective screening is imperfect.
  - [ ] Historical regression membership: membership in the regression universe over time is uncertain.
  - [ ] Absent verified investor access and merger proceeds: not verified that a retail investor could buy these classes, or what merger proceeds look like.
  - [ ] Nonrandom missingness: funds that merge or close drop out, so missing outcomes are not random.

## 3. Chronological baseline — complete for review

See [Milestone 3 results](reports/2026-11-16-chronological-baseline.md): both models forecast all 81 months, but neither has a fully observed top-minus-bottom abnormal-return month. Do not relax missingness rules to manufacture a spread. Matched experiments and investor evaluation below belong to Milestone 4.

- [X] Implement a momentum ranking and a regularized linear model using flow and momentum. Produce month-end rankings, equal-weighted research deciles, constituent weights and realized outcome coverage, with chronological refits and prior-only tuning.

## 3.5 Resolve missing-outcome coverage — next

- [X] Attribute missing weight in selected extreme-decile portfolios by month and model, including overlaps and formation-time characteristics. See [selected coverage](reports/2026-11-16-selected-coverage.md). No new performance was computed.
- [X] Trace missing outcomes in the available export: absent future classes are terminal observations; 234 of 239 unique missing-expense cases have a historical expense whose assumed availability is too late. See [source recovery review](reports/2026-11-16-source-recovery-review.md). No outcomes have been recovered; source acquisition and a possible delayed-label protocol remain pending.
- [ ] Choose and document a follow-up estimand and missingness treatment, including any observed-constituent diagnostic, explicit renormalization, coverage thresholds, assumptions and selection bias. Retain the v1 unestimable result.
- [ ] Version and freeze any new protocol and input hashes before evaluating new outcomes; document that v1 outcomes have already been examined. Test timing and weights, report paired-month coverage, and apply inference only when its requirements are met. If coverage cannot be recovered defensibly, report the unanswered question.

**Review gate:** stop before evaluating the follow-up; review the proposed method and its limitations.

## 4. Matched experiments and economic evaluation

- [ ] Run matched experiments A–C, preserving fixed feature definitions, target and evaluation dates where feasible. Report paired monthly A–B and B–C differences, training-set sizes, each design's complete formation universe and the ex-post matched outcome sample.
- [ ] Evaluate the long-only portfolio separately using observed net share-class returns. Working investor: U.S. retail. Specify one-class-per-fund selection, open status, access, minimums, turnover, loads and redemption costs. If those cannot be established, label the result a net-return proxy rather than an investable portfolio.
- [ ] Compare long-only results with a suitable passive alternative and an equal-weighted eligible active-fund portfolio. Report missing realized weights, risk-adjusted returns, paired monthly uncertainty and effect sizes; do not subtract annual expenses twice.

## 5. Extensions and reporting

- [ ] Add broader available fund/family features and a paper-inspired 64-unit ReLU network after the baseline works. Compare the network with a linear sentiment-interaction model before attributing gains to nonlinear complexity. Prediction-strength weighting is secondary and requires a prespecified formula and tie/zero-weight rules.
- [ ] Run a limited, prespecified set of lag, mapping and return-cutoff sensitivities. Record WRDS release vintages if available. Optional: obtain CFNAI (D4) and the additional eight-factor inputs (D8), document vintages, then run those checks. Strict PIT is a separate extension if appropriate historical data become available.
- [ ] Write up the sample waterfall, common and full-universe coverage, comparisons, costs, missing outcomes, confidence intervals, specification count and limitations. The paper reports **+72% and −119% cumulative abnormal returns for the top and bottom legs**, respectively; those are not themselves a single decile-spread statistic and are not targets to force-match.

## Done and current limitations

- [X] Research proposal and project scaffold created; latest GitHub history fetched and merged locally. Milestones 2 and 3 were pushed in commit `6912ad0`.
- [X] Source audit and initial lagged fund-only panel implemented with tests. Reports: `reports/2026-11-09-data-audit.md` and `reports/2026-11-09-fund-panel.md`. The raw observation overlap is 1999-03 through 2025-12; the lagged panel begins in 1999-06.
- [X] D1a/D1b/D2/D3 loaders, a retrospective objective/name screen and the common-window calculation exist. The reported retrospective screen has 2,739,850 share-class months through 2025-12 after removing 16 share-class returns above 100%; this is a diagnostic, not the lagged fund-panel universe.
- [X] D5 is incomplete and blocked; D5, D6 and D7 are not needed for Option A. WRDS release vintages remain unrecorded. The chronological baseline was run; its spread is unestimable under the registered missingness rule.
