# Sample-definition review: fund-type filter, universe, access, missing funds

Date: 2026-11-17. Script: [review_sample_definition.py](../scripts/review_sample_definition.py) (reads D1a and D1b only). This is a data-quality review. It computes no target, model or portfolio result.

**Approximation.** The script works on share classes with at least one quarterly summary row in the seven domestic-equity objective codes that also pass the name, index-flag and ETF-flag screens at any quarter (24,255 classes). The panel applies these screens as of each date, so counts here differ slightly from the panel's. Rows are class-quarters unless stated.

## 1. Fund-type filter

The panel excludes a class if its name matches `international|global|foreign|emerging market|balanced|bond|money market|index|sector|real estate|healthcare|technology|financial services|natural resources|precious metal`. This is broader than the paper's list in `src/config/sample.py` (which has no "global", "foreign", "real estate", "healthcare", "technology", "financial services", "natural resources" or "precious metal"). The difference has not been documented before.

- The name screen removes 93,465 of 1,042,008 class-quarters (9.0%) in the seven codes. 60,404 of them (64.6%) already carry an index or ETF flag.
- The screen misses much of what the flags catch: 52,828 of 113,232 flagged rows (46.7%) have no matching word in their name. The flags are the stronger index filter; the name screen adds little for "index".
- **Family-name false positives.** Fund names read "Trust: Fund". 5,111 name hits (5.5%) match only the trust part. 4,765 of those are not index-flagged (195 classes). Examples: "AIM Sector Funds" (2,525 rows, which holds ordinary value and dividend funds such as Invesco Comstock), "Legg Mason Global Asset Management Trust" (1,200) and "Franklin Global Trust". "INVESCO Combination Stock & Bond Funds" is another trust-name hit.
- Some hits look right: "Multi-Sector Bond Fund" and "PIMCO Small Cap RAE PLUS Bond Alpha" are bond-heavy, and "Global Allocation" and "Lifecycle Index 20xx" are not active US equity.
- The words "global", "balanced" and "sector" mostly occur in names that are not index-flagged (8%, 6% and 14% flagged). Whether those funds are really non-domestic or non-equity cannot be told from names. The objective code already says domestic equity, so for these the name rule overrides CRSP's own classification.
- Objective codes change over time for 5,362 of 27,673 classes (19.4%) that ever appear in the seven codes. The panel uses the code known as of each date, so a class can enter or leave the sample.

**Conclusion.** The name screen is imperfect but its damage is small and measurable: about 4,800 class-quarters from 195 classes are dropped because of the trust name. A cleaner rule is to apply the name screen to the fund part only and rely on the index and ETF flags for index funds. That is a protocol change.

## 2. Who was in the universe

- CRSP includes dead funds. 61.6% of sample classes are flagged dead at pull time; at year-end 1999, 74.9% of the classes then alive are flagged dead by now, falling to 13.2% for 2023. The data are not survivor-only.
- Class counts at year-end rise from 4,345 (1999) to about 11,000 (2008 onward) with no obvious break.
- **Incubation and backfill.** 96,313 of 3,573,013 class-months (2.7%) carry a return dated before `first_offer_dt`. The median gap between `first_offer_dt` and the first monthly record is −1 day (10th to 90th percentile: −31 to +30 days), so most classes start on time. Small classes are common: 25.1% of class-months with a TNA have TNA below 5 million and 13.3% below 1 million (CRSP TNA is in millions). TNA is missing for 5.1% of class-months. The panel has no minimum-size filter; the paper's rules are not applied here. Small, young funds are where backfill bias is most likely.
- 3,623 of 76,080 classes in D1a (4.8%) have no row in D1b, so they have no objective code and cannot enter the sample.
- What this cannot tell us: whether CRSP added funds retroactively after they existed (a known "history backfill" issue) or when a fund first appeared in a database. No source gives that date (see the [revision review](2026-11-17-data-publication-and-revision-review.md)).

## 3. Could an investor really buy these?

Latest summary row per sample class:

| Flag | Result |
|---|---|
| `open_to_inv` | 20,777 Y, 3,386 N (14.0%), 92 blank |
| `sales_restrict` | 60 Y |
| Retail and institutional flags | Retail only: 11,185 classes, 45.7% of latest TNA. Institutional only: 10,079 classes, 44.3%. Neither flag: 2,899 classes, 10.0%. |

- Roughly half of the TNA sits in classes that are not flagged retail. The panel does not use these flags, so selected portfolios can hold institutional classes that a retail investor cannot buy. `open_to_inv` is only the latest value; it changes over time and the panel does not use it.
- **Mergers and liquidations.** Of 14,941 dead classes: 5,924 merged (M), 3,927 liquidated (L), 5,090 have no code. 97.3% of merged classes name a successor fund number; the successor is in D1b for 97.2% and in the sample for 87.1%. What a shareholder received (successor shares, or cash) is not in the data, and merger terms are not dated.
- Not in D1a or D1b: minimum investment, loads, 12b-1 distribution costs and platform availability. These cannot be tested from the files we have.

## 4. Is disappearing random?

For each class-month with a full year of past returns, I compared the trailing 12-month return rank within the month (0.5 is average) for classes that stop reporting within the next 12 months against those that keep reporting. Only past returns are used, not the target.

| What happens in the next 12 months | Class-months | Mean trailing-return rank | Median TNA (millions) |
|---|---:|---:|---:|
| Keeps reporting | 2,868,399 | 0.506 | 50.6 |
| Disappears, liquidated | 44,429 | 0.386 | 2.6 |
| Disappears, merged | 72,375 | 0.424 | 11.7 |
| Disappears, no code | 70,898 | 0.416 | 5.9 |

Funds that vanish did worse over the prior year than funds that survive (rank 0.39 to 0.42 against 0.51) and are far smaller (median TNA 2.6 to 11.7 against 50.6). About 5% to 10% of class-months disappear within a year, depending on the year (10.3% in 2008). Dropping funds with a missing outcome therefore removes weaker, smaller funds and biases measured performance upward. This is consistent with the existing finding that missing-target rows have a median TNA of 248 against 513 (see [panel validation](2026-11-16-panel-validation.md)). The size of the effect on returns, which depends on the unobserved terminal returns, is not measured.

## What changes the plan

None of these findings was used to change a rule. Each needs a decision before evaluation; the decisions are listed in the hand-off note and in section 3.5 of TODO.md. Any change gets a new protocol version before outcomes are examined. Note that v1 outcomes have already been examined.

## Limits

- The sample is the approximation described above, not the panel.
- The disappearance table treats the last reported month as the end. A fund can also stop reporting for a short time and return.
- Flags are as of the latest summary row; they are not historical.
