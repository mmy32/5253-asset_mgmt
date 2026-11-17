# Milestone 3.5: source recovery review

The diagnostic joins frozen baseline constituents to class lineage, all stored class returns and summary/fee histories. It does not rerank funds or calculate new performance. The database and factor hashes are verified. Detailed requests for missing records remain local in `data/interim/selected_source_final/source_repair_requests.csv`; the output also records input and diagnostic-code hashes. Run the existing `src.data_processing.selected_coverage` command with a fresh output directory to reproduce.

## Findings

All absent selected future class observations are after the class's last recorded return in the export, not internal gaps. For ridge, the bottom and top deciles contain respectively 456 and 155 absent class-month observations (313 and 106 distinct classes). Momentum has 457 and 157 (314 and 108 classes). These counts overlap across models and repeated fund-months; they must not be summed as independent funds. There are also 13 bottom and 11 top class-months missing lagged TNA, and 18 bottom and four top with missing/invalid positive-weight returns in each model.

A terminal export observation does not establish closure, merger, liquidation proceeds or a successor. Existing records cannot supply the absent returns. Source repair requests must seek final class returns, asset balances and independently dated merger/liquidation evidence. Do not use pull-date termination fields to select funds or infer a zero outcome. D5 remains excluded.

For ridge, 109 bottom-decile and 117 top-decile class-month expense failures have no available fee record; another 12 bottom-decile failures have a stale record. Across both models there are 239 unique affected class-months. None has a valid fee record meeting the registered timing and staleness rules. However, 234 have a nonnegative expense on an unambiguous summary dated no later than the target month: their latest such expense is not yet assumed available at the target's current maturity date. Five have no such historical expense. These are potential delayed-label candidates, not 234 recovered fund targets: a fund may also lack another selected class's return, TNA or fee, and cutoff dates still apply.

## Recommended next design, pending review

Preserve v1 and its unestimable spread. Before selecting an observed-only estimator, investigate **later outcome-label maturity** as a versioned target-construction change. Later information may be used to measure a past outcome only if the label is withheld from training until all components are available. It must never change that past forecast's inputs, membership or weights. Define expense applicability to the target period, a maximum allowed delay and the final sample cutoff before evaluating performance; do not treat arbitrary later fee values as historical truth. Verify that delay does not simply move observations beyond the 2025-12 cutoff. Rebuild training-label availability, retune chronologically and reconcile to v1 under any approved follow-up. The existing 239 cases alone cannot establish the resulting portfolio coverage.

In parallel, pursue the terminal-class records and missing TNA/return values using the local source request list. The current extract does not justify inventing those outcomes. No external requests were sent.

If defensible recovery remains insufficient, an observed-constituent analysis can be proposed as a secondary diagnostic with explicit renormalization, prespecified coverage thresholds and missing-weight sensitivity analysis. It estimates the observed subset, not the original portfolio, and the bottom/top missingness asymmetry prevents a missing-at-random claim. Keep it separate from v1 H1 and from investable retail performance.

## Review gate

Source-level diagnosis is complete for the available stored export; actual data recovery and a new protocol are not complete. Review the delayed-label proposal and source acquisition needs before implementing v2 or examining revised performance. No alternative performance was calculated, no new protocol was frozen, and Milestone 4 has not started. Any v2 is a post-review follow-up, not an untouched preregistration.
