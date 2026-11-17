# Research protocol v2: single-class funds

Registered locally: 2026-11-17. Settings: `configs/research_protocol_v2.json`. Supersedes [v1](2026-11-12-research-protocol-v1.md) for the one change below. Everything else in v1 still applies.

## The change

v1 excluded every share class that had no class group (`crsp_cl_grp`) on its latest available summary. 13.0% of selected class-months were excluded this way.

v2 treats such a class as a single-class fund, identified by its own fund number. It stays in the formation universe, the feature history, the targets and the selected portfolios.

## Why

CRSP's April 2024 release notes say it removed nearly 60,000 class-group ids "where only a single share class exists". A test on D1b ([summary](2026-11-17-crsp-release-notes-summary.md)) supports this as the main reason for blank groups:

- Only 64 of 14,511 remaining groups have a single member.
- 90% of ungrouped funds that have a portfolio number share it with no other class, against 2% of grouped funds.
- About 74% of the 16,425 ungrouped funds look like single-class funds, about 8% may be genuine gaps, and about 18% cannot be tested.

So v1 was dropping real funds, not only filling data gaps.

## What this decision did not use

No return, outcome or portfolio result informed it. The v1 baseline had already been run and its outcomes examined before this change, so v2 is not a blind registration. The rationale is the data-vintage review, not performance.

## Further changes decided 2026-11-17

These were decided together and folded into v2 rather than a v3: no v2 panel had been built and no v2 result seen. v1 outcomes were examined earlier, so the registration is not blind. Evidence is in the [sample-definition review](2026-11-17-sample-definition-review.md) and the [point-in-time response](2026-11-17-pit-challenge-response.md).

| Item | v1 | v2 | Sensitivity |
|---|---|---|---|
| Name screen | 15 words matched on the full name | The paper's six words (international, balanced, sector, bond, money market, index), matched on the fund part of the name only (after the first colon). Index and ETF flags still apply. | Add "global" |
| Minimum size | None | Fund TNA known at formation of at least 5 million; a missing TNA fails. Months below the floor stay in the history used for loadings, momentum and family features. | No floor |
| Ungrouped funds sharing a portfolio number (about 8%) | Excluded with all ungrouped | Kept as their own funds and flagged `ungrouped_shares_portno` (whole-file flag, not point-in-time) | Drop flagged funds |
| Funds that vanish | No substitution, no renormalising | Unchanged; report the missing weight | Follow merged funds into the named successor (not yet implemented; merger terms are undated) |

Set aside: investability (retail-only classes, open-to-investors flags). It is not a concern for this study and no rule is added.

## Missing-outcome estimand, decided 2026-11-17

Folded into v2, not a v3. It runs on the v2 panel. The question is unchanged from v1 H1: does the top decile beat the bottom decile? What changes is how missing outcomes are treated, because v1 could not estimate the spread (no month had both legs complete; see the [baseline](2026-11-16-chronological-baseline.md)). v1 results stay on record. v1 outcomes were examined before this decision, so the registration is not blind. No v2 outcome has been examined.

**1. Coverage threshold (primary estimate).** A leg counts as observed in a month if at least 90% of its weight has an outcome. Weights are rescaled over the observed funds within that leg. A month enters the spread only if both legs pass. Months that fail are listed and counted, not dropped silently. The 90% value was chosen from the coverage discussion, not from returns.

**2. Bounds (alongside the primary estimate).** For every month, fill each missing weight with a low and a high value to get a range for the spread:

- Low value: the 5th percentile of observed outcomes that month. High value: the 95th. Both come from the same month's eligible funds, so no future information is used. The 5th and 95th percentiles are a proposed choice, to be confirmed before freezing.
- Lower bound on the spread = top leg at low value minus bottom leg at high value. Upper bound = top leg at high value minus bottom leg at low value.
- If the range excludes zero, the sign is robust to the missing funds. If it includes zero, report the spread as not identified.

**3. Two targets, reported separately and never combined.**

| | Abnormal return | Net-return proxy |
|---|---|---|
| Definition | (gross return − RF) − beta × factors, 36-month betas, as in v1 | Reported class return, net of fees |
| Needs expense ratio and 30 prior months | Yes | No |
| Question | Skill after factor adjustment (v1 H1) | Investor payoff after fees |

Each target gets its own threshold estimate and its own bounds. Which one is primary is not yet decided; v1 H1 stays registered on abnormal return, and the net-return proxy is added as a second hypothesis.

**Not run yet.** The v2 sensitivities in the table above come first, then the mechanics checks (timing, weights), then freezing the plan and input hashes. The new estimand is not run until then.

## Open design points

1. **Untestable funds.** About 18% of ungrouped funds have no portfolio number and are treated as single-class under the rule.

## Required before evaluation

1. ~~Implement the rules in the panel, with tests.~~ Done: identity rule, name rule, size floor and portfolio-number flag (not yet rebuilt).
2. ~~Rebuild the panel and record new code, config and panel hashes.~~ Done.
3. ~~Rerun the coverage and missing-target counts and compare them with v1.~~ Done.
4. ~~Report v1 and v2 side by side.~~ Done. The sensitivities in the table above are still to run.

Status: **panel rebuilt 2026-11-17; coverage compared with v1 in the [comparison report](2026-11-17-v1-v2-panel-comparison.md). Hashes are in the protocol JSON. The sensitivities in the table above have not been run, and no model or performance result exists.**
