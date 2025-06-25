import pandas as pd
import yfinance as yf
import numpy as np
import re
import time
import investor_agent.stock_data as sd


def volume_analysis(ticker, period="6mo"):
    """
    Fetch stock data from Yahoo Finance and analyze for smart money accumulation.

    Parameters:
    ticker (str): Stock ticker symbol.
    period (str): Data period for analysis (default is '6mo' for 6 months).

    Returns:
    dict: Dictionary containing the analyzed DataFrame and key insights.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval="1wk")

    if df.empty:
        return {
            "error": f"No data found for {ticker}. Ensure the ticker is correct and try again."
        }

    df.reset_index(inplace=True)
    df.rename(
        columns={"Date": "Date", "Close": "Close", "Volume": "Volume"}, inplace=True
    )

    # Moving average volume, filling NaN with 0
    df["10_Week_MA_Volume"] = df["Volume"].rolling(window=10).mean().fillna(0)

    df["Above_Avg_Volume"] = df["Volume"] > df["10_Week_MA_Volume"]
    df["Price_Increase"] = df["Close"].diff().fillna(0) > 0  # Avoid NaN in first row
    df["Strong_Price_Increase"] = (
        df["Close"].pct_change().fillna(0) > 0.005
    )  # At least 0.5% increase
    df["Above_Avg_Volume"] = df["Volume"] > (
        df["10_Week_MA_Volume"] * 1.2
    )  # Volume 20% above average
    df["Closing_Strong"] = (df["Close"] - df["Low"]) / (
        df["High"] - df["Low"]
    ) > 0.5  # Closes in top 50% of range

    df["Accumulation_Day"] = (
        df["Above_Avg_Volume"] & df["Strong_Price_Increase"] & df["Closing_Strong"]
    )
    df["Mild_Pullback"] = (
        df["Close"].pct_change().fillna(0) > -0.05
    )  # Decline is less than 5%
    df["Volatility_Check"] = (df["High"] - df["Low"]) / df[
        "Low"
    ] < 0.08  # Weekly volatility under 8%
    df["Previous_Uptrend"] = df["Close"].shift(1) > df["Close"].shift(
        2
    )  # Prior week was an uptrend

    df["Low_Volume_Pullback"] = (
        (~df["Above_Avg_Volume"])
        & (df["Close"].diff().fillna(0) < 0)
        & df["Mild_Pullback"]
        & df["Volatility_Check"]
        & df["Previous_Uptrend"]
    )

    # Insight generation
    accumulation_count = int(df["Accumulation_Day"].sum())  # Convert to Python int
    pullback_count = int(df["Low_Volume_Pullback"].sum())  # Convert to Python int
    # Convert period string into an integer number of weeks

    match = re.match(r"(\d+)(wk|mo|y)", period)
    if match:
        period_value, period_unit = int(match.group(1)), match.group(2)

        # Convert months and years to weeks if necessary
        if period_unit == "mo":
            period_value *= 4  # Assume 1 month ≈ 4 weeks
        elif period_unit == "y":
            period_value *= 52  # Assume 1 year = 52 weeks

    else:
        period_value = 26  # Default to 6 months (26 weeks) if format is unclear

    # Select moving average and trend confirmation window based on the period
    if period_value <= 26:  # 6 months or less
        ma_window = 10  # Short-term trend (10-week SMA)
        recent_weeks = 4  # Use last 4 weeks for trend confirmation
    elif 27 <= period_value <= 52:  # 6 months to 1 year
        ma_window = 20  # Medium-term trend (20-week SMA)
        recent_weeks = 6  # Use last 6 weeks for trend confirmation
    elif 53 <= period_value <= 104:  # 1 to 2 years
        ma_window = 50  # Long-term trend (50-week SMA)
        recent_weeks = 8  # Use last 8 weeks for trend confirmation
    else:  # More than 2 years
        ma_window = 50  # Default to 50-week SMA
        recent_weeks = 10  # Use last 10 weeks for trend confirmation

    # Compute the selected moving average
    df[f"SMA_{ma_window}"] = df["Close"].rolling(window=ma_window).mean()

    # Count how many of the last N weeks had price increases
    df["Price_Increase_Weeks"] = df["Close"].diff().fillna(0) > 0
    recent_price_increases = df["Price_Increase_Weeks"].tail(recent_weeks).sum()

    # Ensure the stock is above its moving average and that the moving average is rising
    is_above_sma = df["Close"].iloc[-1] > df[f"SMA_{ma_window}"].iloc[-1]
    is_sma_rising = df[f"SMA_{ma_window}"].iloc[-1] > df[f"SMA_{ma_window}"].iloc[-2]

    # Final Uptrend condition based on period
    if recent_price_increases >= recent_weeks * 0.75 and is_above_sma and is_sma_rising:
        latest_trend = "Uptrend"
    elif (
        recent_price_increases <= recent_weeks * 0.25
        and not is_above_sma
        and not is_sma_rising
    ):
        latest_trend = "Downtrend"
    else:
        latest_trend = "Sideways"
    # Calculate institutional sentiment score

    # Avoid division by zero
    total_weeks = max(len(df), 1)  # Ensure at least 1 to prevent division by zero

    # Calculate weighted accumulation based on volume strength
    df["Volume_Strength"] = df["Volume"] / df["10_Week_MA_Volume"]
    df["Volume_Strength"].replace(
        [np.inf, -np.inf], np.nan, inplace=True
    )  # Replace infinite values
    df["Volume_Strength"].fillna(0, inplace=True)  # Replace NaN with 0

    weighted_accumulation = df.loc[df["Accumulation_Day"], "Volume_Strength"].sum()

    # Compute sentiment score, ensuring no invalid values
    sentiment_score = (
        (2 * weighted_accumulation) - (1.5 * pullback_count)
    ) / total_weeks

    # Replace invalid sentiment scores
    if np.isnan(sentiment_score) or np.isinf(sentiment_score):
        sentiment_score = 0  # Default to 0 if invalid

    # Ensure sentiment score is a standard Python float
    sentiment_score = round(
        float(sentiment_score), 2
    )  # Determine institutional activity based on sentiment score
    if sentiment_score > 0.3:
        institution_activity = "strong institutional accumulation and bullish momentum."
    elif sentiment_score > 0.1:
        institution_activity = "moderate accumulation with potential bullish trend."
    elif sentiment_score < -0.1:
        institution_activity = (
            "potential distribution, suggesting institutional selling pressure."
        )
    elif sentiment_score < -0.3:
        institution_activity = "high distribution, indicating possible downtrend."
    else:
        institution_activity = (
            "mixed activity, with no clear sign of accumulation or distribution."
        )

    insights = {
        "Ticker": ticker,
        "Accumulation Days": accumulation_count,
        "Low Volume Pullbacks": pullback_count,
        "Sentiment Score": round(sentiment_score, 2),
        "Latest Trend": latest_trend,  # ✅ Include the trend in the output
        "Analysis": (
            f"The stock has shown {accumulation_count} accumulation days over the last {period}, "
            f"while experiencing {pullback_count} low-volume pullbacks. "
            f"The latest trend is {latest_trend}. "
            f"This suggests {institution_activity}"
        ),
    }
    # Convert DataFrame to JSON-serializable format
    data_json = df[
        [
            "Date",
            "Close",
            "Volume",
            "10_Week_MA_Volume",
            "Accumulation_Day",
            "Low_Volume_Pullback",
        ]
    ].copy()

    data_json["Date"] = data_json["Date"].astype(str)  # Convert dates to string
    data_json.fillna(0, inplace=True)  # Ensure no NaN values before converting
    data_json = data_json.to_dict(
        orient="records"
    )  # Convert DataFrame to list of dictionaries

    return {
        # "data": data_json,  # JSON-serializable format
        "insights": insights,
    }


def search_high_volume_tickers(market="sp500", period="6mo", min_volume_factor=1.5):
    high_volume_tickers = []

    if market == "sp500":
        tickers = sd.get_sp500_tickers()
    elif market == "hkex":
        tickers = sd.convert_to_yahoo_format(sd.get_hk_mainboard_equities())
    else:
        raise ValueError("Supported markets: 'sp500', 'hkex'")

    for ticker in tickers:
        time.sleep(2)
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval="1wk")

            if df.empty or "Volume" not in df or len(df) < 10:
                continue

            df["10_Week_MA_Volume"] = df["Volume"].rolling(window=10).mean().fillna(0)

            latest_week_volume = df["Volume"].iloc[-1]
            latest_ma_volume = df["10_Week_MA_Volume"].iloc[-1]

            if latest_week_volume > latest_ma_volume * min_volume_factor:
                high_volume_tickers.append(ticker)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    return high_volume_tickers
