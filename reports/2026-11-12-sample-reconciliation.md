# Retrospective sample and lagged-panel reconciliation

Date: 2026-11-12

Status: Milestone 2, step 1 complete. The mapping and classification rules have **not** been chosen as canonical.

This diagnostic reads the registered, SHA-256-verified fund-panel database built from D1a/D1b. It does not read D5, calculate model performance or alter the source panel. Reproduce it with `python -m src.data_processing.sample_reconciliation --output-dir <new-directory>`; the outputs include a complete JSON summary, waterfall, mapping sensitivity and annual comparison. The database's stored summary table has already retained one representative for each of six duplicate summary keys, so it is not an independent re-read of the original CSVs.

## Retrospective attrition: supplied counts reproduced

| Screen | Share-class months remaining | Removed at this step |
|---|---:|---:|
| D1a source | 10,345,662 | — |
| Source return dates 1999-03-31 to 2025-12-31 | 8,857,549 | 1,488,113 |
| Objective known | 8,188,728 | 668,821 |
| Seven active domestic equity codes | 2,985,898 | 5,202,830 |
| Name screen | 2,739,866 | 246,032 |
| Raw class return not above 100% | 2,739,850 | 16 |

These counts reproduce the supplied **share-class-month** sequence. Of the 668,821 without an objective, 402,268 have no earlier or same-day summary row and 266,553 have a summary with a blank objective. The screen does not drop missing returns: 7,568 selected class-months have no usable return. It also retains 673 rows with a blank name because the name exclusion does not match a blank. Eighteen rows in the full window use a summary date with duplicate records; none survives the complete retrospective screen. The earlier preprocessing chose one representative per duplicate key, so the six keys still require proper resolution.

## Grouping sensitivity

All three rows below use the same 2,739,850 selected class-months. A missing class group is treated as a separate class-level singleton only in the last column; this can overcount true funds. The reduction from class-months to fund-months is aggregation, not evidence that those funds were lost.

| Group mapping | Class-months with no mapping | Fund-months with mapped groups only | Fund-months if missing groups are singletons |
|---|---:|---:|---:|
| Group on the latest summary row as of the source return date | 356,434 | 704,603 | 1,061,037 |
| Last **nonblank** group observed on or before the source return date | 356,020 | 704,727 | 1,060,747 |
| Latest nonblank group anywhere in the full file | 355,992 | 704,743 | **1,060,735** |

The first row confirms that 356,434 / 2,739,850 = **13.0%** of selected class-months lack a group on the latest as-of summary row. Carrying forward a previously observed nonblank group recovers 414 class-months and reduces the singleton estimate by 290 fund-months. Whether those earlier mappings remain valid under the lagged pipeline's publication and staleness rules needs separate validation.

The full-file mapping reproduces the supplied **1,060,735** estimate exactly. It also supplies a group to **28 historical class-months across five share classes** for which no nonblank group is present on or before the source date; their source dates span 2003-03-31 to 2024-02-29. For 23 of those rows, the group first appears after formation. For the remaining five it first appears between the source date and formation, but all 28 are unavailable by formation under the registered 90-day assumption. Relative to the last-nonblank as-of sensitivity, that reduces the singleton total by 12. No selected row with an earlier nonblank group has a different full-file group in this snapshot. The full-file method is a **look-ahead diagnostic**, not a forecast input. Its numerical match is not proof that it was the method originally used to obtain the supplied estimate.

The paper's 407,158 final fund-months cover a different period and apply additional eligibility rules, including holdings. They should not be subtracted from any row above or interpreted as a final count for this fund-only study.

## Same-record comparison with the lagged pipeline

The retrospective source-date window includes December 2025. To compare the same records with the local panel by **formation date**, the aligned comparison uses formation months 1999-04 through 2025-12, corresponding to source-return months 1999-03 through 2025-11. The December 2025 source rows form in January 2026 and are not part of this comparison. This leaves 8,827,991 matched source class-months, of which 2,730,264 pass the retrospective screen and 2,261,158 are selected by the lagged pipeline.

| Retrospective status | Lagged status | Class-months |
|---|---|---:|
| Selected | Selected | 2,258,409 |
| Selected | Not selected | 471,855 |
| Not selected | Selected | 2,749 |
| Not selected | Not selected | 6,094,978 |

For the 471,855 retrospective-only observations, the lagged pipeline's **first applicable** exclusion is missing class group for 348,736, index flag for 56,848, no available summary for 27,286, name for 16,893, unknown objective for 16,870, stale summary for 2,994 and other objective for 2,228. These are sequential labels: other conditions can overlap, so they are not isolated causal effects.

For the 2,749 lagged-only observations, the first retrospective exclusion is other objective for 2,128, name for 486, unknown objective for 123 and raw class return above 100% for 12. These differences reflect both rules **and** which quarterly observation was available; they cannot be attributed to just one change. The lagged pipeline retains class rows with extreme returns and later applies its cutoff at fund level.

Across all 8,827,991 aligned rows, the retrospective summary date is later than the lagged summary date in 5,471,062 cases; the dates agree in 2,813,683, and the lagged pipeline has no available summary in 543,246. The retrospective screen has no prior summary in 402,110 cases, a subset of the no-lagged-summary group. Those counts describe date differences under the configured 90-day lag, not verified historical disclosure timing.

## What this does and does not resolve

This step reconciles the reported class-level waterfall and demonstrates the effect of three grouping choices. It does **not** decide whether carrying forward a group is valid for the canonical panel, verify historical release dates, or reconcile the paper's holdings-dependent final sample. The local lagged panel's 666,430 fund-months and 297,858 observed targets in the 1999–2025 formation window use additional aggregation, availability and outcome rules, so the grouped retrospective figures are not an adjacent step in that panel's waterfall.

Next: choose and validate the canonical loader and mapping rules, then diagnose missing targets in ordered, mutually exclusive categories. Do not use D5.
