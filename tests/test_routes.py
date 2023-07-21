import pytest

from app import app
from app.constants import NOTEBOOK_DIRECTORY


@pytest.fixture
def client():
    """
    test client
    """
    app.config["TESTING"] = True
    yield app.test_client()


def test_routes(client):  # pylint: disable=redefined-outer-name
    """
    Tests all of the main routes return something without
    raising errors
    """

    routes_to_test = ["/", "/publications", "/blog", "/advent_of_code", "/robots.txt", "/sitemap.xml", "/changelog"]
    routes_to_test += [f'/blog/{i}' for i in range(50)]

    routes_to_test += [
        f"/notebooks/{f.parts[-1]}"
        for f in NOTEBOOK_DIRECTORY.iterdir()
        if str(f).endswith(".html")
    ]

    for route in routes_to_test:
        resp = client.get(route)
        assert "404 Not Found" not in resp.data.decode("utf-8")
