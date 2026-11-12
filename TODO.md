git p

# TODO

Project: point-in-time (PIT) replication of Kaniel, Lin, Pelger and Van Nieuwerburgh (2022), "Machine-Learning the Skill of Mutual Fund Managers". Source: `reports/2026-10-22-research-proposal.md`.

**Scope: Option A (fund-level predictors only).** The 13 fund and family characteristics plus sentiment. The proposal says flow, momentum and sentiment carry nearly all the signal. The 46 holdings-based stock characteristics are out of scope.

## In Progress

- [ ] Connect to GitHub repo (gh CLI not installed)

## Backlog

### Data pulls (all logged in `DATA.md`)

- [X] D3: sentiment ends 2025-12, so the sample ends 2025-12 (decided; no rebuild from the input series). Optional: first-release vintage of the index, if one exists.
- [ ] D8: extra factors for the eight-factor check (paper footnote 6): market, size, value, momentum, investment, profitability, short-term reversal, long-term reversal
- [ ] Optional D4: CFNAI (Chicago Fed), the paper's alternative macro state
- [ ] Record the WRDS release (vintage) for D1a, D1b, D5, D6, D7; `DATA.md` has file timestamps only

### Data checks and cleaning

- [X] Raw returns above 1: `drop_extreme_returns` runs after the screen. 244 rows become 16 after the screen, 14 of them on or before 2019-01 (paper: 11). Sample 2,825,906 share-class months, 25,749 share classes, 1999-03 to 2026-09.
- [X] Treat the codes `R` (`mret`), `T` (`mtna`) and `N` (`mnav`) as missing (done in `load_monthly_returns`)
- [ ] Gross vs net returns: the paper builds abnormal returns from gross returns, while `mret` is net of fees. Decide how to add `exp_ratio` back and confirm against the paper's summary statistics (mean −0.03%/month, sd 2.00%).
- [X] Pre-1999 fund attributes: sample starts 1999-03, the first D1b quarter (decided; no fallback for 1980 to 1998). The paper's 1980 to 2019 window is not matched, so the benchmark replication covers 1999 to 2019.
- [ ] Data hygiene: keep dead funds; no outcome-based sample filter (do not require a return at t)

### Build

- [X] Loaders in `src/data_loader/` for D1a, D1b, D2, D3 with tests in `tests/data_loader/`; paths in `src/config/paths.py`, column names and codes in `src/config/schema.py`. Verified against `DATA.md` counts. D2 loader returns decimals; the factor join starts 1927-01 because Mom does.
- [X] Sample screen in `src/data_processing/sample_screen.py` (rules in `src/config/sample.py`): objective code and name as of the latest quarter on or before each month, active U.S. equity codes, name screen, `mret` > 1 drop.
- [X] Full-coverage window in `src/data_processing/coverage.py`: 1999-03-31 to 2025-12-31, computed as the overlap of D1a, D1b, D2 and D3 (SENT present from 1965-07, no gaps). Screened sample in the window: 2,739,850 share-class months, 25,516 share classes, 322 months.
- [ ] Verify the objective-code list in `src/config/sample.py` against CRSP documentation. It was inferred from the code scheme (EDC* and EDYG/EDYB/EDYI kept; EDS*, EDYH, EDYS excluded); the paper lists no codes. Check what EDYH and EDYS contain, and whether the retirement-trust names in EDYG/EDYB belong in the sample.
- [ ] 668,821 fund-months inside the window have no objective code (no quarterly row on or before the month) and are dropped by the screen. Check which funds and whether a later code can legitimately fill them.
- [ ] 1. Build `data_loader` and `data_processing` for the CRSP fund panel: aggregate share classes to fund level via `crsp_cl_grp` (TNA summed; return, expense ratio, turnover and flow averaged weighted by lagged TNA); compute flow, fund momentum, Carhart abnormal returns (36-month loadings, at least 30 non-missing returns) → verify: unit tests on shape and dates; summary stats match paper
- [ ] 2. Add an availability-date field to every input and a guard that rejects features dated after the forecast date → verify: test that shifting a feature's date forward changes the output. Do not use `dead_flag`, `end_dt`, `delist_cd` or `first_offer_dt` as predictors (look-ahead; fine for sample construction).

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

- [X] Project scaffold
- [X] Research proposal drafted (`reports/2026-10-22-research-proposal.md`)
- [X] Scope decided: Option A
- [X] Data check: profiled every raw file for holes (2026-11-11)
- [X] `DATA.md` entries for D5 and D6 written; D5, D6, D7 marked unused; D7 post-cutoff rows noted
