"""
Imagen 3 でマネキン画像を生成して GCS にアップロードするスクリプト。

使い方:
    uv run python scripts/generate_mannequins.py

環境変数 (direnv / .envrc で設定済みであること):
    GCP_PROJECT, GCS_BUCKET, VERTEX_AI_REGION, GCS_MANNEQUINS_PREFIX
"""

import os
import sys
import time

from google import genai
from google.genai import types
from google.cloud import storage

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]
VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION", "asia-southeast1")
MANNEQUINS_PREFIX = os.environ.get("GCS_MANNEQUINS_PREFIX", "mannequins/")

MANNEQUINS = [
    # (ファイル名, プロンプト)
    # ---- 男性マネキン ----
    (
        "male-1.png",
        "full body male fashion mannequin standing straight, front view, "
        "neutral pose with arms slightly away from body, pure white background, "
        "studio photography, high quality, realistic",
    ),
    (
        "male-2.png",
        "full body male fashion mannequin standing straight, front view, "
        "relaxed natural pose, pure white background, "
        "studio photography, high quality, realistic",
    ),
    # ---- 女性マネキン ----
    (
        "female-1.png",
        "full body female fashion mannequin standing straight, front view, "
        "neutral pose with arms slightly away from body, pure white background, "
        "studio photography, high quality, realistic",
    ),
    (
        "female-2.png",
        "full body female fashion mannequin standing straight, front view, "
        "relaxed natural pose, pure white background, "
        "studio photography, high quality, realistic",
    ),
]


def generate_image(client: genai.Client, prompt: str) -> bytes:
    response = client.models.generate_images(
        model="imagen-3.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="3:4",
            person_generation="allow_adult",
        ),
    )
    return response.generated_images[0].image.image_bytes


def upload_to_gcs(gcs_client: storage.Client, image_bytes: bytes, blob_name: str) -> str:
    bucket = gcs_client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type="image/png")
    uri = f"gs://{GCS_BUCKET}/{blob_name}"
    print(f"  ✓ uploaded: {uri}")
    return uri


def main():
    print(f"Project      : {GCP_PROJECT}")
    print(f"Bucket       : {GCS_BUCKET}")
    print(f"Vertex region: {VERTEX_AI_REGION}")
    print(f"Prefix       : {MANNEQUINS_PREFIX}")
    print()

    imagen_client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=VERTEX_AI_REGION,
    )
    gcs_client = storage.Client(project=GCP_PROJECT)

    for filename, prompt in MANNEQUINS:
        blob_name = f"{MANNEQUINS_PREFIX}{filename}"
        print(f"Generating: {filename}")
        try:
            image_bytes = generate_image(imagen_client, prompt)
            upload_to_gcs(gcs_client, image_bytes, blob_name)
        except Exception as e:
            print(f"  ✗ failed: {e}", file=sys.stderr)
        time.sleep(2)

    print("\nDone.")


if __name__ == "__main__":
    main()
