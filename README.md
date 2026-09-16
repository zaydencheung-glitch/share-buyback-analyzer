# Share Buyback Analyzer

An independent research project analyzing whether corporate share
buybacks actually reduce shareholders' diluted share count.

## 1\. Project Title

**Share Buyback Analyzer: Measuring Net Diluted Share-Count Change Across Ten Large-Cap Companies**

## 2\. Research Question

> Do corporate share buybacks result in a lower diluted average share
> count, after accounting for the combined effects of share issuance and
> dilution (including, but not limited to, stock-based compensation)?

This project does **not** ask "how many shares did each company buy back?"
It asks a narrower, more measurable question: did the company's diluted
average share count actually go down, up, or stay flat from one fiscal
year to the next? Diluted average shares already nets buybacks against
all forms of issuance in the same figure — this project does not
separately subtract stock-based compensation or any other single cause
from the share count; it measures the combined net outcome and leaves
attribution to a specific cause to the Interpretation section of the
research report, where it is discussed only in general terms unless a
filing supports a more specific claim.

## 3\. Motivation

Share buybacks are frequently reported in the financial press as a
straightforward reduction in share count. In reality, many companies —
particularly in technology — issue large amounts of new equity every year
through employee stock-based compensation (SBC), which can partially or
fully offset the effect of repurchases. A company can spend billions of
dollars buying back stock and still end the year with the same or a
*higher* diluted share count. This project builds a small, reproducible
tool to measure that net effect directly from reported financial
statement data, rather than relying on buyback dollar totals alone.

## 4\. Methodology

For each company:



1\. Retrieve financial statement data through `yfinance`, including Diluted Average Shares and, where available, Basic Average Shares, repurchase spending, and stock-based compensation.

2\. Standardize the analysis to the same four fiscal years for every company: FY2022 through FY2025. This creates three year-to-year comparisons: 2022→2023, 2023→2024, and 2024→2025.

3\. If `yfinance` does not provide a required historical observation, use a manually verified value from an official SEC filing. These fallback observations are explicitly labeled in the raw data rather than being presented as `yfinance` data.

4\. Clean and validate the data before analysis. Missing values are not replaced with zero, duplicate fiscal years are flagged, and share counts must be positive.

5\. For each pair of consecutive fiscal years, compute Net Shares Retired and Net Share Reduction Yield % (Section 7).

6\. Classify each year as Net Share Reduction, Net Dilution, or Flat / Neutral.

7\. Calculate each company's average annual yield, cumulative share-count change, number of reduction/dilution/neutral years, best year, worst year, and overall classification.

8\. Optionally compute the Project Buyback Effectiveness Score (Section 9), a project-defined heuristic rather than an industry-standard financial metric.

9\. Compare the ten companies and generate the final CSV files and charts.5. Data Sources

|Source|Role|Reliability status|
|-|-|-|
|**Yahoo Finance via `yfinance`**|Automated initial data collection for all ten companies|**Not** an official or primary source. Convenient for rapid, scriptable retrieval, but Yahoo Finance aggregates and sometimes restates figures, and its schema can change without notice.|
|**SEC EDGAR (10-K filings)**|Primary-source verification|Official filed financial statements. This is the source you should cite in any final write-up or interview, not Yahoo Finance.|
|**Company annual reports / investor relations pages**|Primary-source verification, sometimes friendlier formatting than raw 10-Ks|Official, but presentation can differ slightly from the SEC filing (e.g., rounding, non-GAAP adjustments) — the 10-K is the authoritative version if they conflict.|
|**Manual entry**|Fallback when `yfinance` cannot reliably supply a figure|Only as reliable as the person entering it; always record where the manually-entered number came from.|

**The distinction that matters most:** every figure in this project's
output CSVs carries a `Data Source` / `data\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_source` field. Anything
labeled `Yahoo Finance / yfinance (automated, unverified)` should be
treated as a *draft* number suitable for exploration, not as a citable
research finding, until you have checked it against the company's actual
10-K (see Section 12, "Verifying data against SEC filings").

## 6\. Definitions

It is easy to conflate several related-but-different figures. This
project deliberately keeps them separate:

* **Shares Outstanding** — the number of shares actually in existence at
a specific point in time (a snapshot, not a period average).
* **Diluted Average Shares** — a *weighted average* of shares outstanding
over the fiscal year, adjusted to include the dilutive effect of
options, RSUs, convertible securities, and similar instruments *as if*
they were already converted to common stock. **This is the metric this
project uses.** It is an accounting construct, not a literal share
count you could point to on any single day.
* **Basic Average Shares** — the same weighted-average concept as above,
but *without* the dilutive adjustment. Included in the raw data where
available, for context, but not used in the core calculation.
* **Shares Repurchased** — shares a company actually bought back on the
open market or via tender offer during the year. This project reports
repurchase *spending* (dollars) where reliably available, but does
**not** treat repurchase spending as equivalent to a share count, and
does not convert dollars spent into an implied share count (that would
require an average repurchase price per share, which this project does
not estimate).
* **Stock-Based Compensation (SBC)** — non-cash compensation expense
associated with equity awards to employees. SBC is *one possible*
contributor to share issuance/dilution, but this project does not
claim SBC specifically *caused* any observed dilution in a given year
unless the underlying filing provides that level of detail. Other
causes include secondary offerings, convertible note conversions, and
M\&A-related share issuance.
* **Net Shares Retired** / **Net Share Reduction Yield** — this project's own
derived measures of the year-over-year *change* in diluted average
shares (Section 7). These describe **net diluted share-count change**,
not a literal count of shares physically retired from the market.

## 7\. Mathematical Formulas

**Net Shares Retired** (per fiscal year, vs. the prior fiscal year):

```
Net Shares Retired = Previous Year Diluted Average Shares
                      − Current Year Diluted Average Shares
```

**Net Share Reduction Yield %:**

```
Net Share Reduction Yield % = (Net Shares Retired / Previous Year Diluted Average Shares) × 100
```

* Positive → diluted average share count decreased that year.
* Negative → diluted average share count increased (net dilution) that year.
* Values within ±0.10 percentage points are classified as "Flat / Neutral."

**Cumulative percentage change in diluted average shares** (across the
full multi-year window, computed from the two endpoints, *not* by
averaging the annual percentage changes — averaging percentage changes
does not correctly represent compounding and can be misleading, e.g. a
−50% year followed by a +100% year returns you to the starting point,
but naively averaging (−50 + 100)/2 = +25% suggests growth that did not
happen):

```
Cumulative % Change = (Last Year Diluted Avg Shares − First Year Diluted Avg Shares)
                       / First Year Diluted Avg Shares × 100
```

Note the sign convention differs from Net Share Reduction Yield: for cumulative
change, a *negative* value means the share count fell (a reduction),
matching how you'd naturally describe "shares decreased by X%." The code
converts between conventions explicitly and internally; see the
`\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_overall\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_classification` docstring in `buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py` if you're
reading the source.

## 8\. Data Validation Process

Before any figure is used in a calculation, the program checks:

* Whether the required field (Diluted Average Shares) exists at all for
that fiscal year.
* Missing values — never filled with zero or any other placeholder;
years with missing data are excluded from that company's calculations
and reported as a warning.
* Duplicate fiscal years for the same company. These are **preserved**
(not silently removed) through the cleaning step specifically so that
validation can catch and report them — a company with a duplicated
fiscal year is flagged as insufficient data rather than having one
copy quietly discarded.
* Correct chronological ordering of fiscal years.
* **Consecutive-year comparisons only.** Even after missing years are
excluded, the program will not compute a year-over-year yield across
a gap (e.g., comparing 2023 directly to 2021 when 2022 is missing).
Non-adjacent comparisons are skipped and logged, not silently treated
as a one-year change.
* Share counts must be strictly positive (zero or negative triggers a
hard validation failure for that company).
* A basic plausibility check that a repurchase-spending figure hasn't
been accidentally mapped into the share-count column (flagged as a
warning if a repurchase value and a share-count value are identical
for the same year, which would be a strong signal of a column-mapping
bug).
* Whether fewer than four usable fiscal years were found, which is
reported, not hidden.

Companies that fail validation are still listed in the final summary
table with `Insufficient Data = True` and an explanation — they are
never silently dropped.

## 9\. Project Buyback Effectiveness Score

An **optional**, **project-defined** 0–100 heuristic called the
**"Project Buyback Effectiveness Score."** It is explicitly *not*
presented as an objective financial truth, an industry-standard metric,
or investment advice — it exists to give this project a single
comparable number across companies, built transparently from the
underlying data.

|Component|Points|What it rewards|
|-|-|-|
|Cumulative diluted share-count reduction|40|The headline research question — did share count actually fall over the full window? Scaled linearly: 0% cumulative reduction → 0 pts, 20%+ cumulative reduction → full 40 pts. (20% was chosen as a plausible upper bound for a 4-year window for a large-cap buyback program — a project-defined reference point, not a statistical benchmark.)|
|Consistency of annual reduction|25|`(years with net reduction / total years) × 25`. Rewards steady policy over one flashy year offsetting several dilutive ones.|
|Average annual net buyback yield|20|Rewards a *typical* year's magnitude, distinct from the endpoints. Scaled against a 5% average-annual-yield reference point for full credit, capped at 20.|
|Absence of persistent net dilution|15|Full 15 points with zero dilutive years, scaled down as dilutive years increase, reaching 0 once dilutive years reach half the analysis window.|

All four components are always ≥ 0 and independent, so the maximum
possible score is exactly 100 and the minimum is exactly 0. A high buyback
yield alone does not guarantee a high score — a company with one huge
buyback year and two dilutive years will be held back by the consistency
and cumulative-change components.

## 10\. Results

Results are **not** included as static numbers in this README. They must
be generated by actually running the program (Section 12), because:

* Real 10-year/4-year fiscal data changes as new filings are released.
* This project's data-integrity rules explicitly forbid presenting
invented or placeholder results as findings.

After running `python buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py`, look at:

* `data/processed/net\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_yield\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_all\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_companies.csv` — every company's
year-by-year table.
* `data/processed/company\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_summary\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_ranking.csv` — the cross-company
ranking and aggregate metrics.
* `reports/research\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_report.md` — fill in this template with your actual
output (see Section 14 template file).

## 11\. Charts

Generated in `charts/` from the real processed dataset (never hand-entered):

1. `01\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_net\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_share\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_reduction\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_yield\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_by\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_company.png` — average annual net share reduction yield, by company.
2. `02\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_net\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_share\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_reduction\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_yield\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_over\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_time.png` — net share reduction yield trend, one line per company.
3. `03\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_cumulative\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_share\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_change\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_by\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_company.png` — cumulative diluted share-count change, by company.
4. `04\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_years\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_reduction\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_vs\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_dilution.png` — count of reduction/dilution/neutral years, by company.
5. `05\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_effectiveness\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_score\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_by\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_company.png` — Project Buyback Effectiveness Score, by company (only generated if the score could be computed for at least one company).

Each chart includes a title, axis labels with units, a legend where
relevant, and a small source note.

## 12\. Limitations

* **Diluted average shares is an accounting measure**, not a literal
physical count on any given day — see Section 6.
* **A falling share count does not, by itself, prove that buybacks
created shareholder value.** Whether a buyback was a good use of
capital depends on the price paid relative to intrinsic value, which
this project does not assess.
* **Share-count changes can have multiple causes** beyond buybacks:
new issuance, SBC, convertible note conversions, M\&A, secondary
offerings, and more. This project reports the *net* change, not a
causal attribution.
* **Stock-based compensation is one possible source of dilution**,
not necessarily *the* source, in any given company-year, unless the
underlying filing specifically supports that attribution.
* **Four fiscal years is a short research window.** Multi-year capital
allocation strategies can look very different over 10+ years.
* **`yfinance` data can differ from a company's actual SEC filings**
due to restatements, aggregation choices, or scraping/schema drift.
Treat all `yfinance`-sourced figures as provisional until verified.
* **Fiscal years are not aligned across companies** (e.g., a company
with a non-calendar fiscal year-end will not line up month-for-month
against one that reports on a calendar-year basis). This project
preserves each company's actual reported fiscal year rather than
forcing calendar-year alignment.
* **Buyback timing within the year matters** for any price-based
analysis (e.g., repurchases at different points in the year face
different prices) — this project does not attempt intra-year timing
analysis.
* **Consecutive-fiscal-year detection is calendar-year-based**, not
exact-date-based (to tolerate normal 52/53-week fiscal-calendar
drift). In the rare case where a company's fiscal year-end shifts
across the January 1 boundary in a way that puts two genuinely
consecutive fiscal years in the *same* calendar year, that pair would
be (safely) skipped rather than (incorrectly) compared. None of the
ten companies in this project's default list are known to exhibit
that pattern, but this is a known limitation of the check.
* **This project does not evaluate valuation.** It cannot tell you
whether a company repurchased shares at an attractive price.
* **Correlation does not establish causation.** A company that both
reduced its share count and performed well in the stock market did
not necessarily perform well *because* of the buyback.

## 13\. How to Run the Project

```bash
# 1. Clone/copy the project folder, then from inside it:
python -m venv venv
source venv/bin/activate         # on Windows: venv\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\Scripts\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the analyzer
python buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py

# 4. Run the automated tests
pytest tests/ -v
```

The program will:

1. Explain what it's doing.
2. Retrieve data for each ticker in `TICKERS` (see the CONFIGURATION
section at the top of `buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py` — edit that list to
change which companies are analyzed; you never need to touch the
rest of the code). Each company is fetched from `yfinance` exactly
once per run — the retrieved dataset is reused for analysis rather
than requested a second time.
3. Validate the data for each company.
4. Analyze all companies and print a running summary.
5. Save raw data to `data/raw/`.
6. Save processed/combined data to `data/processed/`.
7. Generate charts to `charts/`.
8. Print exactly where every output file was saved.
9. Clearly list any companies that failed or had insufficient data.



The analyzer has been tested against live `yfinance` data for all ten companies in the default dataset. Because `yfinance` does not always expose every historical fiscal year needed for the fixed FY2022–FY2025 window, the program supports verified historical fallback observations from official SEC filings. These observations are explicitly labeled in the raw CSV files so that automated and manually verified data remain distinguishable.



All `yfinance` observations should still be treated as provisional until checked against the corresponding company's SEC filing. The final research dataset should rely on primary-source verification wherever possible.



## 14\. File Structure

```
share-buyback-analyzer/
├── buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py          # Main program (all core functions)
├── requirements.txt             # Exact dependency list
├── README.md                    # This file
├── data/
│   ├── raw/                     # Raw retrieved data per company (CSV)
│   └── processed/               # Cleaned per-year table + summary ranking (CSV)
├── charts/                      # Generated PNG charts
├── reports/
│   └── research\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_report.md       # Research report template (fill in with real output)
└── tests/
    └── test\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_buyback\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_analyzer.py # pytest test suite
```



\## Current Verification Status



The automated dataset is being checked against official SEC filings before the results are treated as final.



| Company | Status | Notes |

|---|---|---|

| Apple (AAPL) | In Progress | FY2022–FY2025 diluted weighted-average shares verified against SEC filings. A difference in the presentation of FY2022 repurchase spending remains documented for further review. |

| Microsoft (MSFT) | In Progress | Diluted weighted-average shares checked against SEC filings. FY2022 uses a verified SEC fallback because the required year was not returned by `yfinance`. |

| NVIDIA (NVDA) | In Progress | FY2022 uses a verified historical SEC observation adjusted for NVIDIA's 2024 10-for-1 stock split to maintain comparability with later years. |

| Meta (META) | Verified | FY2022–FY2025 diluted weighted-average shares verified against official SEC filings; all four observations match the automated data. |

| Tesla (TSLA) | Verified | FY2022–FY2025 diluted weighted-average shares verified against official SEC filings. Verified SEC values override the automated diluted-share observations for this analysis. |

| Palantir (PLTR) | Verified | FY2022–FY2025 diluted weighted-average shares verified against official SEC filings. Exact SEC values override the automated diluted-share observations for this analysis. |

| Alphabet (GOOGL) | Verified | FY2022–FY2025 diluted weighted-average shares verified against official SEC filings; all four observations match the automated data. |

| Amazon (AMZN) | Pending | SEC verification not yet completed. |

| JPMorgan Chase (JPM) | Pending | SEC verification not yet completed. |

| Costco (COST) | Pending | SEC verification not yet completed. |



Verification focuses first on diluted weighted-average shares because this is the primary variable used to calculate net share reduction. Supporting fields such as repurchase spending and stock-based compensation are also reviewed where relevant.





## Disclaimer

This is an **educational research project**, built to explore a specific,
narrow accounting question. It is **not investment advice**, is **not**
a professional financial analysis, and its "Project Buyback Effectiveness
Score" is a heuristic created solely for this project — not an
established industry standard. Figures retrieved automatically via
`yfinance` should be verified against SEC filings before being cited or
relied upon for any purpose beyond this project.

