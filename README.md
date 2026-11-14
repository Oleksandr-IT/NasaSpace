# Field Shift — NASA Space Apps 2026

Сайт-дашборд для фермерів США: порівнює поточну сівозміну поля з 3 альтернативами
на основі даних NASA та USDA. Челендж: [Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/).

## Структура

```
backend/            FastAPI (Python)
  main.py           ендпоінти API
  services/
    power.py        NASA POWER: клімат 1995–2025 і метрики (заморозки, GDD, опади, тренди)
    soil.py         USDA SSURGO: ґрунт у точці
    cdl.py          USDA Cropland Data Layer: що росло на полі 2016–2025, поточна сівозміна
    strategies.py   генерація 3 альтернатив, бали 0–100, пояснення
    earthdata.py    NASA Earthdata: опади GPM IMERG (з 2001) і вологість ґрунту SMAP (з 2016) через OPeNDAP
    nass.py         USDA NASS: врожайність і ціни (вмикається, якщо є NASS_API_KEY)
    cache.py        кеш відповідей у backend/cache/
  data/
    crops.json      характеристики культур: вода і посуха — FAO, решта — оцінки команди
    demo_fields.json
  cache/            збережені дані для 3 демо-полів (демо працює без інтернету)
frontend/           React + Vite
  src/pages/        5 екранів: Field, Conditions, Compare, Details, How it works
  src/components/   карта, смуги балів, календар сівозміни
  src/mocks/        приклад відповідей API (поле в Айові)
design/             макети з Figma і промт
docs/               текст челенджу (PDF і збережені сторінки)
```

## Як запустити

Потрібно: **Python 3.11+** і **Node.js LTS** (https://nodejs.org).

**1. Бекенд** (термінал 1):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; на Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Перевірка: http://127.0.0.1:8000/docs — там можна викликати всі ендпоінти.

**2. Фронтенд** (термінал 2):

```bash
cd frontend
npm install
npm run dev
```

Відкрити http://localhost:5173. Якщо бекенд не запущений, сайт покаже мок-дані для Айови.

**3. Ключі** — файл `.env` у корені проєкту. Його **не комітимо**, передаємо особисто:

```
EARTHDATA_TOKEN=...   # NASA SMAP та IMERG. Перевірка: cd backend && python -m services.earthdata
NASS_API_KEY=...      # необов'язково: справжні ціни USDA. Ключ: https://quickstats.nass.usda.gov/api
```

Без `EARTHDATA_TOKEN` сайт працює, але картка «Satellite check» буде порожня (крім демо-полів — для них дані вже в кеші).

## API

| Метод | Адреса | Що повертає |
|---|---|---|
| GET | `/api/field?lat=42.1&lon=-93.55` | клімат, ґрунт, поточна сівозміна |
| POST | `/api/strategies` | 4 стратегії з балами, календарем і поясненнями |
| GET | `/api/satellite?lat=42.1&lon=-93.55` | опади IMERG і вологість SMAP за роками (нове поле — ~2 хв) |
| GET | `/api/geocode?q=Ames, Iowa` | координати місця (OpenStreetMap) |
| GET | `/api/demo-fields` | 3 демо-поля |

Тіло для `/api/strategies`:

```json
{"lat": 42.1, "lon": -93.55,
 "priorities": {"water": 4, "soil": 5, "erosion": 4, "income": 3},
 "constraints": {"irrigation": false, "livestock": false, "small_grain_equipment": false},
 "scenario": "normal"}
```

`scenario`: `normal`, `dry` або `wet`.

## Джерела даних

| Джерело | Для чого | Доступ |
|---|---|---|
| NASA POWER | щоденний клімат, вологість ґрунту (модель) | без ключа |
| NASA GIBS | шари SMAP, MODIS NDVI, IMERG на карті (картинки) | без ключа |
| USDA SSURGO (Soil Data Access) | ґрунт | без ключа |
| USDA Cropland Data Layer | культури по роках | без ключа |
| NASA GPM IMERG, NASA SMAP L4 | справжні супутникові числа: опади і вологість ґрунту | токен у `.env` |
| FAO (Training Manual No. 3, табл. 6, 14) | потреба культур у воді, чутливість до посухи | у `crops.json` |
| USDA NASS QuickStats | врожайність і ціни | ключ у `.env` (необов'язково) |
| OpenStreetMap Nominatim | пошук місця за назвою | без ключа |

## Що є оцінкою команди, а не даними

Чесно кажемо журі: у `crops.json` поля в `estimated` (стійкість до спеки, глибина коріння, рештки,
дохідність без NASS), дати сівби/збору і вартість покривних культур — наші оцінки. Формули балів —
прості правила, не перевірені агрономами.

## Що лишилось

- Деплой: бекенд (Render), фронтенд (Vercel або Netlify).
- Презентація, відео, сторінка проєкту на Space Apps.
