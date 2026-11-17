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

## Open design points

1. **Untestable funds.** About 18% of ungrouped funds have no portfolio number and are treated as single-class under the rule.

## Required before evaluation

1. ~~Implement the rules in the panel, with tests.~~ Done: identity rule, name rule, size floor and portfolio-number flag (not yet rebuilt).
2. Rebuild the panel and record new code, config and panel hashes in `configs/research_protocol_v2.json`.
3. Rerun the coverage and missing-target counts and compare them with v1.
4. Report v1 and v2 side by side, plus the sensitivities in the table above.

Status: **design registered; the panel has not been rebuilt and no v2 counts exist.**
