from crypto.client import get_authenticated_client
from constants import TRADED_COINS

def get_current_balance(against='USDT'):

    client = get_authenticated_client()
    prices = client.get_all_tickers()

    relevant_prices = {price['symbol'][:-4]:float(price['price']) for price in prices if price['symbol'].endswith('USDT') and price['symbol'][:-4] in TRADED_COINS}

    total = 0
    for coin in TRADED_COINS:
        balance = float(client.get_asset_balance(coin)['free'])
        total += relevant_prices[coin] * balance

    return total




