# FleetCare — REST API kontrakt

**Base prefix:** `/api` · **Formát:** JSON · **Auth:** `Authorization: Bearer <access>`
(okrem `/auth/login`, `/auth/refresh`, `/health`). **Časy:** ISO 8601 (UTC).
**Chyby:** `{ "detail": "..." }` so štandardnými HTTP kódmi (400/401/403/404/409/422).
**Stránkovanie** (kde relevantné): `?limit=&offset=`.

> Tento kontrakt je záväzný pre backend (implementácia) aj frontend (typy + api klient).
> Camel vs snake: **API používa `snake_case`** v JSON kľúčoch (zhoda s DB/Pydantic).

---

## Health
- `GET /api/health` → `200 {"status":"ok","db":"ok","redis":"ok","version":"0.2.0","build":"<yyyymmddhhmm|dev>"}`

## Auth
- `POST /api/auth/login` — body `{ "username": str, "password": str }`
  → `200 { "access_token": str, "token_type": "bearer", "user": User }`
  + nastaví `refresh_token` httpOnly+Secure cookie (30 d). 401 pri zlých údajoch.
- `POST /api/auth/refresh` — z cookie → `200 { "access_token": str }`. 401 ak neplatný.
- `POST /api/auth/logout` — zruší refresh cookie → `204`.
- `GET /api/auth/me` → `200 User`.

**User objekt:** `{ id, username, email, full_name, is_admin, is_active, locale, cars:[{id,name}] }`

## Users (len admin)
- `GET /api/users` → `200 [User]`
- `POST /api/users` — `{ username, email, full_name, password, is_admin, locale, car_ids:[int] }` → `201 User`
- `GET /api/users/{id}` → `200 User`
- `PATCH /api/users/{id}` — čiastočná úprava (vrátane `is_active`, `car_ids`, `password`) → `200 User`
- `DELETE /api/users/{id}` → `204` (alebo deaktivácia podľa `is_active`)

## Cars
- `GET /api/cars` → `200 [CarListItem]` (user vidí len pridelené; admin všetky)
- `POST /api/cars` — `{ name?, make, model, year, license_plate, vin, current_odometer_km }`
  → `201 Car` (+ auto-vytvorené default notif. pravidlá). `name` je **voliteľné** – ak chýba,
  odvodí sa z `"{make} {model}"` (fallback na `license_plate`).
- `GET /api/cars/{id}` → `200 CarDetail`
- `PATCH /api/cars/{id}` → `200 Car`
- `DELETE /api/cars/{id}` → `204` — **len admin** (non-admin dostane `403`; archivuje/odpája).

**Car:** `{ id, name, full_name, make, model, year, license_plate, vin, current_odometer_km }`
**CarListItem** = Car + per-dokument stav + overdue (zoznam áut zobrazí STK/PZP/KASKO zvlášť):
```
{ ...Car,
  stk:   { valid_until, days_left } | null,   // aktuálny (najneskorší valid_until) STK
  pzp:   { valid_until, days_left } | null,
  kasko: { valid_until, days_left } | null,
  overdue: bool }
```
**CarDetail** = Car + aggregované polia (parita s dashboard kartou):
```
{ ...Car,
  stk:   STK|null,            // jediný AKTUÁLNY záznam (najneskorší valid_until) alebo null
  pzp:   Insurance|null,      // dtto
  kasko: Insurance|null,      // dtto
  vignettes: [Vignette],      // všetky platné/aktuálne vinetky
  active_tire_set: { id, name, season, avg_tread_mm, projection_date } | null,
  next_service: { name, label, km_left, days_left } | null,
  overdue: bool,              // true ak je hocijaká sledovaná položka po termíne
  monthly_cost: number }
```
Plná história dokumentov je cez `/api/cars/{id}/stk|insurance|vignettes`.

## Odometer
- `GET /api/cars/{id}/odometer` → `200 [{ id, reading_km, recorded_at, note }]`
- `POST /api/cars/{id}/odometer` — `{ reading_km, recorded_at?, note? }` → `201` (aktualizuje `current_odometer_km`)

## Dokumenty
### STK (technical_inspections)
- `GET /api/cars/{id}/stk` → `200 [STK]`  `STK = { id, inspected_at, valid_until, cost, provider, note, days_left }`
- `POST /api/cars/{id}/stk` → `201 STK` · `PATCH /api/stk/{stk_id}` · `DELETE /api/stk/{stk_id}`

### Poistenie (insurance_policies)
- `GET /api/cars/{id}/insurance` → `200 [Insurance]`
  `Insurance = { id, type:'PZP'|'KASKO', provider, policy_number, valid_from, valid_until, cost, days_left }`
- `POST /api/cars/{id}/insurance` → `201` · `PATCH /api/insurance/{id}` · `DELETE /api/insurance/{id}`

### Vinetky (vignettes)
- `GET /api/cars/{id}/vignettes` → `200 [Vignette]`
  `Vignette = { id, country, valid_from, valid_until, cost, provider, days_left }`
- `POST /api/cars/{id}/vignettes` → `201` · `PATCH /api/vignettes/{id}` · `DELETE /api/vignettes/{id}`

> Spoločný pohľad: `GET /api/cars/{id}/documents` → `{ stk:[], insurance:[], vignettes:[] }`
> s farebným `status` (green/yellow/red/gray) na základe `days_left`.

## Pneumatiky
- `GET /api/cars/{id}/tires` → `200 [TireSet]`
  `TireSet = { id, name, season, is_active, mounted_at, mounted_odometer_km, expected_change_date,
              avg_tread_mm, mileage_km, avg_pressure_bar, projection_date, measurements:[Measurement] }`
- `POST /api/cars/{id}/tires` — vytvor sadu (+ voliteľné prvé meranie); nová sa stane aktívnou
  `{ name, season, mounted_at, mounted_odometer_km, expected_change_date,
     initial_measurement?: Measurement }` → `201 TireSet`
- `PATCH /api/tires/{set_id}` (archivácia = `is_active:false` smie vlastník) ·
  `DELETE /api/tires/{set_id}` — **len admin** (non-admin `403`)
- `POST /api/tires/{set_id}/measurements` — `Measurement` → `201`
  `Measurement = { id?, measured_at, odometer_km,
    tread_fl_mm, tread_fr_mm, tread_rl_mm, tread_rr_mm,
    pressure_fl_before_bar?, pressure_fr_before_bar?, pressure_rl_before_bar?, pressure_rr_before_bar?,
    pressure_fl_after_bar?, pressure_fr_after_bar?, pressure_rl_after_bar?, pressure_rr_after_bar? }`
  > Číselné polia (`tread_*`, `pressure_*`, `avg_tread_mm`) sa serializujú ako JSON **number** (nie string).
- `PATCH /api/tires/measurements/{measurement_id}` — čiastočná úprava (všetky polia voliteľné) → `200 Measurement`
- `DELETE /api/tires/measurements/{measurement_id}` → `204`
  (vlastníctvo cez meranie→sada→auto; non-admin len vlastné autá, inak `403`)
- `GET /api/tires/{set_id}/trend` → `200`
  `{ points: [{ km, actual }], projection: [{ km, projected }], reference_mm: 1.6,
     projection_date: date|null, km_at_reference: number|null }`
  (lineárna regresia; `projection` prázdne ak < 2 merania / nezostupný trend.
  Keď chýba denný nájazd, dátum sa odhadne z meraní sady; ak sa nedá, `projection_date=null`,
  ale `km_at_reference` (km pri 1,6 mm) je vyplnené → FE ukáže „≈ pri X km".)

## Servis
### Záznamy
- `GET /api/cars/{id}/services` → `200 [ServiceRecord]`
- `POST /api/cars/{id}/services` → `201` · `PATCH /api/services/{id}` · `DELETE /api/services/{id}`
  `ServiceRecord = { id, performed_at, odometer_km, category:'service'|'repair'|'tires'|'other',
    description, cost, shop?, warranty_until?, performed_items?:[str], additional_work?:[str],
    oil_name?, next_oil_change_km?, defect_found?, defect_description?, tire_action?, season?, create_reminder?,
    next_service_date?, next_service_km?, next_service_by_indicator?,
    next_additional_desc?, next_additional_date?, next_additional_km? }`
  > „Vaše ďalšie termíny servisu": ak `create_reminder=true` a je zadaný `next_service_date`/`next_service_km`,
  > backend **idempotentne upsertne `ServiceInterval`** (názov = `description`/kategória) – objaví sa v paneli
  > intervalov a spúšťa smart notifikáciu. `cost` sa serializuje ako JSON **number**.
### Intervaly
- `GET /api/cars/{id}/service-intervals` → `200 [ServiceInterval]`
  `ServiceInterval = { id, name, interval_km, interval_months, last_performed_km, last_performed_at,
    next_due_km, next_due_date, km_left, days_left, is_active }`
- `POST /api/cars/{id}/service-intervals` → `201` · `PATCH /api/service-intervals/{id}` · `DELETE …`

## Palivo
- `GET /api/cars/{id}/fuel` (`?from_date=&to_date=`) → `200 [FuelRecord]`
  `FuelRecord = { id, refueled_at, odometer_km, liters, price_per_liter, total_cost, full_tank, consumption_l_100km }`
  > Číselné polia sa serializujú ako JSON **number**. `consumption` sa počíta z celej histórie,
  > date-range filtruje len vrátené riadky.
- `POST /api/cars/{id}/fuel` → `201` · `PATCH /api/fuel/{id}` · `DELETE /api/fuel/{id}`
- `GET /api/cars/{id}/fuel/stats` (`?from_date=&to_date=&group_by=month|year`) →
  `{ avg_consumption, total_spent, count, monthly:[{ month, consumption }] }`
  (`group_by=year` → `month` kľúč nesie `YYYY`)

## Náklady
- `GET /api/cars/{id}/expenses` (`?from_date=&to_date=`) → `200 [Expense]`
  `Expense = { id, occurred_at, description, amount, category }` (`amount` = JSON number)
- `POST /api/cars/{id}/expenses` → `201` · `PATCH /api/expenses/{id}` · `DELETE /api/expenses/{id}`
- `GET /api/cars/{id}/expenses/breakdown` (`?from_date=&to_date=`) → `{ total, breakdown:[{ category, amount }] }`
  > Breakdown **agreguje** manuálne `expenses` + `fuel_records.total_cost` (bucket `fuel`) +
  > `service_records.cost` (bucket `service`) – používa existujúce anglické kľúče kategórií
  > (`fuel|service|documents|tires|other`). Nulové buckety sa vynechávajú. Dashboard `monthly_cost`
  > (kĺzavých 30 dní) rovnako sčítava expenses + palivo + servis.

## Dashboard
- `GET /api/dashboard` → `200`
  ```json
  {
    "stats": { "cars": 6, "notifications_today": 7, "overdue_items": 1, "monthly_cost": 747 },
    "cars": [
      { "id":1, "name":"Škoda Octavia", "license_plate":"BA123AB", "current_odometer_km":127540,
        "chips":[{ "label":"STK", "days_left":12 }, { "label":"PZP", "days_left":187 },
                 { "label":"SK", "days_left":4 }],
        "next_service":"Olej za 800 km", "tires":"Zima · 4.2 mm", "overdue":false }
    ]
  }
  ```
  `chips` zoradené; FE farbí podľa `days_left`. Zoradenie áut podľa urgentnosti (overdue prvé).

## Notifikácie
### Pravidlá
- `GET /api/notification-rules` (`?car_id=`) → `200 [Rule]` (non-admin len pravidlá svojich áut)
  `Rule = { id, car_id, car_name, item_type, lead_days_1, lead_days_2, lead_days_3, is_active,
    is_smart, channel_email, channel_matrix, status }`
- `POST /api/notification-rules` → `201` · `PATCH /api/notification-rules/{id}` · `DELETE …`
  > Create/Update/Delete smie **vlastník auta** pravidla (overené cez `user_owns_car`); admin čokoľvek.
  > Pri cudzom aute → `403`.
### Log
- `GET /api/notification-log` (`?limit=&status=`) → `200 [LogEntry]`
  `LogEntry = { id, sent_at, car_name, item_type, channel, recipient, status, subject }`
  > Non-admin vidí len log pre **svoje** autá; admin vidí všetko.
- `GET /api/notification-log/export.csv` (admin) → CSV
### Test / spustenie
- `POST /api/notifications/test` (admin) — `{ channel:'email'|'matrix', car_id?, to? }` → `200 { status }`
- `POST /api/notifications/run` (admin) — manuálne spustenie denného behu → `202`

## Nastavenia (app_settings)
- `GET /api/settings` → `200` (tajomstvá maskované)
  `{ fleet_name, timezone, default_locale, currency, default_lead_days:{1,2,3}, daily_send_time,
     tire_min_tread_mm, smtp:{ host, port, encryption, username, from, password_set:bool },
     matrix:{ enabled, homeserver, default_room, token_set:bool } }`
- `PUT /api/settings` — čiastočná/úplná aktualizácia → `200`
- `POST /api/settings/smtp/test` → `200 { status }`
- `POST /api/settings/matrix/test` → `200 { status }`
- `GET /api/settings/export` → JSON backup · `POST /api/settings/wipe` (admin, potvrdenie) → `204`

---

## Autorizačné pravidlá
- Endpointy nad `/api/users`, `/api/settings`, `/api/notifications/{test,run}` a
  `/api/notification-log/export.csv` vyžadujú **admin**.
- `DELETE /api/cars/{id}` a `DELETE /api/tires/{set_id}` sú **admin-only**.
- `/api/notification-rules` (write) a `/api/notification-log` (read) sú prístupné **vlastníkovi auta**
  (cez `user_car_groups`); admin vidí/spravuje všetko.
- Pri `/api/cars/{id}/*` sa overuje, že non-admin používateľ má dané auto v `user_car_groups`.
- 403 pri pokuse o prístup k cudziemu autu; 401 bez/po expirovanom tokene (→ refresh flow).

## Konvencie odpovedí
- Vytvorenie → `201` + telo objektu. Update → `200` + objekt. Delete → `204`.
- Validácia (Pydantic) → `422` s detailom polí.
- `days_left` = `(valid_until − today)` v dňoch (môže byť záporné = overdue).
