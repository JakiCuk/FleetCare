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
