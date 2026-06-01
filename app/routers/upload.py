from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.gcs import upload_user_image

router = APIRouter(prefix="/api/upload", tags=["upload"])

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}


@router.post("")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="JPEG または PNG 画像のみアップロード可能です")
    data = await file.read()
    return upload_user_image(data, file.content_type)
