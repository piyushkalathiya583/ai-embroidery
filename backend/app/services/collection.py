"""Phase 4 — Collection Builder.

From one base sketch (its vision + composition), generate a matching set of
companion pieces — Blouse, Dupatta, Border, Kurti, Panel — that share the same
style, motifs and density so the whole outfit reads as one collection.
"""
from app.schemas import (
    CompositionResult,
    Garment,
    GarmentSelection,
    MeasurementResult,
    Placement,
    VisionResult,
)

# Each companion piece -> (garment, placement) used to retarget the prompt.
COMPANION_PIECES: dict[str, tuple[Garment, Placement]] = {
    "Blouse": (Garment.blouse, Placement.all_over),
    "Dupatta": (Garment.dupatta, Placement.all_over),
    "Border": (Garment.dupatta, Placement.border),
    "Kurti": (Garment.kurti, Placement.all_over),
    "Panel": (Garment.panel, Placement.panel),
}


def piece_context(
    piece: str, vision: VisionResult, composition: CompositionResult
) -> tuple[GarmentSelection, VisionResult, CompositionResult]:
    """Build the (selection, vision, composition) for a single companion piece.

    The vision/composition are kept identical to the base so motifs, style and
    palette stay consistent across the set; only the garment/placement changes.
    """
    garment, placement = COMPANION_PIECES[piece]
    selection = GarmentSelection(garment=garment, placement=placement)
    return selection, vision, composition


def companion_measurements(base: MeasurementResult) -> MeasurementResult:
    """Companion pieces reuse the base safe area; geometry is piece-agnostic here."""
    return base
