"""USDA NASS QuickStats: справжня врожайність і ціни, щоб порахувати дохід з акра.

Потрібен безкоштовний ключ: https://quickstats.nass.usda.gov/api -> "Request API Key".
Додати в .env у корені проєкту: NASS_API_KEY=...
Без ключа модель використовує оцінки дохідності з data/crops.json.

Дохід, $/acre = середня врожайність у штаті (2020+) x середня ціна по США (2020+).
"""
import os
from pathlib import Path
from statistics import mean

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

API_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
FIRST_YEAR = 2020

# id культури -> (назва в NASS, одиниця врожайності, одиниця ціни, слово, яке має бути в short_desc)
COMMODITIES = {
    "corn": ("CORN", "BU / ACRE", "$ / BU", "GRAIN"),
    "soybean": ("SOYBEANS", "BU / ACRE", "$ / BU", "SOYBEANS"),
    "winter_wheat": ("WHEAT", "BU / ACRE", "$ / BU", "WINTER"),
    "spring_wheat": ("WHEAT", "BU / ACRE", "$ / BU", "SPRING"),
    "oats": ("OATS", "BU / ACRE", "$ / BU", "OATS"),
    "sorghum": ("SORGHUM", "BU / ACRE", "$ / CWT", "GRAIN"),
    "sunflower": ("SUNFLOWER", "LB / ACRE", "$ / CWT", "SUNFLOWER"),
    "cotton": ("COTTON", "LB / ACRE", "$ / LB", "UPLAND"),
    "alfalfa": ("HAY", "TONS / ACRE", "$ / TON", "ALFALFA"),
}


def api_key() -> str | None:
    return os.getenv("NASS_API_KEY")


def _query(**params) -> list[dict]:
    params.update({"key": api_key(), "format": "JSON", "year__GE": FIRST_YEAR})
    response = requests.get(API_URL, params=params, timeout=60)
    if response.status_code == 400:  # NASS повертає 400, коли нічого не знайдено
        return []
    response.raise_for_status()
    return response.json().get("data", [])


def _values(rows, unit, word) -> list[float]:
    result = []
    for row in rows:
        if row["unit_desc"] == unit and word in row["short_desc"]:
            try:
                result.append(float(row["Value"].replace(",", "")))
            except ValueError:
                pass  # "(D)" = дані приховані
    return result


def revenue_per_acre(crop_id: str, state_name: str) -> float | None:
    commodity, yield_unit, price_unit, word = COMMODITIES[crop_id]
    yields = _values(_query(commodity_desc=commodity, statisticcat_desc="YIELD", agg_level_desc="STATE",
                            state_name=state_name.upper(), reference_period_desc="YEAR"), yield_unit, word)
    prices = _values(_query(commodity_desc=commodity, statisticcat_desc="PRICE RECEIVED", agg_level_desc="NATIONAL",
                            freq_desc="ANNUAL"), price_unit, word.replace("WINTER", "WHEAT").replace("SPRING", "WHEAT"))
    if not yields or not prices:
        return None
    price = mean(prices)
    if price_unit == "$ / CWT":  # ціна за 100 фунтів
        price = price / 100 * (56 if yield_unit == "BU / ACRE" else 1)  # бушель сорго = 56 фунтів
    return round(mean(yields) * price)


def state_revenues(state_name: str) -> dict:
    """Дохід з акра для всіх культур у штаті. Культури без даних пропускаємо."""
    result = {}
    for crop_id in COMMODITIES:
        try:
            value = revenue_per_acre(crop_id, state_name)
        except requests.RequestException:
            value = None
        if value:
            result[crop_id] = value
    return {"state": state_name, "revenue_per_acre": result, "source": f"USDA NASS QuickStats {FIRST_YEAR}+"}
