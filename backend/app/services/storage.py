"""Module 3 — Upload Reference storage helper.

Stores the original image + a thumbnail via the asset store (filesystem locally,
Postgres bytes on serverless). Accepts JPG / PNG / WEBP.
"""
import io
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.config import settings
from app.services import assets

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
THUMBNAIL_SIZE = (400, 400)
_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


async def save_reference(file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPG, PNG, WEBP are allowed.",
        )

    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Max upload size is {settings.max_upload_mb} MB.",
        )

    uid = uuid.uuid4().hex
    original_key = f"uploads/{uid}.{_EXT[file.content_type]}"
    thumb_key = f"thumbnails/{uid}_thumb.png"

    assets.save(original_key, contents, file.content_type)

    with Image.open(io.BytesIO(contents)) as img:
        thumb = img.convert("RGB")
        thumb.thumbnail(THUMBNAIL_SIZE)
        buf = io.BytesIO()
        thumb.save(buf, "PNG")
        assets.save(thumb_key, buf.getvalue(), "image/png")

    return {
        "original_path": original_key,
        "thumbnail_path": thumb_key,
        "mime_type": file.content_type,
    }
