from google.cloud import secretmanager
from dataclasses import dataclass

@dataclass
class GCPSecret:

    project_id: str
    secret_id: str
    version: str

    def get_name(self, client: secretmanager.SecretManagerServiceClient):
        return client.secret_version_path(
            self.project_id, 
            self.secret_id, 
            self.version
        )

def get_gcp_secret(gcp_secret) -> str:

    client = secretmanager.SecretManagerServiceClient()

    # Get the secret.
    response = client.access_secret_version(request={"name": gcp_secret.get_name(client)})

    return response.payload.data.decode("UTF-8")

def get_telegram_key():

    secret = GCPSecret(
        project_id = 'personal-website-318015',
        secret_id = 'JIMMY_MAIN',
        version = 1
    )
    
    return get_gcp_secret(secret)

