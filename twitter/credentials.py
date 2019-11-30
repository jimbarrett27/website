"""
Tidy store for the credentials for the twitter bot
"""
import os
from dataclasses import make_dataclass

TwitterCredentials = make_dataclass(  # pylint: disable=invalid-name
        "TwitterCredentials", ["consumer", "consumer_secret", "access", "access_secret"]
    )

CREDENTIALS = TwitterCredentials(
    os.environ.get("TWITTER_CONSUMER"),
    os.environ.get("TWITTER_CONSUMER_SECRET"),
    os.environ.get("TWITTER_ACCESS"),
    os.environ.get("TWITTER_ACCESS_SECRET"),
)
