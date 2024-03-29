"""
Functions for interacting with blob storage on GCP
"""

import json
from typing import Any, Dict, List

from google.cloud import storage


def get_stored_json(blob_name: str, client: storage.Client = None):
    """
    Retrieves and deserialises a json blob stored at blob_name
    """

    if client is None:
        client = storage.Client()

    bucket = client.bucket("jim_data")
    blob = bucket.get_blob(blob_name)
    stored_json = json.loads(blob.download_as_string().decode("utf-8"))

    return stored_json


def update_stored_json(
    blob_name: str, update_dict: Dict[str, Any], client: storage.Client = None
) -> bool:
    """
    Appends the "update dict" to the json list stored at blob_name
    """

    if client is None:
        client = storage.Client()

    existing_data: List[Dict[str, Any]] = get_stored_json(blob_name=blob_name)
    existing_data.append(update_dict)

    bucket = client.bucket("jim_data")
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(existing_data))

    new_json = get_stored_json(blob_name, client=client)

    if update_dict in new_json:
        return True

    return False
