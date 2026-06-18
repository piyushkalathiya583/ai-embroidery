"""Vercel serverless entry point — exposes the FastAPI app.

The backend lives under /backend; add it to sys.path so `app.*` imports resolve
inside the lambda (backend/** is bundled via vercel.json includeFiles).
"""
import os
import sys

_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(_BACKEND))

from app.main import app, init_db  # noqa: E402

# Vercel's Python runtime may not fire ASGI lifespan, so init tables eagerly.
try:
    init_db()
except Exception as exc:  # pragma: no cover - surfaced in Vercel logs
    print(f"init_db failed: {exc}")
