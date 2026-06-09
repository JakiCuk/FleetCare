# FleetCare — Nasadenie (Docker)

> ✅ FleetCare je **funkčný** a beží ako kompletný Docker stack. Nasadenie je samohostené;
> pred vystavením na internet zmeň predvolené tajomstvá a nasaď HTTPS. Aplikácia sa ďalej
> vyvíja — pribúdajú nové funkcie.

## Predpoklady
- Docker + Docker Compose v2.
- Otvorené porty podľa `.env` (default 8080 frontend, 8000 backend).

## Kroky
```bash
git clone <repo> FleetCare && cd FleetCare
cp .env.example .env
# Uprav .env: POSTGRES_PASSWORD, JWT_SECRET, ADMIN_PASSWORD, (SMTP/Matrix podľa potreby)
docker compose up -d --build
```

Backend pri štarte spustí migrácie (`alembic upgrade head`) a seed (admin + default
nastavenia). Skontroluj zdravie:
```bash
docker compose ps
curl -s http://localhost:8000/api/health   # -> {"status":"ok",...}
```

Otvor `http://localhost:8080` a prihlás sa ako `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

## Verzia buildu (yyyymmddhhmm)
Každý image nesie verziu vo formáte `yyyymmddhhmm` (UTC, čas buildu):
- **Backend** — `GET /api/health` → pole `build` (napr. `"build":"202606081345"`).
- **Frontend** — vľavo dole v sidebare „build …".

Lokálny build dostane verziu z premennej `BUILD_VERSION` (default `dev`):
```bash
BUILD_VERSION=$(date -u +%Y%m%d%H%M) docker compose up -d --build
```
V GHCR sa nastavuje automaticky (workflow „Publish Docker images (GHCR)").

## Beh z hotových GHCR images (GitHub Packages)
Celý stack (DB, Redis, backend, worker, beat, frontend) sa spustí z publikovaných
images **jedným príkazom** — netreba lokálny build:
```bash
docker login ghcr.io        # len ak je balík privátny (heslo = PAT s read:packages)
docker compose -f docker-compose.ghcr.yml up -d
```
> `docker pull ghcr.io/<owner>/fleetcare-backend:latest` stiahne len **jeden** zo šiestich
> kontajnerov; appka potrebuje celý stack, preto ho `docker compose` poskladá naraz.
> Voliteľne v `.env`: `GHCR_OWNER` (default `jakicuk`), `IMAGE_TAG` (default `latest`, alebo
> konkrétny `yyyymmddhhmm`). Novo vytvorené balíky sú **privátne** — prihlás sa, alebo ich
> v GitHube prepni na *Public* (Package → Settings). Images sa publikujú pri pushi na `main`,
> pri tagu `v*`, alebo ručne cez *Run workflow*.

## Komponenty
| Služba | Popis |
|---|---|
| `db` | PostgreSQL 16 (volume `db_data`) |
| `redis` | broker/result backend pre Celery |
| `backend` | FastAPI (REST API + migrácie + seed) |
| `worker` | Celery worker (odosielanie notifikácií) |
| `beat` | Celery scheduler (denné úlohy o `daily_send_time`) |
| `frontend` | nginx servuje React build + proxy `/api` na backend |

## Konfigurácia notifikácií
- **SMTP** a **Matrix** sa nastavujú v `.env` (default) a/alebo v Admin paneli (uložené v DB).
- „Test send" v Admine overí funkčnosť kanálov.

## Aktualizácia
```bash
git pull
docker compose up -d --build
```

## Riešenie problémov

### Windows: kontajnery `backend`/`worker`/`beat`/`frontend` padajú (db a redis bežia)
Takmer vždy ide o **CRLF konce riadkov** a/alebo **hostovský `node_modules`**:
- Git na Windows má v predvolenom nastavení `core.autocrlf=true` a prepíše `entrypoint.sh`
  na CRLF → shebang `#!/usr/bin/env bash` zlyhá v Linux kontajneri
  (`env: 'bash\r': No such file or directory`) → backend/worker/beat sa reštartujú dokola.
  Repo má `.gitattributes` (vynucuje LF) a Dockerfile CRLF aj tak odstráni pri builde, takže
  stačí **stiahnuť aktuálnu vetvu a rebuildnúť**:
  ```bash
  git pull
  docker compose build --no-cache backend worker beat
  docker compose up -d
  ```
- Ak si predtým na Windows hosti spustil `npm install`, zmaž `frontend/node_modules`
  (image si nainštaluje vlastné Linux závislosti; `.dockerignore` ho už do buildu nekopíruje):
  ```bash
  rmdir /s /q frontend\node_modules   # PowerShell: Remove-Item -Recurse -Force frontend\node_modules
  docker compose build --no-cache frontend
  docker compose up -d
  ```
- Diagnostika konkrétneho pádu: `docker compose logs backend` (resp. `frontend`).

## Zálohovanie
- DB: `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`
- Alebo „Exportovať všetky dáta" (JSON) v Nastaveniach.

## Bezpečnostné odporúčania (pred produkčným použitím)
- Silné `JWT_SECRET`, `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`.
- HTTPS (reverzná proxy/Traefik/Caddy pred nginx) a `Secure` cookies.
- Uzamknutý `CORS_ORIGINS` na reálnu doménu.
- Nepúšťať s `SEED_DEMO=true` v produkcii.
