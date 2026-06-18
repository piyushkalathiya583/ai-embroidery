"""Module 7 — Measurement Engine.

Pure, deterministic geometry. Given the waist circumference, garment height,
seam margin and number of kalis (panels), compute the per-kali panel geometry.

A "kali" is a single flared panel of a ghaghra/lehenga. The waist circumference
is split across all kalis to get each panel's top width; the panels flare out to
form the full hem (sweep) at the bottom.
"""
from app.schemas import MeasurementInput, MeasurementResult

# Hem sweep is modelled as a multiple of the waist. A fuller flare → bigger sweep.
DEFAULT_SWEEP_FACTOR = 2.2


def compute_measurements(
    data: MeasurementInput, sweep_factor: float = DEFAULT_SWEEP_FACTOR
) -> MeasurementResult:
    top_width = round(data.waist / data.kali, 2)
    bottom_width = round((data.waist * sweep_factor) / data.kali, 2)
    # Safe area = embroiderable height after reserving the seam margin top & bottom.
    safe_area = round(data.height - data.margin, 2)

    return MeasurementResult(
        top_width=top_width,
        bottom_width=bottom_width,
        height=data.height,
        safe_area=safe_area,
    )
