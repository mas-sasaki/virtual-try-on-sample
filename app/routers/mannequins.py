from fastapi import APIRouter
from app.services.gcs import list_mannequins

router = APIRouter(prefix="/api/mannequins", tags=["mannequins"])


@router.get("")
def get_mannequins():
    return list_mannequins()
