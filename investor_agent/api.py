from fastapi import FastAPI
from investor_agent.screener import (
    get_screened_hk_stocks,
    get_screened_us_stocks,
    get_screened_hk_stocks_vol,
)
from investor_agent.analyze_stages import analyze_stock_stage2  # Import your function
from investor_agent.analyze_volume import volume_analysis
from investor_agent.stock_data import (
    get_hk_mainboard_equities,
    convert_to_yahoo_format,
    fetch_stock_data,
    get_bulk_price_changes,  # New import added
)  # Import stock functions


app = FastAPI()


@app.get("/analyze/stage2/{ticker}")
async def analyze_stock(ticker: str):
    """
    API Endpoint: GET /analyze/stage2/{ticker}
    Example: /analyze/stage2/AAPL
    """
    try:
        result = analyze_stock_stage2(ticker)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/stocks/hk/yahoo_codes")
async def get_hk_yahoo_codes():
    """
    API Endpoint: GET /stocks/hk/yahoo_codes
    Returns a list of Hong Kong stock Yahoo Finance codes (e.g., ["0001.HK", "1000.HK"]).
    """
    try:
        hk_stocks = get_hk_mainboard_equities()  # Get HK stock codes
        yahoo_codes = convert_to_yahoo_format(
            hk_stocks
        )  # Convert to Yahoo Finance format

        # Return as a plain list for easy iteration in n8n
        return {"status": "success", "data": yahoo_codes}  # yahoo_codes is now a list
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/analyze/volume/{ticker}")
async def analyze_volume(ticker: str, period: str = "6mo"):
    """
    API Endpoint: GET /analyze/volume/{ticker}
    Example: /analyze/volume/AAPL?period=6mo
    """
    try:
        result = volume_analysis(ticker, period)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/stocks/hk/screener")
async def screened_hk_stocks(type: str = "t2"):
    """
    API Endpoint: GET /stocks/hk/screener
    Returns a list of Hong Kong stock Yahoo Finance codes that match the screening criteria.
    """
    try:
        match type:
            case "t2":
                stock_codes = get_screened_hk_stocks()
            case "vol":
                stock_codes = get_screened_hk_stocks_vol()

        yahoo_codes = convert_to_yahoo_format(stock_codes)

        return {"status": "success", "data": yahoo_codes}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/stocks/us/screener")
async def screened_us_stocks():
    """
    API Endpoint: GET /stocks/us/screener
    Returns a list of US stock Yahoo Finance codes that match the screening criteria.
    """
    try:
        stock_codes = get_screened_us_stocks()

        return {"status": "success", "data": stock_codes}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/stocks/close")
async def get_bulk_closing_prices(tickers: str):
    """
    API Endpoint: GET /stocks/close?tickers=AAPL,MSFT,TSLA
    Accepts a comma-separated list of tickers and returns their current and previous close prices with change percent.
    """
    try:
        ticker_list = [
            ticker.strip() for ticker in tickers.split(",") if ticker.strip()
        ]
        result = get_bulk_price_changes(ticker_list)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
