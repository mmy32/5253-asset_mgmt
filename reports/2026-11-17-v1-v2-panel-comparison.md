# Panel rebuild: v1 and v2 side by side

Date: 2026-11-17. Both panels were rebuilt from the raw D1a, D1b and D2 files with the current code. v1 uses `configs/fund_panel.json`; v2 uses `configs/fund_panel_v2.json` (ungrouped classes as their own funds, the paper's six name words on the fund part of the name, a 5 million fund-size floor). Counts come from `protocol_coverage` and `target_diagnosis`, run on each rebuilt database. This is a coverage comparison. No model, ranked-portfolio or performance result was computed.

## Check: the v1 rebuild reproduces v1

Every v1 count matches the registered numbers: 666,430 formation rows, 297,858 nonmissing targets (295,308 timely, 2,550 late), 82,539 feature-complete evaluation rows, 2,268 without an abnormal-return target, 1,441 without a next-month net return, the 1.76% mean missing share (range 0.12% to 4.72%) and the full class-month waterfall (2,261,158 selected). The v1 config and the raw input files hash identically to the v1 registration. The v1 database file hash differs (DuckDB files are not byte-identical across builds), so the contents are verified by counts, not by file hash. The panel code changed, so its hash is new. All hashes are in `configs/research_protocol_v2.json`.

## Coverage

Common window 1999-03 to 2025-12 (formation dates); evaluation window 2019-02 to 2025-10 (81 months).

| | v1 | v2 | Change |
|---|---:|---:|---:|
| Funds, common window | 5,294 | 7,343 | +39% |
| Fund-months, common window | 666,430 | 853,470 | +28% |
| Complete features, common window | 264,959 | 363,521 | +37% |
| Nonmissing targets (timely by 2025-12-31) | 297,858 (295,308) | 404,984 (401,605) | +36% (+36%) |
| Evaluation: fund-months | 177,185 | 229,682 | +30% |
| Evaluation: funds | 2,820 | 3,817 | +35% |
| Evaluation: feature-complete rows | 82,539 | 110,677 | +34% |
| Evaluation: feature-complete rows with a target by the cutoff | 80,271 | 108,172 | +35% |
| Feature-complete funds per evaluation month (min / median / max) | 789 / 1,079 / 1,168 | 1,133 / 1,430 / 1,521 | |
| Median fund TNA, feature-complete rows (millions) | 453.7 | 391.0 | |

- In v2, 222,166 of 853,470 common-window fund-months (26%) belong to funds identified by their own fund number (`S:` ids). 43,262 (5.1%) are flagged as sharing a portfolio number with another class.
- The 5 million floor removed 79,111 of 956,320 fund-months built over the full period (8.3%).
- In the evaluation window, 4,378 feature-complete rows are flagged as sharing a portfolio number.

## Missing targets

Among feature-complete evaluation rows:

| | v1 | v2 |
|---|---:|---:|
| No abnormal-return target | 2,268 (2.75%) | 2,505 (2.26%) |
| No next-month net return | 1,441 (1.76% mean monthly share; 0.12% to 4.72%) | 1,638 (1.49%; 0.20% to 3.66%) |
| Months with at least one missing net return | 81 of 81 | 81 of 81 |
| Median TNA, missing vs observed (millions) | 248.2 vs 512.9 | 248.9 vs 407.3 |

Ordered missing-target reasons, common window (first applicable reason):

| Reason | v1 | v2 |
|---|---:|---:|
| Target observed by cutoff | 295,308 | 401,605 |
| Observed after cutoff | 2,550 | 3,379 |
| Missing, availability after cutoff | 1,540 | 1,951 |
| Future class absent | 9,110 | 8,933 |
| Future class weight missing or nonpositive | 11,389 | 3,310 |
| Future return missing or invalid | 666 | 790 |
| Return above 100% cutoff | 4 | 4 |
| Future expense unavailable | 170,976 | 226,266 |
| Fewer than 30 valid prior months | 174,887 | 207,232 |
| **Total missing targets** | 368,572 | 448,486 |

## What this shows

- Counting single-class funds adds about a third more fund-months and funds, and the share of feature-complete rows missing a target falls a little (2.75% to 2.26%). The gain is mostly in rows, not in a cleaner missing-data picture.
- The two largest causes of missing targets are unchanged in kind: missing future expense data (226,266 rows) and too little history for the factor regression (207,232). The v1 finding that most of these expense gaps arrive later than assumed has not been retested on v2.
- "Future class weight missing" falls from 11,389 to 3,310. I have not investigated why. A likely reason is that groups of several classes with a missing TNA are no longer the unit; this is a guess.
- Missing-outcome funds are still smaller than observed ones (median TNA 248.9 against 407.3), and every one of the 81 months still has a missing net return. The v1 conclusion that the top and bottom groups cannot both be fully observed in a month is not changed by these counts. It needs the model rankings to test, which has not been done on v2.
- The upstream class-month status counts are not comparable between versions. In v1 a missing group was labelled first, so many index and exchange-traded classes appear as "missing class group". In v2 that label does not exist, so those classes appear under index, exchange-traded or other-objective.

## Limits

- The 5 million floor, the new name rule and the grouping rule changed together, so these counts do not separate their effects. The sensitivities registered in v2 (add "global", no floor, drop the flagged funds) have not been run.
- v1 outcomes were examined before v2 was registered; v2 is not a blind registration.
- The v2 build took 107 minutes of wall time but about 3 minutes of processor time, so the machine was most likely asleep for part of the run. v1 took 94 seconds. I have not rerun v2 to confirm the time.
- The v2 panel's database holds more rows than v1's (877,209 against 684,617 over the whole period), so later steps will be slower.
