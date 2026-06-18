"""Module 10 — Prompt Builder.

Backend-only. Combines Vision output + Composition JSON + Rules + Measurements +
Garment into the final image-model prompt. The end user never sees this prompt.

Supports two render styles:
  - photoreal: a close, photorealistic render of stitched embroidery so a designer
    can see individual threads, stitch types and thread colours to digitise from.
  - pencil: the original monochrome pencil design sketch.
"""
from app.models import Rule
from app.schemas import (
    CompositionResult,
    GarmentSelection,
    MeasurementResult,
    RenderStyle,
    VisionResult,
)


def _design_brief(
    vision: VisionResult,
    composition: CompositionResult,
    rules: list[Rule],
    measurements: MeasurementResult,
    selection: GarmentSelection,
) -> str:
    rule_lines = "\n".join(f"- {r.description}" for r in rules)
    motifs = ", ".join(vision.motifs)
    secondary = "; ".join(
        f"{s.get('motif', 'motif')} at ({s['x']},{s['y']})"
        for s in composition.secondary
    ) or "balanced fillers"

    return f"""GARMENT: {selection.garment.value} — placement: {selection.placement.value}.
STYLE: {vision.style}, {vision.density} density, {vision.layout} layout, \
{'symmetrical' if vision.symmetry else 'asymmetrical'}, {vision.border} border.
MOTIFS: {motifs}.
COMPOSITION (canvas percentages):
- Main motif at ({composition.main['x']},{composition.main['y']}).
- Secondary motifs: {secondary}.
- Border height: {composition.border['height']} units. Fill: {composition.fill}.
PANEL GEOMETRY: top width {measurements.top_width}in, bottom width \
{measurements.bottom_width}in, height {measurements.height}in, \
safe area {measurements.safe_area}in (keep all embroidery inside the safe area).
DESIGN RULES:
{rule_lines}"""


_PHOTOREAL_HEADER = (
    "Ultra-detailed, photorealistic macro photograph of hand embroidery on fabric. "
    "Real silk floss and metallic zari/zardozi threads with visible individual "
    "stitches (satin, fill, chain, aari), thread sheen, raised 3D texture, sequins "
    "and beadwork where appropriate. Sharp focus, even studio lighting, crisp thread "
    "definition so an embroidery designer can read every stitch and thread colour."
)

_PHOTOREAL_FOOTER = (
    "Render as a finished, original embroidered piece on plain fabric, top-down flat "
    "lay, high resolution, no hands, no mannequin, no background clutter, no text or "
    "watermark. Do not copy any existing artwork."
)

_PENCIL_HEADER = (
    "Hand-drawn pencil embroidery design sketch on white paper, monochrome graphite."
)

_PENCIL_FOOTER = (
    "Render as a clean, original pencil sketch suitable for machine embroidery. "
    "Do not copy any existing artwork. Pencil shading only, no color, no fabric texture."
)


def build_prompt(
    vision: VisionResult,
    composition: CompositionResult,
    rules: list[Rule],
    measurements: MeasurementResult,
    selection: GarmentSelection,
    style: RenderStyle = RenderStyle.photoreal,
) -> str:
    brief = _design_brief(vision, composition, rules, measurements, selection)
    if style == RenderStyle.pencil:
        return f"{_PENCIL_HEADER}\n\n{brief}\n\n{_PENCIL_FOOTER}"
    return f"{_PHOTOREAL_HEADER}\n\n{brief}\n\n{_PHOTOREAL_FOOTER}"
