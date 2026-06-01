import base64

import google.auth
import google.auth.transport.requests
import requests as http_requests

from app.config import settings

_ENDPOINT_TEMPLATE = (
    "https://{region}-aiplatform.googleapis.com/v1/projects/{project}"
    "/locations/{region}/publishers/google/models/virtual-try-on-001:predict"
)


def _get_access_token() -> str:
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def run_virtual_tryon(
    person_image_bytes: bytes,
    garment_image_bytes: bytes,
) -> bytes:
    url = _ENDPOINT_TEMPLATE.format(
        region=settings.gcp_region,
        project=settings.gcp_project,
    )
    payload = {
        "instances": [
            {
                "personImage": {
                    "image": {
                        "bytesBase64Encoded": base64.b64encode(person_image_bytes).decode()
                    }
                },
                "productImages": [
                    {
                        "image": {
                            "bytesBase64Encoded": base64.b64encode(garment_image_bytes).decode()
                        }
                    }
                ],
            }
        ],
        "parameters": {
            "sampleCount": 1,
        },
    }
    headers = {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }
    response = http_requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()
    encoded = data["predictions"][0]["bytesBase64Encoded"]
    return base64.b64decode(encoded)
