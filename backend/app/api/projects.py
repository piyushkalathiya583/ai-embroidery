"""Module 2 — Project (new, list, history, favourite, delete) + Module 5/6."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User
from app.schemas import GarmentSelection, ProjectCreate, ProjectOut
from app.security import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_owned(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id or project.is_deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = Project(name=data.name, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    favourite: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Project).filter(
        Project.owner_id == user.id, Project.is_deleted.is_(False)
    )
    if favourite is not None:
        q = q.filter(Project.is_favourite.is_(favourite))
    return q.order_by(Project.created_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_owned(db, project_id, user)


@router.patch("/{project_id}/favourite", response_model=ProjectOut)
def toggle_favourite(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)
    project.is_favourite = not project.is_favourite
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}/garment", response_model=ProjectOut)
def set_garment(
    project_id: int,
    selection: GarmentSelection,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)
    project.garment = selection.garment.value
    project.placement = selection.placement.value
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_owned(db, project_id, user)
    project.is_deleted = True  # soft delete
    db.commit()
