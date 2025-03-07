import pandas as pd
import numpy as np
import yfinance as yf  # Uncomment this when running in a live environment with internet


def analyze_stock_stage2(ticker):
    """Fetch stock data and analyze Stage 2 criteria for the given ticker."""
    # Fetch 2 years of daily data for the stock
    stock = yf.Ticker(ticker)
    df = stock.history(period="2y")  # Get last 2 years of price history
    # For illustration (since we cannot fetch live data here), assume df is obtained.
    # df = yf.download(ticker, period="2y")

    if df.empty or "Close" not in df.columns:
        raise Exception(
            f"No data retrieved for {ticker}. Please check the ticker symbol."
        )

    # Calculate moving averages
    df["MA10"] = df["Close"].rolling(window=10).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["MA100"] = df["Close"].rolling(window=100).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()

    # Get the latest values (last row)
    latest = df.iloc[-1]
    ma10, ma20 = latest["MA10"], latest["MA20"]
    ma50, ma100 = latest["MA50"], latest["MA100"]
    ma200 = latest["MA200"]
    price = latest["Close"]

    # 1. Moving averages in sequence
    ma_sequence = False
    if pd.notna(ma10) and pd.notna(ma200):
        ma_sequence = ma10 > ma20 > ma50 > ma100 > ma200

    # 2. Moving averages trending up (not declining)
    # Check if current MA is >= MA value some time ago (half the window length ago, for example)
    def is_trending_up(series, days_ago):
        if len(series) <= days_ago:
            return True  # not enough data to compare, assume True or skip
        return series.iloc[-1] >= series.iloc[-(days_ago + 1)]

    ma10_trend = is_trending_up(df["MA10"], 5)  # 5 days ago
    ma20_trend = is_trending_up(df["MA20"], 10)  # 10 days ago
    ma50_trend = is_trending_up(df["MA50"], 25)  # 25 days ago (~half of 50)
    ma100_trend = is_trending_up(df["MA100"], 50)  # 50 days ago (~half of 100)
    ma200_trend = is_trending_up(df["MA200"], 100)  # 100 days ago (~half of 200)
    mas_trending_up = (
        ma10_trend and ma20_trend and ma50_trend and ma100_trend and ma200_trend
    )

    # 3. Price above 50-day MA (and 150-day MA as proxy for 30-week)
    price_above_50d = price > ma50 if pd.notna(ma50) else False
    # Compute 150-day MA for 30-week comparison:
    df["MA150"] = df["Close"].rolling(window=150).mean()
    ma150 = latest.get("MA150", np.nan)
    price_above_150d = price > ma150 if pd.notna(ma150) else False

    # 4. Higher highs and higher lows (over last ~6 months vs previous 6 months)
    higher_highs_lows = False
    if len(df) >= 120:  # roughly 6 months of trading days
        # Split data into two halves (last 120 days and the 120 before that)
        recent_period = df.iloc[-120:]
        prior_period = df.iloc[-240:-120] if len(df) >= 240 else df.iloc[:-120]
        if not recent_period.empty and not prior_period.empty:
            recent_high = recent_period["High"].max()
            recent_low = recent_period["Low"].min()
            prior_high = prior_period["High"].max()
            prior_low = prior_period["Low"].min()
            if recent_high > prior_high and recent_low > prior_low:
                higher_highs_lows = True

    # 5. EPS and Sales growth for last 3 quarters (fundamental check)
    # eps_sales_growth = None  # default to None if data not fetched
    # (In a real implementation, fetch quarterly EPS and revenue and compute growth.)
    # For example, using yfinance:
    # financials = stock.quarterly_financials   # DataFrame of financials (revenue, net income, etc.)
    # earnings_hist = stock.quarterly_earnings  # DataFrame of past quarterly EPS if available
    # Here, one would calculate year-over-year growth for EPS and revenue for 3 consecutive quarters.
    # This requires fundamental data; if not available, mark this criterion as not evaluated or False.

    # As a placeholder, we'll skip actual computation. In practice, you'd compare each quarter's EPS and revenue to the same quarter a year prior.
    # eps_sales_growth = False  # assume fail or not met unless data proves otherwise

    # 5. EPS and Sales growth for last 3 quarters (fundamental check)
    eps_sales_growth = None  # Default to None if data not fetched

    try:
        # Fetch last 4 quarters of Net Income (EPS proxy)
        income_stmt = stock.income_stmt  # Get Income Statement
        if income_stmt is not None and "Net Income" in income_stmt.index:
            net_income_values = (
                income_stmt.loc["Net Income"].dropna().iloc[:4]
            )  # Get last 4 quarters
        else:
            net_income_values = pd.Series(dtype=float)  # Empty if not found

        # Compute YoY EPS Growth for last 3 quarters
        eps_growth = []
        if len(net_income_values) == 4:
            eps_growth = [
                (net_income_values.iloc[i] - net_income_values.iloc[i + 1])
                / abs(net_income_values.iloc[i + 1])
                if net_income_values.iloc[i + 1] != 0
                else 0
                for i in range(3)
            ]

        # Check if at least 2 out of 3 quarters had positive EPS growth
        eps_growth_pass = sum(1 for g in eps_growth if g > 0) >= 2

        # Fetch last 4 quarters of Total Revenue (Sales)
        financials = stock.financials  # Get Financial Statement
        if financials is not None and "Total Revenue" in financials.index:
            revenue_values = financials.loc["Total Revenue"].dropna().iloc[:4]
        else:
            revenue_values = pd.Series(dtype=float)  # Empty if not found

        # Compute YoY Sales Growth for last 3 quarters
        sales_growth = []
        if len(revenue_values) == 4:
            sales_growth = [
                (revenue_values.iloc[i] - revenue_values.iloc[i + 1])
                / abs(revenue_values.iloc[i + 1])
                if revenue_values.iloc[i + 1] != 0
                else 0
                for i in range(3)
            ]

        # Check if at least 2 out of 3 quarters had positive Sales growth
        sales_growth_pass = sum(1 for g in sales_growth if g > 0) >= 2

        # Final EPS & Sales Growth Check (must meet at least one condition)
        eps_sales_growth = eps_growth_pass and sales_growth_pass

    except Exception as e:
        print(f"Error fetching EPS/Sales data: {e}")
    eps_sales_growth = False  # Default to fail if data can't be retrieved

    # 6. Relative Strength (RS) >= 70
    rs_70 = None  # default None if not computed
    # To approximate RS, one approach is to compare the stock's return over 6-12 months to an index or peers.
    # For simplicity, we might compute 6-month return and assume RS pass if stock outperformed S&P 500.
    if len(df) >= 126:  # 6 months
        start_price = df["Close"].iloc[-126]
        if pd.notna(start_price) and start_price > 0:
            ret_6m = (price - start_price) / start_price
            # If S&P 500 data available, compare; otherwise, set a threshold like > 0 (positive) or a high percentile.
            rs_70 = True if ret_6m > 0 else False  # (Placeholder logic)

    # Compile results
    results = {
        "Ticker": ticker,
        "MA_sequence_10>20>50>100>200": "Yes" if ma_sequence else "No",
        "MAs_trending_up": "Yes" if mas_trending_up else "No",
        "Price_above_50d": "Yes" if price_above_50d else "No",
        "Price_above_30w(150d)": "Yes" if price_above_150d else "No",
        "Higher_highs_higher_lows": "Yes" if higher_highs_lows else "No",
        "EPS_sales_growth_3Q": "Yes" if eps_sales_growth else "No",
        "RS_>=70": "Yes" if rs_70 else "No",
    }

    # Define a combined price condition
    price_condition = price_above_50d or price_above_150d

    # Determine overall Stage 2 (technical criteria must all pass)
    tech_criteria = [ma_sequence, mas_trending_up, price_condition, higher_highs_lows]
    results["Stage2_Overall"] = "Yes" if all(tech_criteria) else "No"
    return results


# Example usage:
# result = analyze_stock_stage2("AAPL")
# print(result)
