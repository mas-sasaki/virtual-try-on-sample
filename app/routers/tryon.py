from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gcs import get_blob_bytes, save_result_image
from app.services.vertex_ai import run_virtual_tryon

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


class TryOnRequest(BaseModel):
    person_gcs_uri: str
    garment_gcs_uri: str


@router.post("")
def try_on(req: TryOnRequest):
    try:
        person_bytes = get_blob_bytes(req.person_gcs_uri)
        garment_bytes = get_blob_bytes(req.garment_gcs_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GCS から画像を取得できませんでした: {e}")

    try:
        result_bytes = run_virtual_tryon(person_bytes, garment_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Virtual Try-On API エラー: {e}")

    result = save_result_image(result_bytes)
    return {"result_url": result["signed_url"], "result_gcs_uri": result["gcs_uri"]}
