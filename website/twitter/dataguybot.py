"""
Entry point to the twitter bot
"""

from twitter.util import get_tweepy_api
from pathlib import Path

import numpy as np

def dataguybot_tweet():
    """
    Entrypoint function for the twitterbot
    """

    with open(Path("twitter") / "positive_adjectives.txt", "r") as f:
        adjectives = [l[:-1].lower() for l in f]

    api = get_tweepy_api()   

    api.update_status(f"My favourite data is {np.random.choice(adjectives)} data")


if __name__ == "__main__":
    dataguybot_tweet()
