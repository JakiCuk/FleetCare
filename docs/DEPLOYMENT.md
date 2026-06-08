# FleetCare — Nasadenie (manuálne)

> ⚠️ Projekt je **vo vývoji**. Tento návod je pripravený pre budúce nasadenie; nasadenie
> vykonáva používateľ ručne (mimo automatizovaného workflowu). Počas vývoja sa **netestuje
> na PC**.

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
Namiesto lokálneho buildu sa dajú stiahnuť publikované images z GHCR
(`ghcr.io/<owner>/fleetcare-backend` a `…-frontend`). Po prvom behu workflowu
`.github/workflows/docker-publish.yml` (push na `main` / `claude/**`) sa objavia
v sekcii **Packages** repozitára.
```bash
docker login ghcr.io               # ak je balík privátny (heslo = PAT s read:packages)
export GHCR_OWNER=jakicuk           # GHCR namespace, malými písmenami
export BUILD_VERSION=latest         # alebo konkrétny yyyymmddhhmm tag
docker compose -f docker-compose.yml -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.yml -f docker-compose.ghcr.yml up -d
```
> Novo vytvorené balíky sú **privátne** — buď sa pri pulle prihlás (`docker login ghcr.io`),
> alebo ich v GitHube prepni na *Public* (Package → Settings).

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

## Zálohovanie
- DB: `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`
- Alebo „Exportovať všetky dáta" (JSON) v Nastaveniach.

## Bezpečnostné odporúčania (pred produkčným použitím)
- Silné `JWT_SECRET`, `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`.
- HTTPS (reverzná proxy/Traefik/Caddy pred nginx) a `Secure` cookies.
- Uzamknutý `CORS_ORIGINS` na reálnu doménu.
- Nepúšťať s `SEED_DEMO=true` v produkcii.
