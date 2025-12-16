from fastapi import FastAPI
from typing import Optional

# Import tools
from tools import (
    get_current_price,
    get_historical_data,
    get_fundamentals,
    predict_volatility,
    predict_price_trend,
)

app = FastAPI(
    title="MCP Financial Analysis Server",
    description="MCP-powered stock risk, volatility, and trend analysis",
    version="1.0.0"
)

# -------------------------
# Health Check
# -------------------------

@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "MCP Financial Server is live"
    }

# -------------------------
# Price Endpoints
# -------------------------

@app.get("/price/{symbol}")
def current_price(symbol: str):
    return get_current_price(symbol.upper())

# -------------------------
# Historical Summary
# -------------------------

@app.get("/history/{symbol}")
def historical_summary(
    symbol: str,
    period: Optional[str] = "1mo",
    interval: Optional[str] = "1d"
):
    return get_historical_data(symbol.upper(), period, interval)

# -------------------------
# Fundamentals
# -------------------------

@app.get("/fundamentals/{symbol}")
def fundamentals(symbol: str):
    return get_fundamentals(symbol.upper())

# -------------------------
# ML Endpoints
# -------------------------

@app.get("/ml/volatility/{symbol}")
def volatility(symbol: str):
    return predict_volatility(symbol.upper())

@app.get("/ml/trend/{symbol}")
def trend(symbol: str):
    return predict_price_trend(symbol.upper())
