# TODO

**Goal:** Find out whether we can predict which mutual funds will do well, using only information an investor would actually have had at the time. We test this by "replaying history" month by month, always leaving a delay between when data is dated and when we assume it was public. Then we check whether a simple buy-only portfolio would have made money after costs.

**Scope:** We use only fund-level and fund-family information (things like money flowing in and out, and recent returns). We do not use what funds hold. A stricter test using the exact data as it looked back then is a possible later extension.

The plan is written up in `reports/2026-11-12-research-protocol-v1.md`, with one change (single-class funds) in `reports/2026-11-17-research-protocol-v2.md`. Pause for review after each major milestone.

## 1. Write down the plan before looking at results — done

- [X] Save the study plan: which information we use (money flows and recent returns, no investor-sentiment data), the monthly calendar, and three comparison setups (A: random splits, B: replaying history in order, C: replaying history with extra-cautious delays).
- [X] Fix the testing details in advance: dates, how the model is tuned, how we measure uncertainty, how often we rebalance, example trading costs, and how we pick one share class per fund for a retail investor.
- [X] Check the data is complete and the assumed release dates are reasonable. Any later change to the plan gets saved as a new version before we evaluate anything.
- [X] Note what is still unverified: what the data looked like on the day it was released, and whether a retail investor could really buy these funds.

## 2. Build the clean fund dataset and find out why outcomes are missing — done, decisions pending

- [X] Match share classes to funds and funds to groups. We use the latest information that was available at the time, never information from the future.
- [X] Count every fund-month in the shared date range (666,430) and sort each into a category: outcome arrived on time (295,308), outcome arrived late (2,550), or outcome missing. See the [panel validation report](reports/2026-11-16-panel-validation.md).
- [X] Check whether funds with missing outcomes look different from the rest, by year and by fund type. Decide how to handle funds that merged or closed.
- [X] Choose the dataset and the source for the market-factor data. Confirm both factor sources agree, and test for timing errors, double-counted returns and later edits to the source files.
- [X] Record the test window: 81 months, with 82,539 fund-months that have all the inputs we need. Every month has at least 20 usable funds. Some outcomes are missing (2,268 fund-months have no future outcome, and 1,441 have no net return).

**Still to review before we evaluate anything.** If any of these makes us change the plan, save it as a new version first. The findings are packaged in the [point-in-time response](reports/2026-11-17-pit-challenge-response.md).

- [X] **Data revisions:** Reviewed what each source publicly says about release dates and corrections. No source gives a publication date per observation, and the CRSP notes confirm repeated corrections to returns, TNA, fees and class groups, with no sizes given. See the [summary](reports/2026-11-17-crsp-release-notes-summary.md) and [full review](reports/2026-11-17-data-publication-and-revision-review.md). The size of the changes is still unmeasured.
- [X] **Missing group labels:** Some share classes have no group assigned. About 74% of ungrouped funds look like genuine single-class funds. Decision made: count them as their own funds (protocol v2). The rule is built and tested; the rebuild is listed in section 3.5.
- [X] **Fund-type filter:** Reviewed. The name screen removes 9.0% of rows in our fund types. About 4,800 rows from 195 funds are dropped only because the fund *family* name contains a banned word (such as "Sector Funds"). The index flags catch more than the name does. Our name list is also broader than the paper's. See the [sample-definition review](reports/2026-11-17-sample-definition-review.md). A fix is a decision, listed in 3.5.
- [X] **Who was in the universe:** Reviewed. The data include dead funds (61.6% of sample classes are dead today), so it is not survivors only. 2.7% of class-months carry a return dated before the fund's start date, and 25% have under 5 million in assets. We cannot tell when each fund first appeared in the database. See the [review](reports/2026-11-17-sample-definition-review.md). A minimum-size rule is a decision, listed in 3.5.
- [X] **Could an investor really buy these?** Reviewed and set aside: not a concern for this study, so no retail-only rule will be added. For the record: about 44% of assets sit in institutional-only classes and 14% of classes are closed to new money, and the panel ignores both. 97% of merged classes name a successor, but the data do not say what shareholders received. Minimum investments and loads are not in our files, so those cannot be tested. See the [review](reports/2026-11-17-sample-definition-review.md). 
- [X] **Missing is not random:** Confirmed. Funds that vanish within a year had weaker prior-year returns (average rank 0.39 to 0.42 against 0.51 for survivors) and are far smaller (median 2.6 to 11.7 million against 50.6). Dropping them likely biases results upward. How to treat them is the question in 3.5. See the [review](reports/2026-11-17-sample-definition-review.md).

## 3. First real test: replay history in order — done, awaiting review

Results are in the [baseline report](reports/2026-11-16-chronological-baseline.md). Both models made predictions for all 81 months. But in no month do we have complete outcomes for both the top-ranked and bottom-ranked funds. So we cannot yet say whether the top beats the bottom. We will not loosen the rules just to get an answer.

- [X] Build two predictors: a simple "recent winners" ranking, and a basic statistical model using money flows and recent returns. Each month, rank funds, split them into ten equal groups, and record the funds in each group and how many outcomes we actually observed. The model is retrained in time order and tuned only on past data.

## 3.5 Deal with missing outcomes — next

First, apply the protocol v2 decision to count single-class funds as their own funds:

- [X] **Settle fund identity:** Decided: follow each class's own history and link it to a group only from the date the group is known.
- [X] **Decide the sample rules raised in section 2:** Decided and folded into v2: the paper's six name words matched on the fund part only, a 5 million fund-size floor, vanishing funds left missing with the gap reported, no retail-only rule. See the [v2 protocol](reports/2026-11-17-research-protocol-v2.md).
- [X] **Decide on possible true gaps:** About 8% of ungrouped funds share a portfolio number with other classes. Decided: keep them as their own funds, flag them, and report a sensitivity that drops them.
- [X] **Change the panel and test it:** (identity rule, name rule, size floor and the shared-portfolio-number flag are built and tested.) Build the single-class rule into the panel code, with tests.
- [ ] **Rebuild and record:** Rebuild the panel and save its new file fingerprints in the v2 settings.
- [ ] **Compare with v1:** Rerun the coverage and missing-outcome counts and report v1 and v2 side by side.

Then the missing-outcome work:

What we have learned so far:

- [X] For the top and bottom funds we picked, we measured how much was missing each month and why. See [selected coverage](reports/2026-11-16-selected-coverage.md). No new performance numbers were computed.
- [X] We traced where the missing outcomes went. Funds that stop appearing have simply ended. For 234 of 239 missing-expense cases, the expense data exists but arrived later than we assumed it would be public. See [source recovery review](reports/2026-11-16-source-recovery-review.md). Nothing has been recovered yet.

What is left:

- [ ] **Decide the new question:** Pick a follow-up question we can honestly answer with partial data, and say how we will treat the missing funds.
- [ ] **List the options:** Compare the choices, such as looking only at funds we can observe, or rescaling the weights to cover the gap, or requiring a minimum share of observed funds.
- [ ] **Write down the risks:** State the assumptions and how the gaps could bias the answer.
- [ ] **Keep the original result:** The original "can't be estimated" finding stays on record.
- [ ] **Freeze before testing:** Save the new plan and the exact input files before looking at any new results. Note that we have already seen the original results.
- [ ] **Check the mechanics:** Test the timing and the weights before running anything.
- [ ] **Report the overlap:** Show how many months have outcomes for both the top and bottom groups.
- [ ] **Only claim what the data supports:** Run the uncertainty analysis only if its requirements are met. If coverage can't be repaired credibly, say plainly that the question is unanswered.

**Pause for review:** Stop before running the follow-up. Review the proposed method and its weaknesses first.

## 4. Compare setups and check real-world profit

- [ ] **Compare setups A, B and C:** Keep the inputs, the target and the test dates the same wherever possible. Report month-by-month differences between A and B and between B and C, how much training data each used, and how many funds ended up in each.
- [ ] **Test the buy-only portfolio:** Use real returns after fees for retail investors. Decide how we pick one share class per fund and whether the fund is open to new money. Also decide on minimum investments, trading volume, sales charges and exit fees.
- [ ] **Be honest about investability:** If we cannot confirm an investor could actually buy these funds, call the result an "after-fees return estimate", not a real portfolio.
- [ ] **Compare against simple alternatives:** Test against a passive index fund and against an equal-weighted basket of all eligible active funds.
- [ ] **Report the full picture:** Show missing weights, risk-adjusted returns, month-by-month uncertainty and the size of the effect. Do not subtract annual fees twice.

## 5. Extensions and write-up

- [ ] **Add more inputs:** Bring in more fund and family information, and a small neural network inspired by the paper.
- [ ] **Fair comparison for the network:** Compare it with a simpler model that also uses investor sentiment, so we do not credit complexity for gains that a simpler model could also deliver.
- [ ] **Weighting by strength (optional):** Weighting funds by how strongly they are predicted is secondary. It needs a formula and tie-handling rules written down first.
- [ ] **Robustness checks:** Run a small, pre-chosen set of checks on the delays, the fund matching and the return cutoffs.
- [ ] **Record data versions:** Note which data release we used, if the data provider lists them.
- [ ] **Optional extra data:** Get the economic-activity index (D4) and the extra eight-factor inputs (D8), note their versions and rerun the checks.
- [ ] **Write the paper:** Include the sample count at each step, coverage, comparisons, costs, missing outcomes, confidence intervals, how many variations we tried, and the limitations.
- [ ] **Do not force-match the original paper:** The paper reports +72% for its top group and −119% for its bottom group over time. Those are two separate figures, not a single top-minus-bottom gap, so we should not try to reproduce them.

## Done so far

- [X] Research proposal and project structure created. Milestones 2 and 3 were pushed in commit `6912ad0`.
- [X] Data audit and a first fund-only dataset, built with tests. Reports: `reports/2026-11-09-data-audit.md` and `reports/2026-11-09-fund-panel.md`. The data overlaps from 1999-03 to 2025-12, and the delayed dataset starts in 1999-06.
- [X] Data loaders for the first four sources (D1a, D1b, D2, D3), a rough fund-type filter and the shared date range. The filter finds 2,739,850 share-class months through 2025-12, after dropping 16 returns above 100%. This is a diagnostic check, not the final dataset.
- [X] D5 is incomplete and blocked, but D5, D6 and D7 are not needed for this scope. The data provider's release versions are still unrecorded.
- [X] The baseline was run, and its top-minus-bottom result cannot be estimated under our missing-data rule.
