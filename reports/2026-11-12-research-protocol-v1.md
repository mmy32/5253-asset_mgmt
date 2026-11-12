# Research protocol v1: flow and momentum

Registered locally: 2026-11-12

Status: **design v1 recorded; panel and missing-outcome validation required before model evaluation.** This file and its configuration are local and not an independent public preregistration. If the design or input data need to change, record the reason and create a new version before evaluating portfolio outcomes.

The executable settings and snapshot hashes are in `configs/research_protocol_v1.json`; the deterministic month assignments are in `configs/research_folds_v1.csv`. The original implementation plan remains untracked. The model, retrospective feature view and portfolio evaluation have not been implemented or run. Aggregate target moments across the previously built panel were inspected during earlier diagnostics, so this work is not fully blind to the raw target distribution; no ranked-portfolio or predictive-model performance has been examined.

## Question and hypotheses

Does fund flow and momentum predict next-month abnormal returns under chronological training and conservative information-availability assumptions, and does a long-only portfolio add value after fees and supportable costs? The baseline is an **availability-lagged chronological backtest using revised data**, not a verified strict point-in-time reconstruction.

- **H1:** the primary chronological model's mean monthly top-minus-bottom abnormal-return spread is positive; the one-sided null is a nonpositive mean.
- **H2:** on the matched sample, the random-fold benchmark has a larger mean monthly spread than the chronological model with the same retrospective feature timing. Test the paired A–B monthly difference. Differences in training-set size and composition prevent interpreting it as a pure estimate of look-ahead bias.
- **Economic value:** assess the long-only leg separately against the active-fund and market references below.

A non-significant result does not prove that the published finding depended on look-ahead; a significant sort does not by itself establish manager skill. Holdings and D5 are outside scope. Sentiment and broader features are extensions.

## Data, dates and timing

| Item | Registered specification |
|---|---|
| Formation | Rank once at each calendar month-end `t` for the next economic month; the selected group is determined without future outcomes. |
| Evaluation | Formation months **2019-02 through 2025-10**; require targets assumed available by **2025-12-31**. |
| Initial training | Formation months from 2002-01 onward with valid labels assumed available by 2016-12-31. |
| Initial validation | Formation months 2017-01 through 2018-12, with labels assumed available by the first decision on 2019-02-28. Walk each validation forecast forward using only data available at that historical validation date. |
| Refitting | Select alpha by month-weighted validation MSE. Refit monthly on available earlier labels; each January retune using the latest 24 formation months with matured validation labels and walk-forward validation. |
| Quarterly and fees | Summary date + 90 calendar days, maximum summary age 365 days; fees no earlier than the later of summary availability or fiscal year-end + 180 days, maximum fee-summary age 730 days. |
| Monthly inputs | Returns, TNA and factors assumed available at the following month-end. Dates are assumed, not verified publication timestamps. |
| Inputs | Fund flow and `momentum_12_2`; no sentiment. Missing/non-finite features are excluded from scoring at formation and counted; no imputation. |

**Concrete example:** at the June 2025 month-end decision, the primary model can use returns through May 2025 under the stated lag and holds the selected portfolio for July. Its July outcome is assumed available at August 2025 month-end. Trading at the next available fund NAV and mapping monthly returns to that execution cannot be verified from monthly returns alone; treat economic results as a proxy until the execution convention and access are substantiated.

For target month `s=t+1`, the outcome is `(gross fund return_s − RF_s) − beta_t · factors_s`. Estimate the loadings with an intercept from the 36 economic months `t-35` through `t`; require 30 valid months and a full-rank design. Do not subtract the fitted intercept. The month-`t` return used for beta is unavailable at the month-`t` decision under the lag, so beta is an **ex-post target component**, never a formation-date feature. A completed target is eligible for later training no earlier than month-end `t+2`. Gross return is approximated as reported net return + annual expense/12; do not subtract expenses again when evaluating reported net class returns.

## Experiments and model

| Run | Training | Feature timing | Role |
|---|---|---|---|
| A | Three seeded random date folds; one train, one validation and one test fold, rotated | Retrospective; no sentiment | Paper-style diagnostic. It can train on months later than a test month. |
| B | Expanding chronological | Same retrospective feature timing as A | Chronology comparison on matched observations. |
| C | Expanding chronological | Conservative information-availability assumptions | **Primary** experiment. |
| D | Same chronological design as C | Revised March 2026 sentiment added and labeled | Later extension, including explicit linear interaction terms. |

The random calendar includes 286 months from 2002-01 through 2025-10, assigned without observing fund returns or outcomes. The file contains 96/95/95 months in folds 0/1/2; the proposed 81 evaluation months are split 25/26/30. Each formation month, including every fund in it, belongs to one fold. Rotations are test/train/validation `(0,1,2)`, `(1,2,0)`, `(2,0,1)`.

Runs A–C use ridge regression with an unpenalized intercept, minimizing `sum of squared residuals + alpha × sum of squared slopes`. Standardize features using training rows only; a zero-variance feature invalidates the fit. Select from `[0.01, 0.1, 1, 10, 100]` by equal-month-weighted validation MSE, breaking ties toward the smaller alpha. Use the 12–2 momentum ranking as a separate simple reference.

For A/B, compute flow for month `t` retrospectively, using the fixed formation membership; C uses the latest flow assumed available at `t`, currently month `t-1`. The 12–2 abnormal-return momentum is the mean for months `t-11` through `t-1`, requiring eight observations. The retrospective A/B view still needs to be implemented and validated; no result is implied by its presence in this protocol.

Primary C ranks its own formation-eligible universe without conditioning on future outcomes or on whether A/B features are later available. Controlled comparisons use canonical lagged formation eligibility and the same target/class-membership rule, then report an **ex-post** common complete-case analysis, its coverage losses, and each design's full-universe results. Cross-design feature matching can itself be retrospective; it is not evidence of an executable formation rule. Freeze and run C before examining A's retrospective benchmark; rolling C may subsequently train on **earlier matured evaluation-period labels** as specified, so it is prequential rather than a static fixed-model holdout.

## Portfolios, missingness and inference

Sort predictions ascending, resolving ties by `fund_id`; assign decile `floor(10 × zero-based rank / n) + 1`. Require at least 20 eligible funds in a month and use equal weights within each decile. The spread is a research diagnostic, not an investable mutual-fund short position.

The long-only working case is a U.S. retail investor. Among classes with lagged retail/open indicators and a known expense ratio, select the lowest known expense ratio and break ties by `crsp_fundno`. Those indicators are proxies and are not currently incorporated into the panel; verify minimums, access, openness and pricing before calling the result investable. If a positive-weight selected holding lacks its realized class return, mark the portfolio month missing and report missing weight; do not set returns to zero or renormalize the surviving holdings. Investigate closures and mergers rather than inventing outcomes.

Compare against an equal-weighted eligible active-fund portfolio. The French market factor plus RF is only a **gross market research proxy**, not an investable passive fund. A separately sourced, net passive benchmark is necessary for an investable passive comparison. Illustrative transaction-cost scenarios are 0, 25 and 50 basis points per traded dollar on both buys and sells, with 25 bps central; these are assumptions, not observed loads or redemption fees. Compute traded dollars including both sides and do not double count fund expenses.

Use 12-month overlapping moving blocks from contiguous observed monthly runs, 10,000 draws and seed `5253`. Report 95% percentile confidence intervals, effect sizes and one-sided null-centered bootstrap p-values with a plus-one adjustment. Never join nonadjacent months inside a block. If no 12-month contiguous block exists, do not report this inference. Missing portfolio months can be selective; report their number and concentration and interpret inference as conditional on observed months.

## Coverage check: existing lagged panel

These are **counts and null/availability checks only**, not model or portfolio results. They are not a reconciled final sample. Training and validation counts are ex-post complete cases; evaluation eligibility must not use future target presence.

| Window | Formation rows | Months | Flow and momentum present | Target present | Features and timely target |
|---|---:|---:|---:|---:|---:|
| Common window, 1999-03–2025-12 | 666,430 | 319 | 264,959 | 297,858 | 253,083 |
| Initial training, 2002-01–2016-12 | 379,975 | 180 | 160,433 | 183,477 | 152,740 |
| Initial validation, 2017-01–2018-12 | 57,346 | 24 | 18,956 | 21,216 | 17,840 |
| Evaluation, 2019-02–2025-10 | 177,185 | 81 | 82,539 | 89,717 | 80,271 |

In the full common window, 368,572 rows (about 55%) lack a target, and 2,550 nonmissing targets have assumed availability after the 2025 cutoff. In the proposed evaluation window, 87,468 formation rows lack a target; among the 82,539 rows with both primary features, 2,268 lack a timely target. These overlapping counts do not establish causes or eliminate selection bias. Eligible-feature counts range from 789 to 1,168 per evaluation month, and no month falls below the 20-fund minimum before outcomes are considered.

The read-only check found zero duplicate fund/formation keys and zero violations of the panel's **stored assumed** summary, fee, monthly-return and target date rules. This does not prove historical publication timing or vintage accuracy. Reproduce counts with:

```bash
python -m src.data_processing.protocol_coverage
```

The source and panel hashes were checked for this snapshot. Verify them again before evaluation; a changed source or design requires a new protocol version. The existing panel is local under ignored `data/`, and D5 was not read for this milestone.

## Review gate and next step

Milestone 1 records v1 and the coverage baseline; it does not certify the panel, access restrictions, costs or historical vintages. The next milestone is a canonical-panel and missing-target diagnosis, including the 2,550 post-cutoff targets, class-mapping attrition, overlapping causes and year-by-year coverage. Do not train or evaluate the models until that review gate is complete.
