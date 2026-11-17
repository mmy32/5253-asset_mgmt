# Milestone 3.5: selected-portfolio coverage diagnostic

This is the first step of Milestone 3.5, not a new performance evaluation. The v1 panel hash is verified, baseline constituents are read without reranking, and the output manifest records their hash. D5 is not read. Run `python -m src.data_processing.selected_coverage --raw-dir /path/to/raw --output-dir data/interim/selected-coverage-new`.

For ridge, mean monthly missing abnormal-return weight is 3.60% in the bottom decile and 2.14% in the top decile. First-applicable attribution is:

| Cause | Bottom weight | Top weight |
|---|---:|---:|
| Future selected class absent | 2.28% | 0.88% |
| Future weight unavailable | 0.06% | 0.05% |
| Future return missing or invalid | 0.11% | 0.02% |
| Future expense unavailable | 1.14% | 1.19% |

Counts are repeated fund-month holdings, not independent funds. The ridge bottom decile has 293 missing targets, the top 170; momentum has 295 and 171 respectively. None is first attributed to insufficient regression history. Missing bottom-decile targets have median formation TNA 88.0 versus 393.4 among observed targets, in source units; top-decile medians are 422.45 and 413.5. This asymmetry reinforces that an observed-only subset need not represent the original portfolio.

An older nonnegative fee record, already available and within the existing 730-day staleness limit, recovers **zero** missing positive-weight class expenses in either model's extreme deciles. This does not rule out recovery from additional verified source data, but the existing-file carry-forward sensitivity is insufficient. Absent class observations cannot be interpreted as a closure, merger or zero return without supporting event data.

Outputs under `data/interim/selected_coverage_v1/` contain monthly reason weights, overlap counts, formation comparisons and fee recovery counts. No new portfolio performance was calculated. The next step remains source-level investigation of absent classes, missing TNA/returns and expense records, including whether additional exports or independently dated event information are needed. No replacement missingness rule or follow-up protocol has been selected. Preserve v1 and do not proceed to matched performance evaluation on this evidence alone.
