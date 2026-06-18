"""Module 9 — Rules Engine.

The most important module: all design rules live here as data, not code, so they
can be edited/seeded without redeploying. Rules are selected based on the garment,
placement and vision analysis, then handed to the Prompt Builder.
"""
from app.models import Rule
from app.schemas import GarmentSelection, VisionResult

# Default seed rules (Module 9). Persisted to the `rules` table on startup.
DEFAULT_RULES: list[dict] = [
    {
        "key": "no_embroidery_in_seam",
        "description": "No embroidery in seam allowance.",
        "definition": {"reserve_margin_inches": 0.5, "applies_to": "all"},
    },
    {
        "key": "minimum_gap",
        "description": "Maintain a minimum gap between motifs.",
        "definition": {"min_gap_mm": 4},
    },
    {
        "key": "heavy_border",
        "description": "Use a heavy, ornate border.",
        "definition": {"when": {"border": "Heavy"}},
    },
    {
        "key": "perfect_symmetry",
        "description": "Enforce perfect mirror symmetry.",
        "definition": {"when": {"symmetry": True}},
    },
    {
        "key": "luxury_spacing",
        "description": "Luxury, breathable spacing — avoid overcrowding.",
        "definition": {"when": {"style_contains": "Luxury"}},
    },
    {
        "key": "commercial_layout",
        "description": "Balanced, repeatable commercial layout.",
        "definition": {},
    },
    {
        "key": "machine_friendly",
        "description": "Machine-embroidery friendly: clean lines, no micro detail.",
        "definition": {"min_stitch_detail_mm": 1.0},
    },
]


def seed_rules(db) -> None:
    existing = {r.key for r in db.query(Rule).all()}
    for r in DEFAULT_RULES:
        if r["key"] not in existing:
            db.add(Rule(**r, is_active=True))
    db.commit()


def select_rules(
    db, vision: VisionResult, selection: GarmentSelection
) -> list[Rule]:
    """Return the active rules that apply to this design context."""
    applicable: list[Rule] = []
    for rule in db.query(Rule).filter(Rule.is_active.is_(True)).all():
        when = rule.definition.get("when", {})
        if not when:
            applicable.append(rule)
            continue
        if "symmetry" in when and when["symmetry"] != vision.symmetry:
            continue
        if "border" in when and when["border"] != vision.border:
            continue
        if "style_contains" in when and when["style_contains"] not in vision.style:
            continue
        applicable.append(rule)
    return applicable
