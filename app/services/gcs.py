import uuid
from urllib.parse import urlparse, urlencode

from google.cloud import storage

from app.config import settings


def _client() -> storage.Client:
    return storage.Client(project=settings.gcp_project)


def _image_url(gcs_uri: str) -> str:
    return "/api/image?" + urlencode({"uri": gcs_uri})


def list_garments() -> list[dict]:
    client = _client()
    blobs = client.list_blobs(settings.gcs_bucket, prefix=settings.gcs_garments_prefix)
    results = []
    for blob in blobs:
        if blob.name == settings.gcs_garments_prefix:
            continue
        gcs_uri = f"gs://{settings.gcs_bucket}/{blob.name}"
        results.append(
            {
                "name": blob.name.removeprefix(settings.gcs_garments_prefix),
                "gcs_uri": gcs_uri,
                "image_url": _image_url(gcs_uri),
            }
        )
    return results


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
