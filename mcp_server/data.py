from yfinance import Ticker
from pprint import pprint

supported_tickers = {
    # Tech Company ticker symbols and their names
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "NVDA": "NVIDIA",
    "META": "Meta",

    # Auto/EV Company ticker symbols and their names
    "TSLA": "Tesla",
    "GM": "General Motors",
    "F": "Ford",

    # Finance Company ticker symbols and their names
    "JPM": "JPMorgan Chase",
    "BAC": "Bank of America",
    "V": "Visa",

    # Consumer Company ticker symbols and their names
    "AMZN": "Amazon",
    "WMT": "Walmart",
}

Error = f"Symbol Not Found In Our List: {supported_tickers}"

def fetch_current_price(ticker_symbol: str):
    if ticker_symbol not in supported_tickers:
        return Error
    
    ticker = Ticker(ticker_symbol)
    if ticker.fast_info is None:
        return None
    
    return ticker.fast_info.last_price

def fetch_historical_data(ticker_symbol: str, period: str = "1mo", interval: str = "1d"):
    if ticker_symbol not in supported_tickers:
        return Error

    ticker = Ticker(ticker_symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        return None
    
    return hist

def fetch_fundamentals(ticker_symbol: str):

    if ticker_symbol not in supported_tickers:
        return None

    ticker = Ticker(ticker_symbol)
    info = ticker.info
    fundamentals = {
      "market_cap": info.get("marketCap"),
      "total_revenue": info.get("totalRevenue"),
      "gross_margin": info.get("grossMargins"),
      "operating_margin": info.get("operatingMargins"),
      "beta": info.get("beta"),
      "debt_to_equity": info.get("debtToEquity"),
      "free_cashflow": info.get("freeCashflow"),
      "trailing_pe": info.get("trailingPE"),
     }
    
    if not any(fundamentals.values()):
        return None

    return fundamentals