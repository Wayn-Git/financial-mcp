import data
from data import fetch_current_price, fetch_historical_data, fetch_fundamentals
import pprint

def get_current_price(ticker_symbol: str):
    price = fetch_current_price(ticker_symbol)

    if price == None:
        return {
            "status": "error",
            "message": "Ticker Not Supported or Price Unavailable",
            "symbol": ticker_symbol
        }
    return {
        "status": "success",
        "symbol": ticker_symbol,
        "company": data.supported_tickers[ticker_symbol],
        "price": price,
        "currency": "USD"
    }




def get_historical_data(ticker_symbol: str, period: str = "1mo", interval: str = "1d"):
    df = fetch_historical_data(ticker_symbol, period, interval)

    if df is None:
        return {
            "status": "error",
            "message": "Ticker not supported or historical data unavailable",
            "symbol": ticker_symbol
        }

    summary = {
        "start_date": str(df.index[0].date()),
        "end_date": str(df.index[-1].date()),
        "data_points": len(df),
        "last_close": float(df["Close"].iloc[-1])
    }

    return {
        "status": "success",
        "symbol": ticker_symbol,
        "company": data.supported_tickers[ticker_symbol],
        "period": period,
        "interval": interval,
        "summary": summary
    }


    
def get_fundamentals(ticker_symbol: str):
    fundamentals = fetch_fundamentals(ticker_symbol)

    if fundamentals == None:
        return {
            "status": "error",
            "message": "Ticker Not Supported or Company Fundamentals Unavailable",
            "symbol": ticker_symbol
        }
    return {
        "status": "success",
        "symbol": ticker_symbol,
        "company": data.supported_tickers[ticker_symbol],
        "fundamentals": fundamentals,
        "currency": "USD"
    }
    
