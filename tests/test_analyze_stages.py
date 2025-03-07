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
    if ticker == "TEST_UP":
        # Create a DataFrame with strictly increasing prices over 300 days.
        days = 300
        data = {
            "Close": np.arange(100, 100 + days),  # steadily increasing
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        # Set index to simulate dates.
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        return DummyTicker(ticker, df)
    elif ticker == "TEST_FLAT":
        # Create a DataFrame with constant price over 300 days.
        days = 300
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
        days = 300
        data = {
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        return DummyTicker(ticker, df)
    else:
        # Default behavior: use increasing prices.
        days = 300
        data = {
            "Close": np.arange(100, 100 + days),
            "High": np.arange(102, 102 + days),
            "Low": np.arange(98, 98 + days),
        }
        df = pd.DataFrame(data)
        df.index = pd.date_range(end=pd.Timestamp.today(), periods=days)
        return DummyTicker(ticker, df)


# Test when all technical criteria are met (uptrend)
def test_analyze_stock_stage2_up(monkeypatch):
    # Monkey-patch yf.Ticker so that our dummy data is used.
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    result = analyze_stock_stage2("TEST_UP")

    # Check that the overall Stage 2 filter is "Yes"
    assert result["Stage2_Overall"] == "Yes"
    # Technical criteria based on our increasing data should be met:
    assert result["MA_sequence_10>20>50>100>200"] == "Yes"
    assert result["MAs_trending_up"] == "Yes"
    # At least one of the price conditions should be True.
    assert (
        result["Price_above_50d"] == "Yes" or result["Price_above_30w(150d)"] == "Yes"
    )
    assert result["Higher_highs_higher_lows"] == "Yes"
    # Note: The fundamental check is a placeholder so EPS growth remains "No"
    assert result["EPS_sales_growth_3Q"] == "No"
    # RS is computed using a positive 6-month return in our dummy data.
    assert result["RS_>=70"] == "Yes"


# Test when the technical criteria fail due to flat prices
def test_analyze_stock_stage2_flat(monkeypatch):
    monkeypatch.setattr(yf, "Ticker", lambda ticker: dummy_ticker_factory(ticker))
    result = analyze_stock_stage2("TEST_FLAT")

    # With constant prices, the moving average sequence is not strictly descending.
    assert result["MA_sequence_10>20>50>100>200"] == "No"
    # Price condition should fail (price equals the moving average, not greater)
    assert result["Price_above_50d"] == "No"
    # With no variation, there are no higher highs/lows.
    assert result["Higher_highs_higher_lows"] == "No"
    # Overall Stage2 should be "No"
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
