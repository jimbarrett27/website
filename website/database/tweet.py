"""
Description of the tweet table
"""
from dataclasses import dataclass
from database.tweeter import Tweeter

@dataclass
class tweet:
    id: int
    tweeter: Tweeter
