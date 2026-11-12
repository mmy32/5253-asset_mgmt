"""Column names, missing-value codes and encodings of the raw data files (see DATA.md)."""

# D1a: CRSP monthly returns, NAV, TNA. A letter code in a numeric column means missing.
D1A_ID = "crsp_fundno"
D1A_DATE = "caldt"
D1A_MISSING_CODES = {"mret": "R", "mtna": "T", "mnav": "N"}
D1A_NUMERIC = tuple(D1A_MISSING_CODES)

# D1b: CRSP fund summary (quarterly). Only the columns the pipeline uses.
D1B_ENCODING = "latin-1"
D1B_ID = "crsp_fundno"
D1B_DATE = "caldt"
D1B_DATE_COLUMNS = (D1B_DATE, "first_offer_dt", "end_dt")
D1B_TEXT_COLUMNS = (
    D1B_ID,
    "crsp_cl_grp",
    "crsp_obj_cd",
    "fund_name",
    "mgmt_cd",
    "mgmt_name",
    "dead_flag",
    "summary_period2",
)
D1B_NUMERIC_COLUMNS = ("exp_ratio", "turn_ratio")
D1B_COLUMNS = D1B_TEXT_COLUMNS + D1B_DATE_COLUMNS + D1B_NUMERIC_COLUMNS

# D2: Ken French factor files. Values are in percent.
D2_FACTOR_COLUMNS = ("Mkt-RF", "SMB", "HML", "RF")
D2_MOMENTUM_COLUMN = "Mom"
D2_MISSING_VALUES = (-99.99, -999.0)
D2_PERCENT_DIVISOR = 100.0

# D3: Baker-Wurgler sentiment workbook.
D3_SHEET = "DATA"
D3_DATE = "yearmo"
D3_SENTIMENT_COLUMNS = ("SENT", "SENT_ORTH")
