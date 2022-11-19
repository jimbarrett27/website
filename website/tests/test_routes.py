import pytest

from app import app
from app.constants import NOTEBOOK_DIRECTORY
from app.routes import get_blog_metadata


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

    routes_to_test = ["/", "/publications", "/blog"]

    blog_metadata = get_blog_metadata()
    routes_to_test += [f"/blog/{metadata['post_id']}" for metadata in blog_metadata]

    routes_to_test += [
        f"/notebooks/{f.parts[-1]}"
        for f in NOTEBOOK_DIRECTORY.iterdir()
        if str(f).endswith(".html")
    ]

    for route in routes_to_test:
        resp = client.get(route)
        assert "404 Not Found" not in resp.data.decode("utf-8")
