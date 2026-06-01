"""
Imagen 3 で衣服サンプル画像を生成して GCS にアップロードするスクリプト。

使い方:
    uv run python scripts/generate_garments.py

環境変数 (direnv / .envrc で設定済みであること):
    GCP_PROJECT, GCS_BUCKET, VERTEX_AI_REGION, GCS_GARMENTS_PREFIX
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
GARMENTS_PREFIX = os.environ.get("GCS_GARMENTS_PREFIX", "garments/")

GARMENTS = [
    # (ファイル名, プロンプト)
    # ---- トップス ----
    (
        "tops/white-tshirt.png",
        "white plain cotton t-shirt, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    (
        "tops/blue-denim-shirt.png",
        "blue denim button-up shirt, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    (
        "tops/black-blazer.png",
        "black formal blazer jacket, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    (
        "tops/light-blue-hoodie.png",
        "light blue pullover hoodie sweatshirt, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    # ---- ボトムス ----
    (
        "bottoms/blue-jeans.png",
        "blue straight-leg denim jeans, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    (
        "bottoms/black-slacks.png",
        "black formal slim trousers slacks, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    (
        "bottoms/beige-chinos.png",
        "beige chino pants, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
    (
        "bottoms/grey-sweatpants.png",
        "grey cotton sweatpants joggers, flat lay on pure white background, "
        "front view, product photography, clean minimal style",
    ),
]


def generate_image(client: genai.Client, prompt: str) -> bytes:
    response = client.models.generate_images(
        model="imagen-3.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="dont_allow",
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
    print(f"Prefix       : {GARMENTS_PREFIX}")
    print()

    imagen_client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=VERTEX_AI_REGION,
    )
    gcs_client = storage.Client(project=GCP_PROJECT)

    for filename, prompt in GARMENTS:
        blob_name = f"{GARMENTS_PREFIX}{filename}"
        print(f"Generating: {filename}")
        try:
            image_bytes = generate_image(imagen_client, prompt)
            upload_to_gcs(gcs_client, image_bytes, blob_name)
        except Exception as e:
            print(f"  ✗ failed: {e}", file=sys.stderr)
        # API レート制限を避けるため少し待機
        time.sleep(2)

    print("\nDone.")


if __name__ == "__main__":
    main()
