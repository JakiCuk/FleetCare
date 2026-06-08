# FleetCare — Databázová schéma (kontrakt)

**DB:** PostgreSQL 16 · **ORM:** SQLAlchemy 2.0 (async) · **Migrácie:** Alembic
**Konvencie:** názvy tabuliek `snake_case` v množnom čísle; PK `id BIGSERIAL`; časové údaje
`TIMESTAMPTZ` v UTC; peniaze `NUMERIC(10,2)`; meranie `NUMERIC`. Každá tabuľka má
`created_at TIMESTAMPTZ DEFAULT now()` a (kde dáva zmysel) `updated_at`.
FK `ON DELETE CASCADE` pre závislé záznamy auta.

> Tento súbor je záväzný. Názvy stĺpcov sa nesmú meniť bez aktualizácie tohto dokumentu,
> migrácií aj API kontraktu.

---

## users
| stĺpec | typ | poznámka |
|---|---|---|
| id | BIGSERIAL PK | |
| username | VARCHAR(64) UNIQUE NOT NULL | |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| full_name | VARCHAR(128) | |
| hashed_password | VARCHAR(255) NOT NULL | argon2/bcrypt |
| is_admin | BOOLEAN NOT NULL DEFAULT false | |
| is_active | BOOLEAN NOT NULL DEFAULT true | |
| locale | VARCHAR(5) NOT NULL DEFAULT 'sk' | 'sk' \| 'en' |
| created_at, updated_at | TIMESTAMPTZ | |

## cars
| stĺpec | typ | poznámka |
|---|---|---|
| id | BIGSERIAL PK | |
| name | VARCHAR(128) NOT NULL | krátky názov (napr. „Škoda Octavia") |
| make | VARCHAR(64) | značka |
| model | VARCHAR(64) | model |
| year | INTEGER | rok výroby |
| license_plate | VARCHAR(16) NOT NULL | ŠPZ/EČV |
| vin | VARCHAR(32) | 17 znakov |
| current_odometer_km | INTEGER NOT NULL DEFAULT 0 | denormalizovaný posledný stav |
| created_at, updated_at | TIMESTAMPTZ | |

`full_name` (napr. „Škoda Octavia 2.0 TDI") sa skladá na API/FE z `make model`/`name`;
voliteľne stĺpec `trim VARCHAR(64)`.

## user_car_groups
| stĺpec | typ | poznámka |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT FK→users.id ON DELETE CASCADE | |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE | |
| notification_enabled | BOOLEAN NOT NULL DEFAULT true | |
| **UNIQUE(user_id, car_id)** | | |

## odometer_readings
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| reading_km | INTEGER NOT NULL |
| recorded_at | TIMESTAMPTZ NOT NULL DEFAULT now() |
| note | VARCHAR(255) |

Index `(car_id, recorded_at)`. Po vložení sa aktualizuje `cars.current_odometer_km` na max.

## tire_sets
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| name | VARCHAR(128) NOT NULL | značka+model (napr. „Nokian Hakkapeliitta R3") |
| season | VARCHAR(16) NOT NULL | 'winter' \| 'summer' \| 'all_season' |
| is_active | BOOLEAN NOT NULL DEFAULT true |
| mounted_at | DATE |
| mounted_odometer_km | INTEGER |
| expected_change_date | DATE | plánovaná výmena |
| created_at | TIMESTAMPTZ |

Pri aktivácii novej sady sa ostatné sady auta nastavia `is_active=false` (max 1 aktívna/auto).

## tire_measurements
Dezén na 4 kolesách + tlak **pred a po hustení** pre každé koleso.
| id | BIGSERIAL PK |
| tire_set_id | BIGINT FK→tire_sets.id ON DELETE CASCADE |
| measured_at | DATE NOT NULL |
| odometer_km | INTEGER NOT NULL |
| tread_fl_mm, tread_fr_mm, tread_rl_mm, tread_rr_mm | NUMERIC(4,2) | hĺbka dezénu |
| pressure_fl_before_bar, pressure_fr_before_bar, pressure_rl_before_bar, pressure_rr_before_bar | NUMERIC(4,2) NULL | tlak pred hustením (voliteľné) |
| pressure_fl_after_bar, pressure_fr_after_bar, pressure_rl_after_bar, pressure_rr_after_bar | NUMERIC(4,2) NULL | tlak po hustení |
| created_at | TIMESTAMPTZ |

Index `(tire_set_id, measured_at)`. `avg_tread = (fl+fr+rl+rr)/4` sa počíta na API.

## vignettes
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| country | VARCHAR(4) NOT NULL | 'SK' \| 'AT' \| 'CZ' \| 'HU' \| … |
| valid_from | DATE |
| valid_until | DATE NOT NULL |
| cost | NUMERIC(10,2) |
| provider | VARCHAR(128) |
| created_at | TIMESTAMPTZ |

## technical_inspections  (STK)
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| inspected_at | DATE |
| valid_until | DATE NOT NULL |
| cost | NUMERIC(10,2) |
| provider | VARCHAR(128) |
| note | VARCHAR(255) |
| created_at | TIMESTAMPTZ |

## insurance_policies
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| type | VARCHAR(8) NOT NULL | 'PZP' \| 'KASKO' |
| provider | VARCHAR(128) |
| policy_number | VARCHAR(64) |
| valid_from | DATE |
| valid_until | DATE NOT NULL |
| cost | NUMERIC(10,2) |
| created_at | TIMESTAMPTZ |

## service_records
Záznam servisu/opravy + detail podľa **servisnej knižky** (kategória „Servis").
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| performed_at | DATE NOT NULL |
| odometer_km | INTEGER |
| category | VARCHAR(16) NOT NULL | 'service' \| 'repair' \| 'tires' \| 'other' |
| description | TEXT |
| cost | NUMERIC(10,2) |
| shop | VARCHAR(128) | dielňa/servis |
| warranty_until | DATE | (oprava) |
| performed_items | JSONB | checklist „Vykonané" (zoznam stringov/bool) |
| additional_work | JSONB | checklist „Dodatočné práce – výmena" (+ vlastné položky) |
| oil_name | VARCHAR(128) | druh oleja |
| next_oil_change_km | INTEGER | |
| defect_found | BOOLEAN DEFAULT false | kontrola karosérie |
| defect_description | TEXT | |
| tire_action | VARCHAR(32) | (pneumatiky) prezutie/vyváženie/geometria/oprava |
| season | VARCHAR(16) | (pneumatiky) |
| create_reminder | BOOLEAN DEFAULT false | vytvoriť pripomienku na ďalší termín |
| created_at | TIMESTAMPTZ |

> Voliteľné polia podľa kategórie. JSONB pre flexibilný checklist (presná štruktúra v API kontrakte).

## service_intervals
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| name | VARCHAR(128) NOT NULL | napr. „Výmena oleja" |
| interval_km | INTEGER | |
| interval_months | INTEGER | |
| last_performed_km | INTEGER | |
| last_performed_at | DATE | |
| is_active | BOOLEAN NOT NULL DEFAULT true |
| created_at | TIMESTAMPTZ |

`next_due_km`, `next_due_date`, `km_left`, `days_left` sa počítajú na API (nie sú stĺpce).

## fuel_records
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| refueled_at | DATE NOT NULL |
| odometer_km | INTEGER NOT NULL |
| liters | NUMERIC(6,2) NOT NULL |
| price_per_liter | NUMERIC(6,3) |
| total_cost | NUMERIC(10,2) | (alebo dopočítané liters·price) |
| full_tank | BOOLEAN NOT NULL DEFAULT true |
| created_at | TIMESTAMPTZ |

`consumption_l_100km` sa počíta na API z po sebe idúcich `full_tank=true`.

## expenses
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| occurred_at | DATE NOT NULL |
| description | VARCHAR(255) |
| amount | NUMERIC(10,2) NOT NULL |
| category | VARCHAR(32) NOT NULL | 'fuel' \| 'service' \| 'documents' \| 'tires' \| 'other' |
| created_at | TIMESTAMPTZ |

## notification_rules
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| item_type | VARCHAR(32) NOT NULL | 'stk' \| 'pzp' \| 'kasko' \| 'vignette' \| 'tires' \| 'service' (príp. s krajinou: 'vignette:AT') |
| lead_days_1 | INTEGER DEFAULT 30 | NULL pri „smart" |
| lead_days_2 | INTEGER DEFAULT 14 | |
| lead_days_3 | INTEGER DEFAULT 7 | |
| is_active | BOOLEAN NOT NULL DEFAULT true |
| is_smart | BOOLEAN NOT NULL DEFAULT false | pneumatiky/servis (dynamické) |
| channel_email | BOOLEAN NOT NULL DEFAULT true |
| channel_matrix | BOOLEAN NOT NULL DEFAULT false |
| created_at, updated_at | TIMESTAMPTZ |

Status na FE (`active`/`overdue`/`smart`/`paused`) je odvodený: `paused` = `is_active=false`,
`smart` = `is_smart=true`, `overdue` = existuje prekročená položka, inak `active`.

## notification_log
| id | BIGSERIAL PK |
| car_id | BIGINT FK→cars.id ON DELETE CASCADE |
| rule_id | BIGINT FK→notification_rules.id ON DELETE SET NULL |
| item_type | VARCHAR(32) |
| lead_bucket | INTEGER | ktorý lead (1/2/3) alebo 0 pre smart/overdue |
| channel | VARCHAR(16) NOT NULL | 'email' \| 'matrix' |
| recipient | VARCHAR(255) |
| subject | VARCHAR(255) |
| status | VARCHAR(16) NOT NULL | 'sent' \| 'failed' \| 'skipped' |
| error | TEXT |
| sent_at | TIMESTAMPTZ NOT NULL DEFAULT now() |

Index `(car_id, rule_id, item_type, lead_bucket, channel, sent_at)` pre dedup dotaz (23 h).

## app_settings
Key/value konfigurácia (jeden riadok per kľúč) alebo jeden JSONB riadok. Odporúčané kľúče:
`smtp_host`, `smtp_port`, `smtp_encryption`, `smtp_username`, `smtp_password`,
`smtp_from`, `matrix_enabled`, `matrix_homeserver`, `matrix_token`, `matrix_default_room`,
`fleet_name`, `timezone`, `default_locale`, `currency`,
`default_lead_days_1/2/3`, `daily_send_time`, `tire_min_tread_mm`.
| key | VARCHAR(64) PK | | value | TEXT/JSONB | | updated_at | TIMESTAMPTZ |

> Tajomstvá (heslá/tokeny) sa nikdy nevracajú v plaintexte cez API (maskované).

---

## Seed / demo dáta
`backend/app/seed.py` vytvorí:
- **admin** (`username=admin`, heslo z `.env` `ADMIN_PASSWORD`, `is_admin=true`),
- (voliteľne) demo autá a záznamy zodpovedajúce mockupu (za flagom `SEED_DEMO=true`),
- default `app_settings` (lead days 30/14/7, daily_send_time 08:00, tire_min_tread_mm 2.5).

## Default notifikačné pravidlá pri vytvorení auta
Pri `POST /api/cars` sa automaticky vytvoria pravidlá pre `stk`, `pzp`/`kasko` (podľa
zadaného poistenia), `vignette` (per krajina) s lead days 30/14/7, `channel_email=true`.
