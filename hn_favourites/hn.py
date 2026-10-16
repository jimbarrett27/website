"""Read a user's Hacker News favourites.

HN has no API for favourites, but the page is public and plain HTML: one
``<tr class="athing">`` per story, newest favourite first, thirty to a page,
with a "More" link to the next. Each row carries the item id (stable, so it is
what we deduplicate on) and the story's own link -- or a relative ``item?id=``
link for Ask HN and other text posts, which we resolve to the discussion page.
"""

import html
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests

BASE_URL = "https://news.ycombinator.com/"
FAVOURITES_URL = BASE_URL + "favorites?id={}"
# Pause between pages: HN throttles fast clients with a "Sorry, we're not able
# to serve your requests this quickly" page rather than a 429.
PAGE_DELAY_SECONDS = 2

_ROW = re.compile(r'<tr class="athing[^"]*" id="(?P<id>\d+)">')
# Flagged stories put a bare marker before the link: `titleline"> [dupe] <a ...`.
_TITLE = re.compile(
    r'<span class="titleline">[^<]*<a href="(?P<url>[^"]*)"[^>]*>(?P<title>.*?)</a>',
    re.DOTALL,
)
_MORE = re.compile(r"<a href='(?P<href>favorites\?[^']*)' class='morelink'")


@dataclass(frozen=True)
class Favourite:
    item_id: int
    url: str
    title: str


def parse_page(page: str) -> tuple[list[Favourite], str | None]:
    """The favourites on one page, and the absolute URL of the next (or None)."""
    # Search for the title within each row's own slice of the page, so a row
    # whose markup we don't recognise is skipped rather than borrowing the
    # next row's link.
    rows = list(_ROW.finditer(page))
    favourites = []
    for row, following in zip(rows, rows[1:] + [None]):
        chunk = page[row.end():following.start() if following else len(page)]
        title = _TITLE.search(chunk)
        if title:
            favourites.append(Favourite(
                item_id=int(row["id"]),
                url=urljoin(BASE_URL, html.unescape(title["url"])),
                title=html.unescape(title["title"]),
            ))
    more = _MORE.search(page)
    next_url = urljoin(BASE_URL, html.unescape(more["href"])) if more else None
    return favourites, next_url


def fetch_page(url: str) -> str:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    if "not able to serve your requests this quickly" in response.text:
        raise RuntimeError("Hacker News is rate limiting us")
    return response.text


def new_favourites(username: str, seen: set[int], max_pages: int) -> list[Favourite]:
    """Favourites not in ``seen``, newest first.

    Pages are newest-first, so once a whole page is already known everything
    after it is too and we stop -- a routine run reads one page. The first run
    has nothing in ``seen`` and walks back through the lot, up to ``max_pages``.
    """
    found: list[Favourite] = []
    url: str | None = FAVOURITES_URL.format(username)
    for page_number in range(max_pages):
        if page_number:
            time.sleep(PAGE_DELAY_SECONDS)
        favourites, url = parse_page(fetch_page(url))
        fresh = [f for f in favourites if f.item_id not in seen]
        found.extend(fresh)
        if not fresh or url is None:
            break
    return found
