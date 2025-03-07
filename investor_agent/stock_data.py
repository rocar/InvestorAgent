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

        # Filter for Main Board equities
        mainboard_equities = df[
            (df["Category"] == "Equity")
            & (df["Sub-Category"] == "Equity Securities (Main Board)")
        ]

        # Ensure Stock Code is a string and properly zero-padded to 5 digits
        mainboard_equities["Stock Code"] = (
            mainboard_equities["Stock Code"].astype(str).str.zfill(5)
        )

        return mainboard_equities[["Stock Code"]]
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return pd.DataFrame(columns=["Stock Code"])


def convert_to_yahoo_format(df):
    """Convert HK stock codes to Yahoo Finance format (e.g., 00001 -> 0001.HK, 01000 -> 1000.HK, 80011 -> 80011.HK)"""
    if df.empty:
        return df

    def format_yahoo_code(stock_code):
        if stock_code.startswith(
            "0"
        ):  # If it starts with "0", remove only one leading zero
            return stock_code[1:] + ".HK"
        return stock_code + ".HK"  # Otherwise, keep it as is and append ".HK"

    return df["Stock Code"].apply(format_yahoo_code).tolist()


# Example usage
if __name__ == "__main__":
    hk_stocks = get_hk_mainboard_equities()
    yahoo_stocks = convert_to_yahoo_format(hk_stocks)
    print(yahoo_stocks.head())
    print(yahoo_stocks.tail())
