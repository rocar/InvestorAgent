import pandas as pd
import numpy as np
import pytest
import yfinance as yf
from investor_agent.analyze_stages import analyze_stock_stage2


# Define a dummy ticker class that returns preset data.
class DummyTicker:
    def __init__(self, ticker, df, income_stmt=None, financials=None):
        self.ticker = ticker
        self._df = df
        self.income_stmt = income_stmt
        self.financials = financials

    def history(self, period):
        return self._df


# Factory function to return a DummyTicker based on the ticker symbol.
def dummy_ticker_factory(ticker):
    days = 300
    if ticker == "TEST_UP":
        # Create a DataFrame with strictly increasing prices over 300 days.
        data = {
            "Close": np.arange(100, 100 + days),  # steadily increasing
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        # For TEST_UP, fundamentals are not simulated (EPS remains False)
        # but the rising prices yield a positive relative strength.
        return DummyTicker(ticker, df)
    elif ticker == "TEST_BONUS_BOTH":
        # Create a DataFrame with strictly increasing prices over 300 days.
        data = {
            "Close": np.arange(100, 100 + days),
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        # Simulate positive fundamentals by constructing DataFrames
        # with a single row and four columns (e.g., Q1, Q2, Q3, Q4)
        income_stmt = pd.DataFrame(
            [[200, 150, 100, 50]],
            index=["Net Income"],
            columns=["Q1", "Q2", "Q3", "Q4"],
        )
        financials = pd.DataFrame(
            [[400, 300, 200, 100]],
            index=["Total Revenue"],
            columns=["Q1", "Q2", "Q3", "Q4"],
        )
        return DummyTicker(ticker, df, income_stmt=income_stmt, financials=financials)
    elif ticker == "TEST_FLAT":
        # Create a DataFrame with constant price over 300 days.
        data = {
            "Close": np.full(days, 100),
            "High": np.full(days, 102),
            "Low": np.full(days, 98),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        return DummyTicker(ticker, df)
    elif ticker == "EMPTY":
        # Return an empty DataFrame.
        df = pd.DataFrame()
        return DummyTicker(ticker, df)
    elif ticker == "MISSING_CLOSE":
        # Create a DataFrame without the "Close" column.
        data = {
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        return DummyTicker(ticker, df)
    else:
        # Default behavior: use increasing prices.
        data = {
            "Close": np.arange(100, 100 + days),
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        return DummyTicker(ticker, df)


# Test when all technical criteria are met (uptrend) with one bonus (RS only)
def test_analyze_stock_stage2_up(monkeypatch):
    # Monkey-patch yf.Ticker so that our dummy data is used.
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    result = analyze_stock_stage2("TEST_UP")

    # Check that technical criteria are met.
    assert result["MA_sequence_10>20>50>100>200"] == "Yes"
    assert result["MAs_trending_up"] == "Yes"
    assert result["Price_above_50d_or_30w(150d)"] == "Yes"
    assert result["Higher_highs_higher_lows"] == "Yes"
    # For TEST_UP, the fundamental check is a placeholder so EPS remains "No",
    # while RS_>=70 is "Yes". Thus bonus_count == 1.
    assert result["EPS_sales_growth_3Q"] == "No"
    assert result["RS_>=70"] == "Yes"
    # Overall technical criteria are met so base is "Yes" and bonus adds a "+"
    assert result["Stage2_Overall"] == "Yes+"


# Test when both bonus conditions are met.
def test_analyze_stock_stage2_bonus_both(monkeypatch):
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    result = analyze_stock_stage2("TEST_BONUS_BOTH")

    # Technical criteria should be met.
    assert result["MA_sequence_10>20>50>100>200"] == "Yes"
    assert result["MAs_trending_up"] == "Yes"
    assert result["Price_above_50d_or_30w(150d)"] == "Yes"
    assert result["Higher_highs_higher_lows"] == "Yes"
    # With TEST_BONUS_BOTH, the fundamentals simulate positive growth,
    # so EPS_sales_growth_3Q is "Yes", and RS_>=70 is "Yes" from price data.
    assert result["EPS_sales_growth_3Q"] == "Yes"
    assert result["RS_>=70"] == "Yes"
    # Both bonus conditions are true, so bonus_count == 2 and overall should be "Yes++".
    assert result["Stage2_Overall"] == "Yes++"


# Test when the technical criteria fail due to flat prices.
def test_analyze_stock_stage2_flat(monkeypatch):
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    result = analyze_stock_stage2("TEST_FLAT")

    # With constant prices, the moving average sequence is not strictly descending.
    assert result["MA_sequence_10>20>50>100>200"] == "No"
    assert result["Price_above_50d_or_30w(150d)"] == "No"
    assert result["Higher_highs_higher_lows"] == "No"
    # Overall Stage2 should be "No" so bonus logic is not applied.
    assert result["Stage2_Overall"] == "No"
    # EPS growth and RS remain "No"
    assert result["EPS_sales_growth_3Q"] == "No"
    assert result["RS_>=70"] == "No"


# Test that an empty DataFrame raises an exception.
def test_analyze_stock_stage2_empty(monkeypatch):
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    with pytest.raises(Exception) as excinfo:
        analyze_stock_stage2("EMPTY")
    assert "No data retrieved" in str(excinfo.value)


# Test that a DataFrame missing the "Close" column raises an exception.
def test_analyze_stock_stage2_missing_close(monkeypatch):
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    with pytest.raises(Exception) as excinfo:
        analyze_stock_stage2("MISSING_CLOSE")
    assert "No data retrieved" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main(["-v"])
