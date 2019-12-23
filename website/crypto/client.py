"""
Methods for client boilerplate
"""

import os

from binance.client import Client


def get_authenticated_client():
    """
    gets the keys and constructs the python binance client
    """
    api_public = os.environ.get("BINANCE_PUBLIC")
    api_private = os.environ.get("BINANCE_PRIVATE")

    return Client(api_public, api_private)
