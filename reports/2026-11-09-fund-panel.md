# Fund-universe and fund-month panel

Date: 2026-11-09

The panel is an **assumption-based historical backtest**, not a verified first-release point-in-time dataset. It uses D1a share-class returns and TNA, D1b fund attributes, and D2 Carhart factors. It does not read D5 or any other holdings file. Run instructions are in `README.md`; the exact settings used are saved alongside the output.

## Coverage in this run

| Measure | Result |
|---|---:|
| Fund-months | 684,617 |
| Distinct class groups | 5,307 |
| Formation dates | 1999-06-30 to 2026-09-30 |
| Valid net fund return / TNA / cleaned flow | 671,899 / 671,849 / 669,262 |
| Available expense / estimated gross return | 480,343 / 479,800 |
| Prior abnormal return / 12–2 momentum | 304,129 / 277,269 |
| Next-month abnormal-return target | 307,979 |
| Formation rows with a missing future selected class | 11,320 |
| Fund-months with known excluded classes in the same group | 24,112 |
| Fund-months with net returns above 100% | 4 |

Targets are available from formation month 2002-01 through 2026-08; the 30-observation factor-regression requirement and missing fees limit coverage. These counts are not directly comparable to the paper's 1980–2019 sample. The panel covers only funds with available D1b attributes and mapped class groups. The counts include rows without targets; no formation row is dropped for a missing future return.

The class-month universe report records the first applicable exclusion: 2,330,528 selected; 1,330,811 missing a class-group mapping; 594,667 lacking an available summary; and additional exclusions by objective, name, index/ETN flag, stale summary and ambiguous summary. These categories are sequential, not independent reasons. Annual fund coverage and monthly/annual class coverage are in the output directory.

## Universe and aggregation

- Use CRSP domestic equity cap/style codes starting `EDC` or `EDY`, excluding hedged and short styles `EDYH` and `EDYS`. When the CRSP code is blank, use the Strategic Insight, Lipper and Wiesenberger fallback lists from the paper's Appendix A. Exclude names matching the configured international, balanced, bond, money-market, index and sector-related terms. This simple name screen can produce false positives and negatives; review its impact before interpreting results.
- Exclude CRSP index flags `B`, `D` and `E`, and exchange-traded flags `F` and `N`. In CRSP, `N` means ETN. Blank flags mean **not flagged**, not independently verified active or non-exchange-traded status. Every retained fund-month has at least one class with blank index and exchange-traded flags. [CRSP's mutual fund guide](https://www.crsp.org/wp-content/uploads/guides/CRSP_US_Mutual_Funds_Guide_SAS_ASCII_R.pdf) defines these flags and the objective-code hierarchy.
- Exclude class-months with missing class-group IDs. Do not infer singleton funds. Conflicting duplicate summary records are unavailable until a later unambiguous summary. The fund panel aggregates only eligible identified share classes; `known_excluded_classes` flags groups where other identified classes failed a rule. Classes without a usable group cannot be assigned to this flag, so aggregation may still be incomplete.
- Sum TNA across selected classes only when all selected class TNAs are valid. Use prior-month class TNA weights for fund returns, expenses and turnover. Require complete positive-weight inputs; do not silently renormalize missing class returns. Compute flow from class-level net returns and asset changes. Family counts, TNA, flow and momentum exclude the focal fund and use only the eligible universe, so they may understate the full fund family.
- Retain observed net returns and `raw_flow`. Flag net fund returns above 1.0 (100%) and make cleaned `flow`, gross returns and corresponding targets unavailable, following the paper's return cutoff. The four flagged rows remain in the panel and lineage. One source return is 12,012.418; its neighboring NAV changes suggest a possible scale or adjustment issue, but its cause has not been verified.

## Availability and labels

| Input | Assumption used |
|---|---|
| Monthly return and TNA | The economic month is normalized to calendar month-end, retaining the source trading date in class lineage. Values are assumed available at the following month-end. |
| Quarterly summary | `caldt` plus 90 calendar days; discard summaries more than 365 days old. |
| Expense and turnover | An independently joined fee record becomes available at the later of summary availability or fiscal year-end plus 180 days. Discard fee records more than 730 days after their summary date. |
| Factors | Assume monthly values are available by the end of the following month. The supplied French files are revised current-vintage data. |

These are configurable in `configs/fund_panel.json` where applicable; none establishes a historical publication date. Both the fund and factor files can contain later revisions, so neither the panel nor any backtest using it should be described as strict PIT. No pull-date `dead_flag`, delisting flag, end date or `first_offer_dt` is used to select funds or as a predictor. The static inception date is not treated as historically verified, so fund age and family age are omitted.

For formation month `t`, the panel uses return and TNA from economic month `t-1`. Gross return is net return plus the annual expense ratio divided by 12; it is an approximation. The 12–2 feature averages the 11 eligible abnormal returns from `t-11` to `t-1`, requiring eight. The panel also contains the prior-month abnormal return; the paper's descriptions of its short-term momentum and reversal variables require further clarification before treating them as separate signals.

For a target in month `s=t+1`, factor loadings use only months `s-36` through `s-1`, with at least 30 valid observations and a full-rank regression. The target is gross return minus the risk-free rate and the factor contribution; the estimated intercept is not subtracted. The target uses the **share classes selected at formation**, not their later objective or class-group status. If a selected class has no future observation, or a positive-weight class lacks a return or available fee, the outcome is missing and the original formation row remains. `target_assumed_available_at` marks the assumed time the future target can be used for training. Historical regression inputs still depend on the eligible, observed fund panel and its missing-data rules.

## Verification and remaining work

Synthetic tests cover trading-day month normalization, class weighting, flow, missing returns and future outcomes, ETN flag handling, fee availability, duplicate economic months, the return cutoff, the rolling intercept and future classification changes. For a sampled three-class fund-month, an independent calculation reproduced the panel's weighted return and flow. The full run found no duplicate fund/formation keys or selected class records with future summary or fee availability dates.

Before modeling, review the assumed lags and classification screen, investigate large returns and partial groups, and obtain first-release data if a strict PIT claim is required. Fund age and family age remain unavailable under the current provenance. D5 remains blocked until repaired or reconciled.
