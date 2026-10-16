"""Tests for hn_favourites.hn -- parsing the favourites page and when to stop paging.

The fixture is synthetic but copies the markup of a live favourites page
(October 2026), including a text post's relative ``item?id=`` link, a story
flagged ``[dupe]``, and the single-quoted "More" link.
"""

from pathlib import Path

import pytest

from hn_favourites import hn
from hn_favourites.hn import Favourite

PAGE = (Path(__file__).parent / "fixtures" / "favorites_page.html").read_text()


def test_parse_page_reads_every_row():
    favourites, _ = hn.parse_page(PAGE)
    assert [f.item_id for f in favourites] == [49535752, 34055123, 47000001, 48794568]


def test_flagged_story_keeps_its_own_link():
    dupe = hn.parse_page(PAGE)[0][2]
    assert dupe.url == "https://example.com/dupe"
    assert dupe.title == "A story flagged as a dupe"


def test_parse_page_unescapes_urls_and_titles():
    first = hn.parse_page(PAGE)[0][0]
    assert first.url == "https://lwn.net/Articles/1090585/?a=1&b=2"
    assert first.title == 'A note on "subscription" prices'


def test_text_post_resolves_to_discussion_page():
    ask = hn.parse_page(PAGE)[0][1]
    assert ask.url == "https://news.ycombinator.com/item?id=34055123"


def test_next_page_url():
    _, next_url = hn.parse_page(PAGE)
    assert next_url == (
        "https://news.ycombinator.com/favorites?id=someone"
        "&next=22657447&n=31&time=1.58492450254885e9"
    )


def test_last_page_has_no_next():
    last = PAGE.split('<tr class="morespace"')[0]
    assert hn.parse_page(last)[1] is None


def _fav(item_id):
    return Favourite(item_id, f"https://example.com/{item_id}", str(item_id))


@pytest.fixture
def pages(monkeypatch):
    """Three pages of two favourites each; records which pages were fetched."""
    book = {
        hn.FAVOURITES_URL.format("me"): ([_fav(6), _fav(5)], "p2"),
        "p2": ([_fav(4), _fav(3)], "p3"),
        "p3": ([_fav(2), _fav(1)], None),
    }
    fetched = []
    monkeypatch.setattr(hn, "fetch_page", lambda url: fetched.append(url) or url)
    monkeypatch.setattr(hn, "parse_page", lambda url: book[url])
    monkeypatch.setattr(hn.time, "sleep", lambda _: None)
    return fetched


def test_first_run_walks_every_page(pages):
    found = hn.new_favourites("me", set(), max_pages=10)
    assert [f.item_id for f in found] == [6, 5, 4, 3, 2, 1]
    assert len(pages) == 3


def test_stops_at_first_fully_known_page(pages):
    found = hn.new_favourites("me", {4, 3, 2, 1}, max_pages=10)
    assert [f.item_id for f in found] == [6, 5]
    assert len(pages) == 2


def test_routine_run_reads_one_page(pages):
    assert hn.new_favourites("me", {6, 5, 4, 3, 2, 1}, max_pages=10) == []
    assert len(pages) == 1


def test_max_pages_caps_the_walk(pages):
    found = hn.new_favourites("me", set(), max_pages=2)
    assert [f.item_id for f in found] == [6, 5, 4, 3]
