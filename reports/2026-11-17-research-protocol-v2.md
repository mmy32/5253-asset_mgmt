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

## Open design points

1. **Fund identity over time (settled 2026-11-17).** A class follows its own return history. Once a group is known, it stays attached even after a later blank. If a class gains a group later, its fund id switches on the first date the group is known and its history restarts; earlier months are never re-assigned to the group. Never-grouped classes use `S:` plus the fund number. Implemented in `fund_panel.py` behind `ungrouped_class_rule` (`configs/fund_panel_v2.json`), with tests.
2. **Possible true gaps.** About 8% of ungrouped funds share a portfolio number with other classes. Decide whether to flag or exclude them.
3. **Untestable funds.** About 18% have no portfolio number and are treated as single-class under the rule.

## Required before evaluation

1. ~~Implement the rule in the panel, with tests.~~ Done (not yet rebuilt).
2. Rebuild the panel and record new code, config and panel hashes in `configs/research_protocol_v2.json`.
3. Rerun the coverage and missing-target counts and compare them with v1.
4. Report v1 and v2 side by side.

Status: **design registered; the panel has not been rebuilt and no v2 counts exist.**
