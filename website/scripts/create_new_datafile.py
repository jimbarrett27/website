"""
Script to create new json blobs for data storage
"""

from google.cloud import storage
import json

def create_new_datafile(blob_name: str):
    """
    Create an empty json blob
    """

    client = storage.Client()
    bucket = client.get_bucket('jim_data')
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps([]))

if __name__ == '__main__':

    create_new_datafile(
        blob_name='blob_name.json'
    )