from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.gcs import get_blob_bytes

router = APIRouter(prefix="/api/image", tags=["image"])


@router.get("")
def proxy_image(uri: str):
    if not uri.startswith("gs://"):
        raise HTTPException(status_code=400, detail="GCS URI must start with gs://")
    try:
        data = get_blob_bytes(uri)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    content_type = "image/png" if uri.endswith(".png") else "image/jpeg"
    return Response(content=data, media_type=content_type)
