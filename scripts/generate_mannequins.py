"""
Imagen 3 でマネキン画像を生成して GCS にアップロードするスクリプト。

使い方:
    uv run python scripts/generate_mannequins.py

環境変数 (direnv / .envrc で設定済みであること):
    GCP_PROJECT, GCS_BUCKET, VERTEX_AI_REGION, GCS_MANNEQUINS_PREFIX
"""

import os
import sys

from google import genai
from google.cloud import storage

from scripts.utils import generate_image, upload_to_gcs, sleep_between_requests

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


def main():
    print(f"Project      : {GCP_PROJECT}")
    print(f"Bucket       : {GCS_BUCKET}")
    print(f"Vertex region: {VERTEX_AI_REGION}")
    print(f"Prefix       : {MANNEQUINS_PREFIX}")
    print()

    imagen_client = genai.Client(vertexai=True, project=GCP_PROJECT, location=VERTEX_AI_REGION)
    gcs_client = storage.Client(project=GCP_PROJECT)

    for i, (filename, prompt) in enumerate(MANNEQUINS):
        blob_name = f"{MANNEQUINS_PREFIX}{filename}"
        print(f"Generating: {filename}")
        try:
            image_bytes = generate_image(imagen_client, prompt, aspect_ratio="3:4", person_generation="allow_adult")
            upload_to_gcs(gcs_client, GCS_BUCKET, image_bytes, blob_name)
        except Exception as e:
            print(f"  ✗ failed: {e}", file=sys.stderr)
        if i < len(MANNEQUINS) - 1:
            sleep_between_requests()

    print("\nDone.")


if __name__ == "__main__":
    main()
