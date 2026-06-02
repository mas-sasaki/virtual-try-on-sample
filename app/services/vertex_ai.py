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


def _call_tryon(
    person_image_bytes: bytes,
    garment_image_bytes: bytes,
    categories_to_replace: list[str] | None = None,
) -> bytes:
    """Virtual Try-On API を1回呼び出す（garment は1枚のみ）。"""
    url = _ENDPOINT_TEMPLATE.format(
        region=settings.vertex_ai_region,
        project=settings.gcp_project,
    )
    instance: dict = {
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
    if categories_to_replace:
        instance["parameters"] = {"categories_to_replace": categories_to_replace}

    payload = {
        "instances": [instance],
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


_OUTERWEAR_KEYWORDS = {"jacket", "coat", "blazer", "cardigan", "outerwear", "outer"}

# ガーメントラベルからアウターウェアか判定し、categories_to_replace を返す。
# API がパラメータを未サポートの場合は None を返してフォールバック。
def _categories_for_top(label: str | None) -> list[str] | None:
    if not label:
        return None
    lower = label.lower()
    if any(kw in lower for kw in _OUTERWEAR_KEYWORDS):
        return ["outerwear"]
    return None


def run_virtual_tryon(
    person_image_bytes: bytes,
    top_image_bytes: bytes | None,
    bottom_image_bytes: bytes | None,
    top_label: str | None = None,
) -> bytes:
    """
    トップス・ボトムスをそれぞれ試着する。
    top_label にアウター系キーワード（jacket/coat/blazer等）が含まれる場合、
    categories_to_replace=["outerwear"] をリクエストに付与して
    インナーが消えないよう試みる（実験的・API サポート状況に依存）。
    """
    result = person_image_bytes
    if top_image_bytes:
        cats = _categories_for_top(top_label)
        result = _call_tryon(result, top_image_bytes, categories_to_replace=cats)
    if bottom_image_bytes:
        result = _call_tryon(result, bottom_image_bytes)
    return result
