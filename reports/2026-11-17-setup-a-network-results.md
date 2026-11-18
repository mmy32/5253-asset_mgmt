# Setup A: neural network and ridge on ten inputs

Date: 2026-11-17. Run under the plan registered in `configs/research_protocol_v2.json` (`neural_network_extension`) with settings in `configs/neural_net_v2.json`. Command: `python -m src.models.setup_a --database data/interim/panels/v2/fund_panel.duckdb --output-dir data/interim/setup_a_v2`. Run time 25 minutes. Outputs (local, not in Git): `constituents.csv`, `tuning_log.csv`, `spread_by_month.csv`, `spread_summary.csv`, `manifest.json` (hashes).

**Setup A is the paper's design and is not a real-time test.** Months are split into three random folds; a model trains on one, tunes on another and is tested on the third, so training can use months after the test month. Features keep the panel's lagged timing.

## Answer in one paragraph

The network did not learn a usable signal. Its validation loss barely changed across all 144 settings, and its predictions are nearly flat. On abnormal return it ranks funds mostly by momentum and earns about half the spread of ridge on the same inputs (10 bps against 18 bps a month). On net return it collapsed to a constant prediction in 30 of 81 months. In those months the deciles were set by the fund-ID tie-break, so its negative net-return spread is an artefact, not a finding. Ridge on ten inputs gives a positive abnormal-return spread of about 18 bps a month, with an interval and bounds above zero. Its net-return spread of about 13 bps is not distinguishable from zero.

## Results

Same rules as the [v2 spread](2026-11-17-v2-spread-results.md): a month counts if both deciles are at least 90% observed. 95% moving-block bootstrap interval, one-sided p-value, and bounds on the mean spread from 5th/95th percentile fills over all 81 months. Each model is evaluated only on the target it was trained for. Basis points a month.

| Model | Target | Months passing | Mean spread | 95% interval | One-sided p | Bounds on mean |
|---|---|---:|---:|---|---:|---|
| Network | Abnormal return | 79 of 81 | 9.6 | −2.5 to 22.4 | 0.066 | 1.1 to 16.9 |
| Ridge (10 inputs) | Abnormal return | 78 of 81 | 18.1 | 9.3 to 31.7 | 0.002 | 8.9 to 24.2 |
| Network | Net return | 76 of 81 | −11.3 | −20.6 to 7.5 | 0.94 | −26.4 to −2.3 |
| Ridge (10 inputs) | Net return | 74 of 81 | 13.1 | −7.2 to 30.0 | 0.084 | −2.8 to 23.8 |

**The network net-return row should not be read as a result** (see the next section).

## What went wrong with the network

1. **It learned almost nothing.** Validation loss is measured on the training target's standardised scale, where predicting the training mean scores about 1. The best and worst of the 144 settings differ by about 0.3% in every rotation (for example 1.2168 to 1.2198). No fit diverged. Tuning was therefore choosing among near-identical, near-constant models.
2. **On net return it often collapsed to a constant.** All three net-return rotations picked a learning rate of 0.1. In 30 of 81 evaluation months every fund received the same score. The registered tie rule then sorts by fund ID, which puts single-class funds (IDs starting `S:`) in the top decile and grouped funds in the bottom decile. Those 30 months average −19.7 bps. The other 51 months average −6.0 bps. That remainder is not tested, and it comes from a model that barely fits.
3. **On abnormal return it mostly copies momentum.** Its scores have a mean monthly rank correlation of 0.62 with momentum and 0.80 with ridge, and its predictions are about a third as dispersed as ridge's. It is a weaker version of the linear model.

The likely causes are the training choices the paper does not state and we filled in ourselves: up to 30 epochs with patience 3, batch size 1024, an untrimmed target with heavy tails, and a learning rate of 0.1 kept in the grid. The paper's networks also train on a larger sample with holdings inputs. **None of these causes has been tested.**

## What ridge on ten inputs shows

- **Abnormal return: positive.** About 18 bps a month, with the interval (9 to 32 bps) and the bounds (9 to 24 bps) above zero. Its scores are still led by momentum (rank correlation 0.69), followed by prior-month abnormal return (0.34) and family momentum (0.24).
- **Net return: not distinguishable from zero.** About 13 bps a month. The interval and bounds both include zero. Its scores lean on size (0.34), family size (0.37), family fund count (0.27) and low expenses (−0.29), so it ranks large, cheap funds in big families highly.
- **Ridge chose the largest shrinkage (100) in all six fits.** With ranked inputs and about 100,000 training rows, an alpha of 100 is still almost no shrinkage, so this is effectively ordinary least squares.
- **Not comparable with the v2 spread.** The two-input momentum/ridge result (about 22 bps) used chronological training, two inputs and a larger sample. This one uses random folds, ten inputs and 306,103 complete rows. The difference between 18 and 22 bps says nothing by itself.

## Cautions

- **Setup A is retrospective.** Training may use later months, so these numbers are likely more favourable than a real-time version would be.
- **Departures from registered setup A.** The features use lagged timing, not same-month flow. The family inputs drop the all-siblings rule and are built from the panel, so siblings below the size floor do not count.
- **Not blind.** The v2 two-input spread had already been seen.
- **Many estimates.** There are four rows here, on top of the v2 spread. Nothing was rerun or changed after these results were seen.

## What would be needed to test the network properly

Any change from here is a post-hoc change and has to be labelled as one. Candidate changes:
- drop the 0.1 learning rate;
- train longer or with more patience;
- trim or rank the target before training;
- treat months with constant predictions as unranked instead of breaking ties by fund ID.
