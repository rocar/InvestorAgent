import pandas as pd
import numpy as np
import yfinance as yf


def calculate_moving_averages(df, windows=[10, 20, 50, 100, 200, 150]):
    for window in windows:
        df[f"MA{window}"] = df["Close"].rolling(window=window).mean()
    return df


def is_trending_up(series, days_ago):
    if len(series) <= days_ago:
        return True  # not enough data to compare, assume True
    return series.iloc[-1] >= series.iloc[-(days_ago + 1)]


def check_ma_sequence(latest):
    ma10, ma20 = latest["MA10"], latest["MA20"]
    ma50, ma100 = latest["MA50"], latest["MA100"]
    ma200 = latest["MA200"]
    if pd.notna(ma10) and pd.notna(ma200):
        return ma10 > ma20 > ma50 > ma100 > ma200
    return False


def check_mas_trending_up(df):
    return (
        is_trending_up(df["MA10"], 5)
        and is_trending_up(df["MA20"], 10)
        and is_trending_up(df["MA50"], 25)
        and is_trending_up(df["MA100"], 50)
        and is_trending_up(df["MA200"], 100)
    )


def check_price_conditions(latest):
    price = latest["Close"]
    ma50 = latest["MA50"]
    ma150 = latest.get("MA150", np.nan)
    price_above_50d = price > ma50 if pd.notna(ma50) else False
    price_above_150d = price > ma150 if pd.notna(ma150) else False
    return price_above_50d or price_above_150d


def check_higher_highs_lows(df):
    if len(df) < 120:
        return False
    recent_period = df.iloc[-120:]
    prior_period = df.iloc[-240:-120] if len(df) >= 240 else df.iloc[:-120]
    if recent_period.empty or prior_period.empty:
        return False
    return (
        recent_period["High"].max() > prior_period["High"].max()
        and recent_period["Low"].min() > prior_period["Low"].min()
    )


def check_fundamentals(stock):
    # Placeholder: this function can be expanded to fetch and compute fundamental data.
    try:
        income_stmt = stock.income_stmt
        if income_stmt is not None and "Net Income" in income_stmt.index:
            net_income_values = income_stmt.loc["Net Income"].dropna().iloc[:4]
        else:
            net_income_values = pd.Series(dtype=float)
        eps_growth = []
        if len(net_income_values) == 4:
            eps_growth = [
                (net_income_values.iloc[i] - net_income_values.iloc[i + 1])
                / abs(net_income_values.iloc[i + 1])
                if net_income_values.iloc[i + 1] != 0
                else 0
                for i in range(3)
            ]
        eps_growth_pass = sum(1 for g in eps_growth if g > 0) >= 2

        financials = stock.financials
        if financials is not None and "Total Revenue" in financials.index:
            revenue_values = financials.loc["Total Revenue"].dropna().iloc[:4]
        else:
            revenue_values = pd.Series(dtype=float)
        sales_growth = []
        if len(revenue_values) == 4:
            sales_growth = [
                (revenue_values.iloc[i] - revenue_values.iloc[i + 1])
                / abs(revenue_values.iloc[i + 1])
                if revenue_values.iloc[i + 1] != 0
                else 0
                for i in range(3)
            ]
        sales_growth_pass = sum(1 for g in sales_growth if g > 0) >= 2

        return eps_growth_pass and sales_growth_pass
    except Exception as e:
        print(f"Error fetching EPS/Sales data: {e}")
        return False


def check_relative_strength(df, price):
    if len(df) < 126:
        return False
    start_price = df["Close"].iloc[-126]
    if pd.notna(start_price) and start_price > 0:
        ret_6m = (price - start_price) / start_price
        return ret_6m > 0  # Placeholder logic
    return False


def analyze_stock_stage2(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="2y")
    if df.empty or "Close" not in df.columns:
        raise Exception(
            f"No data retrieved for {ticker}. Please check the ticker symbol."
        )

    # Calculate all moving averages
    df = calculate_moving_averages(df)
    latest = df.iloc[-1]

    # Evaluate criteria
    ma_sequence = check_ma_sequence(latest)
    mas_trending_up = check_mas_trending_up(df)
    price_condition = check_price_conditions(latest)
    higher_highs_lows = check_higher_highs_lows(df)
    eps_sales_growth = check_fundamentals(stock)
    rs_70 = check_relative_strength(df, latest["Close"])

    # Compile results
    results = {
        "Ticker": ticker,
        "MA_sequence_10>20>50>100>200": "Yes" if ma_sequence else "No",
        "MAs_trending_up": "Yes" if mas_trending_up else "No",
        "Price_above_50d_or_30w(150d)": "Yes" if price_condition else "No",
        "Higher_highs_higher_lows": "Yes" if higher_highs_lows else "No",
        "EPS_sales_growth_3Q": "Yes" if eps_sales_growth else "No",
        "RS_>=70": "Yes" if rs_70 else "No",
    }

    tech_criteria = [ma_sequence, mas_trending_up, price_condition, higher_highs_lows]
    overall = "Yes" if all(tech_criteria) else "No"

    # Apply bonus logic if overall Stage 2 is met
    if overall == "Yes":
        bonus_count = 0
        if eps_sales_growth:
            bonus_count += 1
        if rs_70:
            bonus_count += 1
        if bonus_count == 1:
            overall += "+"
        elif bonus_count == 2:
            overall += "++"

    results["Stage2_Overall"] = overall
    return results
