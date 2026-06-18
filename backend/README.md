# AI Embroidery Sketch Composer — Backend

FastAPI backend scaffold for the development roadmap. Generates original pencil
embroidery sketches from a reference image through a multi-module pipeline.

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then add your OPENAI_API_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

## Module → code map

| Roadmap module | Code |
| --- | --- |
| 1. Authentication / Credits | `app/api/auth.py`, `app/security.py` |
| 2. Project | `app/api/projects.py` |
| 3. Upload Reference | `app/api/upload.py`, `app/services/storage.py` |
| 4. Vision Analysis | `app/services/vision.py` (`POST /analyze`) |
| 5. Garment / 6. Placement | `app/schemas.py` enums, `PUT .../garment` |
| 7. Measurement Engine | `app/services/measurements.py` |
| 8. Composition Engine | `app/services/composition.py` |
| 9. Rules Engine | `app/services/rules.py` |
| 10. Prompt Builder | `app/services/prompt_builder.py` |
| 11. Image Generator | `app/services/image_generation.py` |
| 12. Review Engine | `app/services/review.py` |
| Phase 2 pipeline | `app/api/pipeline.py` (`POST .../generate`) |

## Typical flow

1. `POST /api/auth/register` → `POST /api/auth/login` (get token)
2. `POST /api/projects` → create project
3. `POST /api/projects/{id}/reference` → upload JPG/PNG/WEBP
4. `POST /api/projects/{id}/analyze` → Module 4 vision JSON
5. `PUT /api/projects/{id}/garment` → garment + placement
6. `POST /api/projects/{id}/measurements` → Module 7 geometry
7. `POST /api/projects/{id}/generate` → runs Modules 8–12, returns 4 sketches

## Notes / not yet wired

- **Phase 3 Variation Engine** and **Phase 4 Collection Builder** are not built
  yet — the pipeline is structured so they slot on top of `pipeline.py`.
- **Future V2 Composition AI** would replace the deterministic
  `composition.py` planner with an LLM design-plan step (same output contract).
- DB tables are auto-created on startup for dev; add **Alembic** migrations for
  production. Swap SQLite → Postgres via `DATABASE_URL`.
- `forgot-password` is a stub (no email sender wired).
```
