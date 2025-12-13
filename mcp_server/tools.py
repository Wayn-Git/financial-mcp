import data
from data import fetch_current_price, fetch_historical_data, fetch_fundamentals
import pprint

def get_current_price(ticker_symbol: str):
    if fetch_current_price == None:
        print("")


def get_historical_data(ticker_symbol: str, period: str = "1mo", interval: str = "1d"):

    
def get_fundamentals(ticker_symbol: str):
    return fetch_fundamentals(ticker_symbol)
