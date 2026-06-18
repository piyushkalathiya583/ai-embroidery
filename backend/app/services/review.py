"""Module 12 — Review Engine.

AI checks each generated sketch: copied? balanced? symmetry? luxury?
production-friendly? Returns the ReviewResult JSON.

Provider-switchable via VISION_PROVIDER (shares the vision model). Reads the
sketch from the asset store.
"""
import base64
import json

from app.config import settings
from app.schemas import ReviewResult
from app.services import assets, gemini

_REVIEW_INSTRUCTION = """You are a QA reviewer for machine-embroidery design sketches.
Inspect the sketch and return ONLY a JSON object with boolean keys:
  copied              - does it appear copied/traced from a known artwork
  balanced            - is the layout visually balanced
  symmetry            - is it symmetric (if the design intends symmetry)
  luxury              - does it read as a premium/luxury design
  production_friendly - clean enough for machine embroidery
Return only the JSON object."""


def _review_openai(data: bytes, mime: str) -> dict:
    from openai import OpenAI

    b64 = base64.b64encode(data).decode()
    resp = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
        model=settings.vision_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _REVIEW_INSTRUCTION},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Review this embroidery sketch."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            },
        ],
    )
    return json.loads(resp.choices[0].message.content)


def review_sketch(image_key: str) -> ReviewResult | None:
    """Review a sketch. Returns None on any failure — review is optional QA and
    must never break the generation pipeline (e.g. Gemini 503/overloaded)."""
    loaded = assets.load(image_key)
    if loaded is None:
        return None
    data, mime = loaded
    try:
        if settings.vision_provider.lower() == "gemini":
            result = gemini.analyze_json(_REVIEW_INSTRUCTION, data, mime)
        else:
            result = _review_openai(data, mime)
        return ReviewResult(**result)
    except Exception:
        return None


def passed(result: ReviewResult) -> bool:
    return not result.copied and result.balanced and result.production_friendly
