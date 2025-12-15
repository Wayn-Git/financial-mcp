import numpy as np

def compute_volatility(df):

    close_prices = df["Close"]

    # Daily returns
    returns = close_prices.pct_change().dropna()

    if len(returns) == 0:
        return None

    # Raw volatility
    volatility = np.std(returns)

    # Normalize (simple cap for v1)
    normalized_volatility = min(volatility / 0.05, 1.0)

    return float(normalized_volatility)
