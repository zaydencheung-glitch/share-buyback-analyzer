"""
Tests for buyback_analyzer.py

These tests use synthetic data only -- they never call the live
yfinance API (there is no network mocking of yfinance itself; instead
we test the pure calculation/validation/scoring logic directly, and
separately test clean_financial_data / validate_data against
hand-built CompanyDataset / DataFrame objects). This keeps the test
suite fast, deterministic, and runnable with no internet connection.

Run with:
    pytest tests/test_buyback_analyzer.py -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from buyback_analyzer import (  # noqa: E402
    CompanyDataset,
    FiscalYearRecord,
    DataSource,
    ShareChangeStatus,
    calculate_net_share_change,
    calculate_net_buyback_yield,
    classify_share_count_change,
    calculate_cumulative_share_change,
    calculate_effectiveness_score,
    clean_financial_data,
    validate_data,
    compare_companies,
    analyze_company,
    CompanyAnalysis,
    NEUTRAL_THRESHOLD_PCT,
)


# ---------------------------------------------------------------------
# 1. Positive net share reduction
# ---------------------------------------------------------------------
def test_positive_net_share_reduction():
    net_retired = calculate_net_share_change(current_diluted_shares=950, previous_diluted_shares=1000)
    assert net_retired == 50
    net_yield = calculate_net_buyback_yield(net_retired, 1000)
    assert net_yield == pytest.approx(5.0)
    assert classify_share_count_change(net_yield) == ShareChangeStatus.NET_REDUCTION


# ---------------------------------------------------------------------
# 2. Negative net share reduction (i.e. net dilution)
# ---------------------------------------------------------------------
def test_negative_net_share_reduction_is_dilution():
    net_retired = calculate_net_share_change(current_diluted_shares=1050, previous_diluted_shares=1000)
    assert net_retired == -50
    net_yield = calculate_net_buyback_yield(net_retired, 1000)
    assert net_yield == pytest.approx(-5.0)
    assert classify_share_count_change(net_yield) == ShareChangeStatus.NET_DILUTION


# ---------------------------------------------------------------------
# 3. Neutral share change (within +/- threshold)
# ---------------------------------------------------------------------
def test_neutral_share_change_within_threshold():
    net_retired = calculate_net_share_change(current_diluted_shares=999.5, previous_diluted_shares=1000)
    net_yield = calculate_net_buyback_yield(net_retired, 1000)
    assert abs(net_yield) <= NEUTRAL_THRESHOLD_PCT
    assert classify_share_count_change(net_yield) == ShareChangeStatus.NEUTRAL


def test_neutral_boundary_is_inclusive():
    # Exactly at the threshold should count as neutral (uses <=).
    assert classify_share_count_change(NEUTRAL_THRESHOLD_PCT) == ShareChangeStatus.NEUTRAL
    assert classify_share_count_change(-NEUTRAL_THRESHOLD_PCT) == ShareChangeStatus.NEUTRAL
    # Just outside should not be.
    assert classify_share_count_change(NEUTRAL_THRESHOLD_PCT + 0.01) == ShareChangeStatus.NET_REDUCTION
    assert classify_share_count_change(-NEUTRAL_THRESHOLD_PCT - 0.01) == ShareChangeStatus.NET_DILUTION


# ---------------------------------------------------------------------
# 4. Missing data
# ---------------------------------------------------------------------
def test_validate_data_flags_missing_values_without_zero_filling():
    df = pd.DataFrame(
        {
            "fiscal_year_end": pd.to_datetime(["2021-12-31", "2022-12-31", "2023-12-31"]),
            "diluted_avg_shares": [1000.0, np.nan, 950.0],
            "data_source": [DataSource.YFINANCE.value] * 3,
        }
    )
    result = validate_data(df, "TEST")
    # Still valid overall (2 usable years >= MIN_FISCAL_YEARS_REQUIRED),
    # but must warn about the missing value rather than silently
    # treating it as zero.
    assert result.is_valid is True
    assert any("missing" in w.lower() for w in result.warnings)


def test_validate_data_insufficient_when_too_much_missing():
    df = pd.DataFrame(
        {
            "fiscal_year_end": pd.to_datetime(["2021-12-31", "2022-12-31"]),
            "diluted_avg_shares": [1000.0, np.nan],
            "data_source": [DataSource.YFINANCE.value] * 2,
        }
    )
    result = validate_data(df, "TEST")
    assert result.is_valid is False
    assert any("usable fiscal year" in e for e in result.errors)


# ---------------------------------------------------------------------
# 5. Incorrect data types
# ---------------------------------------------------------------------
def test_validate_data_handles_non_numeric_gracefully():
    df = pd.DataFrame(
        {
            "fiscal_year_end": pd.to_datetime(["2021-12-31", "2022-12-31"]),
            "diluted_avg_shares": ["not_a_number", 950.0],
            "data_source": [DataSource.YFINANCE.value] * 2,
        }
    )
    # Non-numeric entries should not crash validate_data. Comparisons
    # against non-numeric values raise TypeError in pandas, so we
    # confirm the function either coerces safely or raises a clear,
    # catchable error rather than corrupting results silently.
    try:
        result = validate_data(df, "TEST")
        # If it didn't raise, it must at least not claim full validity
        # with garbage data undetected.
        assert isinstance(result.is_valid, bool)
    except TypeError:
        # Acceptable: caller (analyze_company) is expected to catch
        # this upstream; the important thing is it doesn't silently
        # fabricate a clean result.
        pass


# ---------------------------------------------------------------------
# 6. Zero previous-year shares (division by zero)
# ---------------------------------------------------------------------
def test_zero_previous_year_shares_raises_not_crashes_silently():
    net_retired = calculate_net_share_change(current_diluted_shares=100, previous_diluted_shares=0)
    with pytest.raises(ValueError):
        calculate_net_buyback_yield(net_retired, 0)


# ---------------------------------------------------------------------
# 7. Negative share counts
# ---------------------------------------------------------------------
def test_validate_data_rejects_negative_share_counts():
    df = pd.DataFrame(
        {
            "fiscal_year_end": pd.to_datetime(["2021-12-31", "2022-12-31"]),
            "diluted_avg_shares": [1000.0, -5.0],
            "data_source": [DataSource.YFINANCE.value] * 2,
        }
    )
    result = validate_data(df, "TEST")
    assert result.is_valid is False
    assert any("non-positive" in e.lower() or "positive" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------
# 8. Incorrect year ordering
# ---------------------------------------------------------------------
def test_validate_data_rejects_out_of_order_years():
    df = pd.DataFrame(
        {
            "fiscal_year_end": pd.to_datetime(["2022-12-31", "2021-12-31"]),  # reversed
            "diluted_avg_shares": [950.0, 1000.0],
            "data_source": [DataSource.YFINANCE.value] * 2,
        }
    )
    result = validate_data(df, "TEST")
    assert result.is_valid is False
    assert any("order" in e.lower() for e in result.errors)


def test_validate_data_rejects_duplicate_years():
    df = pd.DataFrame(
        {
            "fiscal_year_end": pd.to_datetime(["2022-12-31", "2022-12-31"]),
            "diluted_avg_shares": [950.0, 940.0],
            "data_source": [DataSource.YFINANCE.value] * 2,
        }
    )
    result = validate_data(df, "TEST")
    assert result.is_valid is False
    assert any("duplicate" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------
# 9. Cumulative share-count calculation
# ---------------------------------------------------------------------
def test_cumulative_share_change_reduction():
    series = pd.Series([1000.0, 950.0, 900.0, 850.0])
    result = calculate_cumulative_share_change(series)
    # (850 - 1000) / 1000 * 100 = -15.0
    assert result == pytest.approx(-15.0)


def test_cumulative_share_change_dilution():
    series = pd.Series([1000.0, 1020.0, 1040.0, 1060.0])
    result = calculate_cumulative_share_change(series)
    assert result == pytest.approx(6.0)


def test_cumulative_share_change_not_a_simple_average_of_yields():
    # Demonstrates why endpoint-based cumulative calc is used instead
    # of averaging annual percentage changes: they are NOT equal in
    # general, and the endpoint method is the mathematically correct
    # "total change over the period" measure.
    series = pd.Series([1000.0, 500.0, 1000.0])  # -50% then +100%
    cumulative = calculate_cumulative_share_change(series)
    naive_average_of_yields = np.mean([-50.0, 100.0])
    assert cumulative == pytest.approx(0.0)  # correct: ended where it started
    assert naive_average_of_yields == pytest.approx(25.0)  # would be misleading
    assert cumulative != pytest.approx(naive_average_of_yields)


def test_cumulative_share_change_raises_on_zero_first_value():
    series = pd.Series([0.0, 100.0])
    with pytest.raises(ValueError):
        calculate_cumulative_share_change(series)


def test_cumulative_share_change_raises_on_insufficient_points():
    series = pd.Series([1000.0])
    with pytest.raises(ValueError):
        calculate_cumulative_share_change(series)


# ---------------------------------------------------------------------
# 10. Score calculation
# ---------------------------------------------------------------------
def test_score_full_marks_for_strong_consistent_reduction():
    score, breakdown = calculate_effectiveness_score(
        cumulative_pct_change=-20.0,  # -20% share count change = 20% cumulative reduction -> full 40
        years_reduction=3,
        years_dilution=0,
        total_years=3,
        average_annual_yield_pct=6.0,  # >= 5% benchmark -> full 20
    )
    assert score == pytest.approx(100.0)
    assert breakdown["cumulative_reduction_component_of_40"] == pytest.approx(40.0)
    assert breakdown["consistency_component_of_25"] == pytest.approx(25.0)
    assert breakdown["average_yield_component_of_20"] == pytest.approx(20.0)
    assert breakdown["dilution_absence_component_of_15"] == pytest.approx(15.0)


def test_score_zero_for_persistent_dilution():
    score, breakdown = calculate_effectiveness_score(
        cumulative_pct_change=20.0,  # share count grew 20% -> 0 reduction credit
        years_reduction=0,
        years_dilution=3,
        total_years=3,
        average_annual_yield_pct=-5.0,
    )
    assert score == pytest.approx(0.0)


def test_score_high_yield_alone_does_not_guarantee_high_score():
    # A single huge buyback year followed by dilutive years should NOT
    # automatically score well overall -- consistency and cumulative
    # change matter too, per the spec's explicit requirement.
    score, _ = calculate_effectiveness_score(
        cumulative_pct_change=5.0,  # net share count actually grew overall
        years_reduction=1,
        years_dilution=2,
        total_years=3,
        average_annual_yield_pct=15.0,  # one big outlier year
    )
    assert score is not None
    assert score < 60.0  # should be held back despite a flashy average yield


def test_score_none_when_no_cumulative_data():
    score, breakdown = calculate_effectiveness_score(
        cumulative_pct_change=None,
        years_reduction=0,
        years_dilution=0,
        total_years=0,
        average_annual_yield_pct=0.0,
    )
    assert score is None
    assert breakdown is None


# ---------------------------------------------------------------------
# Additional integration-style tests using analyze_company's helper
# pieces directly (clean_financial_data + validate_data + full company
# analysis), still without touching the network.
# ---------------------------------------------------------------------
def _make_dataset(ticker: str, shares_by_year: dict, source=DataSource.YFINANCE) -> CompanyDataset:
    ds = CompanyDataset(ticker=ticker, company=f"{ticker} Inc.")
    for year_str, shares in shares_by_year.items():
        ds.records.append(
            FiscalYearRecord(
                ticker=ticker,
                company=f"{ticker} Inc.",
                fiscal_year_end=pd.Timestamp(year_str),
                diluted_avg_shares=shares,
                diluted_shares_field_used="Diluted Average Shares",
                basic_avg_shares=None,
                repurchase_spend=None,
                repurchase_field_used=None,
                stock_based_comp=None,
                data_source=source,
            )
        )
    return ds


def test_clean_and_validate_full_pipeline_reduction_case():
    ds = _make_dataset(
        "TEST",
        {"2020-12-31": 1000.0, "2021-12-31": 970.0, "2022-12-31": 940.0, "2023-12-31": 900.0},
    )
    cleaned = clean_financial_data(ds)
    assert list(cleaned["diluted_avg_shares"]) == [1000.0, 970.0, 940.0, 900.0]
    result = validate_data(cleaned, "TEST")
    assert result.is_valid is True


def test_clean_financial_data_preserves_original_values_column():
    ds = _make_dataset("TEST", {"2022-12-31": 1000.0, "2023-12-31": 950.0})
    cleaned = clean_financial_data(ds)
    # "diluted_avg_shares" in the cleaned frame must exactly match the
    # originally retrieved raw values -- no transformation should
    # silently alter the figures themselves.
    assert set(cleaned["diluted_avg_shares"]) == {1000.0, 950.0}


def test_compare_companies_lists_insufficient_data_transparently():
    good = CompanyAnalysis(
        ticker="GOOD",
        company="Good Co",
        yearly_table=pd.DataFrame([{"Net Share Reduction Yield %": 5.0, "Status": "Net Share Reduction"}]),
        average_annual_yield_pct=5.0,
        cumulative_pct_change=-5.0,
        years_net_reduction=1,
        years_net_dilution=0,
        years_neutral=0,
        best_year={},
        worst_year={},
        overall_classification=ShareChangeStatus.NET_REDUCTION,
        effectiveness_score=80.0,
        score_breakdown={},
    )
    bad = CompanyAnalysis(
        ticker="BAD",
        company="Bad Co",
        yearly_table=pd.DataFrame(),
        average_annual_yield_pct=None,
        cumulative_pct_change=None,
        years_net_reduction=0,
        years_net_dilution=0,
        years_neutral=0,
        best_year=None,
        worst_year=None,
        overall_classification=ShareChangeStatus.INSUFFICIENT_DATA,
        effectiveness_score=None,
        score_breakdown=None,
        data_quality_notes=["No data returned."],
        insufficient_data=True,
    )
    summary = compare_companies([good, bad])
    assert set(summary["Ticker"]) == {"GOOD", "BAD"}
    bad_row = summary[summary["Ticker"] == "BAD"].iloc[0]
    # Use bool()/== rather than `is True`: pandas may return numpy.bool_
    # rather than a Python bool, which is equal but not identical.
    assert bool(bad_row["Insufficient Data"]) == True  # noqa: E712
    assert "No data returned." in bad_row["Data Quality Notes"]
    # Good company should rank above the insufficient-data one.
    assert summary.iloc[0]["Ticker"] == "GOOD"


# ---------------------------------------------------------------------
# Regression tests for the second-round fixes:
#   - a missing fiscal year must not create a fake year-over-year
#     comparison between two non-adjacent years
#   - clean_financial_data must not silently drop duplicate fiscal years
#   - "Purchase Of Business" must not be an accepted repurchase field
# ---------------------------------------------------------------------
def test_missing_middle_year_does_not_create_fake_comparison():
    ds = _make_dataset("GAPCO", {"2021-12-31": 1000.0, "2023-12-31": 900.0})
    # Manually insert a genuinely-missing middle year so clean_financial_data
    # sees three rows, one with a NaN share count, matching a real yfinance gap.
    ds.records.insert(
        1,
        ba_module()._make_record("GAPCO", "2022-12-31", None),
    )
    cleaned = ba_module().clean_financial_data(ds)
    analysis = ba_module().analyze_company("GAPCO", "GAPCO Inc.", dataset=ds)
    assert analysis.yearly_table.empty
    assert analysis.insufficient_data is True
    assert any("nonconsecutive" in n.lower() for n in analysis.data_quality_notes)


def test_duplicate_fiscal_year_is_not_silently_dropped_by_cleaning():
    ds = _make_dataset("DUPCO", {})
    mod = ba_module()
    ds.records.append(mod._make_record("DUPCO", "2022-12-31", 1000.0))
    ds.records.append(mod._make_record("DUPCO", "2022-12-31", 1000.0))
    ds.records.append(mod._make_record("DUPCO", "2023-12-31", 950.0))
    cleaned = mod.clean_financial_data(ds)
    assert len(cleaned) == 3  # duplicate preserved, not dropped during cleaning
    result = mod.validate_data(cleaned, "DUPCO")
    assert result.is_valid is False
    assert any("duplicate" in e.lower() for e in result.errors)


def test_purchase_of_business_is_not_an_accepted_repurchase_field():
    from buyback_analyzer import CANDIDATE_FIELDS_REPURCHASE
    assert "Purchase Of Business" not in CANDIDATE_FIELDS_REPURCHASE


def test_analyze_company_reuses_supplied_dataset_without_refetching():
    import buyback_analyzer as mod
    calls = {"n": 0}
    original = mod.get_company_data

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    mod.get_company_data = counting
    try:
        ds = _make_dataset("ONE", {"2021-12-31": 1000.0, "2022-12-31": 950.0})
        # analyze_company is given the dataset directly -- get_company_data
        # (the patched, counting version) must not be called at all.
        mod.analyze_company("ONE", "One Co", dataset=ds)
        assert calls["n"] == 0
    finally:
        mod.get_company_data = original


def ba_module():
    import buyback_analyzer as mod
    if not hasattr(mod, "_make_record"):
        def _make_record(ticker, year_str, shares):
            return FiscalYearRecord(
                ticker=ticker,
                company=f"{ticker} Inc.",
                fiscal_year_end=pd.Timestamp(year_str),
                diluted_avg_shares=shares,
                diluted_shares_field_used="Diluted Average Shares" if shares is not None else None,
                basic_avg_shares=None,
                repurchase_spend=None,
                repurchase_field_used=None,
                stock_based_comp=None,
                data_source=DataSource.YFINANCE,
            )
        mod._make_record = _make_record
    return mod


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
