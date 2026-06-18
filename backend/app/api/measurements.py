"""Module 7 — Measurement Engine endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Measurement, Project, User
from app.schemas import MeasurementInput, MeasurementResult
from app.security import get_current_user
from app.services.measurements import compute_measurements

router = APIRouter(prefix="/api/projects/{project_id}", tags=["measurements"])


def _get_owned(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id or project.is_deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.post("/measurements", response_model=MeasurementResult)
def set_measurements(
    project_id: int,
    data: MeasurementInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)
    result = compute_measurements(data)

    existing = (
        db.query(Measurement).filter(Measurement.project_id == project.id).first()
    )
    if existing:
        existing.waist = data.waist
        existing.height = data.height
        existing.margin = data.margin
        existing.kali = data.kali
        existing.result = result.model_dump()
    else:
        db.add(
            Measurement(
                project_id=project.id,
                waist=data.waist,
                height=data.height,
                margin=data.margin,
                kali=data.kali,
                result=result.model_dump(),
            )
        )
    db.commit()
    return result
