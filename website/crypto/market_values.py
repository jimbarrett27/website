"""
Accesses and stores the current market value for all of the traded coins
"""

import json
from time import time

import matplotlib
import matplotlib.pyplot as plot
from psycopg2 import connect, sql

from crypto.client import get_authenticated_client
from crypto.constants import DATABASE_URL, TRADED_COINS

matplotlib.use("Agg")


def get_traded_coin_quantities():
    """
    gets how many of each traded coin I have
    """

    client = get_authenticated_client()
    return {
        coin: float(client.get_asset_balance(coin)["free"]) for coin in TRADED_COINS
    }


def get_current_balance(units="USDT", bar_plot_location=None):
    """
    Returns my current total value in the "units" market
    """

    traded_coin_values = get_traded_coin_values(units=units)
    traded_coin_quantities = get_traded_coin_quantities()

    total = 0
    values = []
    for coin in TRADED_COINS:
        value = traded_coin_values[coin] * traded_coin_quantities[coin]
        values.append(value)
        total += value

    if bar_plot_location:
        plot.bar(TRADED_COINS, values, color="k")
        plot.ylabel(units, size=15)
        plot.savefig(bar_plot_location)

    return total


def get_traded_coin_values(units="USDT"):
    """
    Retrieves the current values of each of the traded coins
    """

    client = get_authenticated_client()
    prices = client.get_all_tickers()

    traded_coin_values = {
        price["symbol"][: -len(units)]: float(price["price"])
        for price in prices
        if price["symbol"].endswith(units)
        and price["symbol"][: -len(units)] in TRADED_COINS
    }

    return traded_coin_values


def create_database_tables():
    """
    Makes a database for each coin
    """

    connection = connect(DATABASE_URL)
    cursor = connection.cursor()

    cursor.execute(
        "CREATE TABLE COIN_VALUES ("
        "ID SERIAL NOT NULL PRIMARY KEY,"
        "VALUES JSON NOT NULL,"
        "QUANTITIES JSON NOT NULL,"
        "TIME INTEGER NOT NULL"
        ");"
    )

    connection.commit()
    connection.close()


def update_ticker_data():
    """
    updates all of the database tables with the latest values
    """

    traded_coin_values = get_traded_coin_values()
    traded_coin_quantities = get_traded_coin_quantities()

    connection = connect(DATABASE_URL)
    cursor = connection.cursor()

    cursor.execute(
        sql.SQL(
            "INSERT INTO COIN_VALUES (VALUES, QUANTITIES, TIME) VALUES ('{}', '{}', {})"
        ).format(
            sql.SQL(json.dumps(traded_coin_values)),
            sql.SQL(json.dumps(traded_coin_quantities)),
            sql.SQL(str(time())),
        )
    )

    connection.commit()
    connection.close()
