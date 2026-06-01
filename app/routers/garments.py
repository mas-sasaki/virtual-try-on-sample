from fastapi import APIRouter, Query
from app.services.gcs import list_garments

router = APIRouter(prefix="/api/garments", tags=["garments"])


@router.get("")
def get_garments(category: str | None = Query(default=None, description="tops または bottoms")):
    items = list_garments()
    if category:
        items = [g for g in items if g["name"].startswith(f"{category}/")]
    return items
