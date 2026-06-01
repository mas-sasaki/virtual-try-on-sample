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


def _call_tryon(person_image_bytes: bytes, garment_image_bytes: bytes) -> bytes:
    """Virtual Try-On API を1回呼び出す（garment は1枚のみ）。"""
    url = _ENDPOINT_TEMPLATE.format(
        region=settings.vertex_ai_region,
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
        "parameters": {"sampleCount": 1},
    }
    headers = {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }
    response = http_requests.post(url, json=payload, headers=headers, timeout=120)
    if not response.ok:
        raise RuntimeError(f"{response.status_code} {response.reason}: {response.text}")
    encoded = response.json()["predictions"][0]["bytesBase64Encoded"]
    return base64.b64decode(encoded)


def run_virtual_tryon(
    person_image_bytes: bytes,
    top_image_bytes: bytes | None,
    bottom_image_bytes: bytes | None,
) -> bytes:
    """
    トップス・ボトムスをそれぞれ試着する。
    両方指定された場合はトップスを先に適用し、結果を人物画像として
    ボトムスを続けて適用する（連鎖呼び出し）。
    """
    result = person_image_bytes
    if top_image_bytes:
        result = _call_tryon(result, top_image_bytes)
    if bottom_image_bytes:
        result = _call_tryon(result, bottom_image_bytes)
    return result
