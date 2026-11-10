"""Construct an assumption-based fund-month panel from CRSP share classes.

Only D1a/D1b and, for returns and targets, D2 are read. Source data are never
rewritten. The output is a research backtest, not proof of first-release PIT data.
"""
from __future__ import annotations

import argparse
import calendar
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd


# Paper Appendix A fallback codes; CRSP's domestic cap/style hierarchy takes precedence.
SI_CODES = "'AGG','GMC','GRI','GRO','ING','SCG'"
LIPPER_CODES = ("'EIEI','G','LCCE','LCGE','LCVE','MCCE','MCGE','MCVE',"
                "'MLCE','MLGE','MLVE','SCCE','SCGE','SCVE'")
WBR_CODES = "'G','G-I','AGG','GCI','GRI','GRO','LTG','MCG','SCG'"
EXCLUDED_NAME = (r"(international|global|foreign|emerging market|balanced|bond|"
                 r"money market|index|sector|real estate|healthcare|technology|"
                 r"financial services|natural resources|precious metal)")


def read_factors(path: Path, momentum: bool = False) -> pd.DataFrame:
    """Read only six-digit monthly rows; factor inputs are percent, not decimal."""
    import csv

    records: list[tuple[Any, ...]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream):
            if not row or len(row[0].strip()) != 6 or not row[0].strip().isdigit():
                continue
            raw = row[0].strip()
            year, month = int(raw[:4]), int(raw[4:])
            if month < 1 or month > 12:
                raise ValueError(f"Invalid factor month {raw}")
            count = 1 if momentum else 4
            if len(row) < count + 1:
                raise ValueError(f"Incomplete factor row {raw}")
            values = [float(value.strip()) for value in row[1:count + 1]]
            values = [np.nan if v in (-99.99, -999.0) else v / 100 for v in values]
            records.append((date(year, month, calendar.monthrange(year, month)[1]), *values))
    names = ["month", "mom"] if momentum else ["month", "mkt", "smb", "hml", "rf"]
    result = pd.DataFrame.from_records(records, columns=names)
    if result.empty or result.month.duplicated().any():
        raise ValueError(f"Empty or duplicate monthly factor data in {path}")
    return result


def abnormal_returns(frame: pd.DataFrame) -> pd.DataFrame:
    """Estimate prior-36-calendar-month loadings; never use the current return."""
    data = frame.sort_values(["fund_id", "return_month"]).reset_index(drop=True).copy()
    factors = ["mkt", "smb", "hml", "mom"]
    beta_values = np.full((len(data), 4), np.nan)
    abnormal = np.full(len(data), np.nan)
    counts = np.zeros(len(data), dtype=int)
    for _, group in data.groupby("fund_id", sort=False):
        positions = group.index.to_numpy()
        months = pd.to_datetime(group.return_month).dt.to_period("M").astype("int64").to_numpy()
        x = group[factors].to_numpy(dtype=float)
        y = (group.gross_return - group.rf).to_numpy(dtype=float)
        valid = np.isfinite(y) & np.isfinite(x).all(axis=1)
        for j in range(len(group)):
            first = np.searchsorted(months, months[j] - 36)
            history = np.arange(first, j)
            history = history[valid[history]]
            counts[positions[j]] = len(history)
            if len(history) < 30:
                continue
            design = np.column_stack((np.ones(len(history)), x[history]))
            beta, _, rank, _ = np.linalg.lstsq(design, y[history], rcond=None)
            if rank == 5:
                beta_values[positions[j]] = beta[1:]
                if valid[j]:
                    abnormal[positions[j]] = y[j] - x[j] @ beta[1:]
    data["abnormal_return"] = abnormal
    data["beta_observations"] = counts
    for i, name in enumerate(factors):
        data["beta_" + name] = beta_values[:, i]
    return data


def make_tables(db: duckdb.DuckDBPyConnection, raw: Path, cfg: dict[str, Any]) -> None:
    """Import only columns needed for the research universe and panel."""
    summary = raw / "D1b_CRSP_fund_summary.csv"
    returns = raw / "D1a_CRSP_monthly_returns.csv"
    print("Reading quarterly fund attributes...", flush=True)
    db.execute("""
        CREATE TABLE summary AS
        WITH raw AS (
          SELECT crsp_fundno, try_cast(caldt AS DATE) AS caldt, crsp_cl_grp,
            crsp_obj_cd, si_obj_cd, lipper_class, lipper_obj_cd, wbrger_obj_cd,
            fund_name, index_fund_flag, et_flag, mgmt_cd,
            try_cast(exp_ratio AS DOUBLE) AS exp_ratio,
            try_cast(turn_ratio AS DOUBLE) AS turn_ratio,
            try_cast(fiscal_yearend AS DATE) AS fiscal_yearend
          FROM read_csv(?, all_varchar=true, encoding='utf-8', sample_size=1000)
        ), numbered AS (
          SELECT *, count(*) OVER (PARTITION BY crsp_fundno, caldt) AS same_date_rows,
            row_number() OVER (PARTITION BY crsp_fundno, caldt ORDER BY crsp_fundno) AS n
          FROM raw
        )
        SELECT *, caldt + ? * INTERVAL '1 day' AS available_at
        FROM numbered WHERE n=1 AND caldt IS NOT NULL
    """, [str(summary), cfg["summary_lag_days"]])
    db.execute("""
      CREATE TABLE fees AS
      WITH dated AS (
        SELECT crsp_fundno, caldt AS fee_summary_date, fiscal_yearend,
          exp_ratio, turn_ratio,
          greatest(available_at, fiscal_yearend + ? * INTERVAL '1 day') AS fee_available_at
        FROM summary WHERE same_date_rows=1 AND fiscal_yearend IS NOT NULL
          AND (exp_ratio IS NOT NULL OR turn_ratio IS NOT NULL)
      )
      SELECT * EXCLUDE (rn) FROM (
        SELECT *, row_number() OVER (
          PARTITION BY crsp_fundno, fee_available_at ORDER BY fee_summary_date DESC
        ) AS rn FROM dated
      ) WHERE rn=1
    """, [cfg["fiscal_lag_days"]])
    print("Reading monthly share-class returns...", flush=True)
    db.execute("""
        CREATE TABLE class_returns AS
        WITH raw AS (
          SELECT crsp_fundno, try_cast(caldt AS DATE) AS source_return_date,
            last_day(try_cast(caldt AS DATE)) AS return_month,
            try_cast(mtna AS DOUBLE) AS tna, try_cast(mret AS DOUBLE) AS net_return
          FROM read_csv(?, all_varchar=true, sample_size=1000, nullstr=['','R','T','N'],
            types={'crsp_fundno':'VARCHAR','caldt':'VARCHAR','mtna':'VARCHAR','mret':'VARCHAR'})
        ), lags AS (
          SELECT *, lag(return_month) OVER w AS previous_month,
            lag(tna) OVER w AS previous_tna
          FROM raw WINDOW w AS (PARTITION BY crsp_fundno ORDER BY return_month)
        )
        SELECT *, last_day(return_month + INTERVAL 1 MONTH) AS formation_date,
          CASE WHEN last_day(previous_month + INTERVAL 1 MONTH)=return_month
                    AND previous_tna >= 0 THEN previous_tna END AS lag_tna
        FROM lags WHERE return_month IS NOT NULL
    """, [str(returns)])
    duplicate = db.execute("""
      SELECT crsp_fundno, return_month FROM class_returns
      GROUP BY 1,2 HAVING count(*)>1 LIMIT 1
    """).fetchone()
    if duplicate is not None:
        raise ValueError(f"Duplicate share-class economic month: {duplicate}")
    # ASOF chooses the latest available quarterly observation for each class and date.
    print("Applying availability and universe rules...", flush=True)
    db.execute(f"""
        CREATE TABLE classes AS
        WITH joined AS (
          SELECT r.*, s.caldt AS summary_date, s.available_at AS summary_available_at,
            s.same_date_rows, s.crsp_cl_grp, s.crsp_obj_cd, s.si_obj_cd, s.lipper_class,
            s.lipper_obj_cd, s.wbrger_obj_cd, s.fund_name, s.index_fund_flag, s.et_flag,
            s.mgmt_cd, f.fiscal_yearend, f.fee_summary_date, f.fee_available_at,
            CASE WHEN date_diff('day',f.fee_summary_date,r.formation_date) <= ?
                 AND f.exp_ratio >= 0 THEN f.exp_ratio END AS expense_ratio,
            CASE WHEN date_diff('day',f.fee_summary_date,r.formation_date) <= ?
                 AND f.turn_ratio >= 0 THEN f.turn_ratio END AS turnover_ratio
          FROM class_returns r ASOF LEFT JOIN summary s
            ON r.crsp_fundno=s.crsp_fundno AND r.formation_date>=s.available_at
          ASOF LEFT JOIN fees f
            ON r.crsp_fundno=f.crsp_fundno AND r.formation_date>=f.fee_available_at
          WHERE r.formation_date BETWEEN ? AND ?
        ), classified AS (
          SELECT *, CASE
            WHEN summary_date IS NULL THEN 'no_available_summary'
            WHEN date_diff('day', summary_date, formation_date) > ? THEN 'stale_summary'
            WHEN same_date_rows > 1 THEN 'ambiguous_summary'
            WHEN crsp_cl_grp IS NULL OR trim(crsp_cl_grp)='' THEN 'missing_class_group'
            WHEN coalesce(index_fund_flag,'') IN ('B','D','E') THEN 'index_fund'
            WHEN coalesce(et_flag,'') IN ('F','N') THEN 'exchange_traded'
            WHEN regexp_matches(lower(coalesce(fund_name,'')), ?) THEN 'excluded_name'
            WHEN crsp_obj_cd IS NOT NULL AND trim(crsp_obj_cd)<>'' AND NOT
              (left(crsp_obj_cd,3) IN ('EDC','EDY') AND crsp_obj_cd NOT IN ('EDYH','EDYS'))
              THEN 'other_objective'
            WHEN (crsp_obj_cd IS NULL OR trim(crsp_obj_cd)='') AND NOT
              (coalesce(si_obj_cd,'') IN ({SI_CODES}) OR
               coalesce(lipper_class,'') IN ({LIPPER_CODES}) OR
               coalesce(lipper_obj_cd,'') IN ({LIPPER_CODES}) OR
               coalesce(wbrger_obj_cd,'') IN ({WBR_CODES})) THEN 'unknown_objective'
            ELSE 'selected' END AS universe_status
          FROM joined
        ) SELECT * FROM classified
    """, [cfg["fee_max_age_days"], cfg["fee_max_age_days"], cfg["formation_start"],
            cfg["formation_end"], cfg["summary_max_age_days"], EXCLUDED_NAME])
    print("Aggregating eligible share classes to funds...", flush=True)
    db.execute("""
        CREATE TABLE fund_base AS
        SELECT crsp_cl_grp AS fund_id, return_month, formation_date,
          formation_date AS return_assumed_available_at,
          count(*) AS share_classes,
          count(*) FILTER (WHERE lag_tna IS NULL) AS classes_missing_lag_tna,
          count(*) FILTER (WHERE tna IS NULL OR tna<0) AS classes_missing_tna,
          count(*) FILTER (WHERE net_return IS NULL OR net_return < -1) AS classes_missing_return,
          count(*) FILTER (WHERE net_return > 1) AS classes_return_above_one,
          count(*) FILTER (WHERE index_fund_flag IS NULL OR index_fund_flag='') AS index_flag_blank,
          count(*) FILTER (WHERE et_flag IS NULL OR et_flag='') AS et_flag_blank,
          CASE WHEN count(*) FILTER (WHERE tna IS NULL OR tna<0)=0 THEN sum(tna) END AS tna,
          CASE WHEN count(*) FILTER (WHERE lag_tna IS NULL)=0 AND sum(lag_tna)>0
                    AND count(*) FILTER (WHERE lag_tna>0 AND
                       (net_return IS NULL OR net_return < -1))=0
            THEN sum(CASE WHEN lag_tna>0 THEN lag_tna * net_return ELSE 0 END)/sum(lag_tna)
          END AS net_return,
          CASE WHEN count(*) FILTER (WHERE lag_tna IS NULL)=0 AND sum(lag_tna)>0
                    AND count(*) FILTER (WHERE lag_tna>0 AND expense_ratio IS NULL)=0
            THEN sum(CASE WHEN lag_tna>0 THEN lag_tna * expense_ratio ELSE 0 END)/sum(lag_tna)
          END AS expense_ratio,
          CASE WHEN count(*) FILTER (WHERE lag_tna IS NULL)=0 AND sum(lag_tna)>0
                    AND count(*) FILTER (WHERE lag_tna>0 AND turnover_ratio IS NULL)=0
            THEN sum(CASE WHEN lag_tna>0 THEN lag_tna * turnover_ratio ELSE 0 END)/sum(lag_tna)
          END AS turnover_ratio,
          CASE WHEN count(*) FILTER (WHERE lag_tna IS NULL OR tna IS NULL OR tna<0)=0
                    AND sum(lag_tna)>0 AND count(*) FILTER (WHERE lag_tna>0 AND
                      (net_return IS NULL OR net_return < -1))=0
            THEN sum(tna - lag_tna * (1+coalesce(net_return,0)))/sum(lag_tna)
          END AS flow,
          CASE WHEN count(DISTINCT mgmt_cd)=1 AND count(mgmt_cd)=count(*)
            THEN min(mgmt_cd) END AS family_id,
          max(summary_date) AS latest_summary_date,
          max(summary_available_at) AS latest_summary_available_at,
          max(fee_available_at) AS latest_fee_available_at
        FROM classes WHERE universe_status='selected'
        GROUP BY crsp_cl_grp, return_month, formation_date
    """)
    db.execute("""
        CREATE TABLE funds AS
        WITH exclusions AS (
          SELECT crsp_cl_grp, formation_date,
            count(*) FILTER (WHERE universe_status<>'selected') AS known_excluded_classes
          FROM classes WHERE crsp_cl_grp IS NOT NULL GROUP BY 1,2
        ), base AS (
          SELECT f.* EXCLUDE (flow), f.flow AS raw_flow,
            CASE WHEN net_return <= ? THEN f.flow END AS flow,
            e.known_excluded_classes, net_return > ? AS return_above_cutoff,
            CASE WHEN net_return <= ? THEN net_return + expense_ratio/12 END AS gross_return
          FROM fund_base f JOIN exclusions e
            ON f.fund_id=e.crsp_cl_grp AND f.formation_date=e.formation_date
        ), family AS (
          SELECT *, count(*) OVER w-1 AS family_fund_count,
            CASE WHEN count(tna) OVER w=count(*) OVER w
              THEN sum(tna) OVER w-tna END AS family_tna,
            CASE WHEN count(*) OVER w>1 AND count(flow) OVER w=count(*) OVER w
                      AND count(tna) OVER w=count(*) OVER w
                      AND sum(tna) OVER w-tna>0
              THEN (sum(flow*tna) OVER w-flow*tna)/(sum(tna) OVER w-tna) END AS family_flow
          FROM base
          WINDOW w AS (PARTITION BY formation_date, family_id)
        )
        SELECT * EXCLUDE (family_fund_count, family_tna, family_flow),
          CASE WHEN family_id IS NOT NULL THEN family_fund_count END AS family_fund_count,
          CASE WHEN family_id IS NOT NULL THEN family_tna END AS family_tna,
          CASE WHEN family_id IS NOT NULL THEN family_flow END AS family_flow
        FROM family
    """, [cfg["max_fund_return"]] * 3)


def add_targets(db: duckdb.DuckDBPyConnection, raw: Path, cfg: dict[str, Any]) -> None:
    """Construct realized abnormal returns and attach next-month outcomes without filtering."""
    directory = raw / "D2_Carhart_factors"
    factors = read_factors(directory / "D2_Carhart_factors_research.csv").merge(
        read_factors(directory / "D2_Carhart_factors_momentum.csv", momentum=True),
        on="month", how="inner", validate="one_to_one",
    )
    db.register("factor_input", factors)
    # Include future target months even if a fund later leaves the eligible universe.
    data = db.execute("""
        WITH months AS (
          SELECT fund_id, return_month FROM funds
          UNION
          SELECT fund_id, last_day(formation_date + INTERVAL 1 MONTH) FROM funds
        )
        SELECT m.fund_id, m.return_month, f.gross_return,
          k.mkt, k.smb, k.hml, k.mom, k.rf
        FROM months m LEFT JOIN funds f
          ON m.fund_id=f.fund_id AND m.return_month=f.return_month
        LEFT JOIN factor_input k ON m.return_month=k.month
        ORDER BY m.fund_id, m.return_month
    """).df()
    print(f"Estimating rolling factor loadings for {len(data):,} fund-months...", flush=True)
    columns = ["fund_id", "return_month", "abnormal_return", "beta_observations",
               "beta_mkt", "beta_smb", "beta_hml", "beta_mom"]
    db.register("abnormal_input", abnormal_returns(data)[columns])
    db.execute("CREATE TABLE abnormal AS SELECT * FROM abnormal_input")
    # Freeze the selected class membership at formation. Do not filter outcomes by
    # future objective codes, future group mappings, or whether the fund survives.
    db.execute("""
      CREATE TABLE outcomes AS
      WITH rows AS (
        SELECT c.crsp_cl_grp AS fund_id, c.formation_date, r.crsp_fundno AS observed_class,
          r.lag_tna, r.net_return,
          CASE WHEN date_diff('day', f.fee_summary_date, r.formation_date) <= ?
                    AND f.exp_ratio >= 0 THEN f.exp_ratio END AS expense_ratio
        FROM classes c LEFT JOIN class_returns r
          ON c.crsp_fundno=r.crsp_fundno
          AND r.return_month=last_day(c.formation_date + INTERVAL 1 MONTH)
        ASOF LEFT JOIN fees f
          ON r.crsp_fundno=f.crsp_fundno AND r.formation_date>=f.fee_available_at
        WHERE c.universe_status='selected'
      )
      SELECT fund_id, formation_date,
        count(*) FILTER (WHERE observed_class IS NULL) AS future_classes_missing,
        CASE WHEN count(*) FILTER (WHERE observed_class IS NULL OR lag_tna IS NULL)=0
                  AND sum(lag_tna)>0 AND count(*) FILTER (WHERE lag_tna>0 AND
                    (net_return IS NULL OR net_return < -1))=0
          THEN sum(CASE WHEN lag_tna>0 THEN lag_tna*net_return ELSE 0 END)/sum(lag_tna)
        END AS target_net_return,
        CASE WHEN count(*) FILTER (WHERE observed_class IS NULL OR lag_tna IS NULL)=0
                  AND sum(lag_tna)>0 AND count(*) FILTER (WHERE lag_tna>0 AND
                    (net_return IS NULL OR net_return < -1 OR expense_ratio IS NULL))=0
                  AND sum(CASE WHEN lag_tna>0 THEN lag_tna*net_return ELSE 0 END)/sum(lag_tna)<=?
          THEN sum(CASE WHEN lag_tna>0 THEN lag_tna*(net_return+expense_ratio/12)
                        ELSE 0 END)/sum(lag_tna) END AS target_gross_return
      FROM rows GROUP BY 1,2
    """, [cfg["fee_max_age_days"], cfg["max_fund_return"]])
    db.execute("""
      CREATE TABLE panel AS
      WITH current AS (
        SELECT f.*, a.abnormal_return AS prior_month_abnormal_return,
          a.beta_observations AS prior_beta_observations,
          avg(a.abnormal_return) OVER (
            PARTITION BY f.fund_id ORDER BY f.return_month
            RANGE BETWEEN INTERVAL 10 MONTH PRECEDING AND CURRENT ROW
          ) AS momentum_mean,
          count(a.abnormal_return) OVER (
            PARTITION BY f.fund_id ORDER BY f.return_month
            RANGE BETWEEN INTERVAL 10 MONTH PRECEDING AND CURRENT ROW
          ) AS momentum_observations
        FROM funds f LEFT JOIN abnormal a
          ON f.fund_id=a.fund_id AND f.return_month=a.return_month
      )
      , momentum AS (
        SELECT * EXCLUDE (momentum_mean),
          CASE WHEN momentum_observations>=8 THEN momentum_mean END AS momentum_12_2
        FROM current
      ), with_family AS (
        SELECT *, CASE WHEN family_id IS NOT NULL AND family_fund_count>0
          AND count(tna) OVER w=count(*) OVER w
          AND count(momentum_12_2) OVER w - CASE WHEN momentum_12_2 IS NULL THEN 0 ELSE 1 END
              = count(*) OVER w - 1
          AND sum(tna) OVER w-tna>0
          THEN (sum(coalesce(momentum_12_2*tna,0)) OVER w-coalesce(momentum_12_2*tna,0))
                / (sum(tna) OVER w-tna) END AS family_momentum_12_2
        FROM momentum WINDOW w AS (PARTITION BY formation_date, family_id)
      )
      , outcomes_with_alpha AS (
        SELECT o.*, b.beta_observations AS target_beta_observations,
          o.target_gross_return - k.rf - (b.beta_mkt*k.mkt + b.beta_smb*k.smb +
            b.beta_hml*k.hml + b.beta_mom*k.mom) AS next_month_abnormal_return
        FROM outcomes o LEFT JOIN abnormal b ON o.fund_id=b.fund_id
          AND b.return_month=last_day(o.formation_date + INTERVAL 1 MONTH)
        LEFT JOIN factor_input k ON k.month=last_day(o.formation_date + INTERVAL 1 MONTH)
      )
      SELECT with_family.*, target.target_net_return, target.target_gross_return,
        target.future_classes_missing,
        target.next_month_abnormal_return, target.target_beta_observations,
        CASE WHEN target.next_month_abnormal_return IS NOT NULL
          THEN last_day(with_family.formation_date + INTERVAL 2 MONTH) END AS target_assumed_available_at
      FROM with_family LEFT JOIN outcomes_with_alpha target
        ON with_family.fund_id=target.fund_id AND with_family.formation_date=target.formation_date
    """)


def build_panel(raw: Path, output: Path, config: dict[str, Any]) -> None:
    raw, output = raw.resolve(), output.resolve()
    if output.is_relative_to(raw):
        raise ValueError("Output directory must be outside the raw data directory")
    if date.fromisoformat(config["formation_start"]) > date.fromisoformat(config["formation_end"]):
        raise ValueError("Formation start must not follow formation end")
    for key in ("summary_lag_days", "fiscal_lag_days", "summary_max_age_days", "fee_max_age_days"):
        if not isinstance(config[key], int) or config[key] < 0:
            raise ValueError(f"{key} must be a nonnegative number of days")
    if not math.isfinite(config["max_fund_return"]) or config["max_fund_return"] < 0:
        raise ValueError("max_fund_return must be a finite nonnegative number")
    source_files = [raw / "D1a_CRSP_monthly_returns.csv", raw / "D1b_CRSP_fund_summary.csv",
                    raw / "D2_Carhart_factors/D2_Carhart_factors_research.csv",
                    raw / "D2_Carhart_factors/D2_Carhart_factors_momentum.csv"]
    missing = [str(path) for path in source_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing input files: {missing}")
    output.mkdir(parents=True, exist_ok=True)
    expected = ["fund_panel.duckdb", "fund_panel.parquet", "class_lineage.parquet",
                "universe_coverage.csv", "universe_coverage_monthly.csv", "fund_coverage.csv",
                "run_config.json"]
    if any((output / name).exists() for name in expected):
        raise FileExistsError(f"Output already exists in {output}; choose a new output directory")
    database = output / "fund_panel.duckdb"
    db = duckdb.connect(str(database))
    try:
        db.execute("SET memory_limit = ?", [config["memory_limit"]])
        db.execute("SET threads = ?", [config["threads"]])
        make_tables(db, raw, config)
        add_targets(db, raw, config)
        print("Writing panel, class lineage, and coverage reports...", flush=True)
        for table, filename in (("panel", "fund_panel.parquet"),
                                ("classes", "class_lineage.parquet")):
            db.execute(f"COPY {table} TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
                       [str(output / filename)])
        for period, filename in (("year(formation_date)", "universe_coverage.csv"),
                                 ("formation_date", "universe_coverage_monthly.csv")):
            db.execute(f"""
              COPY (SELECT {period} AS period, universe_status, count(*) AS class_months
                    FROM classes GROUP BY 1,2 ORDER BY 1,2) TO ? (HEADER, DELIMITER ',')
            """, [str(output / filename)])
        db.execute("""
          COPY (SELECT year(formation_date) AS year, count(*) AS fund_months,
              count(DISTINCT fund_id) AS funds, count(net_return) AS valid_net_returns,
              count(tna) AS valid_tna, count(flow) AS valid_flow,
              count(expense_ratio) AS valid_expense, count(gross_return) AS valid_gross_return,
              count(prior_month_abnormal_return) AS valid_prior_abnormal,
              count(momentum_12_2) AS valid_momentum,
              count(family_momentum_12_2) AS valid_family_momentum,
              count(next_month_abnormal_return) AS valid_next_month_targets,
              sum(classes_return_above_one) AS class_returns_above_one,
              count(*) FILTER (WHERE return_above_cutoff) AS fund_returns_above_cutoff,
              count(*) FILTER (WHERE known_excluded_classes>0) AS partial_known_groups
            FROM panel GROUP BY 1 ORDER BY 1) TO ? (HEADER, DELIMITER ',')
        """, [str(output / "fund_coverage.csv")])
        checks = db.execute("""
          SELECT count(*) FILTER (WHERE summary_available_at>formation_date),
            count(*) FILTER (WHERE formation_date<=return_month),
            count(*) FILTER (WHERE fee_available_at>formation_date)
          FROM classes WHERE universe_status='selected'
        """).fetchone()
        if checks != (0, 0, 0):
            raise ValueError(f"Availability checks failed: {checks}")
        (output / "run_config.json").write_text(json.dumps(config, indent=2) + "\n")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim/fund_panel"))
    parser.add_argument("--config", type=Path, default=Path("configs/fund_panel.json"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    build_panel(args.raw_dir, args.output_dir, config)


if __name__ == "__main__":
    main()
