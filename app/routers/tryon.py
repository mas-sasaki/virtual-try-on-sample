from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from app.services.gcs import get_blob_bytes, get_cached_tryon, save_cached_tryon
from app.services.vertex_ai import run_virtual_tryon

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


class TryOnRequest(BaseModel):
    person_gcs_uri: str
    top_gcs_uri: str | None = None
    bottom_gcs_uri: str | None = None

    @model_validator(mode="after")
    def check_at_least_one_garment(self):
        if not self.top_gcs_uri and not self.bottom_gcs_uri:
            raise ValueError("top_gcs_uri または bottom_gcs_uri のどちらかは必須です")
        return self


@router.post("")
def try_on(req: TryOnRequest):
    cached = get_cached_tryon(req.person_gcs_uri, req.top_gcs_uri, req.bottom_gcs_uri)
    if cached:
        return {"result_url": cached["image_url"], "result_gcs_uri": cached["gcs_uri"]}

    try:
        person_bytes = get_blob_bytes(req.person_gcs_uri)
        top_bytes    = get_blob_bytes(req.top_gcs_uri)    if req.top_gcs_uri    else None
        bottom_bytes = get_blob_bytes(req.bottom_gcs_uri) if req.bottom_gcs_uri else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GCS から画像を取得できませんでした: {e}")

    try:
        result_bytes = run_virtual_tryon(person_bytes, top_bytes, bottom_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Virtual Try-On API エラー: {e}")

    try:
        result = save_cached_tryon(req.person_gcs_uri, req.top_gcs_uri, req.bottom_gcs_uri, result_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"結果画像の保存に失敗しました: {e}")
    return {"result_url": result["image_url"], "result_gcs_uri": result["gcs_uri"]}
