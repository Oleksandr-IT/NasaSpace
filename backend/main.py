"""Field Shift API.

Запуск (з папки backend):
    uvicorn main:app --reload
Документація з усіма ендпоінтами: http://127.0.0.1:8000/docs
"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import cache, cdl, earthdata, nass, power, soil, strategies

app = FastAPI(title="Field Shift API")

# Дозволяємо фронтенду (Vite, порт 5173) звертатися до API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_FIELDS = json.loads((Path(__file__).parent / "data" / "demo_fields.json").read_text(encoding="utf-8"))


def get_field(lat: float, lon: float) -> dict:
    """Збирає все про поле з трьох джерел. Кожне джерело кешується окремо."""
    lat, lon = round(lat, 2), round(lon, 2)
    key = f"{lat}_{lon}"
    warnings = []

    # Три джерела завантажуємо одночасно, а не по черзі
    with ThreadPoolExecutor(max_workers=3) as pool:
        climate_job = pool.submit(cache.cached, f"climate_{key}", lambda: power.climate_summary(power.fetch_daily(lat, lon)))
        soil_job = pool.submit(cache.cached, f"soil_{key}", lambda: soil.fetch_soil(lat, lon))
        cdl_job = pool.submit(cache.cached, f"cdl_{key}", lambda: cdl.fetch_history(lat, lon))

    try:
        climate = climate_job.result()
    except Exception as error:  # без клімату далі рахувати не можемо
        raise HTTPException(status_code=502, detail=f"no NASA POWER climate data ({error})")

    try:
        soil_info = soil_job.result()
    except Exception as error:
        soil_info = None
        warnings.append(f"Soil data not available: {error}")

    try:
        history = cdl_job.result()
    except Exception as error:
        history = []
        warnings.append(f"Crop history not available: {error}")

    rotation = cdl.detect_rotation(history) if history else {"pattern": [], "label": "Unknown"}
    if soil_info is None and not warnings:
        warnings.append("No USDA soil data at this point. Is it farmland? Soil-based scores use default values.")
    if not rotation["pattern"]:
        found = sorted({h["category"] for h in history if h["category"]})
        if found:
            warnings.append(f"USDA maps show this point as {', '.join(found)} in 2016–2025 — no crops from our list. "
                            "Showing a typical corn → soybean rotation as the current one.")
        else:
            warnings.append("No crop history found here on USDA crop maps for 2016–2025. "
                            "Showing a typical corn → soybean rotation as the current one.")

    # Ціни NASS: лише якщо є ключ у .env, інакше модель бере оцінки з crops.json
    revenue = None
    if nass.api_key() and soil_info:
        state = soil_info["area"].split(", ")[-1]  # "Story County, Iowa" -> "Iowa"
        try:
            revenue = cache.cached(f"nass_{state}", lambda: nass.state_revenues(state))
        except Exception as error:
            warnings.append(f"Crop prices not available: {error}")

    return {
        "location": {"lat": lat, "lon": lon, "area": soil_info["area"] if soil_info else None},
        "soil": soil_info,
        "climate": climate,
        "current_rotation": {**rotation, "history": history, "source": "USDA CDL"},
        "satellite": cache.load(f"satellite_{key}"),  # лише якщо вже завантажено через /api/satellite
        "revenue": revenue,
        "warnings": warnings,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo-fields")
def demo_fields():
    return DEMO_FIELDS


@app.get("/api/satellite")
def satellite(lat: float, lon: float):
    """Справжні супутникові дані NASA (IMERG, SMAP). Для нового поля — близько 2 хвилин."""
    lat, lon = round(lat, 2), round(lon, 2)
    try:
        return cache.cached(f"satellite_{lat}_{lon}", lambda: earthdata.satellite_summary(lat, lon))
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"NASA Earthdata is not available: {error}")


@app.get("/api/geocode")
def geocode(q: str):
    """Пошук адреси або назви місця в США через OpenStreetMap Nominatim."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": q, "format": "json", "countrycodes": "us", "limit": 1},
        headers={"User-Agent": "FieldShift-hackathon-app/0.1"},
        timeout=20,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise HTTPException(status_code=404, detail="Place not found")
    return {"lat": float(results[0]["lat"]), "lon": float(results[0]["lon"]), "name": results[0]["display_name"]}


@app.get("/api/field")
def field(lat: float, lon: float):
    return get_field(lat, lon)


class StrategyRequest(BaseModel):
    lat: float
    lon: float
    priorities: dict = {"water": 3, "soil": 3, "erosion": 3, "income": 3}
    constraints: dict = {"irrigation": False, "livestock": False, "small_grain_equipment": True}
    scenario: str = "normal"  # normal | dry | wet


@app.post("/api/strategies")
def build(request: StrategyRequest):
    field_data = get_field(request.lat, request.lon)
    return {
        "scenario": request.scenario,
        "strategies": strategies.build_strategies(field_data, request.priorities, request.constraints, request.scenario),
    }
