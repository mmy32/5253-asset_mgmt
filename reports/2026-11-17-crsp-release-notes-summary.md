# CRSP release notes: summary of findings

Date: 2026-11-17. Detail and sources: [data publication and revision review](2026-11-17-data-publication-and-revision-review.md). Test script: [check_class_group_singletons.py](../scripts/check_class_group_singletons.py).

## What was done

I read 32 CRSP Survivor-Bias-Free US Mutual Fund release notes (January 2019 to September 2026; July 2019 could not be found) to learn when the data we use were published and what CRSP corrected afterward. I then tested one lead from the notes against our own D1b file.

## Findings

1. **The release lag is one month.** Each release says it contains data through the month before the release month. Releases are mostly quarterly, but May 2020 was off-cycle and 2026 has April, July and September releases. No note gives a publication time for an individual fund or value.
2. **CRSP corrected history repeatedly, and our 2026 pull contains every correction.**
   - Returns: five releases (December 2019, July 2020, October 2020, July 2024, October 2024) corrected historical monthly returns. Examples are about 20,000 returns shown as price appreciation instead of total return, missing dividends, missing share splits, and over 200 split ratios.
   - TNA, which drives flow: missing in the March 2020 release (filled in May 2020), and missing again in the December 2022 release (re-released February 22, 2023).
   - Expense ratios and fee dates: fee dates were rebuilt in October 2019, so the dates we use for fees come from CRSP's construction.
   - Management-company history: edited in October 2020 and October 2024, which any family-level feature would use.
   - Class groups (`crsp_cl_grp`): edited in seven releases from July 2020 to July 2025.
3. **The notes never say how large a correction was.** The size of the change to our evaluation-window returns, TNA and fees is unmeasured.
4. **Most missing class groups look like single-class funds.** In April 2024 CRSP removed nearly 60,000 `crsp_cl_grp` ids "where only a single share class exists". I tested whether that explains the 16.4% of funds with no group in D1b.

## Test result: missing class groups

| Check | Result |
|---|---|
| Funds in D1b | 72,461; 56,036 have a group, 16,425 do not |
| Groups with a single member (should be rare if CRSP removed them) | 64 of 14,511 (0.4%) |
| Funds with no group that have a portfolio number | 13,529 of 16,425; of these, 12,169 (90%) share it with no other class |
| Funds with a group that have a portfolio number | 46,377; of these, 45,424 (98%) share it with another class |
| Funds with no group and no portfolio number (cannot be tested) | 2,896 (18%) |
| Funds with no group that share a portfolio number with another class | 1,360 (8%); in 846 of 1,066 such portfolios, a sibling has a group |
| Equity-domestic funds only (objective code starting ED) | Same pattern: 5,789 of 6,420 testable ungrouped funds (90%) have a unique portfolio number |

Reading: grouped funds almost always have siblings, and ungrouped funds mostly do not. About 12,200 of the 16,425 ungrouped funds (74%) look like genuine single-class funds. About 1,360 (8%) share a portfolio with other classes and may be real gaps. About 2,900 (18%) cannot be tested.

Limits of the test: it covers all of D1b, not the 2,739,850 selected class-months; "unique portfolio number" is a proxy for "single class" and is blank for 22% of funds; and I did not confirm any individual fund against a prospectus.

## What this means for the v1 panel

- The v1 panel excludes classes with no group (13.0% of selected class-months: 356,434 of 2,739,850, per the [sample reconciliation](2026-11-12-sample-reconciliation.md)). The test suggests most of those are real single-class funds, so the panel drops real funds, not only data gaps.
- The sample reconciliation already reports a sensitivity that treats each missing-group class as its own fund. That sensitivity now looks closer to the truth for about three quarters of the ungrouped funds.
- Whether the dropped funds differ from the kept ones (for example in size, age or survival) is not known. This matters because missing outcomes are already a problem for the study.

## Decisions for you

1. Keep v1 as is, and report the singleton treatment as a required sensitivity.
2. Register a new protocol version that treats single-class funds as their own funds, then rerun the panel counts before any evaluation.

I have not changed any panel code, protocol or results.

## What is still unknown

- The size of the return, TNA and fee corrections in our window.
- Whether July 2019 or any other off-cycle release contains further corrections.
- Release notes before 2019 were not read.
- No source gives a publication time per observation, so the v1 availability dates remain assumptions.
