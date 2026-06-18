"""Module 3 — Upload Reference + Module 4 trigger."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, ReferenceImage, User, VisionAnalysis
from app.schemas import VisionResult
from app.security import get_current_user
from app.services import vision as vision_service
from app.services.storage import save_reference
from app.config import settings

router = APIRouter(prefix="/api/projects/{project_id}", tags=["upload", "vision"])


def _get_owned(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id or project.is_deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.post("/reference")
async def upload_reference(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)
    stored = await save_reference(file)
    ref = ReferenceImage(project_id=project.id, **stored)
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return {
        "id": ref.id,
        "thumbnail_path": ref.thumbnail_path,
        "original_path": ref.original_path,
    }


@router.post("/analyze", response_model=VisionResult)
def analyze(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Module 4 — run vision analysis on the latest reference image."""
    project = _get_owned(db, project_id, user)
    ref = (
        db.query(ReferenceImage)
        .filter(ReferenceImage.project_id == project.id)
        .order_by(ReferenceImage.created_at.desc())
        .first()
    )
    if not ref:
        raise HTTPException(status_code=400, detail="No reference image uploaded.")

    result = vision_service.analyze_image(ref.original_path)

    # Upsert one analysis per project.
    existing = (
        db.query(VisionAnalysis)
        .filter(VisionAnalysis.project_id == project.id)
        .first()
    )
    if existing:
        existing.result = result.model_dump()
        existing.model = settings.vision_model
    else:
        db.add(
            VisionAnalysis(
                project_id=project.id,
                result=result.model_dump(),
                model=settings.vision_model,
            )
        )
    db.commit()
    return result
