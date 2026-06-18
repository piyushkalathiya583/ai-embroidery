"""SQLAlchemy models — mirrors the DATABASE section of the roadmap."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Subscription / credits (Module 1)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free")
    credits: Mapped[int] = mapped_column(Integer, default=10)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="draft")
    is_favourite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Module 5 / 6: garment + placement selections
    garment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    placement: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now
    )

    owner: Mapped["User"] = relationship(back_populates="projects")
    reference_images: Mapped[list["ReferenceImage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    vision_analysis: Mapped["VisionAnalysis | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    measurement: Mapped["Measurement | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    sketches: Mapped[list["GeneratedSketch"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ReferenceImage(Base):
    __tablename__ = "reference_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    original_path: Mapped[str] = mapped_column(String(512))
    thumbnail_path: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="reference_images")


class VisionAnalysis(Base):
    __tablename__ = "vision_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    # The Module 4 JSON output
    result: Mapped[dict] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="vision_analysis")


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    # Module 7 inputs
    waist: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    margin: Mapped[float] = mapped_column(Float, default=0.5)
    kali: Mapped[int] = mapped_column(Integer, default=12)

    # Module 7 computed output
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="measurement")


class GeneratedSketch(Base):
    __tablename__ = "generated_sketches"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    image_path: Mapped[str] = mapped_column(String(512))
    prompt: Mapped[str] = mapped_column(Text)
    composition: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    variant_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship(back_populates="sketches")
    review: Mapped["Review | None"] = relationship(
        back_populates="sketch", uselist=False, cascade="all, delete-orphan"
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    sketch_id: Mapped[int] = mapped_column(ForeignKey("generated_sketches.id"))
    # Module 12 output: copied / balanced / symmetry / luxury / production_friendly
    result: Mapped[dict] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    sketch: Mapped["GeneratedSketch"] = relationship(back_populates="review")


class Rule(Base):
    """Module 9 — JSON rules library, seedable/editable."""

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    definition: Mapped[dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PromptTemplate(Base):
    """Module 10 — server-side prompt templates (user never sees these)."""

    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    template: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Asset(Base):
    """Binary store for images when STORAGE_BACKEND=db (serverless/Vercel)."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    content_type: Mapped[str] = mapped_column(String(100))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Collection(Base):
    """Phase 4 — a matching set built from one base sketch."""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    base_sketch_id: Mapped[int] = mapped_column(ForeignKey("generated_sketches.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    items: Mapped[list["CollectionItem"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )


class CollectionItem(Base):
    __tablename__ = "collection_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    piece: Mapped[str] = mapped_column(String(50))  # Blouse, Dupatta, Border...
    image_path: Mapped[str] = mapped_column(String(512))
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    collection: Mapped["Collection"] = relationship(back_populates="items")
