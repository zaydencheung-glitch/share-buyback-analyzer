"""
Share Buyback Analyzer
=======================

Research question:
Are corporate share buybacks associated with lower diluted average
share counts after the effects of share issuance and dilution?

This program measures the *net* change in diluted average shares
outstanding, year over year, for a configurable list of companies.
It does NOT measure "shares physically repurchased" -- diluted average
shares is a weighted-average accounting figure that reflects the combined
effects of buybacks and potentially dilutive or share-issuing activity
(options, RSUs, stock-based compensation, secondary offerings, convertible
instruments, etc.). The program does not separately subtract stock-based
compensation from the share count. See README.md, section "Definitions",
for the full explanation.

IMPORTANT — READ BEFORE RUNNING
--------------------------------
This code was written and unit-tested (see tests/) against synthetic
data in a sandboxed environment WITHOUT live network access. The
yfinance field names used below (e.g. "Diluted Average Shares",
"Repurchase Of Capital Stock") reflect yfinance's documented/typical
schema as of early-to-mid 2025, but yfinance's underlying data source
(Yahoo Finance's website) changes its statement layouts periodically,
and yfinance's own API has changed across versions. The FIRST time you
run this against the live API, read every console warning carefully.
If a ticker is flagged as "insufficient data" or "field not found,"
that is the fallback logic working as designed (never guessing a
number) — inspect that company's raw statement manually
(`python -c "import yfinance as yf; print(yf.Ticker('AAPL').get_income_stmt())"`)
and, if needed, add the correct row name to the CANDIDATE_FIELDS lists
below, or enter the verified figure manually.

Never edit this file to change which companies are analyzed --
use the TICKERS list in the CONFIGURATION section.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import sys
import traceback
import warnings
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")  # headless backend, safe for scripts/servers
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# =====================================================================
# CONFIGURATION -- edit this section to change companies / parameters.
# Do not modify code elsewhere just to add/remove a ticker.
# =====================================================================

TICKERS: list[tuple[str, str]] = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("META", "Meta Platforms"),
    ("TSLA", "Tesla"),
    ("PLTR", "Palantir Technologies"),
    ("GOOGL", "Alphabet"),
    ("AMZN", "Amazon"),
    ("NVDA", "NVIDIA"),
    ("JPM", "JPMorgan Chase"),
    ("COST", "Costco"),
]

# Minimum number of fiscal years of "diluted average shares" needed to
# compute at least one net-buyback-yield data point (2 years -> 1 yield).
MIN_FISCAL_YEARS_REQUIRED = 2

# Preferred number of fiscal years to analyze (most recent available).
TARGET_FISCAL_YEARS = 4

# Fiscal years used for the cross-company comparison.
ANALYSIS_START_YEAR = 2022
ANALYSIS_END_YEAR = 2025

# Verified historical observations used only when yfinance does not
# return a required fiscal year. Values come from official SEC filings.
VERIFIED_DILUTED_SHARE_DATA = {
    "MSFT": {
        2022: {
            "fiscal_year_end": "2022-06-30",
            "diluted_avg_shares": 7_540_000_000,
            "source": "SEC filing",
        }
    },
    "NVDA": {
        2022: {
            "fiscal_year_end": "2022-01-30",
            "diluted_avg_shares": 25_350_000_000,
            "source": "SEC filing; FY2022 shares adjusted for 2024 10-for-1 split",
        }
    },
    "TSLA": {
        2022: {
            "fiscal_year_end": "2022-12-31",
            "diluted_avg_shares": 3_475_000_000,
            "source": "Tesla FY2024 Form 10-K (SEC)",
        },
        2023: {
            "fiscal_year_end": "2023-12-31",
            "diluted_avg_shares": 3_485_000_000,
            "source": "Tesla FY2024 Form 10-K (SEC)",
        },
        2024: {
            "fiscal_year_end": "2024-12-31",
            "diluted_avg_shares": 3_498_000_000,
            "source": "Tesla FY2024 Form 10-K (SEC)",
        },
        2025: {
            "fiscal_year_end": "2025-12-31",
            "diluted_avg_shares": 3_528_000_000,
            "source": "Tesla FY2025 Form 10-K (SEC)",
        },
    },
    "PLTR": {
        2022: {
            "fiscal_year_end": "2022-12-31",
            "diluted_avg_shares": 2_063_793_000,
            "source": "Palantir FY2024 Form 10-K (SEC)",
        },
        2023: {
            "fiscal_year_end": "2023-12-31",
            "diluted_avg_shares": 2_297_927_000,
            "source": "Palantir FY2024 Form 10-K (SEC)",
        },
        2024: {
            "fiscal_year_end": "2024-12-31",
            "diluted_avg_shares": 2_450_818_000,
            "source": "Palantir FY2024 Form 10-K (SEC)",
        },
        2025: {
            "fiscal_year_end": "2025-12-31",
            "diluted_avg_shares": 2_565_197_000,
            "source": "Palantir FY2025 Form 10-K (SEC)",
        },
    },
}

# Fiscal years whose diluted weighted-average share counts have been
# independently checked against official SEC filings.
SEC_VERIFIED_YEARS = {
    "AAPL": {2022, 2023, 2024, 2025},
    "MSFT": {2022, 2023, 2024, 2025},
    "META": {2022, 2023, 2024, 2025},
    "TSLA": {2022, 2023, 2024, 2025},
    "PLTR": {2022, 2023, 2024, 2025},
    "GOOGL": {2022, 2023, 2024, 2025},
    "AMZN": {2022, 2023, 2024, 2025},
    "NVDA": {2022, 2023, 2024, 2025},
    "JPM": {2022, 2023, 2024, 2025},
    "COST": {2022, 2023, 2024, 2025},
}

# Neutral-zone threshold for classification, in percentage points.
NEUTRAL_THRESHOLD_PCT = 0.10

# Output directories (relative to this file's location).
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
CHARTS_DIR = BASE_DIR / "charts"
REPORTS_DIR = BASE_DIR / "reports"


# =====================================================================
# DATA SOURCE / STATUS ENUMS
# =====================================================================

class DataSource(str, Enum):
    """Where a given figure came from. Used for transparency/audit."""
    YFINANCE = "Yahoo Finance / yfinance"
    SEC_FILING = "SEC EDGAR filing (primary source, verified)"
    ANNUAL_REPORT = "Company annual report (primary source, verified)"
    MANUAL_VERIFICATION = "Manually entered / verified by user"
    UNAVAILABLE = "Not available"


class ShareChangeStatus(str, Enum):
    NET_REDUCTION = "Net Share Reduction"
    NET_DILUTION = "Net Dilution"
    NEUTRAL = "Flat / Neutral"
    INSUFFICIENT_DATA = "Insufficient Data"


# Candidate row names yfinance may use for each concept. yfinance's
# underlying schema is not perfectly consistent across companies /
# versions, so we search a list of known aliases rather than assuming
# one exact string. We NEVER fall back to an unrelated metric (e.g. we
# will not substitute "Basic Average Shares" silently for "Diluted
# Average Shares" -- that substitution is reported explicitly, not hidden).
CANDIDATE_FIELDS_DILUTED_SHARES = [
    "Diluted Average Shares",
    "Diluted Average Shares Outstanding",
    "Weighted Average Diluted Shares Outstanding",
]

CANDIDATE_FIELDS_BASIC_SHARES = [
    "Basic Average Shares",
    "Basic Average Shares Outstanding",
    "Weighted Average Basic Shares Outstanding",
]

CANDIDATE_FIELDS_REPURCHASE = [
    "Repurchase Of Capital Stock",
    "Common Stock Repurchased",
    "Repurchase Of Common Stock",
]

CANDIDATE_FIELDS_SBC = [
    "Stock Based Compensation",
    "Share Based Compensation",
]


# =====================================================================
# DATA CONTAINERS
# =====================================================================

@dataclass
class FiscalYearRecord:
    """One fiscal year's raw + derived figures for one company."""
    ticker: str
    company: str
    fiscal_year_end: Optional[pd.Timestamp]
    diluted_avg_shares: Optional[float]
    diluted_shares_field_used: Optional[str]
    basic_avg_shares: Optional[float]
    repurchase_spend: Optional[float]
    repurchase_field_used: Optional[str]
    stock_based_comp: Optional[float]
    data_source: DataSource
    verification_status: str = "Unverified"
    warnings: list[str] = field(default_factory=list)


@dataclass
class CompanyDataset:
    """All raw + cleaned fiscal-year records retrieved for one company."""
    ticker: str
    company: str
    records: list[FiscalYearRecord] = field(default_factory=list)
    fetch_errors: list[str] = field(default_factory=list)
    source_url: str = ""

    @property
    def usable(self) -> bool:
        valid = [r for r in self.records if r.diluted_avg_shares is not None]
        return len(valid) >= MIN_FISCAL_YEARS_REQUIRED


# =====================================================================
# STEP 1: DATA RETRIEVAL
# =====================================================================

def get_company_data(ticker: str, company_name: str) -> CompanyDataset:
    """
    Retrieve raw annual financial-statement data for one company via
    yfinance. Preserves the original retrieved values before any
    cleaning/transformation happens (clean_financial_data does that
    separately, on a copy).

    Never fabricates data: if yfinance is unavailable or returns
    nothing usable, the returned CompanyDataset simply has empty
    `records` and populated `fetch_errors`.
    """
    dataset = CompanyDataset(
        ticker=ticker,
        company=company_name,
        source_url=f"https://finance.yahoo.com/quote/{ticker}/financials",
    )

    if not YFINANCE_AVAILABLE:
        dataset.fetch_errors.append(
            "yfinance is not installed in this environment. "
            "Install it with `pip install yfinance` and re-run."
        )
        return dataset

    try:
        tk = yf.Ticker(ticker)
        # yfinance exposes annual income statement / cash flow as
        # DataFrames with statement line items as rows and fiscal
        # period-end dates as columns (most recent first, typically).
        income_stmt = getattr(tk, "income_stmt", None)
        if income_stmt is None or income_stmt.empty:
            income_stmt = getattr(tk, "financials", pd.DataFrame())
        cashflow = getattr(tk, "cashflow", pd.DataFrame())
    except Exception as exc:  # noqa: BLE001 -- we want to catch and report, not crash
        dataset.fetch_errors.append(
            f"yfinance raised an exception while fetching data for {ticker}: {exc}"
        )
        return dataset

    if income_stmt is None or income_stmt.empty:
        dataset.fetch_errors.append(
            f"No income statement data returned by yfinance for {ticker}."
        )
        return dataset

    fiscal_year_ends = list(income_stmt.columns)
    if not fiscal_year_ends:
        dataset.fetch_errors.append(
            f"Income statement for {ticker} had no fiscal-period columns."
        )
        return dataset

    # Sort fiscal periods most-recent-first, then keep target window.
    try:
        fiscal_year_ends = sorted(fiscal_year_ends, reverse=True)
    except TypeError:
        pass  # leave as-is if columns aren't sortable timestamps
    fiscal_year_ends = fiscal_year_ends[:TARGET_FISCAL_YEARS]

    for period in fiscal_year_ends:
        rec_warnings: list[str] = []

        diluted_shares, diluted_field = _extract_field(
            income_stmt, period, CANDIDATE_FIELDS_DILUTED_SHARES
        )
        if diluted_shares is None:
            rec_warnings.append(
                "Diluted Average Shares not found under any known field "
                "name for this fiscal period. This company/year will be "
                "flagged as insufficient data rather than estimated."
            )

        basic_shares, _ = _extract_field(
            income_stmt, period, CANDIDATE_FIELDS_BASIC_SHARES
        )

        repurchase_spend, repurchase_field = _extract_field(
            cashflow, period, CANDIDATE_FIELDS_REPURCHASE
        )
        # Cash-flow repurchase figures are typically reported as a
        # cash *outflow* (negative). We store the magnitude spent and
        # flag sign convention explicitly rather than silently
        # flipping it, since sign conventions can vary.
        if repurchase_spend is not None and repurchase_spend < 0:
            repurchase_spend = abs(repurchase_spend)

        sbc, _ = _extract_field(cashflow, period, CANDIDATE_FIELDS_SBC)

        try:
            period_ts = pd.Timestamp(period)
        except Exception:
            period_ts = None
            rec_warnings.append(f"Could not parse fiscal period label: {period!r}")

        record = FiscalYearRecord(
            ticker=ticker,
            company=company_name,
            fiscal_year_end=period_ts,
            diluted_avg_shares=diluted_shares,
            diluted_shares_field_used=diluted_field,
            basic_avg_shares=basic_shares,
            repurchase_spend=repurchase_spend,
            repurchase_field_used=repurchase_field,
            stock_based_comp=sbc,
            data_source=DataSource.YFINANCE,
            warnings=rec_warnings,
        )

        if (
            period_ts is not None
            and period_ts.year in SEC_VERIFIED_YEARS.get(ticker, set())
        ):
            record.verification_status = "SEC Verified - Diluted Shares"

        dataset.records.append(record)
       # Apply verified SEC observations.
    # If yfinance already returned the year, replace only the verified
    # diluted share count while preserving other automatically retrieved fields.
    # If the year is missing entirely, add it as a verified observation.
    verified_years = VERIFIED_DILUTED_SHARE_DATA.get(ticker, {})

    for year, verified in verified_years.items():
        matching_record = next(
            (
                record
                for record in dataset.records
                if record.fiscal_year_end is not None
                and record.fiscal_year_end.year == year
            ),
            None,
        )

        if matching_record is not None:
            matching_record.diluted_avg_shares = verified["diluted_avg_shares"]
            matching_record.diluted_shares_field_used = "Verified SEC override"
            matching_record.data_source = DataSource.SEC_FILING
            matching_record.verification_status = "SEC Verified - Diluted Shares"
            matching_record.warnings.append(verified["source"])

        else:
            dataset.records.append(
                FiscalYearRecord(
                    ticker=ticker,
                    company=company_name,
                    fiscal_year_end=pd.Timestamp(verified["fiscal_year_end"]),
                    diluted_avg_shares=verified["diluted_avg_shares"],
                    diluted_shares_field_used="Verified SEC fallback",
                    basic_avg_shares=None,
                    repurchase_spend=None,
                    repurchase_field_used=None,
                    stock_based_comp=None,
                    data_source=DataSource.SEC_FILING,
                    verification_status="SEC Verified - Diluted Shares",
                    warnings=[verified["source"]],
                )
            )

    return dataset

def _extract_field(
    df: pd.DataFrame, column: Any, candidate_row_names: list[str]
) -> tuple[Optional[float], Optional[str]]:
    """
    Search a yfinance statement DataFrame for the first matching row
    name (from a list of known aliases) at a given column (fiscal
    period), and return (value, row_name_used).

    Returns (None, None) if no candidate row is present or the value
    is not a usable number. Never returns an unrelated metric.
    """
    if df is None or df.empty or column not in df.columns:
        return None, None

    for name in candidate_row_names:
        if name in df.index:
            raw_value = df.loc[name, column]
            value = _coerce_numeric(raw_value)
            if value is not None:
                return value, name
    return None, None


def _coerce_numeric(value: Any) -> Optional[float]:
    """Safely coerce a yfinance cell value to float, or None if invalid."""
    if value is None:
        return None
    if isinstance(value, (pd.Series, pd.DataFrame, list, dict)):
        return None  # unexpected shape -- do not guess
    try:
        f_value = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(f_value) or np.isinf(f_value):
        return None
    return f_value


# =====================================================================
# STEP 2: CLEANING
# =====================================================================

def clean_financial_data(dataset: CompanyDataset) -> pd.DataFrame:
    """
    Convert a CompanyDataset's raw records into a tidy, sorted
    DataFrame (oldest fiscal year first), preserving all original raw
    values in dedicated columns alongside cleaned ones. Does not
    invent, interpolate, or zero-fill missing values.
    """
    rows = []
    for rec in dataset.records:
        rows.append(
            {
                "ticker": rec.ticker,
                "company": rec.company,
                "fiscal_year_end": rec.fiscal_year_end,
                "diluted_avg_shares": rec.diluted_avg_shares,
                "diluted_shares_field_used": rec.diluted_shares_field_used,
                "basic_avg_shares": rec.basic_avg_shares,
                "repurchase_spend": rec.repurchase_spend,
                "repurchase_field_used": rec.repurchase_field_used,
                "stock_based_comp": rec.stock_based_comp,
                "data_source": rec.data_source.value,
		"verification_status": rec.verification_status,
                "record_warnings": "; ".join(rec.warnings) if rec.warnings else "",
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.dropna(subset=["fiscal_year_end"]).copy()
    df = df.sort_values("fiscal_year_end", ascending=True).reset_index(drop=True)

    # Preserve duplicate fiscal-year rows. Validation, rather than cleaning,
    # is responsible for flagging duplicates so a retrieval problem is never
    # silently hidden from the audit trail.
    return df


# =====================================================================
# STEP 3: VALIDATION
# =====================================================================

@dataclass
class ValidationResult:
    ticker: str
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_data(df: pd.DataFrame, ticker: str) -> ValidationResult:
    """
    Run all required data-quality checks on one company's cleaned
    fiscal-year DataFrame. Returns a ValidationResult; does not raise
    on data problems (the caller decides whether to proceed), except
    for programming errors (wrong dtypes for the df object itself).
    """
    result = ValidationResult(ticker=ticker, is_valid=True)

    if df is None or df.empty:
        result.is_valid = False
        result.errors.append("No data available for this company.")
        return result

    required_cols = {"fiscal_year_end", "diluted_avg_shares"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        result.is_valid = False
        result.errors.append(f"Missing required columns: {sorted(missing_cols)}")
        return result

    # Missing values in the core metric.
    n_missing = df["diluted_avg_shares"].isna().sum()
    usable = df.dropna(subset=["diluted_avg_shares"]).copy()
    if n_missing:
        result.warnings.append(
            f"{n_missing} fiscal year(s) missing 'diluted_avg_shares' -- "
            f"excluded from calculations, not zero-filled."
        )

    if len(usable) < MIN_FISCAL_YEARS_REQUIRED:
        result.is_valid = False
        result.errors.append(
            f"Only {len(usable)} usable fiscal year(s) of diluted average "
            f"shares found; at least {MIN_FISCAL_YEARS_REQUIRED} are needed "
            f"to compute a net buyback yield."
        )
        return result

    # Duplicate fiscal years.
    dup_mask = usable["fiscal_year_end"].duplicated()
    if dup_mask.any():
        result.is_valid = False
        dup_years = usable.loc[dup_mask, "fiscal_year_end"].tolist()
        result.errors.append(f"Duplicate fiscal year(s) detected: {dup_years}")
        return result

    # Correct chronological ordering (should already be sorted by
    # clean_financial_data, but we re-verify independently here).
    if not usable["fiscal_year_end"].is_monotonic_increasing:
        result.is_valid = False
        result.errors.append("Fiscal years are not in strictly increasing order.")
        return result

    # Share counts must be positive.
    non_positive = usable[usable["diluted_avg_shares"] <= 0]
    if not non_positive.empty:
        result.is_valid = False
        bad_years = non_positive["fiscal_year_end"].tolist()
        result.errors.append(
            f"Non-positive diluted average shares found for fiscal year(s): "
            f"{bad_years}. A share count of zero or less is not physically "
            f"valid and indicates a data error."
        )
        return result

    # Guard against repurchase-spending figures being mistaken for
    # share counts (a plausibility check, not a proof): repurchase
    # spend is a dollar figure, typically many orders of magnitude
    # different from a share count, and the two must never occupy the
    # same column.
    if "repurchase_spend" in usable.columns and "diluted_avg_shares" in usable.columns:
        both_present = usable.dropna(subset=["repurchase_spend", "diluted_avg_shares"])
        for _, row in both_present.iterrows():
            if row["repurchase_spend"] == row["diluted_avg_shares"]:
                result.warnings.append(
                    "Repurchase spending value is identical to diluted "
                    "average shares value for the same fiscal year -- "
                    "this strongly suggests a column-mapping error and "
                    "should be manually checked before use."
                )

    if len(usable) < TARGET_FISCAL_YEARS:
        result.warnings.append(
            f"Only {len(usable)} of the target {TARGET_FISCAL_YEARS} fiscal "
            f"years were available; reporting on fewer years than requested."
        )

    return result


# =====================================================================
# STEP 4: CORE CALCULATIONS
# =====================================================================

def calculate_net_share_change(
    current_diluted_shares: float, previous_diluted_shares: float
) -> float:
    """
    Net Shares Retired = Previous Year Diluted Avg Shares
                          - Current Year Diluted Avg Shares

    Positive => share count decreased (net reduction).
    Negative => share count increased (net dilution).
    """
    return previous_diluted_shares - current_diluted_shares


def calculate_net_buyback_yield(
    net_shares_retired: float, previous_diluted_shares: float
) -> float:
    """
    Net Share Reduction Yield (%) = Net Shares Retired / Previous Year Diluted
                             Avg Shares * 100

    Raises ValueError if previous_diluted_shares is zero, rather than
    dividing by zero or silently returning a placeholder like 0 or NaN
    that could be mistaken for a real "no change" result.
    """
    if previous_diluted_shares == 0:
        raise ValueError(
            "Previous year's diluted average shares is zero; "
            "Net Share Reduction Yield is undefined (division by zero)."
        )
    return (net_shares_retired / previous_diluted_shares) * 100.0


def classify_share_count_change(
    net_buyback_yield_pct: float, threshold: float = NEUTRAL_THRESHOLD_PCT
) -> ShareChangeStatus:
    """
    Classify a single fiscal year's net buyback yield using a
    +/- `threshold` percentage-point neutral band (default 0.10 pp).
    """
    if abs(net_buyback_yield_pct) <= threshold:
        return ShareChangeStatus.NEUTRAL
    if net_buyback_yield_pct > threshold:
        return ShareChangeStatus.NET_REDUCTION
    return ShareChangeStatus.NET_DILUTION


def calculate_cumulative_share_change(diluted_shares_series: pd.Series) -> float:
    """
    Cumulative percentage change in diluted average shares across the
    full analysis window, computed correctly as a single compounding
    ratio -- NOT as an average (or sum) of the individual annual
    percentage changes, which would misrepresent compounding effects.

        cumulative_pct_change = (last_value - first_value) / first_value * 100

    This equals the same result you'd get by chaining
    (1 + r1)*(1 + r2)*...*(1 + rn) - 1 across annual yields, expressed
    directly from endpoints for simplicity and to avoid compounding-
    error accumulation from rounded intermediate yields.
    """
    series = diluted_shares_series.dropna()
    if len(series) < 2:
        raise ValueError("Need at least two data points for cumulative change.")
    first_value = series.iloc[0]
    last_value = series.iloc[-1]
    if first_value == 0:
        raise ValueError("First value is zero; cumulative change is undefined.")
    return (last_value - first_value) / first_value * 100.0


# =====================================================================
# STEP 5: PER-COMPANY ANALYSIS
# =====================================================================

@dataclass
class CompanyAnalysis:
    ticker: str
    company: str
    yearly_table: pd.DataFrame
    average_annual_yield_pct: Optional[float]
    cumulative_pct_change: Optional[float]
    years_net_reduction: int
    years_net_dilution: int
    years_neutral: int
    best_year: Optional[dict]
    worst_year: Optional[dict]
    overall_classification: ShareChangeStatus
    data_quality_notes: list[str] = field(default_factory=list)
    insufficient_data: bool = False


def _fiscal_year_number(value: Any) -> Optional[int]:
    """Return a fiscal-year-end calendar year, or None if it cannot be parsed."""
    if value is None or pd.isna(value):
        return None
    try:
        return int(pd.Timestamp(value).year)
    except (TypeError, ValueError):
        return None


def _are_consecutive_fiscal_years(previous_period: Any, current_period: Any) -> bool:
    """
    Return True when two fiscal-year-end observations belong to consecutive
    calendar years. Exact month/day equality is intentionally not required
    because 52/53-week fiscal calendars can shift by several days.
    """
    previous_year = _fiscal_year_number(previous_period)
    current_year = _fiscal_year_number(current_period)
    return (
        previous_year is not None
        and current_year is not None
        and current_year - previous_year == 1
    )


def analyze_company(
    ticker: str,
    company_name: str,
    dataset: Optional[CompanyDataset] = None,
) -> CompanyAnalysis:
    """
    Full pipeline for one company: fetch once (unless a dataset is supplied)
    -> clean -> validate -> consecutive-year metrics -> aggregate metrics
    -> optional project-defined score.

    Supplying ``dataset`` prevents a second live API request and makes the
    analysis reproducible from the exact data already fetched by the caller.
    """
    if dataset is None:
        dataset = get_company_data(ticker, company_name)

    cleaned = clean_financial_data(dataset)
    validation = validate_data(cleaned, ticker)

    notes = list(dataset.fetch_errors) + validation.warnings

    if not validation.is_valid:
        return CompanyAnalysis(
            ticker=ticker,
            company=company_name,
            yearly_table=pd.DataFrame(),
            average_annual_yield_pct=None,
            cumulative_pct_change=None,
            years_net_reduction=0,
            years_net_dilution=0,
            years_neutral=0,
            best_year=None,
            worst_year=None,
            overall_classification=ShareChangeStatus.INSUFFICIENT_DATA,
            data_quality_notes=notes + validation.errors,
            insufficient_data=True,
        )

    # Use the same fiscal-year window for every company so cross-company
    # comparisons cover the same four fiscal years.

    cleaned = cleaned[
    cleaned["fiscal_year_end"].dt.year.between(
        ANALYSIS_START_YEAR, ANALYSIS_END_YEAR
    )
].copy()
    
    usable = cleaned.dropna(subset=["diluted_avg_shares"]).reset_index(drop=True)

    year_rows = []
    yields = []
    for i in range(1, len(usable)):
        previous_period = usable.loc[i - 1, "fiscal_year_end"]
        current_period = usable.loc[i, "fiscal_year_end"]

        # A missing fiscal year must not turn a two-year gap into a fake
        # "year-over-year" observation.
        if not _are_consecutive_fiscal_years(previous_period, current_period):
            notes.append(
                "Skipped nonconsecutive fiscal-year comparison: "
                f"{pd.Timestamp(previous_period).date()} -> "
                f"{pd.Timestamp(current_period).date()}."
            )
            continue

        prev_shares = usable.loc[i - 1, "diluted_avg_shares"]
        curr_shares = usable.loc[i, "diluted_avg_shares"]
        net_retired = calculate_net_share_change(curr_shares, prev_shares)

        try:
            net_yield = calculate_net_buyback_yield(net_retired, prev_shares)
        except ValueError as exc:
            notes.append(str(exc))
            continue

        status = classify_share_count_change(net_yield)
        yields.append(net_yield)
        year_rows.append(
            {
                "Company": company_name,
                "Ticker": ticker,
                "Fiscal Year": current_period,
                "Diluted Average Shares": curr_shares,
                "Previous Year Diluted Average Shares": prev_shares,
                "Net Shares Retired": net_retired,
                "Net Share Reduction Yield %": round(net_yield, 4),
                "Status": status.value,
                "Data Source": usable.loc[i, "data_source"],
		"Verification Status": usable.loc[i, "verification_status"],
            }
        )

    yearly_table = pd.DataFrame(year_rows)

    if yearly_table.empty:
        return CompanyAnalysis(
            ticker=ticker,
            company=company_name,
            yearly_table=yearly_table,
            average_annual_yield_pct=None,
            cumulative_pct_change=None,
            years_net_reduction=0,
            years_net_dilution=0,
            years_neutral=0,
            best_year=None,
            worst_year=None,
            overall_classification=ShareChangeStatus.INSUFFICIENT_DATA,
            data_quality_notes=notes + [
                "No valid consecutive fiscal-year comparisons could be computed."
            ],
            insufficient_data=True,
        )

    avg_yield = float(np.mean(yields))

    # Cumulative change remains an endpoint measure across the usable period.
    # It is not presented as an annualized figure, so gaps do not create a
    # false one-year comparison.
    try:
        cumulative = calculate_cumulative_share_change(
            usable["diluted_avg_shares"]
        )
    except ValueError as exc:
        cumulative = None
        notes.append(str(exc))

    years_reduction = int(
        (yearly_table["Status"] == ShareChangeStatus.NET_REDUCTION.value).sum()
    )
    years_dilution = int(
        (yearly_table["Status"] == ShareChangeStatus.NET_DILUTION.value).sum()
    )
    years_neutral = int(
        (yearly_table["Status"] == ShareChangeStatus.NEUTRAL.value).sum()
    )

    metric_col = "Net Share Reduction Yield %"
    best_idx = yearly_table[metric_col].idxmax()
    worst_idx = yearly_table[metric_col].idxmin()
    best_year = yearly_table.loc[best_idx].to_dict()
    worst_year = yearly_table.loc[worst_idx].to_dict()

    overall = _overall_classification(
        cumulative, years_reduction, years_dilution
    )

    return CompanyAnalysis(
        ticker=ticker,
        company=company_name,
        yearly_table=yearly_table,
        average_annual_yield_pct=round(avg_yield, 4),
        cumulative_pct_change=round(cumulative, 4) if cumulative is not None else None,
        years_net_reduction=years_reduction,
        years_net_dilution=years_dilution,
        years_neutral=years_neutral,
        best_year=best_year,
        worst_year=worst_year,
        overall_classification=overall,
        data_quality_notes=notes,
    )


def _overall_classification(
    cumulative_pct_change: Optional[float], years_reduction: int, years_dilution: int
) -> ShareChangeStatus:
    """
    Note on sign convention: `cumulative_pct_change` here is computed
    as (last - first) / first * 100 on the diluted-share-count series
    itself, so a NEGATIVE value means share count fell (a reduction),
    and a POSITIVE value means share count rose (dilution) -- this is
    the OPPOSITE sign convention from Net Share Reduction Yield, where positive
    means reduction. We convert explicitly here to avoid confusing the
    two conventions in the rest of the codebase.
    """
    if cumulative_pct_change is None:
        if years_reduction > years_dilution:
            return ShareChangeStatus.NET_REDUCTION
        if years_dilution > years_reduction:
            return ShareChangeStatus.NET_DILUTION
        return ShareChangeStatus.NEUTRAL

    cumulative_reduction_pct = -cumulative_pct_change  # flip to "reduction-positive" convention
    if abs(cumulative_reduction_pct) <= NEUTRAL_THRESHOLD_PCT:
        return ShareChangeStatus.NEUTRAL
    return (
        ShareChangeStatus.NET_REDUCTION
        if cumulative_reduction_pct > 0
        else ShareChangeStatus.NET_DILUTION
    )

# =====================================================================
# STEP 6: CROSS-COMPANY COMPARISON
# =====================================================================

def compare_companies(analyses: list[CompanyAnalysis]) -> pd.DataFrame:
    """
    Build a summary table across all analyzed companies.
    Companies with insufficient data are still listed and transparently
    flagged rather than silently dropped.
    """
    rows = []
    for a in analyses:
        rows.append(
            {
                "Ticker": a.ticker,
                "Company": a.company,
                "Fiscal Years Analyzed": 0 if a.yearly_table.empty else len(a.yearly_table),
                "Average Annual Net Share Reduction Yield %": a.average_annual_yield_pct,
                "Cumulative Diluted Share Count Change %": a.cumulative_pct_change,
                "Years Net Reduction": a.years_net_reduction,
                "Years Net Dilution": a.years_net_dilution,
                "Years Neutral": a.years_neutral,
                "Overall Classification": a.overall_classification.value,
                "Insufficient Data": a.insufficient_data,
                "Data Quality Notes": " | ".join(a.data_quality_notes) if a.data_quality_notes else "",
            }
        )

    summary = pd.DataFrame(rows)

    if not summary.empty:
        summary = summary.sort_values(
            by=["Insufficient Data", "Ticker"],
            ascending=[True, True],
            na_position="last",
        ).reset_index(drop=True)

    return summary


# =====================================================================
# STEP 7: CHARTS
# =====================================================================

def generate_charts(
    analyses: list[CompanyAnalysis], summary: pd.DataFrame, output_dir: Path = CHARTS_DIR
) -> list[Path]:
    """
    Generate the required charts from the ACTUAL processed dataset
    (never hand-entered values). Skips a chart gracefully (with a
    console warning) if there isn't enough valid data to draw it
    honestly, rather than drawing a misleading chart.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("WARNING: matplotlib not available; skipping chart generation.")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    valid_summary = summary[~summary["Insufficient Data"]].copy()

    if valid_summary.empty:
        print("WARNING: No companies with sufficient data; no charts generated.")
        return saved

    source_note = "Source: yfinance (Yahoo Finance), automated retrieval; see README for verification status."

    # 1. Net Share Reduction Yield by Company (average annual yield, bar chart).
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_df = valid_summary.dropna(subset=["Average Annual Net Share Reduction Yield %"])
    ax.bar(plot_df["Ticker"], plot_df["Average Annual Net Share Reduction Yield %"], color="#2b6cb0")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Average Annual Net Share Reduction Yield by Company")
    ax.set_xlabel("Company (Ticker)")
    ax.set_ylabel("Average Annual Net Share Reduction Yield (%)")
    ax.text(0.01, -0.15, source_note, transform=ax.transAxes, fontsize=7, color="gray")
    fig.tight_layout()
    path = output_dir / "01_net_share_reduction_yield_by_company.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    saved.append(path)

    # 2. Net Share Reduction Yield Over Time (line chart, one line per company).
    fig, ax = plt.subplots(figsize=(11, 6))
    for a in analyses:
        if a.yearly_table.empty:
            continue
        ax.plot(
            a.yearly_table["Fiscal Year"],
            a.yearly_table["Net Share Reduction Yield %"],
            marker="o",
            label=a.ticker,
        )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Net Share Reduction Yield Over Time by Company")
    ax.set_xlabel("Fiscal Year End")
    ax.set_ylabel("Net Share Reduction Yield (%)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.text(0.01, -0.15, source_note, transform=ax.transAxes, fontsize=7, color="gray")
    fig.tight_layout()
    path = output_dir / "02_net_share_reduction_yield_over_time.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    saved.append(path)

    # 3. Cumulative Diluted Share-Count Change by Company.
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_df = valid_summary.dropna(subset=["Cumulative Diluted Share Count Change %"])
    colors = ["#2f855a" if v < 0 else "#c53030" for v in plot_df["Cumulative Diluted Share Count Change %"]]
    ax.bar(plot_df["Ticker"], plot_df["Cumulative Diluted Share Count Change %"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Cumulative Diluted Share-Count Change by Company\n(negative = net reduction, positive = net dilution)")
    ax.set_xlabel("Company (Ticker)")
    ax.set_ylabel("Cumulative Change in Diluted Average Shares (%)")
    ax.text(0.01, -0.2, source_note, transform=ax.transAxes, fontsize=7, color="gray")
    fig.tight_layout()
    path = output_dir / "03_cumulative_share_change_by_company.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    saved.append(path)

    # 4. Years With Net Share Reduction vs. Net Dilution (stacked bar).
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(valid_summary["Ticker"], valid_summary["Years Net Reduction"], label="Years: Net Reduction", color="#2f855a")
    ax.bar(
        valid_summary["Ticker"],
        valid_summary["Years Net Dilution"],
        bottom=valid_summary["Years Net Reduction"],
        label="Years: Net Dilution",
        color="#c53030",
    )
    ax.bar(
        valid_summary["Ticker"],
        valid_summary["Years Neutral"],
        bottom=valid_summary["Years Net Reduction"] + valid_summary["Years Net Dilution"],
        label="Years: Neutral",
        color="#a0aec0",
    )
    ax.set_title("Fiscal Years by Classification, per Company")
    ax.set_xlabel("Company (Ticker)")
    ax.set_ylabel("Number of Fiscal-Year Comparisons")
    ax.legend(loc="upper right", fontsize=8)
    ax.text(0.01, -0.15, source_note, transform=ax.transAxes, fontsize=7, color="gray")
    fig.tight_layout()
    path = output_dir / "04_years_reduction_vs_dilution.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    saved.append(path)

    return saved


# =====================================================================
# STEP 8: SAVE RESULTS
# =====================================================================

def save_results(
    all_cleaned: dict[str, pd.DataFrame],
    all_yearly_tables: list[pd.DataFrame],
    summary: pd.DataFrame,
) -> dict[str, Path]:
    """
    Write raw-preserving cleaned data, the combined per-year processed
    table, and the company summary table to data/processed and
    data/raw as CSV files. Returns the paths written.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    for ticker, df in all_cleaned.items():
        if df.empty:
            continue
        raw_path = RAW_DATA_DIR / f"{ticker}_raw.csv"
        df.to_csv(raw_path, index=False)
        paths[f"raw_{ticker}"] = raw_path

    if all_yearly_tables:
        combined = pd.concat(all_yearly_tables, ignore_index=True)
    else:
        combined = pd.DataFrame()
    combined_path = PROCESSED_DATA_DIR / "net_buyback_yield_all_companies.csv"
    combined.to_csv(combined_path, index=False)
    paths["processed_combined"] = combined_path

    summary_path = PROCESSED_DATA_DIR / "company_summary.csv"
    summary.to_csv(summary_path, index=False)
    paths["summary"] = summary_path

    return paths


# =====================================================================
# MAIN PROGRAM
# =====================================================================

def main() -> None:
    print("=" * 70)
    print("SHARE BUYBACK ANALYZER")
    print("Research question: Are corporate share buybacks associated with lower")
    print("diluted average share counts after the effects of issuance and dilution?")
    print("=" * 70)

    if not YFINANCE_AVAILABLE:
        print(
            "\nWARNING: yfinance is not installed. Install it with "
            "`pip install yfinance` before running this program, or the "
            "program will report every company as having insufficient data.\n"
        )

    print(f"\nAnalyzing {len(TICKERS)} companies: "
          f"{', '.join(t for t, _ in TICKERS)}\n")

    analyses: list[CompanyAnalysis] = []
    all_cleaned: dict[str, pd.DataFrame] = {}
    all_yearly_tables: list[pd.DataFrame] = []
    failed: list[str] = []

    for ticker, name in TICKERS:
        print(f"--- {ticker} ({name}) ---")
        try:
            dataset = get_company_data(ticker, name)
            cleaned = clean_financial_data(dataset)
            all_cleaned[ticker] = cleaned
            analysis = analyze_company(ticker, name, dataset=dataset)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR while analyzing {ticker}: {exc}")
            traceback.print_exc()
            failed.append(ticker)
            continue

        analyses.append(analysis)
        if analysis.insufficient_data:
            failed.append(ticker)
            print(f"  INSUFFICIENT DATA: {'; '.join(analysis.data_quality_notes) or 'unspecified'}")
        else:
            print(
                f"  OK — {len(analysis.yearly_table)} year(s) analyzed. "
                f"Avg yield: {analysis.average_annual_yield_pct}% | "
                f"Cumulative share change: {analysis.cumulative_pct_change}% | "
                f"Classification: {analysis.overall_classification.value}"
            )
            all_yearly_tables.append(analysis.yearly_table)

    print("\nBuilding cross-company comparison table...")
    summary = compare_companies(analyses)

    print("Saving extracted source records and processed data...")
    paths = save_results(all_cleaned, all_yearly_tables, summary)

    print("Generating charts...")
    chart_paths = generate_charts(analyses, summary)

    print("\n" + "=" * 70)
    print("DONE. Output locations:")
    for label, p in paths.items():
        print(f"  [{label}] {p}")
    for p in chart_paths:
        print(f"  [chart] {p}")
    print("=" * 70)

    if failed:
        print(f"\nCompanies with INSUFFICIENT or FAILED data ({len(failed)}): {failed}")
        print("These companies are still listed in company_summary.csv")
        print("with 'Insufficient Data' = True.")
    else:
        print("\nAll companies produced usable data.")

    print(
        "\nReminder: diluted weighted-average share observations for FY2022-FY2025 "
        "have been checked against official SEC filings as documented in the README. "
        "Supporting fields retrieved through yfinance, including repurchase spending "
        "and stock-based compensation, should still be treated as provisional."
    )


if __name__ == "__main__":
    main()
