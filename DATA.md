# Data Master Document

Catalog of every data pull. Raw files go in `data/raw/` and are never edited. `data/` is gitignored, so this file is the record of what each pull is. Update an entry when a pull is made or redone.

Context: `reports/2026-10-22-research-proposal.md`, `TODO.md`.

## Summary

| ID | Dataset | Filename | Source | Data range |
|---|---|---|---|---|
| D1a | CRSP monthly returns, NAV, TNA | `D1a_CRSP_monthly_returns.csv` | [WRDS CRSP Mutual Funds: Monthly Returns](https://wrds-www-wharton-upenn-edu.proxy.library.cornell.edu/pages/get-data/center-research-security-prices-crsp/quarterly-update/mutual-funds/monthly-returns/) | 1976-01 to 2026-09 |
| D1b | CRSP fund summary (quarterly) | `D1b_CRSP_fund_summary.csv` | [WRDS CRSP Mutual Funds: Fund Summary](https://wrds-www-wharton-upenn-edu.proxy.library.cornell.edu/pages/get-data/center-research-security-prices-crsp/quarterly-update/mutual-funds/fund-summary/) | 1999-03 to 2026-09 |
| D2 | Carhart four factors + risk-free | `D2_Carhart_factors/` (4 files) | [Ken French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) | 1926-07 to 2026-09 |
| D3 | Baker-Wurgler sentiment | `D3_Baker_Wurgler_sentiment.xlsx` | [Wurgler site](https://pages.stern.nyu.edu/~jwurgler/) | 1958-01 to 2025-12 |
| D4 | CFNAI (optional) | not pulled | [Chicago Fed](https://www.chicagofed.org/research/data/cfnai/current-data) | not pulled |
| D5 | CRSP mutual fund portfolio holdings (instead of Thomson) | `D5_CRSP_mutual_fund_holdings.csv` | [WRDS CRSP Mutual Funds: Portfolio Holdings](https://wrds-www-wharton-upenn-edu.proxy.library.cornell.edu/pages/get-data/center-research-security-prices-crsp/quarterly-update/mutual-funds/portfolio-holdings/) (the LSEG S12 page, https://wrds-www-wharton-upenn-edu.proxy.library.cornell.edu/pages/get-data/lseg/mutual-fund-holdings-s12/, was tried and not used) | 2001-12 to 2026-08 in incomplete export (unused under Option A) |
| D6 | CRSP monthly stock returns | `D6_CRSP_monthly_stock_returns.csv` | [WRDS CRSP Monthly Stock File](https://wrds-www-wharton-upenn-edu.proxy.library.cornell.edu/pages/get-data/center-research-security-prices-crsp/monthly-update/stock-version-2/monthly-stock-file/) | 1976-01 to 2026-09 (unused under Option A) |
| D7 | Compustat/CRSP monthly security file | `D7_Compustat_monthly_security.csv` | [WRDS CRSP/Compustat Merged: Security Monthly](https://wrds-www-wharton-upenn-edu.proxy.library.cornell.edu/pages/get-data/center-research-security-prices-crsp/annual-update/crspcompustat-merged/security-monthly/) | 1976-06 to 2026-11 |
| D8 | Extra factors for eight-factor check | not pulled | TBD | not pulled |

## Entry template

Copy this block for each new dataset.

- **ID / name:**
- **Source and access path:** (database, library, table names, URL)
- **Variables pulled:**
- **Frequency:**
- **Requested date range:**
- **Actual date range returned:**
- **Filters applied at pull time:**
- **Pull date:**
- **Vendor vintage / release:** (WRDS update date, file version)
- **Query or script:** (path under `scripts/`)
- **Raw file(s):** (path under `data/raw/`, row count, checksum)
- **Availability-date rule:** (when each record becomes usable; feeds the point-in-time guard)
- **Known issues:** (missingness, revisions, coverage gaps)
- **Used by:** (research plan steps)

## Entries

### D1. CRSP Mutual Fund database
Split into sub-pulls by WRDS table. Both are downloaded. D1b starts 1999-03, so fund attributes (objective code, class group, family, fees, turnover) are missing for 1976 to 1998.

| Sub-pull | WRDS table | Contents | Status |
|---|---|---|---|
| D1a | `monthly_tna_ret_nav` | monthly return, NAV, TNA | Downloaded, 1976-01 to 2026-09 |
| D1b | `fund_summary2` | quarterly fund attributes (identifiers, class group, objective codes, fees, turnover, management company, fund status) | Downloaded, quarterly, 1999-03 to 2026-09 |

#### D1a. Monthly returns, NAV, TNA
- **Source and access path:** WRDS, `crsp_q_mutualfunds` product, library `crspq`, table `monthly_tna_ret_nav` (WRDS saved query "1 Monthly Returns and Net Asset Values", query form page 4733, revision 41773).
- **Variables pulled:** `mret` (total return per share, month end), `mnav` (monthly NAV per share), `mtna` (total net assets, month end). Key `crsp_fundno`; date variable `caldt`.
- **Frequency:** monthly
- **Requested date range:** 1976-01-01 to 2026-09-30 (re-pulled; the first query started 1980-01)
- **Actual date range returned:** 1976-01-30 to 2026-09-30, 609 month-ends
- **Filters applied at pull time:** none. Query method "search the entire database", no conditional statement, so all funds including dead ones are in the file. The paper's active U.S. equity filter must be applied later in `data_processing`, using D1b.
- **Output format:** uncompressed CSV, dates as `YYYY-MM-DD`. Columns: `caldt`, `crsp_fundno`, `mtna`, `mret`, `mnav`.
- **Pull date / vendor vintage:** downloaded 2026-11-06 (file timestamp). WRDS release not recorded; the factor files below were built on the 202609 CRSP database, so the data run through 2026-09.
- **Query or script:** WRDS web query form (parameters above). No script in `scripts/` yet.
- **Raw file(s):** `data/raw/D1a_CRSP_monthly_returns.csv`, 459 MB, 10,345,662 data rows, 76,080 distinct `crsp_fundno`, no duplicate (`crsp_fundno`, `caldt`) pairs. SHA-256 `2dd6772a0fa618ca473d9651ecde283c2f107012668832215acf74d17450d738`.
- **Availability-date rule:** TBD
- **Row counts by year:** 7,058 (1976), 8,393 (1980), 22,567 (1986), 141,478 (1996), 290,602 (2006), 355,100 (2025), 267,398 (2026 through September).
- **Known issues:**
  - **Codes in numeric columns:** `crsp_fundno` has leading zeros, so read it as text. `mret` holds the letter `R` in 94,191 rows and is blank in 255,841 (350,032 unusable in total, 3.4%). `mtna` holds `T` in 166,087 rows and is blank in 400,161. `mnav` holds `N` in 12,984 rows and is blank in 264,555. Treat these codes as missing. I have not looked up what each letter means in the CRSP documentation.
  - **Outliers:** `mret` ranges from −1.0 to 12,012.4, and 244 rows exceed 1. The paper removes only 11 fund-months with a raw return above 1, so this sample has many more; check whether these are data errors and what the paper's cleaning code would do with them.
  - **Coverage:** Coverage varies by field and period; CRSP revises history. TNA can be reported with a lag, which adds noise to flow.
  - **Share classes:** The file is at share-class level (`crsp_fundno`), so it needs aggregating to fund level using `crsp_cl_grp` from D1b. The documented D1b pull starts in 1999-03; `crsp_cl_grp` is present in 83.6% of its rows. Missing mappings require a sensitivity analysis.
  - **Net returns:** `mret` is net of fees. The paper uses gross returns, so expense ratios must be added back (see D1b).
- **Used by:** steps 1 to 9

#### D1b. Fund summary, quarterly, 1999 to 2026
- **Source and access path:** WRDS, `crsp_q_mutualfunds` product, library `crspq`, table `fund_summary2` (query form page 4735, revision 41779), quarterly period option.
- **Variables pulled:** the same 70 variables plus `summary_period2`, `crsp_fundno`, `caldt` (73 columns) as listed in the table above (descriptive, fund summary, capital gains, asset composition, fund style, fees).
- **Key and date variable:** `crsp_fundno`, `caldt`.
- **Frequency:** quarterly. `summary_period2` is `Q` in 2,227,316 rows and `AQ` in 721,789 rows (I have not looked up what `AQ` means; the 6 duplicate pairs may come from it).
- **Requested date range:** 1976-01-01 to 2026-09-30.
- **Actual date range returned:** 1999-03-31 to 2026-09-30, 111 quarter-ends. The table has no quarterly rows before 1999-03, so pre-1999 attributes are missing.
- **Filters applied at pull time:** none (whole database).
- **Output format:** CSV, read with `encoding="latin-1"`; read `crsp_fundno` and `crsp_portno` as text.
- **Pull date / vendor vintage:** downloaded 2026-11-06 (file timestamp). WRDS release not recorded.
- **Raw file(s):** `data/raw/D1b_CRSP_fund_summary.csv`, 1.5 GB, 2,949,105 data rows, 72,461 distinct `crsp_fundno`, 6 duplicate (`crsp_fundno`, `caldt`) pairs. SHA-256 `0e2edbd6d60d309320005d45d928ab6c34216ec0a138bd1a771aa33478d32b60`. This hash matches the first quarterly download (then named `CRSP Mutual Funds - Summary.csv`; later renamed to the current name), so it is the same data under a new filename.
- **Overlap with D1a:** 3,623 funds in D1a are not in D1b (likely funds that ended before 1999; not checked); 4 funds in D1b are not in D1a.
- **Availability-date rule:** TBD. `exp_ratio` and `mgmt_fee` apply as of `fiscal_yearend` but are published later, so a lag is needed.
- **Field coverage (non-missing rows):** `crsp_obj_cd` 96.9%, `mgmt_cd` 88.1%, `crsp_cl_grp` 83.6%, `first_offer_dt` 99.2%, `exp_ratio` 81.4%, `turn_ratio` 75.8%, `crsp_portno` 77.9%, `per_com` 84.4%, `fund_name` 99.3%.
- **Other profile:** `crsp_obj_cd` has 67 distinct codes and changes over time for 14,145 funds; `mgmt_cd` changes for 32,210 funds; `crsp_cl_grp` never changes within a fund. `exp_ratio` is an annual fraction (median 0.0099; mean 0.0108, or about 0.09% a month versus the paper's 0.097%), range −0.006 to 1.46, so there are outliers. `turn_ratio` median 0.49, maximum 1,188.7.
- **Known issues:**
  - **Look-ahead confirmed:** `dead_flag`, `end_dt`, `delist_cd` and `first_offer_dt` never change within a fund, so each describes the fund as of the pull date. Among rows with `dead_flag = Y`, 98.9% are dated before `end_dt`. Do not use these pull-date fields as predictors or to decide historical eligibility; retain dead funds and use only appropriately dated information for sample construction.
  - **Holdings link:** `crsp_portno` is empty for all of 1999 to 2002, 50.7% filled in 2005, 68.3% in 2008, 92.8% in 2011 and about 93% to 97% from 2014.
  - **Unused columns:** many columns (bond composition, maturity, 52-week NAV) are probably not needed for U.S. equity funds.
- **Used by:** steps 1, 2 and 9

### D2. Carhart four factors
- **Source and access path:** Ken French data library. Two files: "Fama/French 3 Factors" and "Momentum Factor (Mom)", both monthly, CSV.
- **Variables pulled:** `Mkt-RF`, `SMB`, `HML`, `RF` (research factors file); `Mom` (momentum file). Values are in percent, not decimals.
- **Frequency:** monthly (`YYYYMM`). Each file also has an annual section after the monthly rows, which must be excluded when parsing.
- **Requested date range:** full file
- **Actual date range returned:** research factors 1926-07 to 2026-09 (the file says "created using the 202609 CRSP database"); momentum 1927-01 to 2026-09.
- **Pull date / vendor vintage:** downloaded 2026-11-06 (zip file timestamp). French's own files are stamped 2026-10-26 inside the zips, and both were built on the 202609 CRSP database.
- **Raw file(s):**
  - `data/raw/D2_Carhart_factors/D2_Carhart_factors_research.zip`, SHA-256 `b03d39e4bb253dda0f14893db3b78e64b40b8d6549a0fc0fd4111dae84c98618`
  - `data/raw/D2_Carhart_factors/D2_Carhart_factors_research.csv`, SHA-256 `a3894d74d553cab812eabbe706bdbf443c97eb20b24b05e3e5f3ce47e46b90bb`
  - `data/raw/D2_Carhart_factors/D2_Carhart_factors_momentum.zip`, SHA-256 `27ed60e5b2caa9ea334a261cddfa864a9926f6bf45e9677c95dfd835c5abb315`
  - `data/raw/D2_Carhart_factors/D2_Carhart_factors_momentum.csv`, SHA-256 `81ff7cab5517159daa5a66c83fd90d4076a0864be2d5fef179719c0f9049a8cb`
  - Each zip was unzipped next to itself; the zips are kept. Original names: `F-F_Research_Data_Factors_CSV.zip`, `F-F_Momentum_Factor_CSV.zip`.
- **Availability-date rule:** TBD
- **Known issues:**
  - **Percent units:** divide by 100 to match CRSP returns in decimals.
  - **Missing values:** the momentum file marks missing data with −99.99 or −999. I did not scan for them in the range used here.
  - **Risk-free rate source:** the one-month T-bill rate comes from Ibbotson Associates until 2024-05 and from the ICE BofA US 1-Month Treasury Bill Index from 2024-06.
  - **Revisions:** French revises the factors when CRSP data change, so the history can differ between downloads; the download date is recorded above.
  - **Not a CRSP file:** these factors are separate from the WRDS pulls, so keep the vintage in mind when comparing them with D1a.
- **Used by:** steps 1, 3 to 9

### D3. Baker-Wurgler sentiment index
- **Source and access path:** Baker and Wurgler investor sentiment data. The README sheet says "UPDATED: March, 2026" and points to the GitHub repository `BWInvestorSentimentIndex/BakerandWurglerInvestorSentimentIndex`. I do not know the exact download URL.
- **Variables pulled:** sheet `DATA`, columns `yearmo`, `SENT`, `SENT_ORTH`, and the input series `pdnd`, `ripo`, `nipo`, `cefd`, `s`, `indpro`, `consdur`, `consnon`, `consserv`, `recess`, `employ`, `cpi`. Sheet `README` holds the notes.
- **Frequency:** monthly (`yearmo` as `YYYYMM`).
- **Actual date range returned:** 1958-01 to 2025-12 (816 monthly rows).
- **Pull date / vintage:** downloaded 2026-11-06 (file timestamp); the file itself is the March 2026 update.
- **Raw file(s):** `data/raw/D3_Baker_Wurgler_sentiment.xlsx`, 130 KB, SHA-256 `3580398aaba6b72ad988844416c7b0ac9caca24fd2ab1d9149a983ec63b9f7a2`.
- **Availability-date rule:** TBD (test a one-month and a longer lag).
- **Known issues:**
  - **Look-ahead:** the index is built with full-sample principal components and revised in each yearly update, so the published history uses information from after each date. This file is the March 2026 vintage, not the first release. The input series are included, but rebuilding with revised inputs would not by itself recover first-release vintages. The current primary experiment excludes sentiment and the revised index is reserved for a labeled extension.
  - **Missing inputs:** some input columns are blank in early rows, and the README notes that CPI is missing for 2025-10 because of the government shutdown.
  - **Excel format:** needs `openpyxl` or a CSV export to read in pandas; it is not installed in the Python 3.13 interpreter used so far.
  - **2026-11-09 audit:** 816 rows. `SENT` is missing in 90 rows, `SENT_ORTH` in 91 and CPI in one; other input missingness is in the machine-readable inventory.
- **Used by:** steps 3, 4, 6, 9

### D4. CFNAI (optional)
- **Source and access path:** Chicago Fed, Chicago Fed National Activity Index.
- **Frequency:** monthly
- **Requested date range:** full history (starts 1967)
- **Everything else:** TBD
- **Used by:** step 9 (alternative macro state)

### D5. CRSP mutual fund portfolio holdings (unused under Option A)
- **Source and access path:** WRDS CRSP Mutual Funds, Portfolio Holdings (see Summary). Replaces the Thomson/S12 holdings the paper uses; the S12 page was tried and not used.
- **Variables pulled:** `crsp_portno`, `report_dt`, `security_rank`, `eff_dt`, `percent_tna`, `nbr_shares`, `market_val`, `crsp_company_key`, `security_name`, `cusip`, `permno`, `permco`, `ticker`, `coupon`, `maturity_dt`.
- **Frequency:** quarterly or monthly report dates (308 distinct `report_dt`).
- **Actual date range returned:** `report_dt` 2001-12-31 to 2026-08-31.
- **Pull date:** downloaded 2026-11-08 (file timestamp). WRDS release not recorded.
- **Raw file:** `data/raw/D5_CRSP_mutual_fund_holdings.csv`, 591 MB, 5,418,660 data rows, 1,020 distinct `crsp_portno`. SHA-256 `af08347a23e5c2ab171429f02aa6a52e3440d047faee5ba4c770d3cc3122cbd4`.
- **Known issues:**
  - **Incomplete fund coverage:** all 1,020 portfolios link to D1b, but that is about 4.6% of the 15,651 portfolios D1b gives equity-domestic objective codes (`crsp_obj_cd` starting `ED`). Funds per year: 730 (2002), 996 (2003), 934 (2009), 846 (2010), then 15 to 18 from 2011 on. The pull looks like a fixed list of funds that mostly stopped reporting around 2010.
  - **Late start:** 2 funds in 2001, 730 in 2002. The paper's holdings start in 1980.
  - **Missingness:** `permno` blank in 27.1% of rows, `percent_tna` in 6.4%, `cusip` in 9.1%; `market_val` is exactly 0 in 15.1%. `eff_dt` differs from `report_dt` in 54.6% of rows.
- **Structural audit:** The final CSV record has 12 fields instead of 15; the export is truncated or incomplete. The 5,418,660 count includes that malformed record. Re-export or reconcile before use.
- **Status:** unusable as pulled and out of scope under Option A. Redo the pull if Option B is revived.
- **Used by:** none

### D6. CRSP monthly stock file (unused under Option A)
- **Source and access path:** WRDS CRSP Monthly Stock File (see Summary). Header uses the new CRSP flat-file naming (`PERMNO`, `MthRet`, `MthCap`, `YYYYMM`, and so on).
- **Frequency:** monthly
- **Actual date range returned:** `YYYYMM` 197601 to 202609, all 609 months, 39,606 `PERMNO`.
- **Pull date:** downloaded 2026-11-08 (file timestamp). Built on the 202609 CRSP database.
- **Raw file:** `data/raw/D6_CRSP_monthly_stock_returns.csv`, 2.3 GB, 4,523,123 data rows. SHA-256 `b90924dc732abacf3d0e9af562cf2a443718bf98e522a7bcc0b95c3aad255a00`.
- **Known issues:**
  - **Duplicates:** the remote data profile reports 52,927 repeated (`PERMNO`, `YYYYMM`) pairs associated with dividend records. Confirm row grain and preserve event information before any deduplication.
  - **Non-equity rows:** `SecurityType` is EQTY 3,714,473, FUND 772,763, DERV 4,866.
  - **Missingness and range:** `MthRet` blank in 1.6% of rows, range −1 to 39.
- **Status:** not needed under Option A.
- **Used by:** none

### D7. Compustat/CRSP monthly security file (merged link)
- **Source and access path:** WRDS. The variable list (`gvkey`, `liid`, `linkdt`, `linkenddt`, `linkprim`, `linktype`, `lpermno`, `lpermco`, plus Compustat security-monthly fields) matches the Compustat Security Monthly table joined to the CRSP-Compustat link table. I have not recorded the exact WRDS query form. The file is named "Compustat fundamentals", but it contains **no balance-sheet or income-statement items**.
- **Variables pulled (88 columns):**
  - *Link (8):* `gvkey`, `liid`, `linkdt`, `linkenddt`, `linkprim` (P/C/J/N), `linktype` (LC/LU), `lpermno`, `lpermco`.
  - *Identifiers and descriptors:* `iid`, `tic`, `cusip`, `conm`, `conml`, `cik`, `exchg`, `secstat`, `tpci`, `costat`, `dlrsn`, `dldte`, `ipodate`, `fic`, `loc`, `incorp`, `state`, `city`, `county`, address and contact fields (`add1` to `add4`, `addzip`, `phone`, `fax`, `weburl`, `ein`), `busdesc`, `fyrc`, `idbflag`, `stko`, `curr_sp500_flag`.
  - *Industry codes:* `sic`, `naics`, `gsector`, `ggroup`, `gind`, `gsubind`, `spcindcd`, `spcseccd`, `spcsrc`, `prican`, `prirow`, `priusa`.
  - *Monthly market data:* `prccm` (close), `prchm`, `prclm`, `trfm`, `trt1m` (total return), `cshtrm` (volume), `cshom` and `cshoq` (shares outstanding), `navm`, `ajexm`, `ajpm`, `rawpm`, `rawxm`, `adrrm`, dividend fields (`dvpspm`, `dvpsxm`, `dvrate`, `cheqvm`, `curcddvm`), `curcdm`, `csfsm`, `isalrt`, `primiss`, `mkvalincl`, `cmth`, `cyear`, `datadate`.
  - *S&P holdings fields:* `sph100`, `sphcusip`, `sphiid`, `sphmid`, `sphname`, `sphsec`, `sphtic`, `sphvg`.
- **Key and date variable:** (`gvkey`, `iid`) or `lpermno`, with `datadate` (monthly month-end).
- **Frequency:** monthly
- **Actual date range returned:** `datadate` 1976-06-30 to 2026-11-30 (606 distinct dates). The remote profile reports 5,935 October 2026 rows and 404 November 2026 rows after the September cutoff; November is later than the 2026-11-06 file timestamp.
- **Filters applied at pull time:** none recorded.
- **Output format:** CSV. Read with `dtype=str` for `gvkey`, `liid`, `lpermno`, `cusip`.
- **Pull date / vendor vintage:** downloaded 2026-11-06 (file timestamp). WRDS release not recorded.
- **Raw file(s):** `data/raw/D7_Compustat_monthly_security.csv`, 2.4 GB, 3,785,886 data rows, 28,574 `gvkey`, 29,172 `lpermno`, 28,486 `lpermco`. No duplicate (`gvkey`, `iid`, `datadate`) or (`lpermno`, `datadate`) pairs. SHA-256 `06c9018d00f8db05ba94475e81052c54ce3f289a17fb4b59f8f63bd0694db2a0`.
- **Row counts by year:** 26,795 (1976), 55,794 (1981), 72,063 (1986), 104,549 (1996), 78,246 (2006), 67,322 (2016), 74,560 (2025), 60,971 (2026).
- **Audit, 2026-11-09:** 404 records have `datadate` later than the documented 2026-11-06 file timestamp. All 3,785,886 records fall within their recorded link windows, treating `E` as open-ended for this diagnostic; vendor semantics still require confirmation.
- **Link table profile:** `linktype` LC 1,929,857 rows and LU 1,856,029; `linkprim` P 3,209,521, C 536,936, J 33,135, N 6,294. Every row has `linkdt` and `linkenddt` filled; confirm vendor semantics for open-ended links.
- **Field coverage (non-missing):** `prccm` 99.8%, `trt1m` 99.3%, `cshtrm` 99.4%, `ajexm` 100%, `cshom` 57.3%, `cshoq` 29.1%, `dvpsxm` 16.6%, `navm` 5.1%, `gsector` 90.9%, `naics` 97.4%, `cik` 94.5%. Entirely empty: `csfsm`, `add3`, `add4`.
- **Availability-date rule:** TBD. Market fields are as of month-end; delisting and link-window information is look-ahead if used before it was known.
- **Known issues:**
  - **No accounting data:** book equity, assets, earnings, cash flow, accruals and similar items are absent. The paper's characteristics built from accounting data (value, profitability, investment and similar) cannot be computed from this file. A separate Compustat Fundamentals Annual or Quarterly pull is needed, with an explicit reporting lag.
  - **Market data only:** this file gives price, return, shares and volume, which also overlaps with CRSP stock data (D6). Whether D6 is still needed depends on whether `trt1m` and `prccm` are adequate; they include delisting returns only if Compustat supplies them (not checked).
  - **Descriptor fields are current:** `conm`, `sic`, `gsector`, `costat`, `dlrsn` and similar fields describe the company as of the pull date, not each month, so they are not point-in-time.
  - **Several fields are of little use:** address, phone, S&P holdings fields and web address.
  - **Still to check:** the nature of the 404 future-dated records, units of `cshom` and `cshoq`, and the numerical outliers reported in the audit inventory.
- **Status:** outside Option A; not used.
- **Used by:** none under Option A.

### D8. Extra factors for the eight-factor check
- **Source and access path:** TBD. Which eight factors the paper uses is unconfirmed.
- **Used by:** step 9
