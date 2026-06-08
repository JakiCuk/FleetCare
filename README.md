# 🚗 FleetCare

> **Správa domácej automobilovej flotily** — centralizovaný dohľad nad viacerými autami:
> dokumenty (STK, poistenie, diaľničné známky), pneumatiky, servis, palivo a náklady,
> s automatickými notifikáciami a predikciou opotrebenia pneumatík.

---

## ✅ Stav projektu: funkčná verzia (v0.1)

FleetCare je **plne funkčný** — celý stack beží v Dockeri (frontend, REST API, Celery
workers, PostgreSQL, Redis). Funguje prihlásenie (JWT), evidencia áut a všetkých záznamov,
grafy, predikcia opotrebenia pneumatík aj denné notifikácie. Projekt sa **aktívne vyvíja a
ďalšie funkcie pribúdajú**.

> 🔒 **Self-hosted:** pred vystavením na internet zmeň predvolené tajomstvá (`JWT_SECRET`,
> `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`), nasaď HTTPS a uzamkni `CORS_ORIGINS`. Používaš na
> vlastné riziko, bez záruky.

> 🇬🇧 **Status: functional (v0.1).** FleetCare runs as a complete Docker stack and is usable;
> it is **actively developed and more features are being added**. Self-hosted — change the
> default secrets and put it behind HTTPS before exposing it.

---

## Čo to je

FleetCare je webová aplikácia (PWA) na **správu domáceho vozového parku**. Na jednom mieste
sleduje stav každého auta a včas upozorní, keď sa blíži expirácia dokumentu, servis alebo
zjazdenie pneumatík.

### Hlavné funkcie

- **Dashboard** — prehľad celej flotily, stat karty (počet áut, notifikácie dnes, overdue
  položky, mesačné náklady) a karty vozidiel s farebnými chipmi (STK / PZP / KASKO / vinetky).
- **Detail auta** so záložkami:
  - **Prehľad** — stav odometra + história, widget „Nadchádzajúce termíny" (servis, STK,
    poistenie, diaľničné známky) zoradený podľa naliehavosti.
  - **Dokumenty** — STK, PZP/KASKO poistenie, diaľničné známky (SK/AT/CZ/HU…) s dátumami
    platnosti a farebným odpočítavaním (zelená/žltá/červená).
  - **Pneumatiky** — sady pneumatík, merania dezénu na všetkých 4 kolesách + tlak (pred a po
    hustení pre každé koleso), **graf trendu s lineárnou predikciou** dosiahnutia hranice
    1,6 mm.
  - **Servis** — záznamy servisov a opráv vrátane detailného formulára podľa **servisnej
    knižky** (vykonané úkony, dodatočné práce, ďalšie termíny), plus servisné intervaly
    (km aj čas) s progress barmi.
  - **Palivo** — log tankovaní a výpočet spotreby (l/100 km) z plných nádrží.
  - **Náklady** — rozdelenie nákladov (koláčový graf) a výdavky.
- **Notifikácie** — automatické upozornenia cez **e-mail** a **Matrix**, s históriou
  odoslaní a deduplikáciou.
- **Admin** — notifikačné pravidlá (lead days 30/14/7 + „smart" pre pneumatiky/servis),
  log, SMTP a Matrix konfigurácia, správa používateľov a priradenie áut.
- **Nastavenia** — názov flotily, časové pásmo, **jazyk (SK/EN)**, mena, predvolené lead
  days, čas denných úloh, PWA inštalácia, export/zmazanie dát.
- **Bilingválne UI (SK + EN)** a **PWA** s podporou inštalácie na mobil.

## Ako to má fungovať (v skratke)

1. Používateľ sa prihlási (JWT). Admin spravuje autá, používateľov a notifikačné pravidlá.
2. Ku každému autu sa priebežne zapisujú údaje (odometer, dokumenty, merania pneumatík,
   servisy, tankovania, výdavky).
3. **Plánovač (Celery beat)** každý deň vyhodnotí:
   - blížiace sa expirácie dokumentov (podľa lead days),
   - servisné intervaly (km/čas),
   - predikciu zjazdenia pneumatík (lineárna regresia → dátum dosiahnutia 1,6 mm),
   a pošle notifikácie cez e-mail/Matrix priradeným používateľom (s deduplikáciou).
4. Dashboard a grafy zobrazujú aktuálny stav a trendy.

## Technológie

| Vrstva | Technológia |
|---|---|
| Backend | Python 3.12 · FastAPI (async) · SQLAlchemy 2.0 · Pydantic v2 · Alembic |
| Databáza | PostgreSQL 16 |
| Úlohy / fronta | Celery + Redis 7 (beat pre denné úlohy) |
| Notifikácie | SMTP (Jinja2 šablóny) · Matrix (matrix-nio) |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · Recharts · Zustand · react-i18next |
| PWA | vite-plugin-pwa + Workbox |
| Nasadenie | Docker Compose (db · redis · backend · worker · beat · frontend/nginx) |

## Architektúra (Docker Compose)

```
┌────────────┐   ┌────────────┐
│  frontend  │   │   backend  │  FastAPI (async REST API + JWT)
│  (nginx)   │──▶│            │──┐
└────────────┘   └────────────┘  │
                  ┌────────────┐  │   ┌──────────────┐
                  │   worker   │  ├──▶│ PostgreSQL 16│
                  │  (celery)  │──┤   └──────────────┘
                  └────────────┘  │   ┌──────────────┐
                  ┌────────────┐  └──▶│   Redis 7    │
                  │    beat    │──────└──────────────┘
                  │  (celery)  │   (denné notifikačné úlohy)
                  └────────────┘
```

## Spustenie (Docker)

**Build lokálne:**
```bash
cp .env.example .env      # vyplň tajomstvá (DB heslo, JWT secret, SMTP, Matrix)
docker compose up -d --build
# Frontend:  http://localhost:8080   ·   Backend health: http://localhost:8000/api/health
```

**Alebo hotové images z GHCR (bez buildu):**
```bash
docker login ghcr.io      # len ak je balík privátny
docker compose -f docker-compose.ghcr.yml up -d
```

Prihlás sa ako `admin` / `ADMIN_PASSWORD`. Verzia buildu (`yyyymmddhhmm`) je v
`GET /api/health` (pole `build`) aj v pätičke sidebaru. Viac v [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Štruktúra repozitára

```
FleetCare/
├── docker-compose.yml         # topológia infraštruktúry
├── .env.example               # vzor konfigurácie
├── backend/                   # FastAPI aplikácia, Celery workers, Alembic migrácie
├── frontend/                  # React + TypeScript (Vite) PWA
├── docs/                      # technické zadanie, DB schéma, API kontrakt, design systém, SDLC
└── .github/workflows/         # CI (lint + testy + build)
```

## Dokumentácia

- [`docs/TECHNICAL_SPECIFICATION.md`](docs/TECHNICAL_SPECIFICATION.md) — technické zadanie
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) — dátový model
- [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) — REST API kontrakt
- [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md) — farby, komponenty, UI
- [`docs/SDLC_PLAN.md`](docs/SDLC_PLAN.md) — plán podľa SDLC + rozdelenie práce
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — nasadenie (Docker / GHCR)

## Licencia

Pozri [`LICENSE`](LICENSE).
