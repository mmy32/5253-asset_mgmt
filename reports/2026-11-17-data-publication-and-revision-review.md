# Data publication timing and revision review

Date: 2026-11-17. Scope: the sources used under Option A (D1a, D1b, D2, D3) plus D4 (optional, not pulled). D5 to D7 are outside Option A and only noted.

This review answers one question for each source: **what is publicly documented about when the data appear and when they get revised?** It is a desk review of public documentation. It did not test any revision empirically, and no panel numbers changed.

## Bottom line

| Source | Release rhythm | Does history change? | Can we recover older versions? | Effect on the v1 lag assumptions |
|---|---|---|---|---|
| D1a/D1b CRSP Mutual Funds (via WRDS) | Updated quarterly, delivered with a monthly lag | Yes. CRSP says it corrects history "as errors are identified". The notes list returns, TNA, fee, class-group and management-company corrections from 2019 to 2025 | Not from WRDS. Release notes name corrections but give no old values. Quarterly vendor files would be needed | Our one-month lag is a research assumption, not a CRSP date. Fund-level publication dates are not in the data |
| D2 Fama-French factors and risk-free rate | Rebuilt whenever the library is updated, in practice about monthly | Yes, by the author's own statement. Several documented one-off changes | Partly. The Internet Archive holds 21 distinct versions of the factor file since 2015, 10 of the momentum file | Our file is one vintage (built on CRSP 202609). Early-sample values may differ from what was visible in 2019 to 2025 |
| D3 Baker-Wurgler sentiment | Yearly update (latest March 2026, with an April 2026 model change) | Yes. The README says data "are subject to change", and the orthogonalized index was rebuilt in 2026 | Weakly. GitHub history starts 2025-08; the Internet Archive has 4 versions of the current file name and 2 of an older name | Not usable as point-in-time. Already excluded from the primary experiment |
| D4 CFNAI (not pulled) | Monthly, near month-end | Yes, every month, and the Chicago Fed publishes the first-release history | Yes. A first-release ("real-time") file exists, plus ALFRED vintages | The only source here where true point-in-time data exists |

Main finding: no source gives a publication timestamp for each observation. The v1 availability dates remain assumptions. The sources differ in how much we can do about it. D4 is the only source with real-time vintages from the publisher. For D2, snapshot recovery through the Internet Archive is possible but incomplete. For D1a/D1b and D3 it is not available.

## D1a and D1b. CRSP Survivor-Bias-Free US Mutual Fund Database

**Publisher and path.** CRSP, distributed by Morningstar and by WRDS. The data themselves come from Lipper and Thomson Reuters since the December 2007 iteration, with history back to August 1998 provided electronically from those vendors. Earlier history was built by hand from printed sources (CRSP guide, "File Development and Data Sources").

**Release timing (documented).**
- The CRSP guide says the database "is updated quarterly and distributed with a monthly lag."
- CRSP's product page links a release calendar covering "all monthly, quarterly and annual releases through 2028." The calendar page is built in the browser and returned no dates to me, so I could not read the schedule. It lists an "effective date" of 2026-08-04 for the current calendar.
- The release notes (read below) state data-through dates showing a one-month gap between the last data month and the release month, in every note through January 2023. A search excerpt of a March 2009 release says it held data through January 30, 2009 (a two-month gap), so the lag has changed over time; I did not open that note.
- Consistent with our own pull: D1a/D1b run through 2026-09 and were downloaded on 2026-11-06.
- WRDS and Morningstar do not publish a per-table or per-field availability date.

**What each date field means (CRSP guide).**
- `caldt` in the monthly tables is the last trading day of the month for NAV and returns. TNA is dated to the last calendar day in some tables (October 2009 release note, from a search excerpt).
- In `fund_summary`, `caldt` is the "effective date for summary data". It is not a filing or publication date.
- `exp_ratio` is "as of the most recently completed fiscal year", with `fiscal_yearend` as the "effective date used for fees". `turn_ratio` covers the twelve months ending on `fiscal_yearend`. These values become public only through annual reports and prospectuses after the fiscal year ends, so the v1 rule of fiscal year-end + 180 days is a reasonable but unverified guess.
- `end_dt` is the "date of latest NAV data", and `dead_flag` and `delist_cd` describe the fund as of the pull. These describe the fund's status at the time of the pull, which agrees with the look-ahead problem already documented in DATA.md.
- Monthly flows come from NSAR filings on EDGAR (`report_dt` is the NSAR reporting date), starting in Q4 1993. The v1 panel does not use these flows; it builds flow from TNA and returns.

**Revisions (documented).**
- The guide: "Data corrections to historical information are made as errors are identified and are detailed in the release notes that accompany each data cut."
- The May 2020 release was off-cycle and filled in monthly TNA for January and February 2020 and March 2020 returns and NAVs, a documented case of history being filled after the fact (see the next section).
- The guide names known biases that change history independently of corrections: share classes can inherit a fund's full prior history, and private-fund histories can be added to the start of public histories (a selection effect that favors successful funds).
- An older NYU working paper (search result, not read in full) argues that the monthly return data are biased upward and that funds with monthly returns have lower merger and liquidation rates than others. I treat this as a lead, not a finding.

**Can we recover older versions?**
- WRDS holds only the current cut. The release notes (read below) say what changed but give no old values.
- A true vintage test needs earlier quarterly cuts from CRSP or from a library that archived them. I found no public source for these.

**Implication for the v1 assumptions.** The panel has no way to show when a given value first appeared. For investors, NAVs and returns are public daily, so the one-month return lag is conservative against the investor's real information. It is not a statement about when the database first showed the number. The risk that matters is the revision of values we use (returns, TNA, fees, class group, objective code), which the next section sizes only by count.

### CRSP release notes, read directly

I read 32 release notes: 29 from CRSP's old site through the Internet Archive (January 2019 to January 2026) and the April, July and September 2026 notes from Morningstar's document library. The one quarterly release I could not retrieve is July 2019, and any off-cycle release other than May 2020 would also be missing from this set. Each note is a 2-page PDF. Most contain only row counts and install instructions. The notes name a correction only when CRSP chose to list one, and give no old values, so the **size of any change to a value we use is unknown**. Everything below is quoted or paraphrased from those notes.

**Release timing (confirmed).** Every note through January 2023 says "contain data through" the month before the release month: January 2019 release through December 2018, April 2019 through March 2019, October 2019 through September 2019, October 2020 through September 2020, July 2022 through June 2022. So the one-month lag is documented for the database as delivered. CRSP does not always keep to the quarterly rhythm: May 2020 was an off-cycle release (data through April 2020, "to address several issues found in the March data release"), and 2026 has April, July and September releases. From April 2023 on, the notes no longer state the data-through month.

**Corrections listed in the notes, by whether they touch fields we use.**

| Release | What CRSP says changed | Field we use |
|---|---|---|
| Jan 2019 | Filled 4,933 missing fees and expense ratios in `fund_fees` | Expense ratio |
| Oct 2019 | "Over 2.8 MM revisions" to historical daily NAV; fee `begdt`/`enddt` ranges corrected to fiscal year end and about 72,000 non-conforming fee rows removed | NAV; expense-ratio dates |
| Dec 2019 | "Mutual fund returns rerun": about 20,000 daily and monthly returns (a quarter of one percent) had been shown as price appreciation instead of total returns, because `reinv_nav` was populated with zeros. A corrected database was released. Also over 30,000 monthly returns corrected by adding missing dividends; over 3,400 duplicate daily NAV rows removed; pre-1998 fee history added back | Monthly return |
| Apr 2020 (off-cycle) | Added monthly TNA for January and February 2020; filled March 2020 monthly returns and NAV after problems in the March release | TNA; return |
| Jul 2020 | Over 12,000 dividends replaced with more granular ones; money-market funds with 0.0 monthly returns corrected by adding accrual dividends; missing `crsp_cl_grp` and `crsp_portno` populated in `fund_hdr` | Return; class group |
| Oct 2020 | Dividend history edited again, and "these dividend changes will also reflect in the daily and monthly returns"; over 21,000 `mgmt_name` corrections; `-99` placeholders replaced by NULL in fund fees, summary, NAV, TNA, flows and load tables | Return; management company; missing-value coding |
| Jan 2022, Apr 2022 | `fund_hdr_hist` and `fund_hdr` clean-up: redundant records removed and `crsp_cl_grp` identifiers corrected | Class group |
| Jul 2022, Oct 2022 | Holdings-table clean-up only (permnos removed from `holdings_co_info`). Nothing for fields we use | None |
| Jan 2023 | The December 2022 database, first released January 31, was re-released on February 22, 2023 "due to missing data in the monthly TNA table". The note says "originally released on January 31, 2022"; I read that year as a typo | TNA |
| Jul 2023 | Over 3,000 `crsp_cl_grp` ids edited "to more correctly reflect the associations between share classes"; "further edits will be made in subsequent releases" | Class group |
| Oct 2023 | "Nearly 18,000 edits" to `crsp_cl_grp` in `fund_hdr`; historical fund flows for 2005 to 2018 added | Class group |
| Apr 2024 | Continued `crsp_cl_grp` clean-up in `fund_hdr_hist`: "nearly 60k crsp_cl_grp ids were removed where only a single share class exists"; manager name/date edits for one fund | Class group |
| Jul 2024 | Missing share splits added in the dividends table, which "also affected the reported fund returns"; pre-2019 flow units corrected from $1,000s to dollars | Return |
| Oct 2024 | Over 200 historical split ratios corrected, "which also produced corresponding revisions to the daily and monthly returns"; over 40,000 changes to `chngdt`/`chngenddt` in `fund_hdr_hist`, giving "a more accurate history of the mgmt_name and mgmt_cd changes" | Return; management company |
| Jul 2025 | `crsp_cl_grp` validated for every fund in `fund_hdr_hist`, with edits | Class group |
| Oct 2025, Jan 2026, Apr, Jul, Sep 2026 | No corrections listed | None stated |

**What this means for our panel.**
- **Returns changed after the dates we assume.** Five releases between December 2019 and October 2024 corrected historical monthly returns (December 2019, July 2020, October 2020, July 2024, October 2024), and April 2020 filled in missing March 2020 returns. Our data are the 2026 cut, so they include all of these. Returns for our 2019 to 2025 evaluation window therefore differ from what a user of the earlier releases saw, by an amount the notes do not give. They also do not say how many equity-fund returns moved.
- **Class grouping is a 2026 view.** CRSP edited `crsp_cl_grp` in seven releases (July 2020, January 2022, April 2022, July 2023, October 2023, April 2024, July 2025; the January and April 2022 notes carry the same message). The panel maps each share class to a fund using the latest group, as DATA.md records. Fund-level aggregation in 2019 to 2024 would have used a different mapping.
- **A possible cause of missing class groups.** In April 2024 CRSP removed nearly 60,000 `crsp_cl_grp` ids where a fund has only one share class. If that is why 16.4% of D1b rows have no group, then many "missing" groups are single-class funds, not data gaps, and the v1 rule that rejects unsupported singletons may be excluding real funds. This began as a hypothesis from one sentence in the notes. I then tested it in D1b: only 64 of 14,511 remaining groups have a single member, and 90% of ungrouped funds that have a `crsp_portno` share it with no other class, against 2% of grouped funds. About 74% of ungrouped funds look like single-class funds. See the [summary report](2026-11-17-crsp-release-notes-summary.md) for the table and limits.
- **Management company (family) history changed.** The October 2020 and October 2024 edits touch `mgmt_name` and `mgmt_cd` histories, which any family-level predictor would use.
- **Expense-ratio timing is partly CRSP's construction.** The October 2019 fee-date correction ("based on fiscal year end") means the dates we use to place fees in time come from a rebuild, not from filing dates. This supports treating the 180-day fee lag as an assumption.
- **TNA, and so flow, was incomplete in at least two releases** (March 2020 and December 2022). April 2019 also shows an odd jump in the monthly TNA row count (8.6 million, against 7.0 million in January and 7.5 million in October), which I did not explain.
- **Fewer sentinels in 2026 data.** Because the `-99` coding was dropped in October 2020, a 2026 pull has no `-99` placeholders; older vintages did. Our D1a letter codes (`R`, `T`, `N`) are a different coding I have still not looked up.

**Row counts across releases.** The notes give table row counts, which I tabulated for monthly returns across all 29 releases. New rows arrive at about 90,000 to 100,000 per quarter, with larger steps where a release skipped one I could not retrieve. `fund_summary` has the same row count (2,837,247) in January and April 2025, an apparent stall. `fund_fees` falls from 507,874 (April 2019) to 447,761 (October 2019), matching the 72,000-row removal noted above. Row counts cannot show value changes, so they say nothing about the size of return revisions. Our D1a has 10,345,662 rows, which exceeds every single table in the September 2026 release (about 10.1 to 10.15 million); this is plausible if the WRDS query takes the union of keys across the three tables, but I did not check.

## D2. Fama-French factors, Mom and risk-free rate

**Publisher.** Kenneth French's data library (Dartmouth Tuck). Current page header: September 2026 data in the library as of my fetch.

**Release timing (observed).**
- The library does not publish a calendar. Our files are stamped 2026-10-26 inside the zip and built on the 202609 CRSP database, so September 2026 returns appeared about 26 days after month-end.
- The Internet Archive holds snapshots with different content of the factor file on 2026-10-19 and 2026-10-30. That is at least two content changes within October 2026. I did not compare their contents, so I cannot say whether the second one is a revision or the addition of September.
- The page notes that "the July cut has data through July and was released in August of that year" for the annual archive.

**Revisions (documented by the author).**
- "We reconstruct the full history of returns each month when we update the portfolios. (Historical returns can change, for example, if CRSP revises its database.)"
- Documented change events on the library pages:
  - 2005: CRSP added 1925 to 1962 daily data; many small changes to historical returns.
  - December 2012: market return definition revised.
  - January 2015: CRSP review of shares outstanding for 1925 to 1946; "many of the returns we report for 1925-1946 change," some by large amounts.
  - May 2015: daily-portfolio computation changes.
  - August 2016: treatment of deferred taxes in book equity changed.
  - August 2018: operating profitability definition changed.
  - September 2021: switched to CRSP-provided Compustat links and time-sensitive fund eligibility.
  - January 2025: switched from CRSP legacy (FIZ) to the new flat file format (CIZ). Monthly returns changed from month-to-month holding-period returns with dividends reinvested at month-end to compounded daily returns with dividends reinvested on ex-dates.
- Risk-free rate: Ibbotson Associates through May 2024; ICE BofA US 1-Month Treasury Bill Index from June 2024 (factor page).
- Most of these documented events affect early history or the build, not our 2019 to 2025 window. The January 2025 format change is the one that touches our window, and it changed how monthly returns are computed.

**Can we recover older versions?** The Internet Archive's index lists these distinct-content snapshots of the three-factor monthly CSV zip (YYYYMMDD): 2015-11-20, 2017-07-09, 2019-03-04, 2020-05-03, 2020-07-14, 2021-04-13, 2022-03-27, 2022-06-11, 2022-09-01, 2022-10-07, 2023-02-19, 2023-09-11, 2024-03-16, 2024-04-19, 2024-08-10, 2025-06-11, 2025-11-12, 2025-12-21, 2026-02-19, 2026-10-19, 2026-10-30. For the momentum zip: 2015-11-17, 2016-03-15, 2017-07-09, 2020-05-03, 2020-07-14, 2022-03-31, 2022-09-01, 2023-02-19, 2024-08-10, 2026-11-12. The coverage is uneven, with a gap between 2026-02 and 2026-10 for the main file, and fewer momentum snapshots than factor snapshots. I listed them only. I did not download or compare them.

**Implication.** A sensitivity check is feasible: replace our file with the nearest earlier snapshot and see how much the month-by-month factor values differ. That would put a number on the "revised data" caveat for D2.

## D3. Baker-Wurgler investor sentiment

**Publisher.** Jeffrey Wurgler's NYU Stern page links `data/SENTIMENT.xlsx`; the code, notes and "yearly updates" are in the public GitHub repository BWInvestorSentimentIndex/BakerandWurglerInvestorSentimentIndex (created 2025-08-25).

**Release timing (documented and observed).**
- The README says "UPDATED: March 2026" and "yearly updates are posted here." The GitHub history shows these data-relevant commits: 2025-03-11 "Updated data for 2025"; 2025-08-25 "Added SENTIMENT.xlsx file"; 2026-03-26 "Updated data for 2026"; 2026-04-01 "Added detrending code"; 2026-04-03 "Detrend update"; 2026-04-21 "Correcting upload of output".
- Our file ends at 2025-12 and was downloaded 2026-11-06. So 2025-12 data were first posted about three months after month-end, in a yearly batch, and months in between were not available at all until the next yearly update.
- The README warns: "Data are subject to change if data improvements are available or revisions occur."

**Revisions (documented).**
- Yearly updates can change history. The 2026 update changed the `SENT_ORTH` model: macro series are now detrended instead of converted to year-over-year growth, because the old transformation produced extreme values in early 2020. This changes `SENT_ORTH` for the whole history. Our file's README contains this notice, so it is the post-April-2026 vintage.
- The index uses full-sample principal components, so each yearly update uses information from after each date (already noted in DATA.md).
- The README says to avoid using differences in sentiment, "due to lag structures." Input series use t-12 values or 12-month sums, so the index at month t reflects information up to a year earlier.
- Input data sources change over time: raw data are built by different people before and after 2011 and 2022. The closed-end fund discount series switches from Herzfeld to Morningstar in 2011. CPI is missing for 2025-10 due to the government shutdown.

**Can we recover older versions?**
- GitHub holds a history for `SENTIMENT.xlsx` only from 2025-08-25 (five commits: 2025-08-25, 2026-03-26, 2026-04-01, 2026-04-03 and 2026-04-21). Earlier yearly versions are not in the repository.
- The Internet Archive lists 4 distinct-content snapshots of `SENTIMENT.xlsx` (2025-10-03, 2025-10-06, 2025-10-06 and 2026-10-29) and 2 of an older file name, `Investor_Sentiment_Data_20190327_POST.xlsx` (2019-10-23 and 2024-04-13). I did not download them.
- No source shows what the index looked like in each month between 2019 and 2025.

**Implication.** Sentiment cannot support a point-in-time claim. The v1 design already excludes it from the primary experiment, and this review supports that decision. Any sentiment extension should be labeled retrospective and should say it uses the April 2026 vintage.

## D4. CFNAI (optional, not pulled)

- The Chicago Fed releases CFNAI at 8:30 a.m. ET "normally toward the end of each calendar month" (current-data page).
- Each release revises earlier months. The Chicago Fed attributes revisions to revised underlying data and to estimates of not-yet-available data. Its published revision table shows median absolute revisions of about 0.09 for the latest month and 0.09 one month back, falling to about 0.02 by five months back (search excerpt).
- The Chicago Fed publishes the history "as originally made available at the time of release." Its PDF reports ended after January 2024, but the real-time archive remains on the Historical Data page.
- ALFRED (St. Louis Fed) lists the CFNAI release with 7 series revisions, with release dates from 2011-05-23 to 2026-03-23 (search excerpt, not opened).
- **Implication.** If D4 is pulled, use the real-time file, not the latest revised series. This is the one place where the strict point-in-time extension is already supported by the publisher.

## D5 to D7 (outside Option A)

Not reviewed. D5 is unusable as pulled, and D5 to D7 are not used. D7 is Compustat/CRSP link data, whose descriptor fields describe companies as of the pull date (DATA.md).

## What this review did not do

- I read the CRSP release notes for January 2019 to September 2026 except July 2019. They list corrections but never give how many equity-fund values moved or by how much, so the size of each correction in our window is unmeasured. Release notes before 2019 were not read.
- The CRSP release calendar returned no dates when fetched. The release months for D1a/D1b are inferred, not read.
- Ken French's pages were readable only over plain HTTP. They matched the content in our files.
- I did not compare any archived file against our files, so the size of each source's revisions in our window is **unmeasured**.
- Statements about when funds publish NAV, TNA and expense information to investors (daily NAV, annual reports, prospectuses) are background knowledge, not something I checked in this review.

## Recommended next steps (for your decision)

1. **Decide how to treat single-class funds** (the D1b test supports the single-class explanation; see the summary report). Either keep v1 and report the singleton sensitivity, or register a new protocol version that counts single-class funds.
2. **Run a D2 sensitivity check** with one or two earlier Internet Archive snapshots of the factor and momentum files, and report the largest month-by-month differences in the evaluation window.
3. **Keep D3 out of the primary results** and state its vintage (post-April 2026 model) in any extension.
4. **If D4 is used,** pull the real-time file.
5. **Update DATA.md** availability-date rules to cite this review: record that no source has per-observation publication timestamps and that v1 dates are assumptions.

## Sources

- CRSP Survivor-Bias-Free US Mutual Fund Database Guide: [CRSP guide (PDF)](https://www.crsp.org/wp-content/uploads/2023/10/CRSP_US_Mutual_Funds_Guide_SAS_ASCII_R.pdf); [WRDS copy, updated March 31, 2014](https://wrds-www.wharton.upenn.edu/documents/410/CRSP_MFDB_Guide.pdf)
- [CRSP Survivor-Bias-Free US Mutual Fund Database product page](https://indexes.morningstar.com/research-data-products/crsp-survivor-bias-free-us-mutual-fund-database) and [document library](https://indexes.morningstar.com/research-data-products/document-library)
- CRSP release notes, read as PDFs: January 2019 to January 2026 from CRSP's old site via the Internet Archive (files named `crsp.org/wp-content/uploads/mf_YYYYMM.pdf`, quarterly months, plus the off-cycle April 2020 file; July 2019 not found), and April, July and September 2026 from [Morningstar's release-note library](https://indexes.morningstar.com/research-data-products/document-library). October 2009 was seen only as a search excerpt.
- Ken French: [data library](http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), [3-factor detail](http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html), [momentum detail](http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html), [changes in CRSP data](http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/changes_crsp.html)
- Baker-Wurgler: [GitHub repository](https://github.com/BWInvestorSentimentIndex/BakerandWurglerInvestorSentimentIndex) (README and commit history via the GitHub API), [Wurgler's NYU page](https://pages.stern.nyu.edu/~jwurgler/), and the README sheet inside `data/raw/D3_Baker_Wurgler_sentiment.xlsx`
- Chicago Fed: [CFNAI current data](https://www.chicagofed.org/research/data/cfnai/current-data), [historical data](https://www.chicagofed.org/research/data/cfnai/historical-data-live); [ALFRED CFNAI release](https://alfred.stlouisfed.org/release?rid=219)
- Internet Archive CDX index (snapshot lists for the French and Wurgler files)
- Project context: `reports/2026-11-12-research-protocol-v1.md` (lag assumptions), `DATA.md`
