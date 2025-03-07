import yfinance as yf
import matplotlib.pyplot as plt
import os


def plot_stock_price(ticker, start="2023-01-01", end="2024-01-01", save_path=None):
    """
    Fetch and plot the stock price of a given ticker.

    Parameters:
        ticker (str): Stock ticker symbol (e.g., "AMZN", "AAPL", "2688.HK").
        start (str): Start date for historical data (format: YYYY-MM-DD).
        end (str): End date for historical data (format: YYYY-MM-DD).
        save_path (str, optional): Path to save the plot image (e.g., "charts/amzn.png"). If None, the plot is displayed.

    Returns:
        None
    """
    try:
        # Load stock data
        stock = yf.Ticker(ticker)
        data = stock.history(start=start, end=end)

        if data.empty:
            print(f"⚠ No data found for {ticker} between {start} and {end}.")
            return

        # Plot stock price
        plt.figure(figsize=(12, 6))
        plt.plot(
            data.index, data["Close"], label=f"{ticker} Closing Price", linewidth=2
        )
        plt.title(f"{ticker} Stock Price ({start} to {end})")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()

        # Save or show the plot
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            print(f"📊 Chart saved: {save_path}")
        else:
            plt.show()

    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")


# Example usage
if __name__ == "__main__":
    plot_stock_price("AMZN", start="2023-08-01", end="2024-03-01")
    # plot_stock_price("NVDA", start="2023-07-01", end="2024-02-01")
    # plot_stock_price("AAPL", start="2021-01-01", end="2021-08-01")
