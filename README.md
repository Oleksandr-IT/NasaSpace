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
    earthdata.py    NASA Earthdata (SMAP, IMERG) — заготовка на день 2
    cache.py        кеш відповідей у backend/cache/
  data/
    crops.json      характеристики культур (оцінки 1–5, треба перевірити)
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

**3. Токен NASA Earthdata** (лише для SMAP/IMERG, день 2): створити файл `.env` у корені проєкту з рядком
`EARTHDATA_TOKEN=...`. Файл **не комітимо**, передаємо особисто. Перевірка: `cd backend && python -m services.earthdata`.

## API

| Метод | Адреса | Що повертає |
|---|---|---|
| GET | `/api/field?lat=42.1&lon=-93.55` | клімат, ґрунт, поточна сівозміна |
| POST | `/api/strategies` | 4 стратегії з балами, календарем і поясненнями |
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
| NASA Earthdata (SMAP, IMERG) | числові дані супутників | токен у `.env` |

## Що далі (TODO по ролях)

- **Роль 1 — дані клімату:** SMAP/IMERG через `services/earthdata.py` для демо-полів; порівняти з POWER.
- **Роль 2 — ґрунт і API:** деплой бекенду (Render), обробка помилок, нові категорії CDL.
- **Роль 3 — модель:** перевірити значення в `data/crops.json` і додати джерела; уточнити формули балів у `strategies.py` (зараз варіант A з покривною культурою майже завжди перемагає); глосарій у `HowItWorks.jsx`.
- **Роль 4 — фронтенд:** пошук адреси, стан завантаження і помилок, деплой (Vercel або Netlify).
- **Роль 5 — дизайн:** полірування екранів 3–4, мобільна версія, скріншоти і відео для подачі.
