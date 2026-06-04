import uuid
from urllib.parse import urlparse, urlencode

from google.cloud import storage

from app.config import settings


def _client() -> storage.Client:
    return storage.Client(project=settings.gcp_project)


def _image_url(gcs_uri: str) -> str:
    return "/api/image?" + urlencode({"uri": gcs_uri})


def _list_blobs(prefix: str) -> list[dict]:
    client = _client()
    blobs = client.list_blobs(settings.gcs_bucket, prefix=prefix)
    results = []
    for blob in blobs:
        if blob.name == prefix:
            continue
        gcs_uri = f"gs://{settings.gcs_bucket}/{blob.name}"
        results.append(
            {
                "name": blob.name.removeprefix(prefix),
                "gcs_uri": gcs_uri,
                "image_url": _image_url(gcs_uri),
            }
        )
    return results


_VALID_FITS = {"just", "tight", "oversized", "relaxed", "box"}


def list_garments() -> list[dict]:
    items = _list_blobs(settings.gcs_garments_prefix)
    result = []
    for item in items:
        name = item["name"]  # e.g. "tops/white-tshirt.png" or "tops/oversized/white-tshirt.png"
        parts = name.split("/")
        if len(parts) == 2:
            category, filename = parts
            fit = "just"
        elif len(parts) == 3:
            category, fit, filename = parts
            if fit not in _VALID_FITS:
                continue
        else:
            continue
        result.append({
            **item,
            "fit": fit,
            "base_name": filename.rsplit(".", 1)[0],
            "category": category,
        })
    return result


def list_mannequins() -> list[dict]:
    items = _list_blobs(settings.gcs_mannequins_prefix)
    for item in items:
        name = item["name"]
        item["gender"] = "female" if name.startswith("female") else "male"
    return items


def upload_user_image(file_bytes: bytes, content_type: str) -> dict:
    ext = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"
    blob_name = f"{settings.gcs_uploads_prefix}{uuid.uuid4()}.{ext}"
    client = _client()
    bucket = client.bucket(settings.gcs_bucket)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_bytes, content_type=content_type)
    gcs_uri = f"gs://{settings.gcs_bucket}/{blob_name}"
    return {
        "gcs_uri": gcs_uri,
        "image_url": _image_url(gcs_uri),
    }


def save_result_image(image_bytes: bytes) -> dict:
    blob_name = f"{settings.gcs_results_prefix}{uuid.uuid4()}.png"
    client = _client()
    bucket = client.bucket(settings.gcs_bucket)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type="image/png")
    gcs_uri = f"gs://{settings.gcs_bucket}/{blob_name}"
    return {
        "gcs_uri": gcs_uri,
        "image_url": _image_url(gcs_uri),
    }


def get_blob_bytes(gcs_uri: str) -> bytes:
    parsed = urlparse(gcs_uri)
    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip("/")
    client = _client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes()
