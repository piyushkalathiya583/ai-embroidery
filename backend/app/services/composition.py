"""Module 8 — Composition Engine (the heart of the project).

The AI does NOT draw a sketch here. It first builds a *layout plan*: where the
main motif sits, the secondary motifs, the flower flow, the border, fillers and
overall balance. The plan is geometry/percentages on the safe-area canvas.
"""
from app.schemas import (
    CompositionResult,
    GarmentSelection,
    MeasurementResult,
    VisionResult,
)

_DENSITY_TO_FILL = {"Low": "Light", "Medium": "Medium", "Heavy": "Heavy"}
_BORDER_HEIGHT = {"None": 0, "Light": 2, "Medium": 3, "Heavy": 4}


def build_composition(
    vision: VisionResult,
    measurements: MeasurementResult,
    selection: GarmentSelection,
) -> CompositionResult:
    """Deterministic v1 layout planner.

    Coordinates are percentages of the safe area (0-100). The Future V2 plan is to
    replace this with a Composition AI that produces the design plan first.
    """
    # Main motif anchored slightly above centre for vertical layouts.
    main = {"x": 50, "y": 60 if vision.layout == "Vertical" else 50}

    border = {"height": _BORDER_HEIGHT.get(vision.border, 3)}

    # Place secondary motifs symmetrically if symmetry is required.
    secondary: list[dict] = []
    extra_motifs = vision.motifs[1:4]
    for i, motif in enumerate(extra_motifs):
        y = 35 + i * 15
        if vision.symmetry:
            secondary.append({"motif": motif, "x": 25, "y": y})
            secondary.append({"motif": motif, "x": 75, "y": y})
        else:
            secondary.append({"motif": motif, "x": 30 + i * 20, "y": y})

    return CompositionResult(
        main=main,
        border=border,
        fill=_DENSITY_TO_FILL.get(vision.density, "Medium"),
        secondary=secondary,
    )
