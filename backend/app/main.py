from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    collection,
    files,
    measurements,
    pipeline,
    projects,
    upload,
)
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.rules import seed_rules


def init_db() -> None:
    """Create tables + seed rules. Idempotent. Use Alembic for real migrations."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_rules(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(upload.router)
app.include_router(measurements.router)
app.include_router(pipeline.router)
app.include_router(collection.router)
app.include_router(files.router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
