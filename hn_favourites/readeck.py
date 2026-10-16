"""Save bookmarks to the self-hosted Readeck instance.

Readeck runs in Docker on this same box (``~/docker/readeck``), published on
port 8085. It checks the Host header against ``READECK_ALLOWED_HOSTS``, which
includes ``localhost:8085``, so talk to it by that name.
"""

import requests

from gcp_util.secrets import get_readeck_api_token

READECK_URL = "http://localhost:8085"
LABEL = "hn-favourite"


def save_bookmark(url: str, title: str) -> None:
    """Queue ``url`` for saving. Readeck fetches and extracts it in the background."""
    response = requests.post(
        f"{READECK_URL}/api/bookmarks",
        headers={"Authorization": f"Bearer {get_readeck_api_token()}"},
        json={"url": url, "title": title, "labels": [LABEL]},
        timeout=20,
    )
    response.raise_for_status()
