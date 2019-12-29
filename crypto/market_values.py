from dataclasses import dataclass, field
from time import time

import matplotlib
import matplotlib.pyplot as plot
from psycopg2 import connect, sql

from crypto.client import get_authenticated_client
from crypto.constants import DATABASE_URL, TRADED_COINS

matplotlib.use("Agg")


def get_traded_coin_quantities():

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

    for coin in TRADED_COINS:
        cursor.execute(
            sql.SQL(
                "CREATE TABLE {} ("
                "ID SERIAL PRIMARY KEY NOT NULL,"
                "QUANTITY FLOAT(8) NOT NULL,"
                "VALUE FLOAT(8) NOT NULL,"
                "TIME INTEGER NOT NULL"
                ");"
            ).format(sql.SQL(coin))
        )

    connection.commit()
    connection.close()


def update_ticker_tables():
    """
    updates all of the database tables with the latest values
    """

    connection = connect(DATABASE_URL)
    cursor = connection.cursor()

    traded_coin_values = get_traded_coin_values()
    traded_coin_quantities = get_traded_coin_quantities()

    now = int(time())

    for coin in TRADED_COINS:
        cursor.execute(
            sql.SQL("INSERT INTO {} (QUANTITY, VALUE, TIME) VALUES ({},{},{});").format(
                sql.SQL(coin),
                sql.SQL(str(traded_coin_values[coin])),
                sql.SQL(str(traded_coin_quantities[coin])),
                sql.SQL(str(now)),
            )
        )

    connection.commit()
    connection.close()
