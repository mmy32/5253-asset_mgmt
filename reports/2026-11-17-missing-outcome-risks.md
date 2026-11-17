# Risks in the missing-outcome plan

Date: 2026-11-17. Applies to the missing-outcome method in the [v2 protocol](2026-11-17-research-protocol-v2.md): a 90% coverage rule, best/worst-case bounds, and two separate targets (abnormal return and net return). Written before any v2 forecast or return was examined. No result is reported here.

**Short version.** The method can tell us whether the top group beat the bottom group, or it can tell us the data cannot say. It cannot fix the fact that the funds that vanish are not like the funds that stay. The bounds show how much that could matter. They do not remove it.

## What we already know about the missing funds

- Funds that vanish within a year were weaker beforehand (average prior-year rank 0.39 to 0.42, against 0.51 for survivors) and much smaller (median 2.6 to 11.7 million, against 50.6). Source: [sample-definition review](2026-11-17-sample-definition-review.md).
- On the v1 panel, the top decile was missing about 2.15% of its weight for the abnormal-return target and about 0.96% for the net-return target. Every one of the 81 months had at least one missing outcome. The bottom decile's missing share was not reported; the overlap report will give it. Source: [baseline report](2026-11-16-chronological-baseline.md).
- For 234 of 239 missing-expense cases, the expense data exists but arrived later than we assumed it would be public. These funds are missing because of our timing rule, not because they ended. Source: [source recovery review](2026-11-16-source-recovery-review.md).

## Risks

| # | Risk | Which way it pushes the answer | How the plan handles it | What is left |
|---|---|---|---|---|
| 1 | **Vanishing funds.** Funds that end tend to have done badly. Averaging only the funds we can see leaves out their bad outcomes. | Raises the level of each group. The effect on the top-minus-bottom gap depends on which group loses more weight, so the sign is not known in advance. | Bounds: fill missing weight with a low and a high value and report the range. | The bounds are only as good as the fill values (risk 4). |
| 2 | **Rescaling assumes the missing funds look like the observed ones in the same group.** Our own evidence says they do not (small, weak prior returns). | Probably upward for the level of a group. | The 90% rule limits how much weight is rescaled to at most 10% per group. | A group at 90% observed can still be biased. The bounds, not the threshold, are the check. |
| 3 | **The 90% cutoff is a choice.** It was set from the coverage discussion, not from data. | A lower cutoff admits more months and more bias. A higher one leaves fewer months. | Fixed before any result. Months that fail are listed. | If too few months pass, the main estimate is weak. See the "enough months" rule below. |
| 4 | **The fill values are not true extremes.** The low and high are the 5th and 95th percentile of that month's observed outcomes. A fund that vanishes after a collapse can lose more than the 5th percentile. A few funds could also gain more than the 95th. | The range may be too narrow, so it can look more informative than it is. | The percentiles come from the same month, so no later information is used. | A wider fill (the minimum and maximum) is a sensitivity to consider. The range is a plausible range, not a guaranteed one. |
| 5 | **Months that pass the rule are not a random sample of months.** Coverage may be better in some years or market conditions. | Unknown. | Report passing months by year and show the failing ones. | The result describes the passing months, not every month. |
| 6 | **Abnormal return is missing for two different reasons.** Some funds ended. Others are missing only because expense data arrived later than we assumed. | Treating both alike overstates the problem for the second group and may understate it for the first. | Run the net-return target as well. It does not need expense data. | We do not separate the two reasons inside the abnormal-return target. |
| 7 | **The two targets use different samples.** Abnormal return needs 30 prior months and an expense ratio, so it leaves out young funds. Net return does not. | Differences between the two results may come from the sample, not the target. | Report them separately and never combine them. | Do not read a gap between them as evidence about anything. |
| 8 | **The model is trained only on funds with an observed outcome.** A training label needs a future return, so funds that vanished contribute nothing. | The model learns from survivors. This affects the ranking itself and is not touched by the threshold or the bounds. | None in this step. | Stated as a limit. A sensitivity that follows merged funds into their successors is not built. |
| 9 | **Revised data and assumed release dates.** Source data are revised, no release date is recorded per observation, and the size of revisions is unmeasured. | Unknown. | Delays are assumptions, applied the same way to every month. | The result is an availability-lagged backtest, not a point-in-time result. |
| 10 | **Fund identity under v2.** About 18% of ungrouped funds cannot be tested and are counted as single-class funds. About 5% of fund-months are flagged as possibly sharing a portfolio with other classes. A class that gains a group later restarts its history. | A wrong identity can split one fund into two, or shorten its history. | Flag the uncertain funds and run the drop-flagged sensitivity. See the [sensitivity report](2026-11-17-v2-sensitivities.md). | The flag is built from the whole file, not point-in-time. |
| 11 | **Size floor.** A 5 million floor removes small funds before they enter the sample, and small funds are the ones that vanish most. | Lowers the missing share and the bias, but also changes who is in the universe. | Run the no-floor sensitivity. | Results may differ between floor and no-floor. |
| 12 | **Equal weights inside a group.** A 5 million fund counts as much as a 5 billion one. | Adds noise and gives small funds more influence than an investor's money would. | Stated as a limit. Value weighting is not part of this plan. | The research spread is not an investable portfolio. |
| 13 | **We have seen v1 results.** The baseline showed only that the spread could not be estimated, and some aggregate target moments were looked at earlier. No v2 forecast or return has been examined. | The registration is not blind. | The freeze note says so. | A reader must trust that settings were not tuned. |
| 14 | **Many estimates.** Two predictors, two targets, a threshold estimate and bounds for each, plus three sample sensitivities. | More chances of a result that looks good by luck. | List every estimate in advance. The ridge model on abnormal return is the original hypothesis (H1). The other estimates are reported alongside it. | The primary target is not yet chosen (see the protocol). |

## Rule for "enough months"

The inference rules from v1 still apply: the bootstrap uses overlapping 12-month blocks inside contiguous runs of passing months. If no run of 12 contiguous passing months exists, we report the monthly numbers and the bounds but no confidence interval or p-value. If the bounds include zero, we report the spread as not identified.

## What would make us say the question is unanswered

- Fewer than 12 contiguous months pass the 90% rule for both groups, and
- the best-to-worst range for the spread includes zero in most months.

In that case the v1 conclusion stands: the data cannot tell us whether the top group beats the bottom group.
