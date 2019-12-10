"""
Description of the tweeter table
"""
from dataclasses import dataclass

@dataclass
class Tweeter:
    id: int
    name: str
    username: str

