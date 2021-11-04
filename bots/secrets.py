"""
Functions for management and retrieval of my GCP secrets
"""

from dataclasses import dataclass

from google.cloud import secretmanager


@dataclass
class GCPSecret:
    """
    Simple dataclass to manage the details of a GCP secret
    """

    project_id: str
    secret_id: str
    version: str

    def get_name(self, client: secretmanager.SecretManagerServiceClient):
        """
        Return the name necessary for fetching the secret content
        """
        return client.secret_version_path(self.project_id, self.secret_id, self.version)


def get_gcp_secret(gcp_secret: GCPSecret) -> str:
    """
    Fetches and decodes the content of a GCP secret
    """

    client = secretmanager.SecretManagerServiceClient()

    # Get the secret.
    response = client.access_secret_version(
        request={"name": gcp_secret.get_name(client)}
    )

    return response.payload.data.decode("UTF-8")


def get_telegram_key() -> str:
    """
    Fetches the token for the main telegram bot
    """

    secret = GCPSecret(
        project_id="personal-website-318015", secret_id="JIMMY_MAIN", version=1
    )

    return get_gcp_secret(secret)
