"""
既存の衣服画像のフィット別バリアントを Imagen 3 で生成して GCS にアップロード。

GCS 構造（生成後）:
    garments/tops/white-tshirt.png            ← 既存（ジャストサイズ）
    garments/tops/tight/white-tshirt.png      ← タイト
    garments/tops/oversized/white-tshirt.png  ← オーバーサイズ
    garments/tops/relaxed/white-tshirt.png    ← ゆったり
    garments/tops/box/white-tshirt.png        ← ボックスシルエット

使い方:
    uv run python scripts/generate_fit_variants.py

環境変数:
    GCP_PROJECT, GCS_BUCKET, VERTEX_AI_REGION, GCS_GARMENTS_PREFIX
"""

import os
import sys

from google import genai
from google.cloud import storage

from scripts.generate_garments import GARMENTS
from scripts.utils import generate_image, sleep_between_requests, upload_to_gcs

GCP_PROJECT = os.environ["GCP_PROJECT"]
GCS_BUCKET = os.environ["GCS_BUCKET"]
VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION", "asia-southeast1")
GARMENTS_PREFIX = os.environ.get("GCS_GARMENTS_PREFIX", "garments/")

FIT_STYLES = [
    (
        "tight",
        "tight slim body-hugging silhouette, narrow fitted cut",
    ),
    (
        "oversized",
        "oversized extremely baggy silhouette, much wider and longer than standard size",
    ),
    (
        "relaxed",
        "relaxed comfortable loose fit, slightly wider than regular fit",
    ),
    (
        "box",
        "boxy box silhouette, equal width straight from shoulder to hem, squared geometric shape",
    ),
]


def build_fit_prompt(original_prompt: str, fit_desc: str) -> str:
    flat_lay_idx = original_prompt.lower().find("flat lay")
    if flat_lay_idx > 0:
        before = original_prompt[:flat_lay_idx].rstrip(", ")
        after = original_prompt[flat_lay_idx:]
        return f"{before}, {fit_desc}, {after}"
    return f"{original_prompt}, {fit_desc}"


def main():
    print(f"Project      : {GCP_PROJECT}")
    print(f"Bucket       : {GCS_BUCKET}")
    print(f"Vertex region: {VERTEX_AI_REGION}")
    print(f"Prefix       : {GARMENTS_PREFIX}")
    print(f"Variants     : {len(GARMENTS)} 服 × {len(FIT_STYLES)} フィット = {len(GARMENTS) * len(FIT_STYLES)} 画像")
    print()

    imagen_client = genai.Client(vertexai=True, project=GCP_PROJECT, location=VERTEX_AI_REGION)
    gcs_client = storage.Client(project=GCP_PROJECT)
    bucket = gcs_client.bucket(GCS_BUCKET)

    variants = []
    for filename, base_prompt in GARMENTS:
        parts = filename.split("/", 1)
        if len(parts) != 2:
            continue
        category, name = parts
        for fit_key, fit_desc in FIT_STYLES:
            blob_name = f"{GARMENTS_PREFIX}{category}/{fit_key}/{name}"
            prompt = build_fit_prompt(base_prompt, fit_desc)
            variants.append((blob_name, prompt))

    pending = [(bn, pr) for bn, pr in variants if not bucket.blob(bn).exists()]
    skipped = len(variants) - len(pending)
    if skipped:
        print(f"Skipping {skipped} already-uploaded variant(s).\n")

    for i, (blob_name, prompt) in enumerate(pending):
        print(f"Generating: {blob_name}")
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
