"""
Functions for expressing the current balances
"""

import matplotlib
import matplotlib.pyplot as plot

from crypto.client import get_authenticated_client
from crypto.constants import TRADED_COINS

matplotlib.use("Agg")


def get_current_balance(against="USDT", bar_plot_location=None):
    """
    Returns my current total value in the "against" market
    """

    client = get_authenticated_client()
    prices = client.get_all_tickers()

    relevant_prices = {
        price["symbol"][:-4]: float(price["price"])
        for price in prices
        if price["symbol"].endswith(against) and price["symbol"][:-4] in TRADED_COINS
    }

    total = 0
    values = []
    for coin in TRADED_COINS:
        balance = float(client.get_asset_balance(coin)["free"])
        value = relevant_prices[coin] * balance
        values.append(value)
        total += value

    if bar_plot_location:
        plot.bar(TRADED_COINS, values, color="k")
        plot.ylabel("US $", size=15)
        plot.savefig(bar_plot_location)

    return total
