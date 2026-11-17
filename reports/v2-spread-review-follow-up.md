# v2 spread review follow-up

1. Preserve the original run at `833cb71`. Verify the exact v1 and v2 protocol contents before evaluation. The [review manifest](../configs/v2_spread_review.json) pins the original v2 file and the reviewed code; the original v2 file pins the base protocol, panel and unchanged code.
2. Keep the original estimate and bootstrap columns. Add a separately labeled uncertainty sensitivity for the same equal-weighted mean of all passing months. It applies Gaussian multipliers to centered monthly spreads with Bartlett dependence over 12 calendar months (correlation decreases linearly to zero at lag 12). This gives an analytic normal interval and one-sided p-value without simulation. Gaps affect calendar distances; no missing month is filled as an outcome. Isolated passing months still contribute. The sensitivity keeps the minimum 12 consecutive passing months rule and reports no interval if estimated variance is zero. It is a post-review sensitivity conditional on passing months, so it does not address missing-fund bias or establish an out-of-sample finding.
3. Treat the 5th/95th percentile fills as conditional scenarios. Their range describes missing-return assumptions, separately from uncertainty about the estimated mean.

The reviewed runner writes the new `calendar_*` columns alongside the original columns. On the machine with the exact registered database, run:

```sh
python -m src.models.spread_report \
  --database data/interim/panels/v2/fund_panel.duckdb \
  --output-dir data/interim/spread_v2_review
```

Before C2, compare the four model/target rows to the original run. Confirm the passing-month counts, mean spreads, scenario ranges and original bootstrap results agree; then report the new intervals and p-values beside them. The registered database is absent from this checkout, so this comparison is pending.
