"""USDA Cropland Data Layer (CropScape): яка культура росла в точці поля кожного року.

Сервіс приймає координати в проєкції EPSG:5070 (Albers), тому переводимо їх через pyproj.
Ключ не потрібен.
"""
import re
from concurrent.futures import ThreadPoolExecutor

import requests
from pyproj import Transformer

CDL_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue"
YEARS = range(2016, 2026)  # останні 10 років (2016–2025); онови, коли вийде новий шар CDL

_to_albers = Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)

# Назви CDL -> наші id культур (див. data/crops.json)
CDL_TO_CROP = {
    "Corn": "corn",
    "Soybeans": "soybean",
    "Winter Wheat": "winter_wheat",
    "Spring Wheat": "spring_wheat",
    "Sorghum": "sorghum",
    "Alfalfa": "alfalfa",
    "Oats": "oats",
    "Cotton": "cotton",
    "Sunflower": "sunflower",
    "Dbl Crop WinWht/Soybeans": "winter_wheat+soybean",
}


def fetch_year(x: float, y: float, year: int) -> str | None:
    response = requests.get(CDL_URL, params={"year": year, "x": x, "y": y}, timeout=90)  # сервіс буває повільним
    response.raise_for_status()
    match = re.search(r'category: "([^"]+)"', response.text)
    return match.group(1) if match else None


def fetch_history(lat: float, lon: float) -> list[dict]:
    x, y = _to_albers.transform(lon, lat)
    # 10 запитів паралельно замість по черзі — у кілька разів швидше
    with ThreadPoolExecutor(max_workers=5) as pool:
        categories = list(pool.map(lambda year: fetch_year(x, y, year), YEARS))
    return [{"year": year, "category": category, "crop": CDL_TO_CROP.get(category)}
            for year, category in zip(YEARS, categories)]


def detect_rotation(history: list[dict]) -> dict:
    """Шукає повторюваний шаблон в останніх роках: 'corn -> soybean', 'continuous corn' тощо."""
    recent = [h["crop"] for h in history[-6:] if h["crop"]]
    if not recent:
        return {"pattern": [], "label": "Unknown (not cropland in CDL)"}
    unique = list(dict.fromkeys(recent))
    if len(unique) == 1:
        return {"pattern": unique, "label": f"Continuous {unique[0]}"}
    # Перевіряємо, чи повторюється цикл довжиною 2 або 3
    for size in (2, 3):
        cycle = recent[-size:]
        if all(recent[i] == cycle[(i - len(recent)) % size] for i in range(len(recent))):
            return {"pattern": cycle, "label": " -> ".join(cycle)}
    return {"pattern": unique, "label": "Mixed: " + ", ".join(unique)}
