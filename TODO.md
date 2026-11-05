# TODO

Project: point-in-time (PIT) replication of Kaniel, Lin, Pelger and Van Nieuwerburgh (2022), "Machine-Learning the Skill of Mutual Fund Managers". Source: `reports/2026-10-22-research-proposal.md`.

## In Progress
- [ ] Connect to GitHub repo (gh CLI not installed; see notes)

## Backlog

### Data and guards
- [ ] 1. Build `data_loader` and `data_processing` for the CRSP fund panel (WRDS): aggregate share classes to fund level; compute flow, fund momentum, Carhart abnormal returns (36-month loadings) → verify: unit tests on shape and dates; summary stats match paper (mean abnormal return ≈ −0.03%/month, sd ≈ 2.00%)
- [ ] 2. Add an availability-date field to every input and a guard that rejects features dated after the forecast date → verify: test that shifting a feature's date forward changes the output
- [ ] Data hygiene: keep dead funds; no outcome-based sample filter (do not require a return at t)

### Data to pull (raw into `data/raw/`, immutable; sample 1980-01 to latest, paper comparison ends 2019-01)
- [ ] CRSP Mutual Fund database (WRDS): monthly fund returns, TNA, expense ratio, turnover, objective codes, share-class fields (for aggregation to fund level), fund family identifiers
- [ ] Carhart four factors (Ken French data library): market, size, value, momentum, plus risk-free rate
- [ ] Baker-Wurgler sentiment index, as first released; also the inputs to rebuild it monthly with data to date
- [ ] Optional: CFNAI (Chicago Fed), the paper's alternative macro state
- [ ] Holdings-based inputs for the 46 stock characteristics (not in the proposal's dataset table; implied by the paper, decide scope before pulling): Thomson mutual fund holdings linked to CRSP, CRSP stock returns, Compustat fundamentals with a stated reporting lag
- [ ] Extra factors for the eight-factor robustness check (confirm which eight the paper uses)
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
