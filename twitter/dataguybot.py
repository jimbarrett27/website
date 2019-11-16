import tweepy
import os
from dataclasses import make_dataclass
from pathlib import Path
import numpy

TwitterCredentials = make_dataclass('TwitterCredentials', ['consumer', 'consumer_secret', 'access', 'access_secret'])

twitter_credentials = TwitterCredentials(os.environ.get('TWITTER_CONSUMER'), os.environ.get('TWITTER_CONSUMER_SECRET'), os.environ.get('TWITTER_ACCESS'), os.environ.get('TWITTER_ACCESS_SECRET'))

current_dir = Path().resolve()

with open(current_dir / "positive_adjectives.txt", 'r') as f:
    adjectives = [l for l in f]

auth = tweepy.OAuthHandler(twitter_credentials.consumer, twitter_credentials.consumer_secret)
auth.set_access_token(twitter_credentials.access, twitter_credentials.access_secret)

api = tweepy.API(auth)

try:
    api.verify_credentials()
    api.update_status(f"My favourite data is {np.random.choice(adjectives)} data")
except:
    print("Something went wrong with authentication!")