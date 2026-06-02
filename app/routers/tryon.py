from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from app.services.gcs import get_blob_bytes, save_result_image
from app.services.vertex_ai import run_virtual_tryon

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


def _stem_from_uri(uri: str | None) -> str | None:
    """GCS URI からファイル名（拡張子なし）を取得する。例: gs://b/garments/tops/black-blazer.png → black-blazer"""
    if not uri:
        return None
    return uri.rstrip("/").rsplit("/", 1)[-1].rsplit(".", 1)[0]


class TryOnRequest(BaseModel):
    person_gcs_uri: str
    top_gcs_uri: str | None = None
    bottom_gcs_uri: str | None = None
    top_label: str | None = None  # 省略時は top_gcs_uri のファイル名を使用

    @model_validator(mode="after")
    def check_at_least_one_garment(self):
        if not self.top_gcs_uri and not self.bottom_gcs_uri:
            raise ValueError("top_gcs_uri または bottom_gcs_uri のどちらかは必須です")
        return self


@router.post("")
def try_on(req: TryOnRequest):
    try:
        person_bytes = get_blob_bytes(req.person_gcs_uri)
        top_bytes    = get_blob_bytes(req.top_gcs_uri)    if req.top_gcs_uri    else None
        bottom_bytes = get_blob_bytes(req.bottom_gcs_uri) if req.bottom_gcs_uri else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GCS から画像を取得できませんでした: {e}")

    top_label = req.top_label or _stem_from_uri(req.top_gcs_uri)

    try:
        result_bytes = run_virtual_tryon(person_bytes, top_bytes, bottom_bytes, top_label=top_label)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Virtual Try-On API エラー: {e}")

    result = save_result_image(result_bytes)
    return {"result_url": result["image_url"], "result_gcs_uri": result["gcs_uri"]}
