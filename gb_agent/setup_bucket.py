"""One-off: create the public-read GCS bucket the live gb_agent page is served from.

Run once (needs GCP credentials with storage admin on the project):

    uv run python -m gb_agent.setup_bucket

Idempotent, like ``tapestry.setup_bucket``, which it mirrors. On top of public
read and CORS it adds a lifecycle rule: anything under ``runs/`` older than 30 days
is deleted, a backstop for runs the publisher has stopped pruning. The full record
of every run stays in the run directory at home.
"""

import logging

from google.cloud import storage

from gb_agent.publish import BUCKET_NAME, PROJECT_ID

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

LOCATION = "EU"
PUBLIC_ROLE = "roles/storage.objectViewer"
MAX_AGE_DAYS = 30

# The page fetches the JSON from the browser via XHR, which is CORS-gated even
# though the objects are public-read. Clips play in <video>, which isn't.
CORS_RULE = {
    "origin": ["*"],
    "method": ["GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600,
}


def main() -> None:
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    if bucket.exists():
        print(f"Bucket gs://{BUCKET_NAME} already exists")
        bucket.reload()
    else:
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket = client.create_bucket(bucket, location=LOCATION)
        print(f"Created gs://{BUCKET_NAME} in {LOCATION}")

    policy = bucket.get_iam_policy(requested_policy_version=3)
    already_public = any(
        b["role"] == PUBLIC_ROLE and "allUsers" in b["members"] for b in policy.bindings
    )
    if already_public:
        print("Public read already granted")
    else:
        policy.bindings.append({"role": PUBLIC_ROLE, "members": {"allUsers"}})
        bucket.set_iam_policy(policy)
        print("Granted allUsers objectViewer (public read)")

    if bucket.cors == [CORS_RULE]:
        print("CORS already configured")
    else:
        bucket.cors = [CORS_RULE]
        bucket.patch()
        print("Configured CORS (GET from any origin)")

    rules = list(bucket.lifecycle_rules)
    if any(r.get("condition", {}).get("age") == MAX_AGE_DAYS for r in rules):
        print("Lifecycle rule already configured")
    else:
        bucket.add_lifecycle_delete_rule(age=MAX_AGE_DAYS, matches_prefix=["runs/"])
        bucket.patch()
        print(f"Added lifecycle rule: delete runs/ objects after {MAX_AGE_DAYS} days")


if __name__ == "__main__":
    main()
