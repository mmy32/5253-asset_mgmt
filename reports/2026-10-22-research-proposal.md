# Turning "Machine-Learning the Skill of Mutual Fund Managers" into a Point-in-Time Predictor: Research Proposal

Date: 2026-10-22
Status: original research proposal; operational scope and hypotheses updated 2026-11-12. The existing PDF remains the original draft. See `reports/2026-11-12-research-protocol-v1.md` and `TODO.md` for the narrower fund-level protocol.

## 1. Research Objectives

Kaniel, Lin, Pelger and Van Nieuwerburgh (2022) show that a neural network can rank active U.S. equity mutual funds by next-month abnormal return. Their random-date evaluation is not a real-time forecast because training can include months after a test month. This project examines whether a reduced fund-level signal survives chronological training and documented information-availability assumptions.

The current primary question is whether fund-flow and momentum predictability survives chronological training and conservative information-availability assumptions, and whether the long-only result adds value after fees and costs. The supplied histories are revised, so the baseline is an availability-lagged chronological backtest. Strict historical-vintage PIT validation is a separate extension if suitable data become available.

## 2. Background of the Paper

**Citation.** Kaniel, R., Lin, Z., Pelger, M., and Van Nieuwerburgh, S., 2022. *Machine-Learning the Skill of Mutual Fund Managers.* NBER Working Paper 29723.

**Question.** Can observable characteristics separate funds that will outperform from funds that will underperform? Earlier work (Carhart, 1997) found little persistence after controlling for momentum. The paper argues that linear methods miss nonlinear effects and interactions.

**Target.** The abnormal return of fund i in month t is the gross fund return minus the Carhart four-factor (market, size, value, momentum) return implied by factor loadings estimated over the prior 36 months. The model predicts next month's abnormal return.

**Data.**
- Sample: 3,275 actively managed U.S. equity funds, 1980 to January 2019, about 407,000 fund-months.
- Fund returns, total net assets (TNA), expenses and objective codes: CRSP Survivor-Bias-Free Mutual Fund Database.
- Holdings: Thomson Financial mutual fund holdings, linked to CRSP.
- 59 predictors: 46 stock characteristics weighted by fund holdings, 3 fund-momentum variables, 5 fund characteristics (including flow), 5 fund-family characteristics.
- Macro state: the Baker-Wurgler investor sentiment index, or the Chicago Fed National Activity Index (CFNAI).

**Method.** A feedforward neural network with one hidden layer of 64 ReLU units, averaged over an ensemble of fits. Evaluation uses a "cross-out-of-sample" scheme. The authors split the months at random into three equal folds. The model trains on two folds and tests on the third, and the roles rotate. The authors sort funds into deciles by predicted abnormal return and weight each decile portfolio by prediction strength.

**Main results.**
- The top predicted decile earns a cumulative abnormal return of +72% over the sample, and the bottom decile earns −119%. The two deciles have similar fees, so fees do not explain the gap.
- The top decile remains positive after fees, at +37% when the model targets net returns directly. About 10 to 20% of funds earn positive alpha after fees. Most of the value comes from avoiding the worst funds.
- Fund flow and fund momentum carry nearly all the signal. A model using only flow, momentum and sentiment achieves close to the full model's spread, about 50 basis points per month between the top and bottom deciles.
- Sentiment amplifies the effect. Flow and momentum predict more strongly when sentiment is high, an interaction that linear models miss. CFNAI shows no comparable interaction.
- Predictability lasts about three years. About half the outperformance comes from holdings between quarterly disclosures and half from trading within the quarter.

**Four gaps between the evidence and a predictor.**

| Gap | Issue |
|---|---|
| Random-date folds | The model trains on months that come after the test month. The authors report that a chronological split gives similar conclusions, but the numbers are not in the main text. |
| Sentiment index | Baker and Wurgler build the index with a full-sample principal-components analysis and revise it, so the published history uses information from after each date. |
| Holdings and fundamentals | Holdings are quarter-end snapshots. The paper does not state whether they are dated by report date or filing date. Stock characteristics depend on the lag applied to Compustat accounting data. |
| Implementability | The long-short spread requires shorting mutual funds, which is not possible. Only the long leg, net of fees and any loads, is investable. |

## 3. Dataset

| Item | Proposal |
|---|---|
| Fund data | CRSP Mutual Fund database via WRDS: returns, TNA, expense ratio, turnover, objective code, share-class fields. Aggregate share classes to fund level as in the paper |
| Factors | Carhart four factors from Ken French's data library |
| Sentiment | Excluded from the primary flow-and-momentum experiment. The revised March 2026 vintage is a labeled extension; strict PIT sentiment requires appropriate first-release vintages. |
| Sample | Fund attributes start in 1999. The draft evaluation reserves formation months 2019-02 to 2025-10 and requires labels to be available by 2025-12-31. The paper's earlier sample cannot be reproduced from these attributes. |
| Storage | Raw pulls in `data/raw/` (immutable), cleaned panels in `data/interim/`, predictions and portfolio returns in `data/processed/`. `data/` is gitignored |

Data hygiene rules: each record carries an availability date, and the feature builder refuses to use a record before that date; funds that die are kept; no outcome-based sample filter (the paper requires a return observed at t, which drops funds that die in month t).

## 4. Hypotheses

**H1 (main).** Under the primary chronological specification and its stated availability assumptions, the average top-minus-bottom next-month abnormal-return spread is positive. The one-sided null is that the mean spread is nonpositive.

**H2.** On matched evaluation observations, the retrospective random-date benchmark has a larger spread than the chronological model using the same retrospective feature timing. Compare their paired monthly differences and training-set sizes; the difference is not a pure measurement of look-ahead bias.

**Economic-value question.** Does the selected long-only portfolio outperform suitable alternatives after fees and supportable implementation costs? A weak or insignificant result does not establish that the paper's finding depended on look-ahead. A positive spread alone does not establish persistent manager skill.

**Known pitfalls the design must address:**
- *Look-ahead in tuning.* Choose hyperparameters using only data that precedes each test period.
- *Look-ahead in preprocessing.* Cross-sectional ranks need no refit. Refit anything that uses full-sample statistics (scaling, sentiment construction) at each date.
- *Stale or restated data.* CRSP and WRDS revise their data, and funds can report TNA with a lag. Flow inherits that noise.
- *Multiple comparisons.* Record and report the number of specifications tried.

## 5. Current research plan

The initial audit and a lagged fund panel are implemented. The remaining work is ordered below; the registered research protocol and `TODO.md` contain the detailed assumptions and review gates.

| Milestone | Task | Verification |
|---|---|---|
| 1 | Freeze the flow-and-momentum, no-sentiment protocol and the staged random-fold, chronological and lagged comparisons | Record dates, hypotheses, target, tuning, investor assumptions, inference settings and seeds before examining evaluation outcomes. |
| 2 | Reconcile both sample screens and validate one canonical panel | Reproduce or explain attrition, report class-group sensitivity, and account for missing targets by year without selecting funds on future outcomes. |
| 3 | Build an end-to-end chronological baseline | Produce monthly rankings, equal-weighted deciles and outcome coverage using prior-only training. |
| 4 | Run matched comparisons and evaluate long-only net performance | Report paired monthly differences, training sizes, full-universe and matched coverage, benchmarks, uncertainty and implementation limitations. |
| 5 | Add broader features, neural network and sentiment extensions; write the report | Compare the neural network with explicit linear sentiment interactions, label revised data, log specifications and report confidence intervals. |

The primary experiment is an availability-lagged chronological backtest, not proof of strict PIT reconstruction. The research spread and the long-only economic evaluation answer different questions. The D5 holdings extract is incomplete and is not used under the current scope.
