# Implementation plan: fund-level mutual fund prediction

Updated: 2026-11-12

Status: protocol v1 registered locally on 2026-11-12; panel and target-coverage validation remain open, and no model or portfolio performance has been evaluated.

## Research question and scope

Does the predictive signal in fund flow and momentum survive chronological training and conservative assumptions about information availability, and does the selected long-only portfolio add value after fees and implementation costs?

The primary study is an **availability-lagged chronological backtest** using the supplied revised data. Assumed publication lags do not recreate historical data vintages. Reserve **strict point-in-time (PIT)** claims for a future validation using substantiated historical values and release dates.

Use Option A: fund and family characteristics. The first experiment uses flow and momentum without sentiment; broader features, the neural network and sentiment follow as extensions. The 46 holdings-based characteristics are outside scope. Do not use D5: the supplied export is incomplete and remains blocked until repaired or reconciled. This is a reduced-information study inspired by the paper, not a full replication.

Stop after each major milestone for review before proceeding.

## Hypotheses and interpretation

- **H1:** The primary chronological model produces a positive average top-minus-bottom abnormal-return spread. Test the null of a nonpositive average spread against this one-sided alternative.
- **H2:** On matched evaluation observations, the retrospective random-fold benchmark produces a larger average spread than the chronological model with the same retrospective feature timing. Test the paired monthly difference; do not interpret it as a pure estimate of look-ahead bias because training-set sizes and other properties can differ.
- **Economic-value question:** Does the selected long-only portfolio outperform appropriate alternatives after fees and supportable implementation costs?

An insignificant result means the study did not find convincing evidence under that specification. It does not prove that the paper's result depended on look-ahead. A significant sorting spread does not by itself establish persistent manager skill.

## Registered protocol before evaluation

The v1 decisions below are recorded in `configs/research_protocol_v1.json` and `reports/2026-11-12-research-protocol-v1.md`. They are locally registered, not independently timestamped. Validate the canonical panel and assumptions in Milestone 2. Any change requires a new version and a dated rationale before examining evaluation outcomes.

| Decision | Primary specification |
|---|---|
| Unit and inputs | One eligible fund per formation month; fund-level flow and prior abnormal-return momentum; no sentiment. Preserve share-class lineage. |
| Decision and holding period | Rank at each calendar month-end `t`; form equal-weighted deciles for month `t+1`. Use only inputs assumed available by the decision timestamp. |
| Common-window boundary | Supplied sentiment ends 2025-12, but the primary run has no sentiment. For a common controlled comparison, require outcome and target availability by 2025-12-31. With the current one-month outcome lag, the last potential formation month is 2025-10; actual coverage must be checked after reconciliation. |
| Initial chronology | Reserve formation months 2019-02 through 2025-10 for evaluation. For the first forecast, train using labels available by 2016-12-31 and select settings on 2017–2018 formation months whose labels are available by the decision date. Refit with all eligible prior data after tuning; subsequent refits and validation use prior available labels only. |
| Availability assumptions | Use the current panel settings: quarterly summary date + 90 calendar days, fiscal year-end + 180 days for fees subject to the later summary availability date, and monthly returns and factors by the following month-end. Confirm these assumptions and staleness limits during panel validation. |
| Model and tuning | Use 12–2 momentum ranking as a reference. For A–C, use ridge regression with flow and momentum, training-only standardization, and alpha grid `0.01, 0.1, 1, 10, 100`; select by validation mean squared error. After the initial validation, retune annually on the most recent 24 months of available validation labels and refit monthly using all earlier eligible labels. |
| Primary portfolio | Equal-weighted deciles; require at least 20 eligible funds per month and resolve prediction ties by stable fund identifier. Report skipped months. |
| Inference | Paired monthly differences; 12-month overlapping moving-block bootstrap, 10,000 draws, seed `5253`, 95% percentile confidence intervals and one-sided null-centered p-values. Preserve calendar gaps rather than concatenating nonadjacent months. Report effect sizes and sample months; fund-months are not independent monthly portfolio observations. |

The current common formation window, 1999-03 through 2025-12, contains 666,430 local panel rows and 297,858 nonmissing next-month targets. This leaves 368,572 formation rows, about 55%, without a usable target. Of the nonmissing targets, 2,550 are assumed available after 2025-12; the corresponding preliminary count available by the cutoff is 295,308. These are **existing-panel diagnostics**, not a frozen evaluation sample. Under the draft 2019-02 through 2025-10 formation dates, the existing panel contains 177,185 rows over 81 months, of which 89,717 have nonmissing targets. Recompute these counts and losses after reconciliation.

### Exact forecast and target timeline

At the close of June 2026, for example, rank eligible funds and form a July portfolio. Under the current conservative monthly lag, June returns are not assumed available until July month-end, so June features can use returns through May. Train only on historical targets whose `target_assumed_available_at` is no later than the June decision. This example illustrates the timing convention; it is outside the primary study's 2025 cutoff.

For an outcome month `s = t+1`, use the paper-style excess-return target:

\[
y_{i,t+1}=(R^{gross}_{i,t+1}-R_{f,t+1})-\widehat{\beta}_{i,t}^{\mathsf T}F_{t+1}.
\]

Estimate the factor loadings with an intercept over the 36 economic months `t-35` through `t`, requiring at least 30 valid observations and full rank. The estimated intercept is **not** subtracted from the target. Because the return for month `t` is assumed unavailable at the decision, this loading is an **ex-post component of the label**, not a June input or portfolio signal. Future realized July returns and factors enter only the outcome scored later; they do not enter the June forecast. Under the current assumptions the completed target becomes eligible for training at the end of month `t+2`, subject to data availability. Verify all dates and the historical inputs used for estimation in Milestone 2.

Use reported net class returns for economic evaluation. Gross returns for the research target are approximated as net return plus annual expense ratio / 12; do not subtract that ratio again from reported net returns.

## Controlled experiments

| Run | Training | Feature timing | Purpose |
|---|---|---|---|
| A | Three random month folds, rotating separate training, validation and test folds | Retrospective timing; no sentiment | Reduced-feature paper-style benchmark. |
| B | Expanding chronological | Same retrospective timing as A; no sentiment | Isolate the change in training chronology as far as possible. |
| C — primary | Expanding chronological | Conservative availability lags; no sentiment | Test the signal under the primary assumptions. |
| D — extension | Same chronological protocol as C | Add the revised March 2026 sentiment vintage, clearly labeled | Test whether the available historical series changes results. |

Use the same model family, feature definitions, target construction and evaluation months for A–C wherever feasible. The timing of feature values differs in B versus C by design. Report A and B training-set sizes and periods, and use paired monthly A–B and B–C differences. A uses future dates relative to some test months, so it is a retrospective diagnostic; its comparison with C does not make the random-fold result an untouched holdout.

For the controlled comparison, use the canonical lagged formation eligibility and the same target and class-membership rule for A–C, determined without future outcomes. Then report the intersection with usable features and targets across designs **as an ex-post matched evaluation sample**, since target availability is only known later. Also report each design's full formation universe, full outcome coverage and results where possible, so matching does not hide missing outcomes or coverage loss. Never use a future target to determine the formation universe.

## Current evidence and reconciliation

The local audit (`e022752`), fund panel (`702efcb`) and GitHub loaders/screens (`9f55214`) are integrated locally. The retrospective screen uses same-date-or-earlier quarterly records and share-class thresholds; the panel uses assumed availability lags, stricter mapping and a fund-level threshold. Their counts cannot be joined into one unqualified waterfall.

| Supplied retrospective attrition step | Remaining |
|---|---:|
| D1a share-class months | 10,345,662 |
| Window 1999-03 to 2025-12 | 8,857,549 |
| Objective code known | 8,188,728 |
| Active U.S. equity code | 2,985,898 |
| Name screen | 2,739,866 |
| Share-class return ≤ 100% | 2,739,850 |
| Approximate fund-months after grouping | 1,060,735 |

The first six rows are share-class months; the last is an approximate fund-month count. The reduction of 1,679,115 during grouping is class consolidation, not fund loss. Reconciliation confirmed that 356,434 selected class-months, about 13.0%, lack `crsp_cl_grp` on the latest as-of summary. Treating them as singletons can overcount funds. A full-file group mapping reproduces 1,060,735 but uses group information first observed after formation for 23 class-months and unavailable at the 90-day cutoff for 28; this numerical match does not prove the original estimate used that method. The paper's 407,158 fund-months use a different period and additional filters, including holdings. Do not subtract the counts or force agreement.

## Milestone 1: Freeze the research protocol

**Completed locally:** v1 records the question, hypotheses, A–D designs, exact date rules, feature and target definitions, model selection, investor assumptions and inference settings. The fold calendar and input/panel hashes are recorded; the coverage check does not calculate outcome statistics. See `reports/2026-11-12-research-protocol-v1.md` for counts and unresolved validation gates. A design or input change requires a new version.

**Review gate:** review v1 and its assumptions; the sample and model remain unvalidated. Reproducing the approximate fund count is a diagnostic, not a prerequisite for the entire project.

## Milestone 2: Canonical panel and missing-target diagnosis

1. **Completed:** the [sample reconciliation](2026-11-12-sample-reconciliation.md) reproduces the supplied class-month waterfall and compares both screens on aligned formation months. The supplied 1,060,735 fund-month estimate matches a full-file group-mapping sensitivity that can use later information; a last-nonblank as-of mapping gives 1,060,747. That numerical match does not establish the original method. The reported 13.0% missing is confirmed for the latest as-of summary. The canonical mapping and publication rules remain to be validated in step 2.
2. Select one canonical loader, factor parser and eligibility specification. Preserve raw files and lineage. Validate month normalization, lagged-TNA aggregation, net/gross treatment, factor windows, class-group changes and the assumptions on quarterly and fiscal availability. Keep fund and family age unavailable until historical inception information is defensible.
3. Produce a **mutually exclusive, ordered** attribution of missing targets, overall and by year: end-of-sample/availability boundary; missing future class return; incomplete class mapping or partial group; missing expense; insufficient valid 30-of-36 history; missing factors or failed/rank-deficient loadings; and any other identified or unresolved cause. Establish and publish the precedence for cases with multiple causes; reconcile the counts to the 666,430 formation rows. Mapping exclusions occurring *before* a fund formation row must be reported in a separate upstream class-level waterfall, not invented as a cause for an existing fund row. Treat a partial-group flag as a demonstrated missing-target cause only when lineage establishes that connection; otherwise report it as an overlapping risk.
4. Compare included versus excluded observations using characteristics available at formation, and report coverage by year and fund type. Preserve formation rows with missing outcomes; quantify selected portfolio weight without realized returns and predefine treatment of closures and mergers. Do not assign a zero return or silently redistribute missing weights. Record the 2,550 post-cutoff targets separately and apply the selected availability cutoff.

**Review gate:** an auditable panel and missingness report reconcile all rows, demonstrate no future inputs determine historical features or eligibility, and document unresolved release/vintage assumptions. Do not choose the look-ahead grouping rule merely because it reproduces 1,060,735; explain the mapping trade-off and use a defensible panel.

## Milestone 3: End-to-end chronological baseline

Build one monthly momentum ranking and the primary regularized flow-and-momentum model with prior-only training, validation and preprocessing. Generate fund rankings, equal-weighted research deciles, constituent weights, outcomes and missing-outcome coverage before adding neural networks or sentiment.

**Review gate:** a reproducible run produces chronological predictions and portfolio return series; tests verify no future features or unavailable labels enter training.

## Milestone 4: Matched experiments and economic evaluation

Run A–C using the frozen protocol and report the paired monthly differences, training-set sizes, common-sample results and each design's full-universe coverage. Keep the top-minus-bottom spread as a **research diagnostic**.

For the long-only analysis, use an illustrative **U.S. retail investor** as the working case. Propose one class per fund: among classes whose lagged records indicate retail access and openness and have a known expense ratio, choose the lowest known expense, breaking ties by `crsp_fundno`. Report funds excluded for missing class information. These indicators are only access proxies; independently verify minimums, eligibility and whether the fund is open before calling the result investable. The supplied file may not establish all restrictions or loads: show data coverage and a clearly labeled net-return proxy where they cannot be verified. Compare the top decile against a suitable passive alternative and an equal-weighted eligible active-fund portfolio. Report monthly rebalancing, net class returns, turnover, missing realized weights and known or explicitly modeled loads and redemption costs. Do not infer unobserved costs are zero or subtract expenses twice.

**Review gate:** long-only net performance, benchmarks, missing-weight coverage, uncertainty and implementation limitations are visible alongside the research spread.

## Milestone 5: Extensions and report

After the baseline works, compare a broader available fund/family linear model and the paper-inspired 64-unit neural network. For the revised-sentiment extension, include an explicit linear interaction model with flow × sentiment and momentum × sentiment before attributing added value to the neural network. The sentiment observation is common to all funds in a month; its cross-sectional role comes through interactions. Report prediction-strength weighting only as a secondary, prespecified comparison with a clear tie/zero-weight rule.

Add a small prespecified set of lag, mapping and return-cutoff sensitivities; add eight-factor or CFNAI checks only if their inputs are documented. If authentic first-release vintages become available, evaluate strict PIT as a separately identified extension. Write the final report with the attrition reconciliation, common and full-universe coverage, results, confidence intervals, cost assumptions, specification count and limitations.
