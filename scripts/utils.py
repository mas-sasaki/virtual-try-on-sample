import sys
import time

from google import genai
from google.genai import types
from google.cloud import storage

_RETRY_WAIT = 30  # 429 時の待機秒数
_MAX_RETRIES = 3
_BETWEEN_REQUESTS = 12  # リクエスト間の待機秒数（quota: ~5 req/min）


def generate_image(
    client: genai.Client,
    prompt: str,
    aspect_ratio: str = "1:1",
    person_generation: str = "dont_allow",
) -> bytes:
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.models.generate_images(
                model="imagen-3.0-generate-001",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    person_generation=person_generation,
                ),
            )
            return response.generated_images[0].image.image_bytes
        except Exception as e:
            if "429" in str(e) and attempt < _MAX_RETRIES:
                print(f"  ⚠ quota exceeded, waiting {_RETRY_WAIT}s (attempt {attempt}/{_MAX_RETRIES})...")
                time.sleep(_RETRY_WAIT)
            else:
                raise


def upload_to_gcs(gcs_client: storage.Client, bucket_name: str, image_bytes: bytes, blob_name: str) -> str:
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type="image/png")
    uri = f"gs://{bucket_name}/{blob_name}"
    print(f"  ✓ uploaded: {uri}")
    return uri


def sleep_between_requests():
    time.sleep(_BETWEEN_REQUESTS)
