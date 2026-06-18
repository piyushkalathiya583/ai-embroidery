"""Pydantic schemas — the JSON contracts in the roadmap's API/JSON flow."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field


# ---------- Module 1: Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str | None
    subscription_tier: str
    credits: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Module 2: Project ----------
class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: str
    is_favourite: bool
    garment: str | None
    placement: str | None
    created_at: datetime


# ---------- Module 4: Vision Analysis output ----------
class VisionResult(BaseModel):
    style: str
    symmetry: bool
    density: str
    motifs: list[str]
    border: str
    layout: str


# ---------- Module 5: Garment ----------
class Garment(str, Enum):
    lehenga = "Lehenga"
    kurti = "Kurti"
    blouse = "Blouse"
    dupatta = "Dupatta"
    panel = "Panel"


# ---------- Module 6: Placement ----------
class Placement(str, Enum):
    single_kali = "Single Kali"
    kali_12 = "12 Kali"
    kali_16 = "16 Kali"
    kali_24 = "24 Kali"
    all_over = "All Over"
    neck = "Neck"
    sleeve = "Sleeve"
    daman = "Daman"
    border = "Border"
    panel = "Panel"


class GarmentSelection(BaseModel):
    garment: Garment
    placement: Placement


# ---------- Module 7: Measurement Engine ----------
class MeasurementInput(BaseModel):
    waist: float = Field(gt=0, description="Waist in inches")
    height: float = Field(gt=0, description="Garment height in inches")
    margin: float = Field(ge=0, default=0.5)
    kali: int = Field(gt=0, default=12)


class MeasurementResult(BaseModel):
    top_width: float
    bottom_width: float
    height: float
    safe_area: float


# ---------- Module 8: Composition Engine ----------
class CompositionResult(BaseModel):
    main: dict = Field(description="Main motif anchor, e.g. {'x':50,'y':60}")
    border: dict = Field(description="Border spec, e.g. {'height':4}")
    fill: str = Field(description="Fill density, e.g. 'Medium'")
    secondary: list[dict] = Field(default_factory=list)


# ---------- Phase 3: Variation Engine ----------
class VariationType(str, Enum):
    more_luxury = "More Luxury"
    more_floral = "More Floral"
    more_empty = "More Empty"
    heavy_border = "Heavy Border"
    simple_border = "Simple Border"
    heavy_fill = "Heavy Fill"
    minimal_fill = "Minimal Fill"


class VariationRequest(BaseModel):
    base_sketch_id: int
    variation: VariationType
    n_variants: int = Field(default=1, ge=1, le=2)


# ---------- Phase 4: Collection Builder ----------
COMPANION_CHOICES = ["Blouse", "Dupatta", "Border", "Kurti", "Panel"]


class CollectionRequest(BaseModel):
    base_sketch_id: int
    pieces: list[str] = Field(
        default_factory=lambda: list(COMPANION_CHOICES),
        description="Which companion pieces to generate.",
    )


class CollectionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    piece: str
    image_path: str
    created_at: datetime

    @computed_field
    @property
    def image_url(self) -> str:
        name = self.image_path.replace("\\", "/").split("/")[-1]
        return f"/files/uploads/{name}"


class CollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    base_sketch_id: int
    created_at: datetime
    items: list[CollectionItemOut]


# ---------- Module 12: Review Engine ----------
class ReviewResult(BaseModel):
    copied: bool
    balanced: bool
    symmetry: bool
    luxury: bool
    production_friendly: bool


class SketchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_path: str
    variant_index: int
    created_at: datetime

    @computed_field
    @property
    def image_url(self) -> str:
        # Served by the StaticFiles mount at /files (storage root).
        name = self.image_path.replace("\\", "/").split("/")[-1]
        return f"/files/uploads/{name}"


# ---------- Full JSON flow (roadmap "JSON Flow") ----------
class SketchPipelineRequest(BaseModel):
    """Kick off the full Phase 2 generation pipeline for a project."""

    # Capped at 2: free Pollinations is ~20s/image from datacenter IPs, so more
    # would exceed the serverless timeout. Raise this if you move off Vercel.
    n_variants: int = Field(default=2, ge=1, le=2)


class ProjectState(BaseModel):
    """Everything needed to rehydrate the Create Sketch page on reopen."""

    project: "ProjectOut"
    vision: VisionResult | None = None
    measurement_input: MeasurementInput | None = None
    measurement_result: MeasurementResult | None = None
    sketches: list["SketchOut"] = []


class SketchPipelineResult(BaseModel):
    reference_analysis: VisionResult
    garment: GarmentSelection
    measurements: MeasurementResult
    composition: CompositionResult
    rules: list[str]
    prompt: str
    output: list[SketchOut]
