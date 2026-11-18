# TODO

**Goal:** Find out whether we can predict which mutual funds will do well, using only information an investor would actually have had at the time. We test this by "replaying history" month by month, always leaving a delay between when data is dated and when we assume it was public. Then we check whether a simple buy-only portfolio would have made money after costs.

**Scope:** We use only fund-level and fund-family information (money flows, recent returns). We do not use what funds hold. A stricter test using the data exactly as it looked back then is a possible later extension.

**Plan documents:** [v1](reports/2026-11-12-research-protocol-v1.md) is the original plan. [v2](reports/2026-11-17-research-protocol-v2.md) changes the sample rules and adds the missing-outcome method below. Pause for review after each major milestone.

**Where we are (2026-11-17):** The v2 panel is built, the missing-outcome method is decided, frozen and checked, and coverage clears the 90% rule in 80 to 81 of 81 months. The spread is run and awaits your review (Part C1): about +22 bps a month on abnormal return, about +2 bps (no evidence) on net return. The neural network has been run under setup A and learned almost nothing; ridge on the same ten inputs does better (Part C2).

---

## Part A. Done

### A1. Plan written before looking at results

- [X] Saved the study plan: inputs (money flows and recent returns, no sentiment), monthly calendar, and three setups (A: random splits, B: replay in order, C: replay in order with extra-cautious delays).
- [X] Fixed the testing details in advance: dates, tuning, uncertainty, rebalancing, example trading costs, how to pick one share class per fund.
- [X] Checked the data is complete and the assumed release dates are reasonable. Any later change gets saved as a new plan version before evaluation.
- [X] Noted what is unverified: what the data looked like on release day, and whether a retail investor could buy these funds.

### A2. Clean fund dataset and why outcomes are missing

- [X] Matched share classes to funds and funds to groups, using only information available at the time.
- [X] Counted every fund-month in the shared date range (666,430) and sorted each: outcome on time (295,308), late (2,550), or missing. See the [panel validation report](reports/2026-11-16-panel-validation.md).
- [X] Checked whether funds with missing outcomes look different, by year and fund type.
- [X] Chose the dataset and market-factor source. Both factor sources agree. Tested for timing errors, double-counted returns and later edits to source files.
- [X] Recorded the test window: 81 months (2019-02 to 2025-10). In v1, 82,539 fund-months have all inputs, and every month has at least 20 usable funds.

### A3. Reviews that led to v2

Findings are packaged in the [point-in-time response](reports/2026-11-17-pit-challenge-response.md).

- [X] **Data revisions:** No source gives a publication date per observation. CRSP notes confirm repeated corrections to returns, fund size, fees and class groups, with no sizes given. See the [summary](reports/2026-11-17-crsp-release-notes-summary.md) and [full review](reports/2026-11-17-data-publication-and-revision-review.md). The size of the changes is unmeasured.
- [X] **Missing group labels:** About 74% of ungrouped funds look like genuine single-class funds. Decided: count them as their own funds.
- [X] **Fund-type filter:** The name screen removes 9.0% of rows. About 4,800 rows from 195 funds were dropped only because the fund *family* name had a banned word. Decided: use the paper's six name words on the fund part of the name only. See the [sample-definition review](reports/2026-11-17-sample-definition-review.md).
- [X] **Who was in the universe:** Dead funds are included (61.6% of sample classes are dead today). 25% of class-months have under 5 million in assets. Decided: 5 million fund-size floor.
- [X] **Could an investor really buy these?** Set aside as not a concern for this study. No retail-only rule. For the record: about 44% of assets sit in institutional-only classes and 14% of classes are closed to new money.
- [X] **Missing is not random:** Confirmed. Funds that vanish within a year had weaker prior returns (rank 0.39 to 0.42 vs 0.51) and are far smaller (median 2.6 to 11.7 million vs 50.6). Dropping them likely biases results upward.
- [X] **Possible true gaps:** About 8% of ungrouped funds share a portfolio number with other classes. Decided: keep them as their own funds, flag them, and report a sensitivity that drops them.

### A4. v2 panel built

- [X] Settled fund identity: each class follows its own history and joins a group only from the date the group is known.
- [X] Built the single-class rule, name rule, size floor and shared-portfolio flag, with tests.
- [X] Rebuilt both panels. The v1 rebuild reproduces every registered v1 count. Fingerprints are saved in the v2 settings.
- [X] Compared v1 and v2 ([comparison](reports/2026-11-17-v1-v2-panel-comparison.md)): v2 has about a third more funds (5,294 to 7,343) and feature-complete evaluation rows (82,539 to 110,677). The share missing a target falls slightly (2.75% to 2.26%). Every month still has missing outcomes.

### A5. First history-replay test (v1 panel)

- [X] Built two predictors: a "recent winners" ranking and a simple statistical model (ridge regression) using money flows and recent returns. Each month: rank funds, split into ten groups, record outcomes observed. Retrained in time order, tuned only on past data. See the [baseline report](reports/2026-11-16-chronological-baseline.md).
- [X] **Result: the top-minus-bottom spread cannot be estimated.** No month has complete outcomes for both the top and bottom group. This is a coverage failure, not evidence for or against predictability. This finding stays on record.
- [X] Measured what was missing and why ([selected coverage](reports/2026-11-16-selected-coverage.md)). Funds that stop appearing have ended. For 234 of 239 missing-expense cases, the data exists but arrived later than we assumed ([source recovery review](reports/2026-11-16-source-recovery-review.md)). Nothing recovered yet.

### A6. Earlier groundwork

- [X] Research proposal and project structure. Data audit and first fund-only dataset, built with tests ([audit](reports/2026-11-09-data-audit.md), [fund panel](reports/2026-11-09-fund-panel.md)).
- [X] Loaders for the first four sources (D1a, D1b, D2, D3). Data overlaps 1999-03 to 2025-12.
- [X] D5 (holdings) is incomplete and blocked; D5, D6 and D7 are not needed for this scope. The data provider's release versions are still unrecorded.

---

## Part B. The new question

**Same question as the paper and v1: does the top predicted decile beat the bottom predicted decile?** We keep it, but treat missing outcomes differently, because v1 could not estimate the spread at all. Decided 2026-11-17 and recorded in the [v2 protocol](reports/2026-11-17-research-protocol-v2.md). It runs on the v2 panel.

1. **90% coverage rule (main estimate).** A group counts as observed in a month if at least 90% of its weight has an outcome. Rescale weights over the observed funds. A month counts only if both top and bottom pass. Failed months are listed, not silently dropped.
2. **Missing-outcome sensitivity (alongside).** Use the month's observed 5th and 95th percentiles as low and high fills for missing outcomes. A range above zero means the sign survives those scenarios; more extreme missing outcomes could still reverse it. This range does not measure sampling uncertainty.
3. **Two targets, reported separately, never combined:**
   - **Abnormal return** (the paper's target): return beyond what market, size, value and momentum exposure explain. Needs expense ratios and 30 months of history. Missing weight in the top group: about 2.15%.
   - **Net return** (what an investor kept after fees): needs neither. Missing weight in the top group: about 0.96%.

**Why this design:** the missing funds are smaller and had weaker returns, so looking at observed funds only probably overstates results. The threshold gives one number. The bounds show how far it could move if the missing funds did badly.

**Confirmed for v2:** use 5th/95th percentile fills and report both targets separately, with neither designated primary. The original v1 hypothesis stays on abnormal return.

---

## Part C. Still to do

### C1. Finish the missing-outcome work (comes first)

- [X] **Run the v2 sample sensitivities:** Done. Adding "global" removes 51 funds (0.7%). Dropping the 5 million floor adds 12% more funds and raises the missing share from 2.26% to 2.42%. Dropping flagged funds removes about 5% of fund-months and leaves the missing share unchanged. No variant fixes the coverage problem: every month still has missing outcomes. See the [sensitivity report](reports/2026-11-17-v2-sensitivities.md).
- [X] **Write down the risks:** Done, 14 risks with direction, handling and what is left. Main points: funds that vanish are weaker, so observed-only results are probably too high; the 5th/95th fill values are plausible, not guaranteed, extremes; the model trains only on funds with outcomes, which the bounds do not fix. See the [risks report](reports/2026-11-17-missing-outcome-risks.md).
- [X] **Freeze before testing:** Done. Settings, code hashes, config hashes, panel hashes and input hashes are saved in `configs/research_protocol_v2.json` under `freeze`. The note says v1 results were already seen, so this is not blind.
- [X] **Check the mechanics:** Done. 60 tests pass. The run stops on error if decile weights do not sum to one, a month lacks ten deciles, or a training label is dated after its decision. All passed on the real v2 panel.
- [X] **Report the overlap:** Done. With the 90% rule, 80 of 81 months pass for abnormal return (longest run 46) and 81 of 81 for net return. The one failing month, 2022-12, has the bottom decile at 89.66% observed. Mean coverage is 97% to 99% per decile. v1 had zero such months. See the [overlap report](reports/2026-11-17-v2-overlap.md).
- [X] **Run the spread:** Done, after you confirmed the 5th/95th fills and both targets. Abnormal return: top beats bottom by about 22 bps a month (95% interval −0.2 to +36 bps, one-sided p 0.005), and the bounds on the mean (7 to 30 bps) stay above zero. Net return: about +2 bps, interval −31 to +29 bps, p 0.44, bounds include zero, so no evidence of an after-fee gain. Ridge and momentum rank funds almost identically (rank correlation 0.9999), so flow adds nothing linearly. See the [results](reports/2026-11-17-v2-spread-results.md).

**Review follow-up before C2:**

1. Pin both protocol files and verify the reviewed runner, frozen code and registered panel before evaluation. Keep the original run at commit `833cb71`.
2. Add an uncertainty sensitivity that uses all passing months, including isolated ones, and report it alongside the original bootstrap without changing the spread or the 90% rule.
3. Describe the 5th/95th fills as conditional scenarios. Verify the changes with tests, then rerun on the exact registered v2 database and compare the original and sensitivity results before C2.

### C2. Reproducing the paper with a neural network (largest remaining gap)

Decided 2026-11-17: the setup A/B/C comparison and the long-only after-fee portfolio test are dropped. The network is evaluated under **setup A only**, the paper's design (random three-fold splits). It was run on 2026-11-17; see the [setup A results](reports/2026-11-17-setup-a-network-results.md).

The paper ([Kaniel, Lin, Pelger, Van Nieuwerburgh](research/MACHINE-LEARNING%20THE%20SKILL%20OF%20MUTUAL%20FUND%20MANAGERS.pdf)) uses a neural network on 59 predictors plus a sentiment index. We now have the network and 10 of the inputs.

| Piece | Paper | We have now | What is left |
|---|---|---|---|
| Model | One hidden layer, 64 ReLU units | **Built** in `src/models/neural_net.py` (numpy, no new dependency), with a numerical gradient check | Run it |
| Tuning | 144 candidate settings: 1 to 3 layers, 32 or 64 first-layer units, dropout, learning rate, two regularizers | **Built.** Same 144 settings, one fit each, picked on the validation fold | Run it. Dropout "0.90, 0.95" is read as the probability of keeping a unit |
| Stability | Average of 8 fits from different random starts | **Built.** The chosen setting is refit 8 times (seeds 5253 to 5260) and averaged | Run it |
| Fund and family inputs | 3 momentum + 5 fund + 5 family characteristics | **10 inputs:** flow, 12-2 momentum, prior-month abnormal return, size, expense ratio, turnover (fund), and family fund count, family size, family flow, family momentum. The three family averages use whichever sibling funds have a value; the all-siblings rule is dropped (`src/models/family_features.py`). Ranked within each month, no imputation. 306,103 complete rows | Fund age and the remaining paper family inputs are not built. Sub-floor siblings do not count, because the family inputs are built from the panel |
| Holdings inputs | 46 stock characteristics weighted by fund holdings | None. Holdings pull is incomplete (D5), no accounting data (D7) | **Out of scope.** The paper says flow and momentum carry nearly all the signal, so this is a stated limitation |
| Sentiment | Baker-Wurgler index; the network uses it to amplify flow and momentum when sentiment is high | Loaded (D3), not used | Add as a labeled extension. The index is revised with later data, so it is not strictly real-time |
| Evaluation | Random 3-fold splits (training can include later months) | **Built** in `src/models/setup_a.py`, reusing the registered folds, the 90% coverage rule, bounds and bootstrap | Run it. Departure: features are the panel's lagged versions, not the same-month flow v1 describes for setup A. Only the training scheme follows setup A |
| Comparator | Linear models | **Built.** Ridge on the same 10 inputs, same folds, same rows | Run it |
| Target | Next-month abnormal return, and net return directly | **Built.** Separate models for each target, each evaluated on its own target only | Run it |
| Portfolio | Deciles weighted by prediction strength | Equal-weighted deciles | Optional. Needs a weight formula and tie rules written down first |
| Headline results | Top decile +72%, bottom −119% cumulative abnormal return. About 50 bps per month spread from flow, momentum and sentiment alone | Not comparable | Do not force a match. These are two separate figures, not one spread |

**Order of work for the network:**

- [X] **Add the remaining fund and family inputs:** Done (10 inputs, see the table). Family inputs use any sibling with a value, which raises family momentum from 92k to 493k rows. Built at model time from the panel, so the frozen panel and code hashes are untouched. On the pre-floor fund table the relaxed version matches the strict one exactly where the strict one exists.
- [X] **Build setup A (random folds):** Done, with tests that test months never enter training or validation and that test rows are not chosen by whether their outcome exists.
- [X] **Build the network:** Done, with the 144-setting grid, early stopping and the 8-fit average. Training settings not given in the paper (batch size 1024, at most 30 epochs, patience 3, Adam) are in `configs/neural_net_v2.json`.
- [X] **Fair comparison, same inputs:** Done. Ridge uses the same 10 inputs, folds and rows.
- [X] **Register and freeze before running:** Done. Hashes are in `configs/research_protocol_v2.json` under `neural_network_extension`, with a note that the two-input spread had already been seen.
- [X] **Run setup A:** Done (25 minutes). The network learned almost nothing: validation loss barely moved across the 144 settings. On abnormal return it earns about 10 bps a month against 18 bps for ridge on the same ten inputs. Ridge's interval and bounds are above zero. On net return the network collapsed to a constant prediction in 30 of 81 months, so its −11 bps is an artefact of the fund-ID tie rule. Ridge's net-return spread (13 bps) is not distinguishable from zero. See the [results](reports/2026-11-17-setup-a-network-results.md).
- [ ] **Decide whether to retrain the network:** Any fix is post hoc and must be labelled. Candidates: drop the 0.1 learning rate, train longer, trim or rank the target, treat constant-prediction months as unranked.
- [ ] **Fair comparison, with sentiment:** Add a simpler linear model with flow-times-sentiment and momentum-times-sentiment terms, so we do not credit the network for gains a simple model also delivers.
- [ ] **Look inside the network:** Which inputs matter, and whether sentiment interactions appear, as the paper reports.
- [ ] **Check how long predictability lasts:** The paper reports about three years.

### C3. Extensions and write-up

- [ ] **Weighting by strength (optional):** Needs a formula and tie rules first.
- [ ] **Robustness checks:** A small, pre-chosen set: delays, fund matching, return cutoffs.
- [ ] **Record data versions:** Which data release we used, if the provider lists it.
- [ ] **Optional extra data:** Economic-activity index (D4) and the eight-factor inputs (D8). Record versions and rerun checks.
- [ ] **Write the paper:** Sample counts at each step, coverage, comparisons, missing outcomes, confidence intervals, how many variations we tried, and the limitations.
