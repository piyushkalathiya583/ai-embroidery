"""Module 11 — Image Generator.

Calls the image model (OpenAI Images by default) and returns N pencil sketches,
saved to the asset store. Swap `generate` for any other image backend.
"""
import base64
import uuid

from openai import OpenAI

from app.config import settings
from app.services import assets


def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def generate(prompt: str, n: int = 4, size: str = "1024x1536") -> list[str]:
    """Generate `n` sketches, return their asset keys (used to build image URLs)."""
    resp = _client().images.generate(
        model=settings.image_model,
        prompt=prompt,
        n=n,
        size=size,
    )

    keys: list[str] = []
    for item in resp.data:
        img_bytes = base64.b64decode(item.b64_json)
        key = f"uploads/sketch_{uuid.uuid4().hex}.png"
        assets.save(key, img_bytes, "image/png")
        keys.append(key)
    return keys
