"""Admin utilities — guarded by the ADMIN_TOKEN env var (X-Admin-Token header)."""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(x_admin_token: str = Header(default="")) -> None:
    if not settings.admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin token required."
        )


@router.post("/credits", response_model=UserOut)
def set_credits(
    email: str,
    credits: int,
    _: None = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.credits = credits
    db.commit()
    db.refresh(user)
    return user
