import numpy as np
import pandas as pd

def compute_volatility(df):
    """
    Measures price risk using standard deviation of daily returns.
    Returns a normalized value between 0 and 1.
    """

    close_prices = df["Close"]
    returns = close_prices.pct_change().dropna()

    if len(returns) == 0:
        return None

    volatility = np.std(returns)

    # Normalize: assume 5% daily volatility is very high
    normalized_volatility = min(volatility / 0.05, 1.0)

    return float(normalized_volatility)

def predict_trend(df, short_window=20, long_window=60):
    """
    Detects price trend using moving average crossover.
    Returns: (trend, confidence)
    """

    close_prices = df["Close"]

    if len(close_prices) < long_window:
        return None, None

    short_ma = close_prices.rolling(window=short_window).mean()
    long_ma = close_prices.rolling(window=long_window).mean()

    latest_short = short_ma.iloc[-1]
    latest_long = long_ma.iloc[-1]

    if np.isnan(latest_short) or np.isnan(latest_long):
        return None, None

    diff_ratio = (latest_short - latest_long) / latest_long
    confidence = min(abs(diff_ratio) * 10, 1.0)

    if latest_short > latest_long:
        return "up", float(confidence)
    elif latest_short < latest_long:
        return "down", float(confidence)
    else:
        return "sideways", 0.0

def detect_anomaly(df, threshold=3.0):
    """
    Detects unusual price movement using z-score on daily returns.
    Returns: (is_anomaly, severity)
    """

    close_prices = df["Close"]
    returns = close_prices.pct_change().dropna()

    if len(returns) < 10:
        return None, None

    mean = returns.mean()
    std = returns.std()

    if std == 0:
        return False, 0.0

    latest_return = returns.iloc[-1]
    z_score = abs((latest_return - mean) / std)

    is_anomaly = z_score > threshold
    severity = min(z_score / threshold, 1.0)

    return bool(is_anomaly), float(severity)
