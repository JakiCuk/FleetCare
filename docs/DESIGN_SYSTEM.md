# FleetCare — Design systém (kontrakt pre frontend)

Odvodené z grafického návrhu (Claude Design mockup). Cieľ: **vizuálne verne** zreprodukovať
mockup v React + TypeScript + Tailwind. Mockup používal inline štýly; my použijeme Tailwind
triedy + tématické tokeny. Grafy: **Recharts** (s vizuálom podľa mockupu).

---

## 1. Farby (tokeny)

| Token | HEX | Použitie |
|---|---|---|
| `bg` | `#f8fafc` | pozadie aplikácie |
| `surface` | `#ffffff` | karty, modály, tabuľky |
| `border` | `#e2e8f0` | rámiky kariet |
| `border-soft` | `#f1f5f9` | jemné oddeľovače/grid |
| `text` | `#0f172a` | primárny text |
| `text-muted` | `#64748b` | sekundárny text |
| `text-faint` | `#94a3b8` | terciárny/placeholder |
| `primary` | `#2563eb` | akcie, aktívny stav, linky |
| `primary-bg` | `#eff6ff` | aktívne pozadie (taby, chipy) |
| `sidebar` | `#1a2332` | tmavý sidebar |

**Stavové farby (chips/badge):**
| variant | text | bg |
|---|---|---|
| green | `#16a34a` | `#dcfce7` |
| yellow | `#d97706` | `#fef3c7` |
| red | `#dc2626` | `#fee2e2` |
| blue | `#2563eb` | `#dbeafe` |
| purple | `#7c3aed` | `#ede9fe` |
| orange | `#ea580c` | `#ffedd5` |
| gray | `#475569` | `#f1f5f9` |

**Pravidlo farby podľa dní (`days_left`):** `<0` alebo `≤7` → red; `≤30` → yellow; inak green;
`null` → gray. (V „Nadchádzajúce termíny" je red už `≤14`.)
**Dezén (mm):** `<3` red, `<5` orange/yellow, inak green.

## 2. Typografia
- Font: **Inter** (Google Fonts), fallback `-apple-system, sans-serif`, antialiased.
- Nadpisy stránok H1 24/700; sekcie 14–16/600; telo 13–14/400–500; popisky 11–12.
- Monospace pre ŠPZ/VIN/časy v logu.

## 3. Layout
- **Sidebar** fixný vľavo, šírka **168 px**, `#1a2332`. Hore logo „🚗 FleetCare"; nav položky
  s ikonou + textom (Dashboard ⊞, Autá 🚗, Notifikácie 🔔, Admin ⚙, Nastavenia ◎); aktívna
  položka `#2563eb` pozadie, biely text; dole používateľ (avatar s iniciálami + meno + rola).
- **Hlavná plocha**: `margin-left:168px`, padding `28px 32px`, `max-width:1200px`.
- **Mobil** (`<768px`): sidebar skrytý → **spodná navigácia** (bottom tabs), karty 1 stĺpec.

## 4. Komponenty (knižnica `components/common`)
Reprodukuj presne (názvy a vzhľad):
- **Btn** — varianty `primary` (modrá), `secondary` (biela+border), `danger` (svetločervená),
  `ghost`. Radius 6, padding 8/16, hover opacity 0.85.
- **Badge** — pill, radius 4, 12/600; varianty podľa §1.
- **StatusChip** — `{label, days}`; text `LABEL Xd`; farba podľa pravidla dní.
- **OverdueBadge** — plná červená „OVERDUE", 11/700, letter-spacing.
- **Card** — biela, border `#e2e8f0`, radius 10, padding 20.
- **StatCard** — `{label, value, color}`; hodnota 28/700.
- **Modal** — overlay `rgba(0,0,0,.4)`, biele okno radius 12, padding 28, max-šírka konfigurovateľná,
  X zatváracie tlačidlo, klik mimo zatvára.
- **FormField** + **Input** + **Select** + **textarea** — label 13/500, input border `#d1d5db`, radius 6.
- **PageHeader** — `{title, subtitle, actions, breadcrumb}`.
- **Tabs** — podčiarknutý aktívny tab (`#2563eb`, 2px border-bottom).
- **Table** — hlavička 12/600 muted, riadky border-soft, hover `#f8fafc`, `emptyMsg`.
- **EmptyState** — ikona + titulok + podtitulok, centrované.

## 5. Stránky (presné podľa mockupu)
- **Login** — vycentrovaná karta s logom, polia username/heslo, „Prihlásiť sa".
- **Dashboard** — PageHeader „Dashboard / Prehľad celého vozového parku" + „+ Pridať auto";
  4× StatCard (Áut v parku/Notifikácie dnes/Overdue položky/Náklady mesiac) vo farbách
  blue/amber/red/green; sekcia „Vozidlá" → 3-stĺpcový grid **CarCard**.
  - **CarCard**: biela karta (červený 2px rám pri overdue + OVERDUE badge vpravo hore),
    názov + km, ŠPZ, riadok chipov (STK/PZP/KASKO/krajiny vinetiek), 2 info stĺpce
    (Nasledujúci servis / Pneumatiky), link „Otvoriť detail →".
  - **Modal „Pridať auto"**: ŠPZ, značka, model, rok, VIN, odometer (**bez poľa „Name"** — názov sa
    odvodí z `make + model` na backende). Mesačné náklady v StatCarde sa po oprave agregácie nákladov
    prepočítavajú (palivo + servis + výdavky).
- **Autá** — vyhľadávací Input + Card s Table (Auto/ŠPZ/VIN/Rok/Odometer/STK/Poistenie/Stav/Detail).
  Stĺpec **STK** = `StatusChip` (`days_left`, urgent `≤14`). Stĺpec **Poistenie** zobrazuje **PZP aj
  KASKO samostatne** (dva chipy vedľa seba, každý s vlastným `days_left`; pomlčka ak nie sú). Stĺpec
  **Stav** = zelený badge „OK" alebo červený **OVERDUE** (ak je ktorýkoľvek termín po splatnosti).
  Dáta z enrichnutého `GET /api/cars` (`stk`/`pzp`/`kasko` s `days_left` + `overdue`).
- **Detail auta** — breadcrumb (Dashboard / Vozidlá / názov), hlavička fullName + meta
  (ŠPZ · VIN · rok · km), Upraviť/Zmazať; **Tabs**: Prehľad, Dokumenty, Pneumatiky, Servis,
  Palivo, Náklady.
  - **Prehľad**: vľavo Card „Stav odometra" (veľký Input + „Uložiť") + Card „História odometra"
    (line chart); vpravo (320px) Card **„Nadchádzajúce termíny"** — mini súhrn (urgentné/čoskoro/ok)
    + zoznam kariet s ľavým farebným pruhom, kategória, názov, meta, vpravo chip (`o X d`/`o X km`,
    `pred X d` + ⚠ pri overdue). Zoradené red→yellow→green→gray.
  - **Dokumenty**: „+ Nový dokument", Table (Typ badge/Platí do/Zostatok chip/Cena/Poskytovateľ/akcie),
    modal (typ select STK/PZP/KASKO/Vinetka SK/AT/CZ, dátum, cena, poskytovateľ).
  - **Pneumatiky**: selektor sád (pill tlačidlá, ✓ pri aktívnej) + „+ Pridať sadu"; header sady má
    badge **„Aktívna sada"/„Neaktívna sada"** (bez výrazného rámika) + **diagram 4 kolies**
    (FL/FR/RL/RR, farba podľa mm) vpravo; akcie sady: **„Nastaviť ako aktívnu"** (PATCH
    `is_active=true`), **Upraviť** (názov/sezóna/dátumy), **Archivovať** (`is_active=false`, vlastník),
    **Zmazať** (len admin). Card s **trend grafom** (skutočné + prerušovaná projekcia + červená čiara
    1.6 mm + popis „Projekcia: 1.6 mm @ dátum") + stĺpec 4 stat kariet (Priemerný dezén/Najazdené/
    Predikcia/Tlak). **Predikcia (text):** ak je `projection_date` → dátum; inak ak je
    `km_at_reference` → „≈ pri X km"; inak „málo dát". Graf kreslí projekciu len keď existuje
    `projection`. Číselné polia (dezén/tlak) prichádzajú ako **number** (nie string) → žiadne NaN;
    priemer počítaný s null-guardom. Tabuľka histórie meraní (Dátum/Odometer/FL/FR/RL/RR/Priemer/Tlak)
    s akciami **Upraviť/Zmazať** na riadku; tlačidlo **„+ Nové meranie"** (modré) je v hlavičke karty
    „História meraní". Modály: **Nové meranie** (4 dezény + tabuľka tlaku 4 kolesá × pred/po hustení,
    zelený info-box) a **Pridať sadu** (názov, sezóna, nasadenie, plánovaná výmena, počiatočný dezén
    + tlak).
  - **Servis**: vľavo „Záznamy servisov" Table (Dátum/Odometer/Popis/Kategória badge/Cena/Upraviť),
    s akciou **Upraviť/Zobraziť** existujúceho záznamu (modál sa otvorí predvyplnený, `servicesApi.update`);
    vpravo (300px) „Servisné intervaly" karty s progress barom a „za X km" badge + CRUD UI. Modal
    „Nový záznam": Dátum + km, **kategória chips** (Servis 🔵/Oprava 🟠/Pneumatiky 🟢/Iné ⚪), popis, cena.
    - Pri **Servis** → rozšírený panel (720px) „Potvrdenie servisných úkonov": **„Vykonané"** a
      **„Dodatočné práce – výmena"** vedľa seba (2 stĺpce checkboxov, položky cez i18n
      `service.performed.*`/`service.additional.*` SK+EN, prvé dva „Vykonané" zvýraznené) + „+ Pridať
      ďalší úkon" (✕); olej (názov + ďalšia výmena km); **„Vaše ďalšie termíny servisu"** = dva
      ohraničené boxy: *Servisná prehliadka* (checkbox „podľa ukazovateľa servisných intervalov" +
      Dňa/Pri) a *Dodatočné práce* (Popis + Dňa/Pri) — mapované na DB polia `next_service_*` /
      `next_additional_*`; **„Kontrola karosérie"** = prepínač **Áno/Nie tlačidlá** (nie checkboxy) →
      textarea „Popis nedostatku"; checkbox „**Vytvoriť pripomienku a notifikáciu pred ďalším termínom
      servisu**" → pri zadanom ďalšom termíne idempotentne upsertne `ServiceInterval` (zobrazí sa
      v paneli intervalov + spúšťa smart notifikáciu).
    - **Oprava** → panel (servis/dielňa, záruka do, rozpis dielov). **Pneumatiky** → panel
      (typ úkonu ako **Select**, sezóna). **Iné** → len základné polia.
  - **Palivo**: **selektor obdobia** (presety Tento mesiac / Tento rok / Vlastné + prepínač
    mesiac/rok); 3× StatCard (Priem. spotreba/Celkové výdavky/Počet tankovaní), bar chart „Spotreba
    l/100km", „Log tankovania" Table, modal „Pridať tankovanie". **Formátovanie:** cena/l **4
    desatinné** (`formatPrice`), celková suma **2** (`formatMoney`), spotreba a litre **1** (`formatNumber`).
  - **Náklady**: **selektor obdobia** (rovnaký ako Palivo, volá `from_date`/`to_date`); vľavo (260px)
    Card s **koláčovým grafom** + legenda + „Spolu"; vpravo „Výdavky" Table (Dátum/Popis/Kategória
    badge/Suma). Breakdown **automaticky započítava palivo** (`fuel_records.total_cost`, kategória
    `fuel`) **a servis** (`service_records.cost`, kategória `service`) popri `expenses` — kategórie
    používajú anglické kľúče (`fuel/service/documents/tires/other`) kvôli farbám.
- **Notifikácie** (dostupné **každému prihlásenému používateľovi**) — 3× StatCard, červený **overdue
  alert** banner, filter (Všetky/Odoslané/Neúspešné), Table (Čas/Auto/Typ/Kanál badge/Príjemca/Stav
  badge). Bežný používateľ vidí **svoj** log (scoped na jeho autá) a spravuje **pravidlá pre svoje
  autá** (znovupoužitý `RulesTab`); admin vidí všetko. SMTP/Matrix/test/run/používatelia ostávajú
  admin-only.
- **Admin** — PageHeader „Admin · Notifikácie" + „Test send" + „+ Nové pravidlo"; Tabs:
  **Pravidlá** (Table s lead 1/2/3, stav, kanály), **Log** (Table + Export CSV), **SMTP**
  (formulár + šablóny emailov), **Matrix** (toggle, homeserver/token/room + per-auto miestnosti),
  **Používatelia** (Table s avatarom, rola badge, pridelené autá, aktivovať/deaktivovať; modal).
- **Nastavenia** (**iba admin** — položka v navigácii `adminOnly`, route obalená `AdminRoute`) —
  Karty: Všeobecné (názov flotily, časové pásmo, **jazyk SK/EN**, mena), Notifikácie (lead 1/2/3,
  čas odosielania, min. dezén mm), PWA (inštalácia), Nebezpečná zóna (Exportovať všetky dáta /
  Zmazať všetky dáta).
- **Detail auta** — tlačidlo **„Zmazať" len pre admina** (`delete_car` = `CurrentAdmin`); bežný
  používateľ auto zmazať nevie (archivácia/úprava áno).

## 6. Grafy (Recharts)
- **História odometra** — `LineChart` (area gradient + body), os km (k formát).
- **Trend dezénu** — `LineChart`/`ComposedChart`: plná čiara „actual", **prerušovaná** „projected",
  `ReferenceLine y=1.6` (červená, prerušovaná, popis „1.6 mm minimum"), os 0–10 mm, os km.
- **Spotreba** — `BarChart` (mesiace), modré stĺpce.
- **Rozdelenie nákladov** — `PieChart` (donut, `innerRadius`), farby kategórií
  (Palivo `#3b82f6`, Servis `#f59e0b`, Dokumenty `#8b5cf6`, Pneumatiky `#10b981`).

## 7. i18n (SK + EN)
- `react-i18next`; default `sk`, fallback `sk`. Prepínač jazyka v Nastaveniach (a v profile).
- Štruktúra: `src/i18n/sk.json`, `src/i18n/en.json`, kľúče po doménach
  (`nav.*`, `dashboard.*`, `car.*`, `tires.*`, `service.*`, `fuel.*`, `costs.*`,
  `notifications.*`, `admin.*`, `settings.*`, `common.*`).
- **Žiadne hardcoded reťazce** v komponentoch — všetko cez `t('...')`. SK texty zhodné s mockupom.
- Persist zvoleného jazyka (localStorage) + podľa `user.locale`.

## 8. Stav & dáta
- **Zustand**: `authStore` (user, tokens, login/logout/refresh), `uiStore` (jazyk, mobilné menu, toasty).
- **API**: typovaný axios klient (`src/api/client.ts`) s JWT interceptorom (auto-refresh na 401),
  doménové hooky (`useCars`, `useCarDetail`, `useTires`, …) — voliteľne TanStack Query.
- **Router**: `react-router-dom` — `/login`, `/`, `/cars`, `/cars/:id`, `/notifications`,
  `/admin`, `/settings`; `PrivateRoute` chráni všetko okrem `/login`.

## 9. PWA
- `vite-plugin-pwa` (Workbox): `manifest.json` (názov „FleetCare", ikony, `display:standalone`,
  `theme_color:#1a2332`, `background_color:#f8fafc`), service worker (cache app shell + runtime
  cache GET `/api/*`), offline fallback.
