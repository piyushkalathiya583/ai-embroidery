"""Phase 4 — Collection Builder endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Collection,
    CollectionItem,
    GeneratedSketch,
    Measurement,
    Project,
    User,
    VisionAnalysis,
)
from app.schemas import (
    CollectionOut,
    CollectionRequest,
    COMPANION_CHOICES,
    CompositionResult,
    MeasurementResult,
    VisionResult,
)
from app.security import get_current_user
from app.services.collection import (
    companion_measurements,
    piece_context,
)
from app.services.image_generation import generate
from app.services.prompt_builder import build_prompt
from app.services.rules import select_rules

router = APIRouter(prefix="/api/projects/{project_id}", tags=["collection"])
user_router = APIRouter(prefix="/api/collections", tags=["collection"])


def _to_collection_out(c: Collection, project: Project | None) -> CollectionOut:
    out = CollectionOut.model_validate(c)
    if project is not None:
        out.project_id = project.id
        out.project_name = project.name
    out.title = f"Collection #{c.id}" + (
        f" — {project.name}" if project else ""
    )
    return out


def _get_owned(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id or project.is_deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.post("/collection", response_model=CollectionOut)
def build_collection(
    project_id: int,
    req: CollectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)

    pieces = [p for p in req.pieces if p in COMPANION_CHOICES]
    if not pieces:
        raise HTTPException(status_code=400, detail="No valid pieces requested.")
    if user.credits < len(pieces):
        raise HTTPException(
            status_code=402,
            detail=f"Need {len(pieces)} credits, have {user.credits}.",
        )

    base = db.get(GeneratedSketch, req.base_sketch_id)
    if not base or base.project_id != project.id or base.composition is None:
        raise HTTPException(status_code=404, detail="Base sketch not found.")

    va = (
        db.query(VisionAnalysis)
        .filter(VisionAnalysis.project_id == project.id)
        .first()
    )
    meas = db.query(Measurement).filter(Measurement.project_id == project.id).first()
    if not va or not meas:
        raise HTTPException(status_code=400, detail="Missing vision/measurements.")

    vision = VisionResult(**va.result)
    composition = CompositionResult(**base.composition)
    measurements = companion_measurements(MeasurementResult(**meas.result))

    collection = Collection(project_id=project.id, base_sketch_id=base.id)
    db.add(collection)
    db.flush()

    for piece in pieces:
        selection, p_vision, p_comp = piece_context(piece, vision, composition)
        rules = select_rules(db, p_vision, selection)
        prompt = build_prompt(p_vision, p_comp, rules, measurements, selection)
        # One image per companion piece, keeping the set tight.
        image_path = generate(prompt, n=1)[0]
        db.add(
            CollectionItem(
                collection_id=collection.id,
                piece=piece,
                image_path=image_path,
                prompt=prompt,
            )
        )

    user.credits -= len(pieces)
    db.commit()
    db.refresh(collection)
    return collection


@router.get("/collections", response_model=list[CollectionOut])
def list_collections(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)
    cols = (
        db.query(Collection)
        .filter(Collection.project_id == project.id)
        .order_by(Collection.created_at.desc())
        .all()
    )
    return [_to_collection_out(c, project) for c in cols]


@user_router.get("", response_model=list[CollectionOut])
def list_all_collections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """All collections across the user's projects — powers the Collection tab."""
    cols = (
        db.query(Collection)
        .join(Project, Collection.project_id == Project.id)
        .filter(Project.owner_id == user.id, Project.is_deleted.is_(False))
        .order_by(Collection.created_at.desc())
        .all()
    )
    out = []
    for c in cols:
        project = db.get(Project, c.project_id)
        out.append(_to_collection_out(c, project))
    return out
