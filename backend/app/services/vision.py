"""Module 4 — Vision Analysis.

Does NOT generate images. It only *understands* the reference image and returns
the structured VisionResult JSON that downstream modules consume.

Provider-switchable via VISION_PROVIDER: "openai" (gpt-4o) or "gemini" (free tier).
The image is read from the asset store (filesystem locally, Postgres on serverless).
"""
import base64
import json

from fastapi import HTTPException
from openai import OpenAI

from app.config import settings
from app.schemas import VisionResult
from app.services import assets, gemini

_VISION_INSTRUCTION = """You are an expert in Indian bridal/luxury embroidery design.
Analyse the reference image and return ONLY a JSON object with these keys:
  style     - short design-style label (e.g. "Luxury Mughal")
  symmetry  - boolean, is the design mirror-symmetric
  density   - one of "Low" | "Medium" | "Heavy"
  motifs    - array of distinct motif names (e.g. "Peacock", "Lotus", "Paisley")
  border    - one of "None" | "Light" | "Medium" | "Heavy"
  layout    - one of "Vertical" | "Horizontal" | "Radial" | "Scatter"
Do not include any prose, only the JSON object."""


def _load(image_key: str) -> tuple[bytes, str]:
    loaded = assets.load(image_key)
    if loaded is None:
        raise HTTPException(status_code=404, detail="Reference image not found.")
    return loaded


def _analyze_openai(data: bytes, mime: str) -> dict:
    b64 = base64.b64encode(data).decode()
    resp = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
        model=settings.vision_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _VISION_INSTRUCTION},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyse this embroidery reference."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            },
        ],
    )
    return json.loads(resp.choices[0].message.content)


def analyze_image(image_key: str) -> VisionResult:
    data, mime = _load(image_key)
    if settings.vision_provider.lower() == "gemini":
        result = gemini.analyze_json(_VISION_INSTRUCTION, data, mime)
    else:
        result = _analyze_openai(data, mime)
    return VisionResult(**result)
