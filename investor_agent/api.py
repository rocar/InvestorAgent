from fastapi import FastAPI
from investor_agent.analyze_stages import analyze_stock_stage2  # Import your function
from stock_data import (
    get_hk_mainboard_equities,
    convert_to_yahoo_format,
    fetch_stock_data,
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
