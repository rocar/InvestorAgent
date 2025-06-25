from tradingview_screener import Query, col


def get_screened_hk_stocks():
    """
    Fetch and filter Hong Kong stocks using TradingView Screener's query builder.

    Returns:
        list: A list of stock codes that match the criteria.
    """
    try:
        query = (
            Query()
            .set_markets("hongkong")
            .select("name")
            .where(
                col("market_cap_basic") > 10_000_000_000,
                col("beta_1_year") > 1,
                col("close") > col("SMA50"),
                col("close") > col("SMA100"),
                col("close") > col("SMA200"),
                col("Value.Traded|1M") > 8_000_000,
            )
            .limit(1000)
        )

        screener_data = query.get_scanner_data()

        _, df = screener_data

        # Drop the 'Ticker' column if it exists
        df = df.drop(columns=["Ticker"], errors="ignore")

        # Rename the "name" column to "Stock Code"
        df = df.rename(columns={"name": "Stock Code"})

        # Keep only the "Stock Code" column
        return df

    except Exception as e:
        return {"error": str(e)}


def get_screened_hk_stocks_vol():
    print("Before Query")
    try:
        query = (
            Query()
            .set_markets("hongkong")
            .select(
                "name",
            )
            .where(
                col("relative_volume_10d_calc|1M")
                > 1.5,  # 50% higher than normal 10-day volume
                col("volume_change|1M")
                > 100,  # More than 100% volume increase compared to prior month
                col("average_volume_30d_calc|1M") > 100_000,  # Avoid illiquid stocks
                col("Value.Traded|1M")
                > 8_000_000,  # Meaningful institutional liquidity
                col("close") > 2,
            )
            # .order_by("relative_volume_10d_calc|1M", ascending=False)
            .limit(100)
        )
        print("Start Query")

        screener_data = query.get_scanner_data()

        _, df = screener_data

        # Drop the 'Ticker' column if it exists
        df = df.drop(columns=["Ticker"], errors="ignore")

        print("Columns found in Excel:", df.columns.tolist())

        # Rename the "name" column to "Stock Code"
        df = df.rename(columns={"name": "Stock Code"})

        # Keep only the "Stock Code" column
        return df
    except Exception as e:
        return {"error": str(e)}


def get_screened_us_stocks():
    """
    Fetch and filter Hong Kong stocks using TradingView Screener's query builder.

    Returns:
        list: A list of stock codes that match the criteria.
    """
    try:
        query = (
            Query()
            .set_markets("america")
            .set_property("preset", "all_stocks")
            .select("name")
            .where(
                col("market_cap_basic") > 2_000_000_000,
                col("beta_1_year") > 1,
                col("close") > col("SMA50"),
                col("close") > col("SMA100"),
                col("close") > col("SMA200"),
                col("Value.Traded|1M") > 900_000_000,
            )
            .order_by("relative_volume_10d_calc|1M", ascending=False)
            .limit(100)
        )

        screener_data = query.get_scanner_data()

        _, df = screener_data

        # Drop the 'Ticker' column if it exists
        df = df.drop(columns=["ticker"], errors="ignore")

        # Keep only the "Stock Code" column
        return df["name"].tolist()

    except Exception as e:
        return {"error": str(e)}
