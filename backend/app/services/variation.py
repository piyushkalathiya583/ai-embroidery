"""Phase 3 — Variation Engine.

Takes the vision + composition of an existing sketch and applies a single
variation modifier (More Luxury, More Floral, Heavy Border, ...), returning the
adjusted (VisionResult, CompositionResult) pair. The pipeline then re-runs the
Rules -> Prompt -> Image -> Review steps on the adjusted plan.
"""
import copy

from app.schemas import CompositionResult, VariationType, VisionResult

_FILL_UP = {"Light": "Medium", "Medium": "Heavy", "Heavy": "Heavy"}
_FILL_DOWN = {"Heavy": "Medium", "Medium": "Light", "Light": "Light"}
_DENSITY_UP = {"Low": "Medium", "Medium": "Heavy", "Heavy": "Heavy"}
_DENSITY_DOWN = {"Heavy": "Medium", "Medium": "Low", "Low": "Low"}
_BORDER_UP = {"None": "Light", "Light": "Medium", "Medium": "Heavy", "Heavy": "Heavy"}
_BORDER_DOWN = {"Heavy": "Medium", "Medium": "Light", "Light": "None", "None": "None"}


def apply_variation(
    variation: VariationType,
    vision: VisionResult,
    composition: CompositionResult,
) -> tuple[VisionResult, CompositionResult]:
    v = vision.model_copy(deep=True)
    c = composition.model_copy(deep=True)
    c.secondary = copy.deepcopy(composition.secondary)

    if variation == VariationType.more_luxury:
        if "Luxury" not in v.style:
            v.style = f"Luxury {v.style}"
        v.border = _BORDER_UP[v.border]
        c.border["height"] = max(c.border.get("height", 3), 4)

    elif variation == VariationType.more_floral:
        for extra in ("Flower", "Floral Vine"):
            if extra not in v.motifs:
                v.motifs.append(extra)

    elif variation == VariationType.more_empty:
        v.density = _DENSITY_DOWN[v.density]
        c.fill = _FILL_DOWN[c.fill]
        c.secondary = c.secondary[: max(0, len(c.secondary) - 2)]

    elif variation == VariationType.heavy_border:
        v.border = "Heavy"
        c.border["height"] = max(c.border.get("height", 3) + 1, 4)

    elif variation == VariationType.simple_border:
        v.border = "Light"
        c.border["height"] = min(c.border.get("height", 3), 2)

    elif variation == VariationType.heavy_fill:
        v.density = _DENSITY_UP[v.density]
        c.fill = _FILL_UP[c.fill]

    elif variation == VariationType.minimal_fill:
        v.density = _DENSITY_DOWN[v.density]
        c.fill = _FILL_DOWN[c.fill]

    return v, c
