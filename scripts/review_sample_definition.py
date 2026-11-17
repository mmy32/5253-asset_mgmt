"""Diagnostics for the open sample-definition questions (TODO section 2).

Reads D1a/D1b only. Works on share classes with at least one quarterly summary row in
the seven domestic-equity objective codes (an approximation of the panel's as-of rule).
Past returns are used only to describe who disappears; no target or portfolio result is
computed.

Usage: python scripts/review_sample_definition.py [raw_dir]
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.config.sample import ACTIVE_US_EQUITY_OBJ_CODES as CODES
from src.data_processing.fund_panel import EXCLUDED_NAME

B_COLS = ["crsp_fundno", "caldt", "fund_name", "index_fund_flag", "et_flag", "open_to_inv",
          "retail_fund", "inst_fund", "delist_cd", "first_offer_dt", "end_dt", "dead_flag",
          "merge_fundno", "sales_restrict", "crsp_obj_cd", "tna_latest"]
TERMS = re.sub(r"^\(|\)$", "", EXCLUDED_NAME).split("|")


def pct(a: float, b: float) -> str:
    return f"{a:,.0f} / {b:,.0f} ({100 * a / b:.1f}%)" if b else "n/a"


def filter_review(s: pd.DataFrame) -> None:
    print("\n== A. Fund-type filter (quarterly summary rows in the seven codes) ==")
    name = s.fund_name.fillna("")
    flagged = s.index_fund_flag.notna() | s.et_flag.notna()
    hit = name.str.contains(EXCLUDED_NAME, case=False, regex=True)
    print(f"rows {len(s):,}; name-excluded {pct(hit.sum(), len(s))}")
    print(f"name-excluded and already index/ETF-flagged: {pct((hit & flagged).sum(), hit.sum())}")
    print("by term (rows containing the term; share also flagged index/ETF):")
    for t in TERMS:
        m = name.str.contains(t, case=False, regex=True)
        print(f"  {t:20s} {m.sum():>8,}  flagged {100 * (m & flagged).sum() / max(m.sum(), 1):5.1f}%")
    parts = name.str.partition(":")
    in_fund = parts[2].str.contains(EXCLUDED_NAME, case=False, regex=True)
    in_trust = parts[0].str.contains(EXCLUDED_NAME, case=False, regex=True)
    has_colon = parts[1] == ":"
    trust_only = in_trust & ~in_fund & has_colon
    print(f"hit only in the trust/family part of the name: {pct(trust_only.sum(), hit.sum())}; "
          f"not index/ETF-flagged: {pct((trust_only & ~flagged).sum(), trust_only.sum())}")
    print(f"  top trusts: {parts[0][trust_only & ~flagged].value_counts().head(5).to_dict()}")
    only = s[hit & ~flagged]
    for t in ("index", "bond", "global", "technology", "sector"):
        m = only.fund_name.fillna("").str.contains(t, case=False)
        print(f"  sample names with '{t}' and no index flag: "
              f"{only[m].fund_name.drop_duplicates().sample(min(6, m.sum()), random_state=0).tolist()}")
    unflagged_index = s[(~hit) & flagged]
    print(f"index/ETF-flagged rows NOT caught by name: {pct(len(unflagged_index), flagged.sum())}")
    codes = s.groupby("crsp_fundno").crsp_obj_cd.nunique()
    print(f"classes with >1 of the seven codes over time: {pct((codes > 1).sum(), len(codes))}")


def universe_review(b: pd.DataFrame, s: pd.DataFrame, r: pd.DataFrame, ids: set[str]) -> None:
    print("\n== B. Who was in the universe ==")
    s = s.assign(year=s.caldt.str[:4])
    ye = s[s.caldt.str[5:7] == "12"].groupby("year").agg(
        classes=("crsp_fundno", "nunique"), dead_at_pull=("dead_flag", lambda x: (x == "Y").mean()))
    print("year-end classes and share flagged dead at pull time:")
    print(ye.iloc[::3].round(3).to_string())
    last = b.sort_values("caldt").groupby("crsp_fundno").last()
    cls = last.loc[last.index.isin(ids)]
    print(f"classes in sample {len(cls):,}; dead at pull {pct((cls.dead_flag == 'Y').sum(), len(cls))}")
    r = r[r.crsp_fundno.isin(ids)].assign(ret_date=lambda x: pd.to_datetime(x.caldt))
    fo = pd.to_datetime(cls.first_offer_dt).rename("first_offer")
    r = r.join(fo, on="crsp_fundno")
    pre = r.ret_date < r.first_offer
    print(f"class-months with a return dated before first_offer_dt: {pct(pre.sum(), r.first_offer.notna().sum())}")
    print(f"class-months with TNA missing: {pct(r.mtna.isna().sum(), len(r))}; "
          f"TNA < 5m: {pct((r.mtna < 5).sum(), r.mtna.notna().sum())}; "
          f"< 1m: {pct((r.mtna < 1).sum(), r.mtna.notna().sum())}")
    a = r.groupby("crsp_fundno").ret_date.min()
    gap = (a - fo.reindex(a.index)).dt.days.dropna()
    print(f"days from first_offer_dt to first monthly record: median {gap.median():.0f}, "
          f"p10 {gap.quantile(.1):.0f}, p90 {gap.quantile(.9):.0f}")


def investability_review(b: pd.DataFrame, ids: set[str]) -> None:
    print("\n== C. Could an investor really buy these? (latest summary row per class) ==")
    last = b.sort_values("caldt").groupby("crsp_fundno").last()
    c = last.loc[last.index.isin(ids)].copy()
    c["tna"] = pd.to_numeric(c.tna_latest, errors="coerce")
    n = len(c)
    print(f"classes {n:,}")
    for col in ("open_to_inv", "retail_fund", "inst_fund", "sales_restrict"):
        print(f"  {col}: {c[col].value_counts(dropna=False).to_dict()}")
    both = c.groupby([c.retail_fund.fillna("?"), c.inst_fund.fillna("?")]).agg(
        classes=("tna", "size"), tna=("tna", "sum"))
    both["tna_share"] = (both.tna / both.tna.sum()).round(3)
    print("retail x institutional flags:\n" + both.to_string())
    dead = c[c.dead_flag == "Y"]
    print(f"dead classes {len(dead):,}: delisting code {dead.delist_cd.value_counts(dropna=False).to_dict()}")
    merged = dead[dead.delist_cd == "M"]
    has_succ = merged.merge_fundno.notna()
    in_b = merged.merge_fundno.isin(b.crsp_fundno.unique())
    print(f"merged classes with a successor fund number {pct(has_succ.sum(), len(merged))}; "
          f"successor present in D1b {pct(in_b.sum(), len(merged))}; "
          f"successor itself in the sample {pct(merged.merge_fundno.isin(ids).sum(), len(merged))}")
    print("minimum investment, loads and 12b-1 are not in D1a/D1b: cannot be tested here")


def missingness_review(b: pd.DataFrame, r: pd.DataFrame, ids: set[str]) -> None:
    print("\n== D. Is disappearing random? (trailing past return, not future outcomes) ==")
    r = r[r.crsp_fundno.isin(ids)].copy()
    r["m"] = pd.to_datetime(r.caldt).dt.to_period("M")
    r = r.dropna(subset=["mret"])
    last_m = r.groupby("crsp_fundno").m.max()
    wide = r.pivot_table(index="m", columns="crsp_fundno", values="mret", aggfunc="first")
    wide = wide.reindex(pd.period_range(wide.index.min(), wide.index.max(), freq="M"))
    trail = np.expm1(np.log1p(wide.where(wide > -1)).rolling(12, min_periods=12).sum())
    tna = r.pivot_table(index="m", columns="crsp_fundno", values="mtna", aggfunc="first").reindex(wide.index)
    horizon = wide.index.max() - 12
    rows = []
    last = b.sort_values("caldt").groupby("crsp_fundno").last().delist_cd
    for t in trail.index[trail.index <= horizon]:
        x = trail.loc[t].dropna()
        if len(x) < 50:
            continue
        gone = last_m.reindex(x.index) <= t + 12
        reason = last.reindex(x.index).fillna("none")
        rank = x.rank(pct=True)
        rows.append(pd.DataFrame({"gone": gone.values, "reason": reason.values,
                                  "rank": rank.values, "tna": tna.loc[t].reindex(x.index).values,
                                  "year": t.year}))
    d = pd.concat(rows)
    d["grp"] = np.where(~d.gone, "survives 12m", "vanishes within 12m: " + d.reason)
    out = d.groupby("grp").agg(class_months=("rank", "size"), mean_rank=("rank", "mean"),
                               median_tna=("tna", "median"))
    print("trailing-12m return rank within month (0.5 = average) by what happens next:")
    print(out.round(3).to_string())
    print(f"vanishing share of class-months by year (all reasons):\n"
          f"{d.groupby('year').gone.mean().round(3).iloc[::4].to_string()}")


def main(raw: Path) -> None:
    b = pd.read_csv(raw / "D1b_CRSP_fund_summary.csv", usecols=B_COLS, dtype=str, encoding="latin-1")
    r = pd.read_csv(raw / "D1a_CRSP_monthly_returns.csv", dtype={"crsp_fundno": str, "caldt": str},
                    na_values=["R", "T", "N", ""])
    for col in ("mret", "mtna"):
        r[col] = pd.to_numeric(r[col], errors="coerce")
    s = b[b.crsp_obj_cd.isin(CODES)].drop_duplicates(["crsp_fundno", "caldt"])
    filter_review(s)
    hit = s.fund_name.fillna("").str.contains(EXCLUDED_NAME, case=False, regex=True)
    kept = s[~hit & s.index_fund_flag.isna() & s.et_flag.isna()]
    ids = set(kept.crsp_fundno)
    print(f"\nsample classes (pass code, name, index and ETF screens at any quarter): {len(ids):,}")
    universe_review(b, s, r, ids)
    print(f"D1a classes with no D1b row: {pct((~r.crsp_fundno.drop_duplicates().isin(b.crsp_fundno)).sum(), r.crsp_fundno.nunique())}")
    investability_review(b, ids)
    missingness_review(b, r, ids)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw"))
