from dataclasses import dataclass
from typing import Dict

from selenium import webdriver
from time import sleep

@dataclass
class ChessComSnapshot:

    current_ratings: Dict['str': int]

def get_chess_com_snapshot():

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver(options=options)
    driver.get("https://www.chess.com/member/jimjimjimmyjim")

    sleep(3)

    ratings = {}
    for speed in ['Rapid', 'Bullet', 'Blitz']:
        css_selector = f'a[title={speed}] div[class=stat-section-user-rating]'
        rating = int(driver.find_element_by_css_selector(css_selector).text)
        ratings[speed] = rating

    return ChessComSnapshot(ratings)
