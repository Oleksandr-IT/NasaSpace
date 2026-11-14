"""Field Shift API.

Запуск (з папки backend):
    uvicorn main:app --reload
Документація з усіма ендпоінтами: http://127.0.0.1:8000/docs
"""
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import cache, cdl, power, soil, strategies

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

    try:
        climate = cache.cached(f"climate_{key}", lambda: power.climate_summary(power.fetch_daily(lat, lon)))
    except Exception as error:  # без клімату далі рахувати не можемо
        raise RuntimeError(f"NASA POWER is not available: {error}")

    try:
        soil_info = cache.cached(f"soil_{key}", lambda: soil.fetch_soil(lat, lon))
    except Exception as error:
        soil_info = None
        warnings.append(f"Soil data not available: {error}")

    try:
        history = cache.cached(f"cdl_{key}", lambda: cdl.fetch_history(lat, lon))
    except Exception as error:
        history = []
        warnings.append(f"Crop history not available: {error}")

    rotation = cdl.detect_rotation(history) if history else {"pattern": [], "label": "Unknown"}
    return {
        "location": {"lat": lat, "lon": lon, "area": soil_info["area"] if soil_info else None},
        "soil": soil_info,
        "climate": climate,
        "current_rotation": {**rotation, "history": history, "source": "USDA CDL"},
        "warnings": warnings,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo-fields")
def demo_fields():
    return DEMO_FIELDS


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
