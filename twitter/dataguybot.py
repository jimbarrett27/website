"""
Entry point to the twitter bot
"""

from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from crypto.balance import get_current_balance
from twitter.util import get_tweepy_api


def dataguybot_tweet():
    """
    Entrypoint function for the twitterbot
    """

    with open(Path("twitter") / "positive_adjectives.txt", "r") as f:
        adjectives = [l[:-1].lower() for l in f]

    api = get_tweepy_api()

    current_hour = datetime.now().hour + 1
    if current_hour % 24 == 0:
        api.update_status(f"My favourite data is {np.random.choice(adjectives)} data")
    if current_hour % 4 == 0:
        with NamedTemporaryFile() as f:
            plot_filepath = f"{f.name}.png"
            current_crypto_balance = get_current_balance(bar_plot_location=plot_filepath)
            tweet = (
                f"Jim's current crypto portfolio is worth "
                + f"approximately ${round(current_crypto_balance, 2)}"
            )
            api.update_with_media(plot_filepath, status=tweet)


if __name__ == "__main__":
    dataguybot_tweet()
