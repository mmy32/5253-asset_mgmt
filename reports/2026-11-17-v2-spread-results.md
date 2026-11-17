# v2 spread results: does the top decile beat the bottom decile?

Date: 2026-11-17. These figures are the original run at commit `833cb71`, on the v2 panel under the frozen [v2 protocol](2026-11-17-research-protocol-v2.md). The [review follow-up](v2-spread-review-follow-up.md) adds stricter protocol verification and a separate inference sensitivity. The sensitivity has not yet been run on the registered data.

**The v1 finding stays on record:** under v1's rule (any missing fund blocks the month) the spread could not be estimated at all. These results come from the changed missing-outcome rule, and v1 outcomes had been looked at before it was chosen.

## Answer in one paragraph

On the abnormal-return target, the top predicted decile beat the bottom by about 22 basis points a month. The gap stays positive under the specified 5th/95th percentile fills for missing outcomes. On the net-return target, the gap is about 2 basis points a month and cannot be told apart from zero. The ridge model ranks funds almost exactly as plain momentum does, so there is no evidence here that adding fund flow improves the ranking.

## Results

Spreads are the mean monthly top-decile minus bottom-decile return, equal-weighted within each decile, in basis points (1 bp = 0.01%). Months passing means both deciles had at least 90% of their weight observed. The interval is the registered 95% percentile interval from a 12-month moving-block bootstrap (10,000 draws, seed 5253). The p-value is one-sided, against a null of zero or less. The bounds are the range for the mean spread if every missing outcome earned that month's 5th or 95th percentile outcome, taken over all 81 months.

| Model | Target | Months passing | Mean spread (bps) | 95% interval (bps) | One-sided p | Bounds on mean spread (bps) |
|---|---|---:|---:|---|---:|---|
| Ridge | Abnormal return | 80 of 81 | 21.8 | −0.2 to 35.9 | 0.005 | 7.1 to 30.4 |
| Momentum | Abnormal return | 80 of 81 | 21.7 | −0.3 to 35.9 | 0.005 | 7.1 to 30.3 |
| Ridge | Net return | 81 of 81 | 1.9 | −30.7 to 28.9 | 0.437 | −8.3 to 11.4 |
| Momentum | Net return | 81 of 81 | 1.9 | −30.6 to 28.6 | 0.439 | −8.3 to 11.4 |

- **Abnormal return.** The mean is positive and the bounds on the mean sit entirely above zero (7.1 to 30.4 bps). The one-sided p-value is 0.005, which stays under 0.05 after doubling for the two targets. The two-sided 95% interval only just reaches zero at its lower end. The spread was positive in 48 of 80 passing months, so it is a small average edge with a lot of month-to-month noise (monthly standard deviation about 111 bps).
- **Net return.** The mean is 1.9 bps with an interval from −31 to +29 bps and a p-value of 0.44. The bounds (−8 to +11 bps) include zero. The data do not distinguish this from no spread.
- **The bounds are narrow.** The missing weight is only 1% to 3% per decile, so filling it with extreme values moves the mean spread by at most about 15 bps (abnormal return: 21.8 down to 7.1 or up to 30.4; net return: 1.9 down to −8.3 or up to 11.4). The average monthly range is 23 bps and the widest month is 68 bps.

## What to be careful about

1. **Ridge and momentum are the same ranking.** The mean rank correlation between their scores is 0.9999, and 99.8% of top-decile and bottom-decile funds are the same under both. Their monthly spreads correlate at 1.00. Flow and momentum are nearly uncorrelated in the panel (0.012), so this means the linear fit puts almost no weight on flow. I did not inspect the fitted coefficients. This is one result reported four times, not four results. It also means the paper's claim that flow carries much of the signal is not supported by a linear model here. A nonlinear model might behave differently, and that is what the neural network step tests.
2. **The abnormal-return target and the net-return target are different samples and different questions.** The abnormal return is gross of fees and adjusted for market, size, value and momentum exposure, and it needs 30 prior months and an expense ratio. The net return is the reported return after fees with no factor adjustment. I did not break down why the gap between 22 bps and 2 bps is so large. Factor adjustment and sample differences are the likely drivers, but that is not tested.
3. **The interval is not centred on the point estimate.** The registered moving-block method gives edge months less weight, so the average over all blocks is 18.9 bps against the 21.8 bps point estimate. That pulls the percentile interval down and is why its lower end sits at zero while the p-value (which is centred under the null) is small. I used the registered rule as written. A bias-corrected interval is a possible check, and I have not run one.
4. **The bounds are plausible extremes, not guaranteed ones.** A fund that collapses before it disappears can lose more than the 5th percentile. The bounds also do not touch the training problem: the model learns only from funds with observed outcomes, so survivors are over-represented in what it learns (risk 8 in the [risks report](2026-11-17-missing-outcome-risks.md)).
5. **Not blind and not a point-in-time result.** v1 outcomes had been examined, and the data are revised vintages with assumed release delays.
6. **Multiple estimates.** Two targets were run, each with two predictors. Because ridge and momentum are the same ranking, there are really two estimates. No other specification, sample variant or threshold was run on these results. The three sample sensitivities are counts only and have not been run through the spread.
7. **Gross spread, not a portfolio.** This is an equal-weighted top-minus-bottom research spread. It does not account for costs, retail access, or the fact that a long-short position in mutual funds cannot be held.

## What this does and does not say

The estimated abnormal-return spread is positive and survives the specified missing-outcome scenarios. Missing returns outside those scenarios could overturn the sign. The scenario range does not account for sampling uncertainty, and the original two-sided interval includes zero. The net-return spread is indistinguishable from zero.

## Next

Run the [inference sensitivity](v2-spread-review-follow-up.md) on the registered panel before Section C2 of the [TODO](../TODO.md).
