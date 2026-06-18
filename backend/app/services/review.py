"""Module 12 — Review Engine.

AI checks each generated sketch: copied? balanced? symmetry? luxury?
production-friendly? Returns the ReviewResult JSON.
"""
import base64
import json

from openai import OpenAI

from app.config import settings
from app.schemas import ReviewResult

_REVIEW_INSTRUCTION = """You are a QA reviewer for machine-embroidery design sketches.
Inspect the sketch and return ONLY a JSON object with boolean keys:
  copied              - does it appear copied/traced from a known artwork
  balanced            - is the layout visually balanced
  symmetry            - is it symmetric (if the design intends symmetry)
  luxury              - does it read as a premium/luxury design
  production_friendly - clean enough for machine embroidery
Return only the JSON object."""


def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def review_sketch(image_path: str) -> ReviewResult:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    resp = _client().chat.completions.create(
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
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            },
        ],
    )
    data = json.loads(resp.choices[0].message.content)
    return ReviewResult(**data)


def passed(result: ReviewResult) -> bool:
    return (
        not result.copied
        and result.balanced
        and result.production_friendly
    )
