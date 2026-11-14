"""NASA Earthdata: справжні супутникові числа для точки поля.

- GPM IMERG (місячні опади, 0.1°, з 2001 р.) — через OPeNDAP на GES DISC
- SMAP L4 (вологість ґрунту в кореневій зоні, 9 км, з 2015 р.) — через Cloud OPeNDAP

OPeNDAP дозволяє вирізати з великого файлу NASA лише одну клітинку, тому
не треба завантажувати сотні мегабайт.

Токен лежить у файлі .env у корені проєкту: EARTHDATA_TOKEN=...
Файл .env НЕ комітимо (він у .gitignore), його передаємо в команді особисто.

Перевірити доступ:  python -m services.earthdata
"""
import calendar
import time
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean

import requests
from dotenv import load_dotenv
from pyproj import Transformer

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
IMERG_URL = ("https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGM.07/{year}/"
             "3B-MO.MS.MRG.3IMERG.{year}{month:02d}01-S000000-E235959.{month:02d}.V07B.HDF5.ascii")
SMAP_COLLECTION = "C3480440870-NSIDC_CPRD"  # SPL4SMGP версія 008
SMAP_URL = "https://opendap.earthdata.nasa.gov/collections/" + SMAP_COLLECTION + "/granules/{granule}.dap.csv"

SEASON = range(5, 10)  # травень–вересень
WORKERS = 4  # більше паралельних запитів сервери NASA не люблять (503)
IMERG_YEARS = range(2001, 2026)
SMAP_YEARS = range(2016, 2026)  # повні сезони SMAP

# Сітка SMAP: EASE-Grid 2.0, 9 км (EPSG:6933)
_to_ease = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
EASE_CELL = 9008.055210146
EASE_X_MIN, EASE_Y_MAX = -17367530.44516138, 7314540.83086444


def token() -> str:
    value = os.getenv("EARTHDATA_TOKEN")
    if not value:
        raise RuntimeError("EARTHDATA_TOKEN not found. Put it into the .env file in the project root.")
    return value


def _get(url: str, **kwargs) -> str:
    """GET з токеном. Якщо сервер NASA зайнятий (429/5xx), чекаємо і пробуємо ще раз."""
    for attempt in range(5):
        response = requests.get(url, headers={"Authorization": f"Bearer {token()}"}, timeout=120, **kwargs)
        if response.status_code not in (429, 500, 502, 503, 504):
            break
        time.sleep(2 ** attempt)
    response.raise_for_status()
    return response.text


# ---------- GPM IMERG ----------

def imerg_month(lat: float, lon: float, year: int, month: int) -> float:
    """Опади за місяць у мм. IMERG дає середню інтенсивність (мм/год), множимо на години місяця."""
    lon_index = int((lon + 180) / 0.1)
    lat_index = int((lat + 90) / 0.1)
    url = IMERG_URL.format(year=year, month=month) + f"?precipitation[0][{lon_index}][{lat_index}]"
    text = _get(url)
    rate = float(text.strip().splitlines()[-1].split(",")[-1])  # останній рядок: "precipitation[0][0], 0.285"
    hours = calendar.monthrange(year, month)[1] * 24
    return round(rate * hours, 1)


def imerg_seasons(lat: float, lon: float) -> list[dict]:
    """Опади травень–вересень за кожен рік 2001–2025."""
    jobs = [(year, month) for year in IMERG_YEARS for month in SEASON]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        values = list(pool.map(lambda job: imerg_month(lat, lon, *job), jobs))
    by_year = {}
    for (year, _), value in zip(jobs, values):
        by_year[year] = by_year.get(year, 0) + value
    return [{"year": year, "value": round(total)} for year, total in by_year.items()]


# ---------- SMAP L4 ----------

def _smap_granule(day: str) -> str | None:
    """Назва файлу SMAP за день (беремо знімок о 10:30 UTC)."""
    params = {"collection_concept_id": SMAP_COLLECTION, "page_size": 1,
              "temporal": f"{day}T10:00:00Z,{day}T11:59:59Z"}
    entries = requests.get(CMR_URL, params=params, timeout=60).json()["feed"]["entry"]
    return entries[0]["title"] if entries else None


def smap_value(lat: float, lon: float, day: str) -> float | None:
    """Вологість кореневої зони (м³/м³) у клітинці поля на дату."""
    x, y = _to_ease.transform(lon, lat)
    row, col = int((EASE_Y_MAX - y) // EASE_CELL), int((x - EASE_X_MIN) // EASE_CELL)
    granule = _smap_granule(day)
    if not granule:
        return None
    # Сервіс не віддає одну клітинку в CSV, тому беремо 2x2 і читаємо верхню ліву
    query = f"/Geophysical_Data/sm_rootzone[{row}:{row + 1}][{col}:{col + 1}]"
    text = _get(SMAP_URL.format(granule=granule), params={"dap4.ce": query})
    first_row = [line for line in text.splitlines() if line.startswith("/Geophysical_Data/sm_rootzone[0]")][0]
    value = float(first_row.split(",")[1])
    return round(value, 3) if value >= 0 else None  # -9999 = немає даних


def smap_seasons(lat: float, lon: float) -> list[dict]:
    """Середня вологість кореневої зони травень–вересень за кожен рік 2016–2025 (2 знімки на місяць)."""
    days = [f"{year}-{month:02d}-{day:02d}" for year in SMAP_YEARS for month in SEASON for day in (5, 20)]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        values = list(pool.map(lambda d: smap_value(lat, lon, d), days))
    result = []
    for year in SMAP_YEARS:
        year_values = [v for d, v in zip(days, values) if d.startswith(str(year)) and v is not None]
        if year_values:
            result.append({"year": year, "value": round(mean(year_values), 3)})
    return result


def satellite_summary(lat: float, lon: float) -> dict:
    return {
        "imerg_season_rain": imerg_seasons(lat, lon),
        "smap_season_soil": smap_seasons(lat, lon),
        "sources": {
            "imerg": "NASA GPM IMERG V07 monthly, 0.1° (~10 km), via GES DISC OPeNDAP",
            "smap": "NASA SMAP L4 root-zone soil moisture v008, 9 km, via Earthdata Cloud OPeNDAP",
        },
    }


def check_access() -> None:
    print("IMERG July 2024, Iowa demo field:", imerg_month(42.1, -93.55, 2024, 7), "mm")
    print("SMAP 2025-07-11, Iowa demo field:", smap_value(42.1, -93.55, "2025-07-11"), "m3/m3")


if __name__ == "__main__":
    check_access()
