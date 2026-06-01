from fastapi import APIRouter
from app.services.gcs import list_garments

router = APIRouter(prefix="/api/garments", tags=["garments"])


@router.get("")
def get_garments():
    return list_garments()
