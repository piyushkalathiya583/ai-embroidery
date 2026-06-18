"""Google Gemini helper — free-tier vision + JSON output for Modules 4 & 12."""
import base64
import json

import httpx

from app.config import settings

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def analyze_json(instruction: str, image_bytes: bytes, mime_type: str) -> dict:
    """Send an image + instruction to Gemini, parse the JSON object it returns."""
    body = {
        "contents": [
            {
                "parts": [
                    {"text": instruction},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_bytes).decode(),
                        }
                    },
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    resp = httpx.post(
        _URL.format(model=settings.gemini_model),
        params={"key": settings.gemini_api_key},
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)
