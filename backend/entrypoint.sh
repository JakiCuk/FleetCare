#!/usr/bin/env bash
# FleetCare backend entrypoint.
#   - optionally waits for the DB,
#   - runs Alembic migrations + seed when RUN_MIGRATIONS=true,
#   - then launches the API server.
set -euo pipefail

RUN_MIGRATIONS="${RUN_MIGRATIONS:-false}"

# Optional best-effort wait for Postgres (compose healthchecks already gate us).
wait_for_db() {
  python - <<'PY' || true
import asyncio
import os

async def main():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return
    try:
        import asyncpg  # noqa: F401
    except Exception:
        return
    # asyncpg needs a plain DSN (strip the SQLAlchemy +asyncpg driver suffix).
    dsn = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    import asyncpg
    for _ in range(30):
        try:
            conn = await asyncpg.connect(dsn=dsn, timeout=3)
            await conn.close()
            print("db: ready")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"db: waiting ({exc})")
            await asyncio.sleep(2)
    print("db: giving up wait; continuing")

asyncio.run(main())
PY
}

if [ "${RUN_MIGRATIONS}" = "true" ]; then
  wait_for_db
  echo "Running Alembic migrations..."
  alembic upgrade head
  echo "Running seed..."
  python -m app.seed
fi

# Run the explicit command if one was given (e.g. the Celery worker/beat
# services pass one via compose `command:`); otherwise default to the API.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
