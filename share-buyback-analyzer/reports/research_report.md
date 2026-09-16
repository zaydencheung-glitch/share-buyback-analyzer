<!--
RESEARCH REPORT TEMPLATE — READ BEFORE FILLING IN

This is a TEMPLATE, not a finished report. Every bracketed placeholder
like [FILL IN: ...] must be replaced with a real number or finding taken
directly from your own run of `python buyback_analyzer.py` and the
resulting CSVs in data/processed/. Do not invent numbers to fill these
placeholders, and do not decide the conclusion before you have the
actual output in front of you — report whatever the data actually shows,
including if some companies reduced their share count and others did not.

Target length once filled in: ~1,500–2,500 words.
-->

# Do Share Buybacks Reduce Diluted Share Count? A Ten-Company Study

## Abstract

[FILL IN: 3–5 sentences. State the research question, the method in one
sentence (net year-over-year change in diluted average shares across
four fiscal years for ten large-cap companies), and a one-sentence
preview of the overall pattern found — e.g. "X of 10 companies showed a
net reduction, Y showed net dilution, Z were roughly flat" — using your
actual counts from company_summary_ranking.csv.]

## 1. Introduction

Corporate share buybacks are often described in financial media as
directly and reliably shrinking a company's share count. This framing
usually skips a key detail: most large companies also issue new equity
every year, especially through employee stock-based compensation. A
company can spend enormous sums repurchasing stock and still end the
year with the same, or a higher, number of diluted shares outstanding.
This project sets out to measure that net effect directly rather than
taking buyback headlines at face value.

## 2. Research Question

Do corporate share buybacks actually reduce shareholders' diluted
average share count, once share issuance and stock-based compensation
are accounted for? This project measures net year-over-year change in
diluted average shares — described here as "net diluted share-count
change" or "net buyback effect" — for ten large-cap companies across up
to four fiscal years.

## 3. Why Share Buybacks Matter

Buybacks are one of two primary ways (alongside dividends) that public
companies return capital to shareholders. Proponents argue buybacks
concentrate ownership among remaining shareholders and can be a
tax-efficient alternative to dividends. Critics argue buybacks can be
used to offset dilution from executive and employee compensation without
delivering a net benefit to long-term shareholders, or that companies
sometimes repurchase stock at unfavorable prices. This project does not
take a position on that debate — it only measures whether, mechanically,
diluted share count fell, rose, or stayed flat.

## 4. Methodology

For each of the ten companies studied, up to four of the most recent
completed fiscal years of Diluted Average Shares were retrieved via the
`yfinance` Python package. Year-over-year Net Shares Retired and Net
Buyback Yield % were computed for each consecutive pair of fiscal years
(see README.md, Section 7, for exact formulas), each year was classified
as Net Share Reduction, Net Dilution, or Flat/Neutral (±0.10 percentage
points), and results were aggregated per company: average annual yield,
cumulative percentage share-count change (computed from period endpoints,
not by averaging annual percentages), count of reduction/dilution/neutral
years, best and worst year, and an overall classification. A transparent,
project-defined 0–100 "Project Buyback Effectiveness Score" was also
computed where possible.

## 5. Data Sources

Automated data collection used `yfinance`, which retrieves data
originating from Yahoo Finance — **not** treated as an official or
primary source in this project. [FILL IN: state which, if any, figures
you cross-checked against SEC 10-K filings or company annual reports for
this write-up, and note any discrepancies you found.]

## 6. Calculations

[FILL IN: Reproduce the Net Shares Retired, Net Share Reduction Yield %, and
cumulative-change formulas from README.md Section 7, and walk through
one fully worked numeric example using a real company/year from your
output — e.g., show the actual previous- and current-year diluted share
figures for one company and the resulting yield.]

## 7. Results

[FILL IN: Insert the full per-year table (or a representative excerpt)
from data/processed/net_buyback_yield_all_companies.csv, and the
cross-company ranking from data/processed/company_summary_ranking.csv.
Report the actual counts: how many companies showed net reduction vs.
net dilution vs. neutral overall, and cite the actual highest and lowest
Project Buyback Effectiveness Scores, if computed.]

## 8. Company Comparisons

[FILL IN: Pick 3–4 companies with contrasting results (e.g., one clear
net-reducer, one clear net-diluter, one mixed/volatile case) and discuss
their year-by-year pattern using the actual numbers. Note any companies
flagged as Insufficient Data and why.]

## 9. Interpretation

[FILL IN: Discuss what the pattern suggests about the relationship
between buyback activity and net share-count change generally, without
overstating causality. If some companies with large repurchase spending
still showed dilution, say so explicitly and explain (in general terms,
not with unsupported specifics) that SBC and other issuance are the
likely offsetting factor — but avoid asserting a specific causal
mechanism unless a filing supports it.]

## 10. Limitations

Reproduce and, where relevant, expand on the limitations in README.md
Section 12: diluted average shares is an accounting measure and not a
literal share count; share-count reduction does not by itself prove
buybacks created shareholder value; share-count changes can have several
causes; stock-based compensation is only one possible source of
dilution; four fiscal years is a short window; `yfinance` data can
differ from filings; fiscal years differ across companies; buyback
timing/pricing was not assessed; valuation attractiveness was not
assessed; and correlation does not establish causation.

## 11. Conclusion

[FILL IN: A short, honest summary directly answering the research
question with your actual findings — e.g., "Across the ten companies and
fiscal years studied, N companies achieved a net reduction in diluted
average shares, N showed net dilution despite repurchase activity, and N
were roughly flat. This suggests buybacks [FILL IN qualifier based on
your real data, e.g. 'frequently, but not universally,' or 'inconsistently,'
etc.] translate into an actual reduction in diluted share count once
issuance is accounted for." Do not claim the project proves buybacks
create or destroy shareholder value — it only measures the net
accounting effect on share count.]

## 12. Sources

- Automated data: Yahoo Finance, via the `yfinance` Python package
  (not an official source; used for initial data collection only).
- [FILL IN: list the specific SEC EDGAR 10-K filings (with URLs, e.g.
  `https://www.sec.gov/cgi-bin/browse-edgar?...` or the direct filing
  link) and/or company annual report pages you used for verification.]
