"""Test whether missing crsp_cl_grp in D1b reflects single-class funds.

CRSP's April 2024 release notes say nearly 60k crsp_cl_grp ids were removed
where only one share class exists. Prediction if that explains missing groups:
(1) no remaining group has a single member; (2) classes with a missing group
rarely share a crsp_portno with another class.

Usage: python scripts/check_class_group_singletons.py [D1b_path]
"""

import sys
from pathlib import Path

import pandas as pd

D1B = Path("data/raw/D1b_CRSP_fund_summary.csv")
COLS = ["crsp_fundno", "caldt", "crsp_cl_grp", "crsp_portno", "crsp_obj_cd"]


def latest_nonblank(d: pd.DataFrame, col: str) -> pd.Series:
    return d.dropna(subset=[col]).groupby("crsp_fundno")[col].last()


def main(path: Path) -> None:
    d = pd.read_csv(path, usecols=COLS, dtype=str, encoding="latin-1")
    d = d.sort_values(["crsp_fundno", "caldt"])
    f = pd.DataFrame(
        {
            "grp": latest_nonblank(d, "crsp_cl_grp"),
            "port": latest_nonblank(d, "crsp_portno"),
            "obj": latest_nonblank(d, "crsp_obj_cd"),
        }
    ).reindex(d["crsp_fundno"].unique())
    f["has_grp"] = f["grp"].notna()
    f["port_n"] = f["port"].map(f.dropna(subset=["port"]).groupby("port").size())

    print(f"funds {len(f):,}; with group {f.has_grp.sum():,}; missing {(~f.has_grp).sum():,}")
    sizes = f[f.has_grp].groupby("grp").size()
    print(f"groups {len(sizes):,}; single-member {(sizes == 1).sum():,}; 2+ {(sizes >= 2).sum():,}")
    print(f"funds in single-member groups: {(sizes == 1).sum():,}")

    subsets = {
        "all": f,
        "equity-domestic (ED*)": f[f["obj"].fillna("").str.startswith("ED")],
    }
    for label, g in subsets.items():
        for status, m in [("missing group", ~g.has_grp), ("has group", g.has_grp)]:
            s = g[m]
            print(
                f"[{label}] {status}: n={len(s):,}; no portno {s.port.isna().sum():,}; "
                f"portno shared {(s.port_n >= 2).sum():,}; portno unique {(s.port_n == 1).sum():,}"
            )

    miss = f[(~f.has_grp) & (f.port_n >= 2)]
    members = f.dropna(subset=["port"]).groupby("port").has_grp.agg(["sum", "size"])
    x = members.loc[miss["port"].unique()]
    print(
        f"portnos holding a missing-group fund and 2+ funds: {len(x):,}; "
        f"all members ungrouped {(x['sum'] == 0).sum():,}; some grouped {(x['sum'] > 0).sum():,}"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else D1B)
