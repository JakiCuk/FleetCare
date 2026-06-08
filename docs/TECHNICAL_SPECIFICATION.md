# FleetCare — Technické zadanie (Technical Specification)

**Verzia:** 0.1 · **Stav:** funkčná (aktívne sa vyvíja) · **Dátum:** 2026-06-08

Tento dokument je záväzný kontrakt pre implementáciu. Vychádza z pôvodného zadania
(`zadanie pre car app`) a z grafického návrhu vytvoreného v Claude Design (kompletný
interaktívny mockup FleetCare). Všetci implementátori (subagenti aj ľudia) sa ním riadia.

---

## 1. Účel a rozsah

FleetCare je samohostovaná webová aplikácia (PWA) na správu **domácej automobilovej
flotily** (jednotky až nízke desiatky áut). Poskytuje:

- evidenciu áut a ich dokumentov (STK, poistenie PZP/KASKO, diaľničné známky),
- evidenciu pneumatík vrátane merania dezénu a tlaku, s **predikciou zjazdenia**,
- evidenciu servisov/opráv a servisných intervalov (km + čas),
- evidenciu tankovaní s výpočtom spotreby a evidenciu nákladov,
- **automatické notifikácie** (e-mail + Matrix) priradeným používateľom,
- dashboard, grafy a trendy.

**Mimo rozsahu (zatiaľ):** mobilná natívna appka, multi-tenant SaaS, fakturácia, GPS
tracking, OBD integrácia.

## 2. Roly používateľov

| Rola | Oprávnenia |
|---|---|
| **Admin** | plný CRUD nad autami, používateľmi, notifikačnými pravidlami, nastaveniami (SMTP/Matrix), test notifikácií, priraďovanie áut používateľom. |
| **Používateľ (user)** | prístup len k **prideleným autám**; CRUD nad záznamami (odometer, dokumenty, pneumatiky, servis, palivo, náklady) svojich áut; nemení systémové nastavenia. |

Priradenie auto↔používateľ je cez `user_car_groups` (vrátane `notification_enabled`).

## 3. Nefunkčné požiadavky

- **Jazyky:** UI bilingválne **SK (default) + EN** (react-i18next). Notifikačné šablóny
  taktiež SK + EN (podľa jazyka príjemcu/nastavenia flotily).
- **Bezpečnosť:** JWT (access 15 min + refresh httpOnly cookie 30 dní), hashovanie hesiel
  (argon2/bcrypt), rate limiting (slowapi) na auth endpointoch, CORS uzamknutý na FE pôvod,
  bezpečnostné hlavičky na nginx, žiadne tajomstvá v gite (`.env`).
- **Async:** backend plne async (FastAPI + SQLAlchemy async + asyncpg).
- **Časové pásmo:** konfigurovateľné (default `Europe/Bratislava`); dátumy v DB v UTC.
- **Mena:** default EUR; zobrazenie konfigurovateľné.
- **Observabilita:** štruktúrované logy (structlog), healthcheck endpointy.
- **Idempotencia notifikácií:** deduplikácia (žiadne dvojité odoslanie v rámci 23 h).
- **Žiadne lokálne testovanie na PC** počas vývoja — kód sa píše do GitHubu; CI beží na
  GitHube; nasadenie robí používateľ ručne.

## 4. Technologický stack

Pozri README. Záväzné verzie/knižnice:

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async, `asyncpg`), Pydantic v2,
  Alembic, Celery 5 + Redis, `passlib[argon2]`/`bcrypt`, `python-jose`/`pyjwt`, `slowapi`,
  `structlog`, `jinja2`, `aiosmtplib`, `matrix-nio`, `numpy` (regresia). Server: `uvicorn`.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Zustand, axios,
  `react-router-dom`, `react-i18next`/`i18next`, `vite-plugin-pwa` (+ Workbox).
- **Infra:** Docker Compose; služby `db`, `redis`, `backend`, `worker`, `beat`,
  `frontend` (nginx). Healthchecky pre `db` a `redis`; `backend` čaká na ich zdravie.

## 5. Doménový model (prehľad)

Detailná schéma v [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md). Kľúčové entity:

`users`, `cars`, `user_car_groups`, `odometer_readings`, `tire_sets`, `tire_measurements`
(per-koleso dezén + tlak pred/po hustení), `vignettes`, `technical_inspections` (STK),
`insurance_policies` (PZP/KASKO), `service_records` (+ detail servisnej knižky),
`service_intervals`, `fuel_records`, `expenses`, `notification_rules`, `notification_log`,
`app_settings`.

## 6. API (prehľad)

Detailný kontrakt v [`API_CONTRACT.md`](API_CONTRACT.md). Prefix **`/api`**. Skupiny:
`auth`, `users`, `cars`, `odometer`, `documents` (stk/insurance/vignettes), `tires`,
`services` (records + intervals), `fuel`, `expenses`, `dashboard`, `notifications`
(rules + log + settings + test-send), `settings`, `health`.

## 7. Kľúčové algoritmy

### 7.1 Predikcia zjazdenia pneumatík
Vstup: merania aktívnej sady (≥ 2, pre notifikáciu ≥ 3). Pre každé meranie `x = odometer_km`,
`y = avg_tread_mm = (fl+fr+rl+rr)/4`.
1. **Lineárna regresia** (least squares, `numpy.polyfit` stupeň 1) → `tread = a·km + b`.
2. **Extrapolácia** na `y = 1.6` → `km_at_1.6 = (1.6 − b) / a` (ak `a < 0`).
3. **Konverzia na dátum:** priemerné denné km z `odometer_readings`
   (`avg_km_per_day`) → `date = today + (km_at_1.6 − current_odometer) / avg_km_per_day`.
4. Trend pre graf: skutočné body + projekčné body (prerušovaná čiara) po prienik s 1,6 mm.
5. **Notifikácia (smart):** ak `projected_date < expected_change_date` (alebo priemerný
   dezén < konfigurovateľný prah, default 2,5 mm) → upozorni.

### 7.2 Spotreba paliva (l/100 km)
Len z **po sebe idúcich** záznamov s `full_tank = true`:
`l/100km = liters_N / (km_N − km_{N−1}) · 100`. Čiastočné tankovania sa do priemeru
nezarátavajú samostatne (pripočítavajú sa k nasledujúcemu plnému).

### 7.3 Servisné intervaly — „splatné za"
Pre každý interval: `next_due_km = last_performed_km + interval_km`,
`next_due_date = last_performed_at + interval_months`. „Splatné" = čo nastane skôr
(km **alebo** čas). Naliehavosť: `km_left < 500` alebo `days_left ≤ 14` → červená;
`< 2000 km` alebo `≤ 30 d` → žltá; inak zelená.

### 7.4 Farebné kódovanie termínov (chips)
`days < 0` alebo `≤ 7` → červená; `≤ 30` → žltá; inak zelená; `null` → sivá.
(V detaile auta sa pre STK/poistenie používa červená už `≤ 14` dní.)

### 7.5 JWT refresh
Access token 15 min (Bearer). Refresh token v httpOnly + Secure cookie (30 dní).
Axios interceptor pri 401 zavolá `POST /api/auth/refresh` a zopakuje pôvodný request.

### 7.6 Deduplikácia notifikácií
Pred odoslaním sa skontroluje `notification_log` pre `(car_id, rule_id, item_type,
lead_bucket, channel)` za posledných 23 h. Ak existuje úspešné odoslanie, preskočí sa.

## 8. Notifikácie

- **Spúšťače (Celery beat, denne o konfigurovateľnom čase, default 08:00):**
  - `check_document_expiries` — STK, poistenia, vinetky vs. lead days.
  - `check_service_intervals` — splatné servisy (km/čas).
  - `check_tire_projections` — predikcia zjazdenia aktívnych sád (≥ 3 merania).
- **Kanály:** e-mail (SMTP, Jinja2 HTML šablóny per typ a jazyk) a Matrix (matrix-nio;
  globálna miestnosť + voliteľná per-auto miestnosť).
- **Konfigurácia:** uložená v `app_settings` (SMTP host/port/credentials/from,
  Matrix homeserver/token/room), editovateľná v Admin paneli; tajomstvá majú default z `.env`.
- **Test send:** admin endpoint na okamžité testovacie odoslanie.

## 9. Frontend — stránky (podľa návrhu)

Detail v [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md). Layout: ľavý tmavý sidebar (168 px,
`#1a2332`) s logom „🚗 FleetCare" a navigáciou **Dashboard · Autá · Notifikácie · Admin ·
Nastavenia**, používateľský pätič. Hlavná plocha max-width 1200, padding 28/32, pozadie
`#f8fafc`, font Inter.

1. **Dashboard** — 4 stat karty + 3-stĺpcová mriežka kariet áut (chips, nasledujúci servis,
   pneumatiky, OVERDUE badge, červený rám pri overdue). Tlačidlo „+ Pridať auto" (modal).
2. **Autá** — vyhľadávanie + tabuľka (Auto, ŠPZ, VIN, Rok, Odometer, STK, Poistenie, Stav).
3. **Detail auta** — breadcrumb, hlavička (fullName, ŠPZ, VIN, rok, km), Upraviť/Zmazať,
   záložky **Prehľad · Dokumenty · Pneumatiky · Servis · Palivo · Náklady** (viď §9 návrhu).
4. **Notifikácie** — stat karty, overdue alert, filter (Všetky/Odoslané/Neúspešné), log tabuľka.
5. **Admin** — záložky **Pravidlá · Log · SMTP · Matrix · Používatelia**.
6. **Nastavenia** — Všeobecné (názov, TZ, jazyk, mena), Notifikácie (lead days, čas, prah mm),
   PWA, Nebezpečná zóna (export/zmazať všetko).
7. **Login** — prihlasovacia stránka (mimo mockupu, ale nutná pre JWT).

Mobilná verzia: responzívny layout + spodná navigácia (PWA, „Add to home screen").

## 10. Akceptačné kritériá (verifikácia)

1. `docker compose up` → všetky healthchecky zelené; `GET /api/health` → 200.
2. Login → JWT v cookie, chránené routy fungujú; refresh interceptor obnoví access token.
3. Pridanie auta → objaví sa v dashboarde aj v zozname áut; automaticky vzniknú default
   notifikačné pravidlá (30/14/7).
4. STK s dátumom +10 dní → karta červená; „Test send" odošle e-mail (a Matrix, ak zapnutý).
5. ≥ 3 merania dezénu klesajúcim trendom → graf zobrazí projekciu (prerušovaná čiara pretne
   hranicu 1,6 mm); pri blízkej projekcii vznikne smart notifikácia.
6. 2+ po sebe idúce plné nádrže → korektný výpočet l/100 km.
7. `docker compose logs beat` → denné úlohy bežia bez chýb; deduplikácia funguje.
8. UI prepínateľné SK/EN; appku možno nainštalovať ako PWA na mobil.
9. Backend lint + testy a frontend lint + build prechádzajú v CI (GitHub Actions).

## 11. Implementačné slices (1–12)

Postavia sa **všetky** (rozsah „everything"). Slices definujú poradie a obsah:

1. **Scaffold & infra** — docker-compose, FastAPI app, async DB, Alembic init, FE scaffold, `GET /api/health`.
2. **Auth & Users** — JWT login/refresh/me, users CRUD (admin), FE login + authStore + interceptor + PrivateRoute.
3. **Cars CRUD & Dashboard shell** — cars + user_car_groups, dashboard skeleton, car detail shell, AppShell.
4. **Dokumenty** — STK/insurance/vignettes CRUD, auto-vytvorenie notif. pravidiel, StatusChip/CountdownChip, chips na karte.
5. **Odometer & Servis** — odometer readings, service records + intervals, Overview odometer + graf, Servis záložka (vrátane detailu servisnej knižky).
6. **Pneumatiky** — tire_sets + measurements (per-koleso dezén + tlak pred/po), projection_service, trend graf + projekcia, modály.
7. **Palivo & Náklady** — fuel_records + expenses, fuel_service (l/100km), grafy (bar + koláč).
8. **Dashboard agregácia** — `GET /api/dashboard` (dni do termínov, ďalší servis, odometer, aktívna sada, overdue flags), zoradenie podľa urgentnosti.
9. **Notifikačný engine (e-mail)** — beat `check_document_expiries`, email_service (Jinja2), Admin SMTP + Pravidlá + Log + Test send.
10. **Smart notifikácie** — `check_tire_projections`, `check_service_intervals`, FE interval formuláre a „splatné za".
11. **PWA & Mobile** — manifest, service worker (offline shell + cache API), MobileNav, rýchly odometer z karty.
12. **Admin & Hardening** — Users priradenie áut, rate limiting, CORS, structlog, nginx gzip + security headers, Matrix integrácia, `.env` dokumentácia.

## 12. SDLC a rozdelenie práce

Pozri [`SDLC_PLAN.md`](SDLC_PLAN.md). Fázy: **Plánovanie → Analýza → Návrh → Vývoj →
Testovanie → Nasadenie**. Vývoj realizujú zameraní subagenti (SQL/DB, Backend/API,
Frontend, QA/testy); orchestrátor (Claude) píše kontrakty, integruje a verzuje do GitHubu.
Nasadenie robí používateľ ručne.

## 13. Kritické súbory

- `docker-compose.yml` — topológia infraštruktúry.
- `backend/app/models/` — ORM modely (základ migrácií).
- `backend/app/workers/tasks.py` — centrálna logika notifikácií.
- `backend/app/services/projection_service.py` — predikcia dezénu (najkomplexnejší algoritmus).
- `frontend/src/api/client.ts` — axios + JWT refresh interceptor (závisí od neho celý FE).
