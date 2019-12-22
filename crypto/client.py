import os
from binance.client import Client

def get_authenticated_client():
    api_public = os.environ.get('BINANCE_PUBLIC')
    api_private = os.environ.get('BINANCE_PRIVATE')

    return Client(api_public, api_private)