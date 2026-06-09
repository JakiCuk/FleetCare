# FleetCare — SDLC plán a rozdelenie práce

Projekt sa riadi klasickým SDLC. Orchestrátor (Claude Code) **zastrešuje** celý cyklus,
píše spoločné kontrakty a integruje; zameraní **subagenti** realizujú jednotlivé časti
vývoja, pričom **každý robí len jednu vec**.

---

## Fázy SDLC

| Fáza | Výstup | Kto |
|---|---|---|
| **1. Plánovanie** | README, ciele, rozsah, tech stack, slices | Orchestrátor ✅ |
| **2. Analýza** | analýza zadania + grafického návrhu, požiadavky, roly | Orchestrátor ✅ |
| **3. Návrh** | DB schéma, API kontrakt, design systém, architektúra | Orchestrátor ✅ |
| **4. Vývoj** | SQL/DB, Backend, Frontend (podľa kontraktov) | Subagenti |
| **5. Testovanie** | jednotkové/integračné testy, CI (GitHub Actions) | Subagent QA |
| **6. Nasadenie** | docker-compose, `.env.example`, DEPLOYMENT.md | Orchestrátor pripraví; **nasadenie robí používateľ ručne** |

> Počas vývoja sa **netestuje na PC**. Subagenti **píšu** kód a testy, ale **nespúšťajú**
> ich lokálne (žiadne `npm`, `docker`, `pytest` behy). Verifikácia beží v CI na GitHube a
> finálne nasadenie vykoná používateľ.

---

## Rozdelenie subagentov (fáza Vývoj/Testovanie)

Každý subagent dostane: tento plán + relevantné kontrakty (`DATABASE_SCHEMA.md`,
`API_CONTRACT.md`, `DESIGN_SYSTEM.md`, `TECHNICAL_SPECIFICATION.md`) a **presný zoznam
súborov, ktoré vlastní** (aby nevznikali konflikty). Subagenti **negitujú** — commit/push
robí orchestrátor.

### A. Subagent „SQL/Databáza"
**Cieľ:** dátová vrstva.
**Vlastní:**
- `backend/app/database.py` (async engine, `Base`, session dependency)
- `backend/app/models/*.py` (všetky ORM modely podľa `DATABASE_SCHEMA.md`)
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_initial.py`
- `backend/app/seed.py` (admin + default app_settings + voliteľné demo dáta)

### B. Subagent „Backend/API"
**Cieľ:** FastAPI aplikácia, biznis logika, notifikácie.
**Vlastní:**
- `backend/app/main.py`, `config.py`, `dependencies.py`, `security.py`
- `backend/app/schemas/*.py` (Pydantic v2)
- `backend/app/routers/*.py` (podľa `API_CONTRACT.md`)
- `backend/app/services/*.py` (`auth_service`, `notification_service`, `email_service`,
  `matrix_service`, `projection_service`, `fuel_service`, `dashboard_service`)
- `backend/app/workers/celery_app.py`, `workers/tasks.py`
- `backend/app/templates/*.j2` (email šablóny SK+EN)
- `backend/Dockerfile`, `backend/requirements.txt`, `backend/pyproject.toml` (ruff/pytest config)
> Importuje modely z `app.models` a `database.py` (vlastní agent A) podľa dohodnutých názvov.

### C. Subagent „Frontend"
**Cieľ:** React + TS + Vite PWA podľa `DESIGN_SYSTEM.md`.
**Vlastní:** celý `frontend/` —
- `frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`,
  `postcss.config.js`, `index.html`, `frontend/Dockerfile`, `frontend/nginx.conf`
- `frontend/src/main.tsx`, `App.tsx`, `router`, `api/client.ts` + doménové api moduly,
  `stores/*`, `components/{layout,common,charts}/*`, `pages/*`, `i18n/{index.ts,sk.json,en.json}`,
  `types/*`, PWA `manifest`/registrácia.

### D. Subagent „QA/Testovanie"
**Cieľ:** testy + CI (písané, nespúšťané lokálne).
**Vlastní:**
- `backend/tests/*` (pytest + httpx async; jednotkové testy `projection_service`, `fuel_service`,
  dedup; integračné testy auth/cars/documents s test DB cez fixtures)
- `frontend/src/**/__tests__/*` alebo `*.test.tsx` (Vitest + React Testing Library na kľúčové
  komponenty: StatusChip farby, CarCard, projekcia grafu)
- `.github/workflows/ci.yml` (backend: ruff + pytest; frontend: eslint + tsc + build; voliteľne
  docker build), `docs/TESTING.md`

---

## Orchestrácia (poradie a paralelizmus)

Keďže sa nič nespúšťa, agenti môžu bežať s maximálnou paralelizáciou, ak dodržia kontrakty:

1. **Round 1 (paralelne):** A (SQL/DB) ‖ B (Backend/API) ‖ C (Frontend).
   Spoločné kontrakty zaručujú zhodu názvov modelov, endpointov a typov.
2. **Round 2:** D (QA/Testovanie) — po dostupnosti kódu z Round 1.
3. **Integračný prechod (orchestrátor):** kontrola zhody (importy, názvy endpointov, typy),
   doplnenie chýbajúcich lepiacich súborov, oprava nezrovnalostí.
4. **Commit & push** po každom zmysluplnom celku na vetvu `claude/friendly-dijkstra-UlGFm`.

## Definícia hotového (DoD) pre prvý úplný prechod
- Repozitár obsahuje kompletnú štruktúru (backend + frontend + docker + CI + docs).
- Kód je vnútorne konzistentný s kontraktmi (kompiluje „by construction"; netestované na PC).
- README uvádza, že ide o funkčnú verziu v0.2, ktorá sa ďalej aktívne vyvíja.
- Migrácie pokrývajú celú schému; seed vytvorí admina a default nastavenia.
- CI workflow je nakonfigurované (beh na GitHube, nie na PC).
