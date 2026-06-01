"""
Imagen 3 で衣服サンプル画像を生成して GCS にアップロードするスクリプト。

使い方:
    uv run python scripts/generate_garments.py

環境変数 (direnv / .envrc で設定済みであること):
    GCP_PROJECT, GCS_BUCKET, VERTEX_AI_REGION, GCS_GARMENTS_PREFIX
"""

import os
import sys

from google import genai
from google.cloud import storage

from scripts.utils import generate_image, upload_to_gcs, sleep_between_requests

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
    (
        "tops/white-blouse.png",
        "white flowy chiffon blouse with delicate ruffles, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
    (
        "tops/floral-top.png",
        "floral print short-sleeve top, pink and white flowers pattern, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
    (
        "tops/pink-knit.png",
        "soft pink cable-knit cropped sweater, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
    (
        "tops/beige-cardigan.png",
        "beige open-front longline cardigan, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
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
    (
        "bottoms/floral-midi-skirt.png",
        "floral print chiffon midi skirt, pink and white flowers, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
    (
        "bottoms/white-pleated-skirt.png",
        "white pleated mini skirt, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
    (
        "bottoms/black-mini-skirt.png",
        "black A-line mini skirt, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
    (
        "bottoms/denim-skirt.png",
        "light blue denim mini skirt with front buttons, "
        "flat lay on pure white background, front view, product photography, clean minimal style",
    ),
]


def main():
    print(f"Project      : {GCP_PROJECT}")
    print(f"Bucket       : {GCS_BUCKET}")
    print(f"Vertex region: {VERTEX_AI_REGION}")
    print(f"Prefix       : {GARMENTS_PREFIX}")
    print()

    imagen_client = genai.Client(vertexai=True, project=GCP_PROJECT, location=VERTEX_AI_REGION)
    gcs_client = storage.Client(project=GCP_PROJECT)

    bucket = gcs_client.bucket(GCS_BUCKET)
    pending = [(fn, pr) for fn, pr in GARMENTS if not bucket.blob(f"{GARMENTS_PREFIX}{fn}").exists()]
    skipped = len(GARMENTS) - len(pending)
    if skipped:
        print(f"Skipping {skipped} already-uploaded image(s).\n")

    for i, (filename, prompt) in enumerate(pending):
        blob_name = f"{GARMENTS_PREFIX}{filename}"
        print(f"Generating: {filename}")
        try:
            image_bytes = generate_image(imagen_client, prompt)
            upload_to_gcs(gcs_client, GCS_BUCKET, image_bytes, blob_name)
        except Exception as e:
            print(f"  ✗ failed: {e}", file=sys.stderr)
        if i < len(pending) - 1:
            sleep_between_requests()

    print("\nDone.")


if __name__ == "__main__":
    main()
