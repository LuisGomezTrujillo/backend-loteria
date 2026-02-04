# Copilot instructions — backend-loteria

Short, actionable guidance for AI coding agents working on this FastAPI + SQLModel backend.

- **Project purpose:** small FastAPI service that stores lottery results (Sorteo records).

- **Entry point:** `main.py` (FastAPI app). Startup calls `create_db_and_tables()`.

- **DB layer:** `database.py` uses `sqlmodel` with an engine selected from `DATABASE_URL`; if unset it falls back to `sqlite:///./database.db`. Note: code normalizes `postgres://` to `postgresql://`.

- **Model & schema:** `models.py` defines `Sorteo` as a `SQLModel` table and as the Pydantic response model. Use the same class for request/response validation.

- **Key endpoints (examples):**
  - `POST /resultados/` — body: `Sorteo` JSON (server sets `creado_at`).
  - `GET /resultados/` — returns all records.
  - `GET /resultados/sorteo/{num_sorteo}` — filter by `numero_sorteo`.

- **Run / dev commands:**
  - Start locally: `uvicorn main:app --reload --port 10000`
  - Production suggestion: bind host `0.0.0.0` and use a proper process manager.

- **Environment notes:**
  - Set `DATABASE_URL` to a full SQLAlchemy URL for Postgres (the code rewrites `postgres://` to `postgresql://`).
  - Default local DB file: `database.db` in the project root.

- **Patterns & conventions to follow:**
  - Use `sqlmodel` models for both ORM and response modeling (see `models.py`).
  - Use dependency `get_session()` from `database.py` (it yields a `Session`) in endpoints.
  - Commit, refresh, and return persisted objects in POST handlers (see `registrar_resultado`).

- **Where to modify / extend:**
  - Add new tables in `models.py` and let `create_db_and_tables()` create them on startup.
  - If adding migrations or production DBs, replace `create_db_and_tables()` with a migration tool (Alembic).

- **Examples (payload):**
  ```json
  {
    "numero_sorteo": "2026-01-28-001",
    "fecha_sorteo": "28 de Enero 2026",
    "plan_premios": "planA",
    "titulo_premio": "MAYOR",
    "resultado_concatenado": "123456",
    "inputs_usados": 6
  }
  ```

- **Files to inspect for context:** `main.py`, `database.py`, `models.py`, `requirements.txt`.

If anything here is unclear or you want more detail (tests, CI, or migration strategy), tell me which area to expand.
