# v2 sample sensitivities

Date: 2026-11-17. Three variants of the v2 panel, compared with the base v2 panel on counts only. No model, ranking or return was computed. Script: `scripts/run_v2_sensitivities.py`. Raw counts: `data/interim/sensitivities/v2_sensitivity_counts.csv` (local, not in Git).

The base row reproduces the registered v2 comparison exactly: 110,677 feature-complete evaluation rows, 2,505 without an abnormal-return target and 1,638 without a next-month net return. Details of the base panel are in the [v1-v2 comparison](2026-11-17-v1-v2-panel-comparison.md).

## What each variant changes

| Variant | Change from v2 | How it was built |
|---|---|---|
| Add "global" | "global" joins the six banned name words | Full rebuild, `configs/fund_panel_v2_global.json` |
| No size floor | The 5 million fund-size floor is removed | Full rebuild, `configs/fund_panel_v2_nofloor.json` |
| Drop flagged | Funds flagged as sharing a portfolio number with other classes are removed | Filter on the v2 panel (`ungrouped_shares_portno`) |

## Counts

Common window is 1999-03 to 2025-12. Evaluation is 2019-02 to 2025-10 (81 months), restricted to rows with complete features.

| | v2 | Add "global" | No floor | Drop flagged |
|---|---:|---:|---:|---:|
| Funds, common window | 7,343 | 7,292 | 8,249 | 6,964 |
| Fund-months, common window | 853,470 | 849,168 | 931,611 | 810,208 |
| Complete features, common window | 363,521 | 362,045 | 380,480 | 337,403 |
| Timely targets, common window | 401,605 | 399,983 | 421,411 | 373,571 |
| Evaluation: feature-complete rows | 110,677 | 109,880 | 112,369 | 106,299 |
| Evaluation: feature-complete funds | 2,193 | 2,187 | 2,262 | 2,103 |
| Evaluation: no abnormal-return target | 2,505 (2.26%) | 2,497 (2.27%) | 2,716 (2.42%) | 2,400 (2.26%) |
| Evaluation: no net return | 1,638 (1.48%) | 1,630 (1.48%) | 1,843 (1.64%) | 1,563 (1.47%) |
| Months with a missing abnormal-return target | 81 of 81 | 81 of 81 | 81 of 81 | 81 of 81 |
| Months with a missing net return | 81 of 81 | 81 of 81 | 81 of 81 | 81 of 81 |
| Feature-complete funds per month (min to max) | 1,133 to 1,521 | 1,129 to 1,511 | 1,164 to 1,541 | 1,059 to 1,476 |

## What this shows

- **"Global" barely matters.** It removes 51 funds (0.7%) and changes the missing share by 0.01 points.
- **The size floor matters a little for missingness.** Without it, 12% more funds enter the common window and the share of evaluation rows missing a target rises from 2.26% to 2.42% (net return: 1.48% to 1.64%). This fits the earlier finding that small funds are the ones that vanish. The floor trims some of that missingness but does not remove it.
- **Dropping flagged funds removes about 5% of fund-months** and leaves the missing share unchanged. Flagged funds are not the source of the missing outcomes.
- **No variant fixes the coverage problem.** Every month still has at least one missing outcome in every variant. The 90% coverage rule and the bounds in the [v2 protocol](2026-11-17-research-protocol-v2.md) are still needed.
- **Every variant keeps at least 1,059 feature-complete funds in every month,** far above the 20-fund minimum.

## What this does not show

These are counts, not results. They say nothing about whether a variant changes the top-minus-bottom spread. Only the base v2 panel will be run in the main test. The variants are reported here for completeness and can be rerun through the same estimand later if a reviewer asks.

The `panel_sha256` values in the CSV are for the DuckDB files. DuckDB files are not byte-identical across builds, so the contents are verified by the counts above, as noted for v1 in the comparison report. The v2 and drop-flagged rows use the same file.
