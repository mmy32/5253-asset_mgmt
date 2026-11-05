# TODO

Project: point-in-time (PIT) replication of Kaniel, Lin, Pelger and Van Nieuwerburgh (2022), "Machine-Learning the Skill of Mutual Fund Managers". Source: `reports/2026-10-22-research-proposal.md`.

## In Progress
- [ ] Connect to GitHub repo (gh CLI not installed; see notes)

## Backlog

### Data and guards
- [ ] 1. Build `data_loader` and `data_processing` for the CRSP fund panel (WRDS): aggregate share classes to fund level; compute flow, fund momentum, Carhart abnormal returns (36-month loadings) → verify: unit tests on shape and dates; summary stats match paper (mean abnormal return ≈ −0.03%/month, sd ≈ 2.00%)
- [ ] 2. Add an availability-date field to every input and a guard that rejects features dated after the forecast date → verify: test that shifting a feature's date forward changes the output
- [ ] Data hygiene: keep dead funds; no outcome-based sample filter (do not require a return at t)
- [ ] Pull Carhart factors (Ken French) and Baker-Wurgler sentiment (as first released, or rebuilt monthly with data to date)

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
