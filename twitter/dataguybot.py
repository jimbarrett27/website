"""
Entry point to the twitter bot
"""

import os
from dataclasses import make_dataclass
from pathlib import Path

import numpy as np
import tweepy


def dataguybot_tweet():
    """
    Entrypoint function for the twitterbot
    """

    TwitterCredentials = make_dataclass(  # pylint: disable=invalid-name
        "TwitterCredentials", ["consumer", "consumer_secret", "access", "access_secret"]
    )

    twitter_credentials = TwitterCredentials(
        os.environ.get("TWITTER_CONSUMER"),
        os.environ.get("TWITTER_CONSUMER_SECRET"),
        os.environ.get("TWITTER_ACCESS"),
        os.environ.get("TWITTER_ACCESS_SECRET"),
    )

    with open(Path("twitter") / "positive_adjectives.txt", "r") as f:
        adjectives = [l[:-1].lower() for l in f]

    auth = tweepy.OAuthHandler(
        twitter_credentials.consumer, twitter_credentials.consumer_secret
    )
    auth.set_access_token(twitter_credentials.access, twitter_credentials.access_secret)

    api = tweepy.API(auth)

    api.verify_credentials()
    api.update_status(f"My favourite data is {np.random.choice(adjectives)} data")


if __name__ == "__main__":
    dataguybot_tweet()
