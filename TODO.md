# TODO

Project: point-in-time (PIT) replication of Kaniel, Lin, Pelger and Van Nieuwerburgh (2022), "Machine-Learning the Skill of Mutual Fund Managers". Source: `reports/2026-10-22-research-proposal.md`.

## In Progress
- [ ] Connect to GitHub repo (gh CLI not installed; see notes)

## Backlog

### Data and guards
- [ ] 1. Build `data_loader` and `data_processing` for the CRSP fund panel (WRDS): aggregate share classes to fund level; compute flow, fund momentum, Carhart abnormal returns (36-month loadings) → verify: unit tests on shape and dates; summary stats match paper (mean abnormal return ≈ −0.03%/month, sd ≈ 2.00%)
- [ ] 2. Add an availability-date field to every input and a guard that rejects features dated after the forecast date → verify: test that shifting a feature's date forward changes the output
- [ ] Data hygiene: keep dead funds; no outcome-based sample filter (do not require a return at t)

### WRDS data pulls (all logged in `DATA.md`; CSV, uncompressed, whole database, no filters at pull time, end 2026-09-30)

CRSP Mutual Fund (`crspq`). These two pulls cover all 5 fund and 5 family characteristics in the paper's Table 1 (age, TNA, flow, expense ratio, turnover; family TNA, fund count, momentum, age, flow).
- [x] D1a: **re-pulled** `monthly_tna_ret_nav` (`mret`, `mnav`, `mtna`) from **1976-01** (the built query starts 1980-01). The paper requires at least 30 non-missing returns in the prior 36 months, so a 1980-01 first month needs returns from about 1977-01; flow needs lagged TNA.
- [x] D1b: pulled `fund_summary2` (all 70 variables), **quarterly**, 1999-03 to 2026-09 (`D1b_CRSP_fund_summary.csv`). Fields used:
  - `crsp_obj_cd`: the paper's sample definition (diversified domestic active equity). Fallbacks listed in the paper: Strategic Insight, Lipper and Wiesenberger codes.
  - `fund_name`: the paper also screens names to drop international, balanced, sector, bond, money market and index funds.
  - `crsp_cl_grp`: aggregates share classes to fund level (TNA summed, return, expense ratio, turnover and flow averaged weighted by lagged TNA).
  - `first_offer_dt`: fund age is years since the oldest share class started.
  - `exp_ratio`, `turn_ratio`, `mgmt_cd`, `mgmt_name`: fees, turnover, fund family. The paper fills a missing management company code from the name-to-code mapping in other quarters.
- [x] Checked in the downloaded D1b: `caldt` was quarterly in the first pull (the 1976 re-pull is annual; the checks below are not repeated on it); `dead_flag`, `end_dt`, `delist_cd` do not vary by date (not point-in-time); `exp_ratio` is an annual fraction. Still open: (a) the paper builds abnormal returns from **gross** (before-fee) returns, while `mret` is net of fees, so decide how to add fees back and confirm against the paper's summary statistics (mean −0.03%, sd 2.00%).
- [ ] Handle raw returns above 1: the paper removes 11 fund-months, but D1a has 244 rows above 1 (maximum 12,012). Check what they are. Also treat the codes `R` (`mret`), `T` (`mtna`) and `N` (`mnav`) as missing.

Holdings and stock characteristics (46 of the 59 predictors; scope not decided)
- [ ] Decide scope. Option A: fund-only first pass with the 13 fund and family characteristics plus sentiment (the proposal says flow, momentum and sentiment carry nearly all the signal). Option B: full 59 predictors.
- [ ] If B, link funds to holdings: the paper links CRSP to Thomson Financial Mutual Fund Holdings but does not say how. MFLINKS on WRDS is the usual route (I have not verified table names). The CRSP "Fund-Portfolio Map" (`crsp_portno`) maps to CRSP's own holdings table instead; I have not checked how far back that goes.
- [ ] If B, pull Thomson holdings from 1980 and keep both report date and filing date (the paper requires holdings at t−1, and does not say which date it uses).
- [x] Compustat/CRSP monthly security file pulled (`D7_Compustat_monthly_security.csv`): market data and CRSP-Compustat link only, **no accounting items**. Accounting-based characteristics need a separate Compustat Fundamentals Annual/Quarterly pull (see `DATA.md` D7).
- [ ] If B, build the 46 stock characteristics. The paper takes them from Chen, Pelger and Zhu (2020), a precomputed dataset (1963 to 2019); I do not know if it is public. If not, rebuild from CRSP stock, Compustat and the CRSP-Compustat link, with an explicit accounting-data lag. The paper also imputes missing characteristics each month with a cross-sectional latent-factor model, and rank-normalizes each to the range −0.5 to 0.5.

Non-WRDS data (sources in `DATA.md`)
- [x] Carhart four factors plus risk-free rate (Ken French), downloaded and unzipped 2026-11-06 (full history to 2026-09; values in percent)
- [ ] Baker-Wurgler sentiment, as first released; also the inputs to rebuild it monthly with data to date
- [ ] Optional: CFNAI (Chicago Fed), the paper's alternative macro state
- [ ] Extra factors for the eight-factor check: market, size, value, momentum, investment, profitability, short-term reversal, long-term reversal (listed in the paper's footnote 6)
- [ ] Record the pull date and WRDS vintage for each raw file (CRSP revises its data)

### Models and comparison
- [ ] 3. Replicate the paper design (random folds, 1980-01 to 2019-01) as benchmark → verify: decile spread of the same order as +72% / −119%
- [ ] 4. Build the PIT design: expanding-window chronological training, tuning on prior data only, PIT sentiment → verify: test asserts no training row is dated after any test row
- [ ] 5. Compare both designs on identical data: spread, Sharpe ratio, decile monotonicity → verify: table of paper vs PIT design (H1 / H2)
- [ ] 6. Repeat with feature subsets (all fund-level + sentiment; flow + momentum + sentiment) → verify: table by information set

### Evaluation and inference
- [ ] 7. Long-only top decile net of fees, with realistic holding periods → verify: net alpha with confidence intervals
- [ ] 8. Block bootstrap on the monthly spread series → verify: CIs and p-values for H1
- [ ] 9. Robustness: sentiment lag (1 month vs longer), eight-factor model, pre/post-2008 subsamples, holdout beyond 2019 → verify: sign and rough size stable, or reasons documented
- [ ] Log the number of specifications tried (multiple comparisons)

### Write-up
- [ ] 10. Write up in `reports/`, citing source notes in `research/` → verify: reviewed by the technical-reviewer agent

## Done
- [x] Project scaffold
- [x] Research proposal drafted (`reports/2026-10-22-research-proposal.md`)
