"""Module 10 — Prompt Builder.

Backend-only. Combines Vision output + Composition JSON + Rules + Measurements +
Garment into the final image-model prompt. The end user never sees this prompt.
"""
from app.models import Rule
from app.schemas import (
    CompositionResult,
    GarmentSelection,
    MeasurementResult,
    VisionResult,
)


def build_prompt(
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

    return f"""Hand-drawn pencil embroidery design sketch on white paper, monochrome graphite.

GARMENT: {selection.garment.value} — placement: {selection.placement.value}.
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
{rule_lines}

Render as a clean, original pencil sketch suitable for machine embroidery. \
Do not copy any existing artwork. Pencil shading only, no color, no fabric texture."""
