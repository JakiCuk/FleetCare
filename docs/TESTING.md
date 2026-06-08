# FleetCare — Testing

This document describes the automated test suites and how they run. Per the
project SDLC, **nothing is executed locally during development**: code is pushed
to GitHub and the test suites run there via GitHub Actions
(`.github/workflows/ci.yml`). The commands below are what CI runs; they are
listed for reference and for anyone reproducing CI on a machine that has the
toolchain installed.

## Layout

```
backend/tests/         pytest suite (unit + integration)
  conftest.py          async fixtures: test engine, session, http client, admin auth
  test_projection_service.py   unit — tread-wear regression/projection (§7.1)
  test_fuel_service.py         unit — l/100km from consecutive full tanks (§7.2)
  test_security.py             unit — argon2 hashing + JWT round-trips/expiry
  test_notification_dedup.py   unit (window) + integration (23h dedup decision, §7.6)
  test_auth.py                 integration — login / me / refresh
  test_cars.py                 integration — car CRUD, CarDetail, ownership 403
  test_health.py               integration — GET /api/health
  test_tires.py                integration — tire set + measurements + trend endpoint

frontend/src/**/__tests__/   Vitest + @testing-library/react suite
  lib/__tests__/colors.test.ts                 chip/tread/interval color rules
  components/common/__tests__/StatusChip.test.tsx
  pages/dashboard/__tests__/CarCard.test.tsx    overdue badge + red border + chips
  components/charts/__tests__/TireTrendChart.test.tsx   render smoke test
```

### Unit vs integration (backend)

- **Unit tests** import the service modules directly and build ORM objects in
  memory — no database. These are `test_projection_service.py`,
  `test_fuel_service.py`, `test_security.py`, and the window-constant test in
  `test_notification_dedup.py`.
- **Integration tests** use the `conftest.py` fixtures, which connect to a real
  Postgres, `create_all()` the schema, override the FastAPI `get_session`
  dependency, and exercise the app over HTTP (httpx `ASGITransport`). These are
  `test_auth.py`, `test_cars.py`, `test_health.py`, `test_tires.py`, and the
  `_already_sent` dedup test in `test_notification_dedup.py`.

The dedup *decision* (`notification_service._already_sent`) reads
`notification_log`, so it can only be tested against a database; only the 23h
window constant is a pure unit assertion.

## Backend — how it runs

Requires Python 3.12 and a reachable Postgres. CI provides a `postgres:16`
service and sets `DATABASE_URL` / `TEST_DATABASE_URL` to point at it
(`postgresql+asyncpg://fleetcare:changeme@localhost:5432/fleetcare`). The test
engine reads `TEST_DATABASE_URL` (falling back to `DATABASE_URL`).

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
ruff check app tests          # lint (config in pyproject.toml [tool.ruff])
pytest tests                  # asyncio_mode=auto is set in pyproject.toml
```

Test-only dependencies live in `backend/requirements-dev.txt`
(`pytest`, `pytest-asyncio`, `anyio`, `httpx`, `ruff`).

## Frontend — how it runs

Requires Node 20. Vitest config lives in `frontend/vite.config.ts`
(`environment: 'jsdom'`, `setupFiles: ['./src/test/setup.ts']`). The test
dependencies (`vitest`, `@testing-library/react`, `@testing-library/jest-dom`,
`jsdom`) are already in `frontend/package.json` devDependencies.

```bash
cd frontend
npm install                   # no package-lock.json is committed -> install, not ci
npm run lint
npx tsc -b --noEmit           # typecheck (also covers test files)
npm run test                  # vitest run
npm run build
```

`src/test/jest-dom.d.ts` pulls in jest-dom's Vitest matcher type augmentations
so `tsc` recognizes `toBeInTheDocument`/`toHaveClass`; runtime registration is in
the existing `src/test/setup.ts`.

## CI (GitHub Actions)

`.github/workflows/ci.yml` runs on every `push` and `pull_request` with two jobs:

- **backend** — ubuntu-latest, `postgres:16` service, Python 3.12, installs both
  requirements files, runs `ruff check` (non-blocking on pre-existing app-code
  style) and `pytest tests`.
- **frontend** — ubuntu-latest, Node 20, `npm install`, `npm run lint`,
  `npx tsc -b --noEmit`, `npm run test`, `npm run build`.
```
