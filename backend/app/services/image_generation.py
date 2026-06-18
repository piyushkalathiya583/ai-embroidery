"""Module 11 — Image Generator.

Provider-switchable via IMAGE_PROVIDER:
  - "openai"       -> OpenAI Images (gpt-image-1), needs OPENAI_API_KEY
  - "pollinations" -> Pollinations.ai, free and keyless (great for dev)

Returns asset keys (used to build /files image URLs).
"""
import base64
import urllib.parse
import uuid

import httpx

from app.config import settings
from app.services import assets

_CT_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


def _key(ext: str) -> str:
    return f"uploads/sketch_{uuid.uuid4().hex}.{ext}"


def _parse_size(size: str) -> tuple[int, int]:
    w, h = size.lower().split("x")
    return int(w), int(h)


def _generate_openai(prompt: str, n: int, size: str) -> list[str]:
    from openai import OpenAI

    resp = OpenAI(api_key=settings.openai_api_key).images.generate(
        model=settings.image_model, prompt=prompt, n=n, size=size
    )
    keys = []
    for item in resp.data:
        key = _key("png")
        assets.save(key, base64.b64decode(item.b64_json), "image/png")
        keys.append(key)
    return keys


def _generate_pollinations(prompt: str, n: int, size: str) -> list[str]:
    width, height = _parse_size(size)
    base = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
    keys = []
    for i in range(n):
        resp = httpx.get(
            base,
            params={
                "width": width,
                "height": height,
                "model": settings.pollinations_model,
                "nologo": "true",
                "seed": i + 1,  # vary per variant
            },
            timeout=120,
            follow_redirects=True,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        ext = _CT_EXT.get(content_type, "jpg")
        key = _key(ext)
        assets.save(key, resp.content, content_type)
        keys.append(key)
    return keys


def generate(prompt: str, n: int = 4, size: str = "1024x1536") -> list[str]:
    if settings.image_provider.lower() == "pollinations":
        return _generate_pollinations(prompt, n, size)
    return _generate_openai(prompt, n, size)
