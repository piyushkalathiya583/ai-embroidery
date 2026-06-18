"""Module 4 — Vision Analysis.

Does NOT generate images. It only *understands* the reference image and returns
the structured VisionResult JSON that downstream modules consume.
"""
import base64
import json

from openai import OpenAI

from app.config import settings
from app.schemas import VisionResult

_VISION_INSTRUCTION = """You are an expert in Indian bridal/luxury embroidery design.
Analyse the reference image and return ONLY a JSON object with these keys:
  style     - short design-style label (e.g. "Luxury Mughal")
  symmetry  - boolean, is the design mirror-symmetric
  density   - one of "Low" | "Medium" | "Heavy"
  motifs    - array of distinct motif names (e.g. "Peacock", "Lotus", "Paisley")
  border    - one of "None" | "Light" | "Medium" | "Heavy"
  layout    - one of "Vertical" | "Horizontal" | "Radial" | "Scatter"
Do not include any prose, only the JSON object."""


def _client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def analyze_image(image_path: str) -> VisionResult:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    resp = _client().chat.completions.create(
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
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            },
        ],
    )
    data = json.loads(resp.choices[0].message.content)
    return VisionResult(**data)
