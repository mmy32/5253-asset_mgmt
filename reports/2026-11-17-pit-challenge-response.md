# Can this data support a point-in-time claim? Response to the PIT challenge

Date: 2026-11-17. Pulls together the six data reviews from TODO section 2: [revisions](2026-11-17-data-publication-and-revision-review.md) ([summary](2026-11-17-crsp-release-notes-summary.md)), [class groups](2026-11-17-research-protocol-v2.md), and the [sample-definition review](2026-11-17-sample-definition-review.md) (fund-type filter, universe, access, missing funds). Nothing here computes a performance result.

## The challenge

Kaniel, Lin, Pelger and Van Nieuwerburgh (2022) evaluate on random date folds, so training can use months after the test month. The project replaces that with a chronological backtest. The challenge is whether the CRSP, Fama-French and sentiment files we hold are good enough to call that backtest point-in-time (PIT): would an investor at each formation date have seen the same funds, fields, labels and returns?

## Answer

**No. The data support an availability-lagged chronological backtest on revised data, not a PIT study.** The lags (summary 90 days, fiscal-year fees 180 days, one month for returns and TNA) are our assumptions. They remove the obvious look-ahead, but six other channels remain. Each is listed below with what we found, which way it likely biases results, and what we can do about it.

| # | Channel | What we found | Likely bias | Handling |
|---|---|---|---|---|
| 1 | **Revised history** | Our pull (2026-11-06) contains every CRSP correction. Notes show repeated fixes to returns (5 releases, 2019 to 2024), TNA (2020, 2022/23), fee dates (2019), management company (2020, 2024) and class groups (7 releases to 2025). No note gives a size. D2 and D3 are also single, later vintages. | Unknown sign. Not measured. | Report as a limit. Quarterly vendor files or Internet Archive snapshots are needed to measure it (D2 only). |
| 2 | **Class-group labels** | 16,425 of 72,461 funds have no group; 13.0% of selected class-months. CRSP deleted nearly 60,000 single-class group ids in April 2024. Test on D1b: 90% of ungrouped funds with a portfolio number share it with no other class (grouped funds: 2%). About 74% of ungrouped funds look single-class. | v1 dropped real funds. The blanks are a 2024 vintage artifact, not what a 2019 investor saw (inference, not verified against an older vintage). | Protocol v2: count ungrouped classes as their own funds. Last known group stays; a group learned later applies only from that date, with no retroactive merging. Built and tested; panel not rebuilt. |
| 3 | **Fund-type filter** | Name screen removes 9.0% of rows in our fund types. 4,765 rows (195 classes) are dropped only because the family or trust name has a banned word, e.g. "AIM Sector Funds". Index flags catch 46.7% of flagged rows that the name misses. Our name list is broader than the paper's. 19.4% of classes change objective code over time. | Mild selection by name; unclear sign. | Open decision: apply the name screen to the fund part only. Codes are used as known at each date. |
| 4 | **Who was in the universe** | Dead funds are included (61.6% of sample classes are dead today), so not survivors only. 2.7% of class-months have a return before `first_offer_dt`; 25.1% have TNA under 5 million; 5.1% have no TNA. No source gives when a fund first entered the database. | Upward, if backfilled early histories of small funds are included. | Open decision: minimum size. Entry dates stay unknown. |
| 5 | **Investability** | 44.3% of latest TNA is in institutional-only classes; 14.0% of classes are closed to new money. Flags are latest-row, not historical. Minimums, loads and platform access are not in D1a/D1b. 97% of merged classes name a successor, but terms are undated. | Upward: the opportunity set is larger than a retail investor's. | Panel does not use the flags (using the latest flag would itself leak). Open decision: retail-only rule or label results an "after-fees return estimate". |
| 6 | **Funds that vanish** | Funds that disappear within 12 months had weaker prior-year returns (mean rank 0.39 to 0.42 against 0.51) and are far smaller (median TNA 2.6 to 11.7 million against 50.6). About 5% to 10% of class-months disappear in a year.  | Upward. Conditioning on an outcome being observed uses future information. | Panel keeps every formation row; portfolio months with missing outcome weight are marked unavailable, not renormalised. Treatment of the gap is an open decision. |

Disappearance here uses past returns only. Target coverage is in the [panel validation](2026-11-16-panel-validation.md).

## What each source can and cannot claim

| Source | PIT status |
|---|---|
| D1a/D1b CRSP (core) | Revised vintage with one-month release lag and quarterly updates. No per-observation publication date. Not PIT. Lagged. |
| D2 factors | One vintage (CRSP 202609). The Internet Archive holds 21 versions of the factor file since 2015, so a vintage test is possible. |
| D3 sentiment | Rebuilt in 2026 with no recoverable history. Excluded from the primary experiment. |
| D4 CFNAI | Not pulled. The only source with publisher-supplied real-time vintages. |

## Claims the evidence allows

- **Allowed:** "predictability survives chronological training under stated availability lags, on revised data."
- **Not allowed:** "this strategy was implementable in real time," "the paper's result is look-ahead bias," or any statement about returns of an investable portfolio. A null result also would not show the paper's finding depended on look-ahead.
- **Direction of remaining bias:** channels 3 to 6 mostly bias toward better-looking results, channel 1 is unknown, channel 2 biased v1 toward fewer funds. Report every headline number with these in view.

## What strict PIT would need

1. Dated CRSP vintage files (quarterly Morningstar deliveries) to measure the size of corrections and to see group labels as they existed.
2. A first-appearance date per fund to remove backfill.
3. Dated merger terms and share-class access data.
4. Internet Archive snapshots for D2 and D4 first-release data. These are partial and a separate extension.

## Open decisions that affect this answer

Fund-type name rule, minimum size, retail-only classes, treatment of vanishing funds, the 8% shared-portfolio-number funds, and whether to fold these into v2 or register v3. All are listed in section 3.5 of [TODO.md](../TODO.md). Any change needs a dated protocol version before outcomes are examined. v1 outcomes were already examined, so no registration is fully blind.

## Limits of this response

Desk review plus D1a/D1b diagnostics. No revision was measured empirically, no older vintage was inspected, and the 74% single-class figure rests on a portfolio-number proxy. Sample counts in the sample-definition review are approximations of the panel, not panel counts.
