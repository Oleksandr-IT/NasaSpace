"""NASA Earthdata (SMAP, GPM IMERG, ECOSTRESS) — заготовка на день 2.

Токен лежить у файлі .env у корені проєкту: EARTHDATA_TOKEN=...
Файл .env НЕ комітимо (він у .gitignore), його передаємо в команді особисто.

Перевірити, що токен працює:
    python -m services.earthdata
"""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"


def token() -> str:
    value = os.getenv("EARTHDATA_TOKEN")
    if not value:
        raise RuntimeError("EARTHDATA_TOKEN not found. Put it into the .env file in the project root.")
    return value


def find_file(short_name: str, start: str, end: str) -> str | None:
    """Шукає в каталозі NASA (CMR) перший файл продукту за період. Повертає URL для завантаження."""
    params = {"short_name": short_name, "temporal": f"{start},{end}", "page_size": 1}
    entries = requests.get(CMR_URL, params=params, timeout=60).json()["feed"]["entry"]
    for link in entries[0]["links"] if entries else []:
        if link["href"].startswith("https") and link["href"].endswith((".h5", ".nc4", ".tif")):
            return link["href"]
    return None


def check_access() -> None:
    """Завантажує перший 1 КБ файлів SMAP та IMERG, щоб переконатися, що доступ є."""
    products = {"SMAP L4 soil moisture": "SPL4SMGP", "GPM IMERG daily rain": "GPM_3IMERGDF"}
    for name, short_name in products.items():
        url = find_file(short_name, "2025-07-12T00:00:00Z", "2025-07-12T23:00:00Z")
        response = requests.get(url, headers={"Authorization": f"Bearer {token()}", "Range": "bytes=0-1023"}, timeout=90)
        print(f"{name}: HTTP {response.status_code}")


# TODO (роль 1, день 2): функції get_smap_root_zone(lat, lon) і get_imerg_rain(lat, lon)
# Ідея: бібліотека earthaccess (pip install earthaccess h5py) — завантажити файли для
# 3 демо-полів один раз, витягти значення в точці і зберегти в cache/ як JSON.

if __name__ == "__main__":
    check_access()
