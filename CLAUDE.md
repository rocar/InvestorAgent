# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InvestorAgent is a FastAPI-based stock analysis service that provides:
- Stage 2 stock analysis using Mark Minervini's methodology
- Volume-based accumulation/distribution analysis
- Stock screening for HK and US markets using TradingView Screener
- Real-time stock data fetching and price change calculations

## Key Architecture

### Core Modules
- `investor_agent/api.py` - FastAPI application with REST endpoints
- `investor_agent/analyze_stages.py` - Stage 2 analysis implementation (moving averages, fundamental checks)
- `investor_agent/analyze_volume.py` - Volume analysis for institutional activity detection
- `investor_agent/stock_data.py` - Data fetching utilities (Yahoo Finance, HKEX listings)
- `investor_agent/screener.py` - TradingView-based stock screening functions

### Data Sources
- Yahoo Finance (via yfinance) for historical price/volume data
- HKEX official Excel listing for Hong Kong stock codes
- TradingView Screener API for market screening
- Wikipedia for S&P 500 ticker lists

## Development Commands

### Local Development
```bash
# Run API server locally with hot reload
make local
# or
uvicorn investor_agent.api:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_analyze_stages.py

# Run with verbose logging (configured in pytest.ini)
pytest -v
```

### Docker Operations
```bash
# Build and push multi-platform image
make build

# Run container locally
make run

# View container logs
make logs

# Clean up stopped containers
make clean
```

## API Endpoints

- `GET /analyze/stage2/{ticker}` - Stage 2 analysis for individual stocks
- `GET /analyze/volume/{ticker}?period=6mo` - Volume accumulation analysis
- `GET /stocks/hk/screener?type=t2|vol` - Screened HK stocks
- `GET /stocks/us/screener` - Screened US stocks
- `GET /stocks/hk/yahoo_codes` - All HK stock Yahoo codes
- `GET /stocks/close?tickers=AAPL,MSFT` - Bulk price changes

## Key Dependencies

- `fastapi` + `uvicorn` for API framework
- `yfinance` for Yahoo Finance data
- `tradingview_screener` for market screening
- `pandas` + `numpy` for data analysis
- `requests` for HTTP calls to HKEX
- `openpyxl` for Excel file processing
- `matplotlib` and `scipy` for statistical analysis

## Code Patterns

### Error Handling
All API endpoints return standardized responses:
```python
{"status": "success", "data": result}
{"status": "error", "message": error_message}
```

### Stock Code Formats
- HK stocks: Convert from "00001" to "0001.HK" format for Yahoo Finance
- US stocks: Use ticker symbols directly
- Handle both 4-digit and 5-digit HK stock codes

### Data Processing
- Use pandas DataFrames for time series analysis
- Apply rolling window calculations for moving averages
- Handle missing data with appropriate fallbacks
- Convert numpy types to native Python types for JSON serialization

## Stage 2 Analysis Criteria

The core methodology implements Mark Minervini's Stage 2 criteria:
1. Moving average sequence: MA10 > MA20 > MA50 > MA100 > MA200
2. All moving averages trending upward
3. Price above 50-day or 150-day moving average
4. Higher highs and higher lows over 120-day periods
5. Fundamental growth (EPS/sales) - bonus criteria
6. Relative strength >= 70 - bonus criteria

## Volume Analysis Logic

Identifies institutional accumulation through:
- Above-average volume on price increases
- Low-volume pullbacks in uptrends
- Weighted sentiment scoring
- Trend confirmation using adaptive moving averages