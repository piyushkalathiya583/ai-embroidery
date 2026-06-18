"""Unified asset store — filesystem locally, Postgres bytes on serverless.

Keys look like "uploads/<name>.png" or "thumbnails/<name>.png". The /files route
serves them back regardless of backend, so URLs stay stable across environments.
"""
import os

from app.config import settings
from app.database import SessionLocal
from app.models import Asset

_EXT_CONTENT_TYPE = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def _use_db() -> bool:
    return settings.storage_backend.lower() == "db"


def save(key: str, data: bytes, content_type: str) -> str:
    if _use_db():
        db = SessionLocal()
        try:
            existing = db.query(Asset).filter(Asset.key == key).first()
            if existing:
                existing.data = data
                existing.content_type = content_type
            else:
                db.add(Asset(key=key, data=data, content_type=content_type))
            db.commit()
        finally:
            db.close()
    else:
        path = os.path.join(settings.storage_root, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    return key


def load(key: str) -> tuple[bytes, str] | None:
    if _use_db():
        db = SessionLocal()
        try:
            obj = db.query(Asset).filter(Asset.key == key).first()
            return (obj.data, obj.content_type) if obj else None
        finally:
            db.close()
    path = os.path.join(settings.storage_root, key)
    if not os.path.isfile(path):
        return None
    ext = key.rsplit(".", 1)[-1].lower()
    with open(path, "rb") as f:
        return f.read(), _EXT_CONTENT_TYPE.get(ext, "application/octet-stream")
