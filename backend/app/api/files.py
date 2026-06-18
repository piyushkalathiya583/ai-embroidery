"""Serve stored assets (images/thumbnails) from either storage backend."""
from fastapi import APIRouter, HTTPException, Response

from app.services import assets

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{key:path}")
def get_file(key: str):
    result = assets.load(key)
    if result is None:
        raise HTTPException(status_code=404, detail="Not found.")
    data, content_type = result
    return Response(content=data, media_type=content_type)
