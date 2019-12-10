"""
Some handy utility function for working with twitter
"""
import tweepy

from twitter.credentials import CREDENTIALS


def get_tweepy_api():
    """
    Authorises and constructs the tweepy api object
    """

    auth = tweepy.OAuthHandler(CREDENTIALS.consumer, CREDENTIALS.consumer_secret)
    auth.set_access_token(CREDENTIALS.access, CREDENTIALS.access_secret)

    api = tweepy.API(auth)

    api.verify_credentials()

    return api
