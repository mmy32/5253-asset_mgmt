# Turning "Machine-Learning the Skill of Mutual Fund Managers" into a Point-in-Time Predictor: Research Proposal

Date: 2026-10-22
Status: draft.

## 1. Research Objectives

Kaniel, Lin, Pelger and Van Nieuwerburgh (2022) show that a neural network can rank active U.S. equity mutual funds by next-month abnormal return. Their evaluation is not a real-time forecast, because the model trains on randomly drawn months, including months after the ones it predicts. This project tests whether the result survives when the model uses only information available at the time of the forecast.

The objective is to turn the paper's result into a predictor that uses point-in-time (PIT) data.

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
| Sentiment | Baker-Wurgler index as first released, or a version rebuilt each month using only data to date. Test a one-month and a longer lag |
| Sample | 1980-01 to 2019-01 for comparison with the paper, then extended to the latest available data as a true holdout |
| Storage | Raw pulls in `data/raw/` (immutable), cleaned panels in `data/interim/`, predictions and portfolio returns in `data/processed/`. `data/` is gitignored |

Data hygiene rules: each record carries an availability date, and the feature builder refuses to use a record before that date; funds that die are kept; no outcome-based sample filter (the paper requires a return observed at t, which drops funds that die in month t).

## 4. Hypotheses

**H1 (main).** A model that uses only PIT inputs and trains on an expanding, chronological window still ranks funds: the top-minus-bottom decile spread in next-month abnormal return is positive and statistically significant out of sample.

**H0.** The PIT spread is zero, so the paper's result depends on look-ahead in its design.

**H2.** The PIT spread is smaller than the paper's. We measure the reduction by rerunning the paper's design and the PIT design on the same data.

**Known pitfalls the design must address:**
- *Look-ahead in tuning.* Choose hyperparameters using only data that precedes each test period.
- *Look-ahead in preprocessing.* Cross-sectional ranks need no refit. Refit anything that uses full-sample statistics (scaling, sentiment construction) at each date.
- *Stale or restated data.* CRSP and WRDS revise their data, and funds can report TNA with a lag. Flow inherits that noise.
- *Multiple comparisons.* Record and report the number of specifications tried.

## 5. Research Plan

| Step | Task | Verification |
|---|---|---|
| 1 | Build `data_loader` and `data_processing` for the CRSP fund panel; aggregate share classes and compute flow, fund momentum and abnormal returns | Unit tests on shape and dates; reproduce the paper's summary statistics (mean abnormal return about −0.03% per month, standard deviation about 2.00%) |
| 2 | Add an availability-date field to every input and a guard that rejects any feature dated after the forecast date | Test that shifting a feature's date forward changes the output |
| 3 | Replicate the paper's design (random folds) on the same sample as a benchmark | Decile spread of the same order as the reported +72% / −119% |
| 4 | Build the PIT design: expanding-window chronological training, tuning on prior data only, point-in-time sentiment | Chronological split asserted in a test; no training row dated after any test row |
| 5 | Compare the two designs on identical data: spread, Sharpe ratio, decile monotonicity | Table of paper design versus PIT design |
| 6 | Repeat with feature subsets (all fund-level variables plus sentiment, flow plus momentum plus sentiment) | Table by information set |
| 7 | Evaluate the long-only top decile net of fees, with realistic holding periods | Net alpha with confidence intervals |
| 8 | Inference: block bootstrap on the monthly spread series | Confidence intervals and p-values for H1 |
| 9 | Robustness: sentiment lag, alternative factor model (the paper uses eight factors as a check), pre- and post-2008 subsamples, holdout beyond 2019 | Sign and rough size of the effect stable, or reasons documented |
| 10 | Write up in `reports/`, citing source notes in `research/` | Reviewed by the technical-reviewer agent |
