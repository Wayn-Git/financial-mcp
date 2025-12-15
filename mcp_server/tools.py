import data
from data import fetch_current_price, fetch_historical_data, fetch_fundamentals
import pprint

def _volatility_to_risk(score: float):
    if score < 0.3:
        return "low", "Low daily price movement indicating stable behavior"
    elif score < 0.6:
        return "medium", "Moderate daily price swings indicating average risk"
    else:
        return "high", "High daily price swings over the last few months"

from ml import compute_volatility
from data import fetch_historical_data
import data

def predict_volatility(ticker_symbol: str):
    df = fetch_historical_data(ticker_symbol, period="3mo", interval="1d")

    if df is None:
        return {
            "status": "error",
            "message": "Historical data unavailable",
            "symbol": ticker_symbol
        }

    score = compute_volatility(df)

    if score is None:
        return {
            "status": "error",
            "message": "Volatility calculation failed",
            "symbol": ticker_symbol
        }

    risk_level, explanation = _volatility_to_risk(score)

    return {
        "status": "success",
        "symbol": ticker_symbol,
        "company": data.supported_tickers[ticker_symbol],
        "volatility_score": round(score, 3),
        "risk_level": risk_level,
        "explanation": explanation,
        "lookback_period": "3 months",
        "method": "std_dev_of_daily_returns"
    }


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
    
