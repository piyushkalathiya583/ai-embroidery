"""Phase 2 — full generation pipeline.

API FLOW (roadmap): Vision JSON -> Composition -> Rules -> Prompt Builder ->
Image API -> Review -> Sketches. Ties Modules 8-12 together.
"""
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings

from app.database import get_db
from app.models import (
    GeneratedSketch,
    Measurement,
    Project,
    Review,
    User,
    VisionAnalysis,
)
from app.schemas import (
    CompositionResult,
    GarmentSelection,
    Garment,
    MeasurementInput,
    MeasurementResult,
    Placement,
    ProjectOut,
    ProjectState,
    SketchOut,
    SketchPipelineRequest,
    SketchPipelineResult,
    VariationRequest,
    VisionResult,
)
from app.security import get_current_user
from app.services.composition import build_composition
from app.services.image_generation import generate
from app.services.prompt_builder import build_prompt
from app.services.review import passed, review_sketch
from app.services.rules import select_rules
from app.services.variation import apply_variation

router = APIRouter(prefix="/api/projects/{project_id}", tags=["pipeline"])


def _get_owned(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id or project.is_deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get("/state", response_model=ProjectState)
def get_state(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return all saved work for a project so the UI can resume where it left off."""
    project = _get_owned(db, project_id, user)

    va = (
        db.query(VisionAnalysis)
        .filter(VisionAnalysis.project_id == project.id)
        .first()
    )
    meas = db.query(Measurement).filter(Measurement.project_id == project.id).first()
    sketches = (
        db.query(GeneratedSketch)
        .filter(GeneratedSketch.project_id == project.id)
        .order_by(GeneratedSketch.created_at.desc())
        .all()
    )

    return ProjectState(
        project=ProjectOut.model_validate(project),
        vision=VisionResult(**va.result) if va else None,
        measurement_input=(
            MeasurementInput(
                waist=meas.waist,
                height=meas.height,
                margin=meas.margin,
                kali=meas.kali,
            )
            if meas
            else None
        ),
        measurement_result=MeasurementResult(**meas.result) if meas else None,
        sketches=[SketchOut.model_validate(s) for s in sketches],
    )


def _generate_and_persist(
    db: Session,
    project: Project,
    vision: VisionResult,
    composition: CompositionResult,
    selection: GarmentSelection,
    measurements: MeasurementResult,
    n_variants: int,
) -> tuple[list[SketchOut], str, list]:
    """Run Rules -> Prompt -> Image -> Review and persist sketches.

    Shared by the initial pipeline and the Phase 3 variation engine.
    """
    rules = select_rules(db, vision, selection)
    prompt = build_prompt(vision, composition, rules, measurements, selection)
    image_paths = generate(prompt, n=n_variants)

    # Module 12 reviews run concurrently (and can be disabled to save time).
    reviews: list = [None] * len(image_paths)
    if settings.review_enabled:
        with ThreadPoolExecutor(max_workers=max(1, len(image_paths))) as pool:
            reviews = list(pool.map(review_sketch, image_paths))

    outputs: list[SketchOut] = []
    for idx, path in enumerate(image_paths):
        sketch = GeneratedSketch(
            project_id=project.id,
            image_path=path,
            prompt=prompt,
            composition=composition.model_dump(),
            variant_index=idx,
        )
        db.add(sketch)
        db.flush()

        review = reviews[idx]
        if review is not None:
            db.add(
                Review(
                    sketch_id=sketch.id,
                    result=review.model_dump(),
                    passed=passed(review),
                )
            )
        outputs.append(SketchOut.model_validate(sketch))

    return outputs, prompt, rules


@router.post("/generate", response_model=SketchPipelineResult)
def run_pipeline(
    project_id: int,
    req: SketchPipelineRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)

    # --- Gather prerequisites ---
    if user.credits < 1:
        raise HTTPException(status_code=402, detail="Not enough credits.")

    va = (
        db.query(VisionAnalysis)
        .filter(VisionAnalysis.project_id == project.id)
        .first()
    )
    if not va:
        raise HTTPException(status_code=400, detail="Run vision analysis first.")
    if not project.garment or not project.placement:
        raise HTTPException(status_code=400, detail="Select garment & placement.")
    meas = db.query(Measurement).filter(Measurement.project_id == project.id).first()
    if not meas:
        raise HTTPException(status_code=400, detail="Enter measurements first.")

    vision = VisionResult(**va.result)
    selection = GarmentSelection(
        garment=Garment(project.garment), placement=Placement(project.placement)
    )
    measurements = MeasurementResult(**meas.result)

    # --- Module 8: Composition ---
    composition: CompositionResult = build_composition(
        vision, measurements, selection
    )

    # --- Modules 9-12 ---
    outputs, prompt, rules = _generate_and_persist(
        db, project, vision, composition, selection, measurements, req.n_variants
    )

    user.credits -= 1
    project.status = "generated"
    db.commit()

    return SketchPipelineResult(
        reference_analysis=vision,
        garment=selection,
        measurements=measurements,
        composition=composition,
        rules=[r.key for r in rules],
        prompt=prompt,
        output=outputs,
    )


@router.post("/variations", response_model=SketchPipelineResult)
def run_variation(
    project_id: int,
    req: VariationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Phase 3 — re-generate from an existing sketch with one variation applied."""
    project = _get_owned(db, project_id, user)

    if user.credits < 1:
        raise HTTPException(status_code=402, detail="Not enough credits.")

    base = db.get(GeneratedSketch, req.base_sketch_id)
    if not base or base.project_id != project.id:
        raise HTTPException(status_code=404, detail="Base sketch not found.")
    if base.composition is None:
        raise HTTPException(status_code=400, detail="Base sketch has no composition.")

    va = (
        db.query(VisionAnalysis)
        .filter(VisionAnalysis.project_id == project.id)
        .first()
    )
    meas = db.query(Measurement).filter(Measurement.project_id == project.id).first()
    if not va or not meas:
        raise HTTPException(status_code=400, detail="Missing vision/measurements.")

    vision = VisionResult(**va.result)
    selection = GarmentSelection(
        garment=Garment(project.garment), placement=Placement(project.placement)
    )
    measurements = MeasurementResult(**meas.result)
    base_composition = CompositionResult(**base.composition)

    # --- Phase 3: apply the variation modifier ---
    vision, composition = apply_variation(req.variation, vision, base_composition)

    outputs, prompt, rules = _generate_and_persist(
        db, project, vision, composition, selection, measurements, req.n_variants
    )

    user.credits -= 1
    db.commit()

    return SketchPipelineResult(
        reference_analysis=vision,
        garment=selection,
        measurements=measurements,
        composition=composition,
        rules=[r.key for r in rules],
        prompt=prompt,
        output=outputs,
    )
