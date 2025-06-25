import pandas as pd
import requests
import yfinance as yf
from io import BytesIO


def fetch_stock_data(ticker, period="6mo", interval="1d"):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    df = df[["Close"]]
    return df


def load_stock_data(ticker, start="2023-01-01", end="2024-01-01"):
    """
    Fetch historical stock data from yfinance.

    Parameters:
        ticker (str): Stock ticker symbol (e.g., "AAPL", "AMZN", "2688.HK").
        start (str): Start date (format: YYYY-MM-DD).
        end (str): End date (format: YYYY-MM-DD).

    Returns:
        pd.DataFrame: Dataframe containing 'Close', 'High', 'Low', 'Volume'.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(start=start, end=end, interval="1d")  # Daily data
    if data.empty:
        raise ValueError(f"No data fetched for ticker {ticker}")
    return data


def get_hk_mainboard_equities():
    url = "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from HKEX: {e}")
        return pd.DataFrame(columns=["Stock Code"])

    try:
        # Read the Excel file
        xls = pd.ExcelFile(BytesIO(response.content))
        df = pd.read_excel(
            xls, sheet_name=xls.sheet_names[0], skiprows=2, dtype={"Stock Code": str}
        )

        # Print the actual columns for debugging
        print("Columns found in Excel:", df.columns.tolist())

        # Ensure required columns exist before filtering
        required_columns = {"Stock Code", "Category", "Sub-Category"}
        if not required_columns.issubset(set(df.columns)):
            print("Warning: Required columns not found in the file!")
            return pd.DataFrame(columns=["Stock Code"])

        print(df.head(5))

        mainboard_equities = df[
            (df["Category"] == "Equity")
            & (df["Sub-Category"] == "Equity Securities (Main Board)")
        ]

        print("Total number of stocks (rows):", len(mainboard_equities))
        return mainboard_equities[["Stock Code"]]

    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return pd.DataFrame(columns=["Stock Code"])


def convert_to_yahoo_format(df):
    """Convert HK stock codes to Yahoo Finance format (e.g., 00001 -> 0001.HK, 01000 -> 1000.HK, 80011 -> 80011.HK)"""
    if df.empty:
        return df

    def format_yahoo_code(stock_code):
        # Ensure stock code is always 4 digits
        stock_code = stock_code.zfill(4)
        return stock_code + ".HK"

    return df["Stock Code"].apply(format_yahoo_code).tolist()


def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = pd.read_html(url)
        sp500_tickers = tables[0]["Symbol"].tolist()
        return sp500_tickers
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        return []


def get_hkex_tickers():
    url = "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), skiprows=2)
        df = df[df.iloc[:, 2].str.contains("Equity", na=False)]
        hkex_tickers = df.iloc[:, 0].astype(str).str.zfill(4) + ".HK"
        return hkex_tickers.tolist()
    except Exception as e:
        print(f"Error fetching HKEX tickers: {e}")
        return []


def get_bulk_price_changes(ticker_list):
    """
    Get current price and percent change from previous close for multiple tickers.

    Args:
        ticker_list (list): List of ticker symbols.

    Returns:
        List of dictionaries with ticker data.
    """
    data = yf.download(ticker_list, period="2d", group_by="ticker", auto_adjust=True)

    result = []
    for ticker in ticker_list:
        try:
            close_prices = data[ticker]["Close"]
            if len(close_prices) < 2:
                result.append({"ticker": ticker, "error": "Not enough data"})
                continue
            previous_close = close_prices[-2]
            current_price = close_prices[-1]
            change_percent = ((current_price - previous_close) / previous_close) * 100
            result.append(
                {
                    "ticker": ticker,
                    "current_price": round(current_price, 2),
                    "previous_close": round(previous_close, 2),
                    "change_percent": round(change_percent, 2),
                }
            )
        except Exception as e:
            result.append({"ticker": ticker, "error": str(e)})

    return result
