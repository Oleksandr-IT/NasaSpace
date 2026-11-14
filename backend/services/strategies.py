"""Проста модель: генеруємо 3 альтернативи до поточної сівозміни,
рахуємо бали 0–100 за 6 критеріями і пишемо пояснення.

Як зберігаємо сівозміну: список років, у кожному році — культури, які ЗБИРАЮТЬ (або
закінчують, для покривних) у цьому році. Так само рахує USDA CDL.
Приклад: [["corn"], ["soybean"]] = кукурудза -> соя.

Звідки числа: потреба у воді і чутливість до посухи — FAO (див. data/crops.json, "_sources"),
решта характеристик культур — оцінки команди ("estimated").
"""
import json
from pathlib import Path
from statistics import mean

CROPS = json.loads((Path(__file__).resolve().parent.parent / "data" / "crops.json").read_text(encoding="utf-8"))
CROPS.pop("_sources")

DROUGHT_SWAP = {"corn": "sorghum", "soybean": "sunflower", "cotton": "sorghum"}

# FAO: чутливість до посухи -> стійкість 1..5
TOLERANCE = {"low": 5, "low-medium": 4, "medium": 3, "medium-high": 2, "high": 1}

COVER_CROP_INCOME_PENALTY = 10  # насіння і сівба покривної культури (оцінка команди)


def attr(crop_id: str, key: str):
    """Характеристика культури: спочатку з джерел, потім з оцінок команди."""
    crop = CROPS[crop_id]
    return crop[key] if key in crop else crop["estimated"][key]


def water_need(crop_id: str) -> float:
    """Середина діапазону FAO, мм за сезон."""
    low, high = CROPS[crop_id]["water_need_mm"]
    return (low + high) / 2


# ---------- Календар і покриття поля ----------

def _month(mm_dd: str) -> float:
    """'05-15' -> 5.45 (місяць з дробом, щоб малювати смуги на календарі)."""
    month, day = mm_dd.split("-")
    return int(month) + (int(day) - 1) / 31


def calendar(years: list[list[str]]) -> list[dict]:
    """Смуги для календаря: які культури в яких місяцях стоять на полі."""
    bars = []
    n = len(years)
    for index, crops in enumerate(years):
        for crop_id in crops:
            crop = CROPS[crop_id]
            start, end = _month(crop["plant"]), _month(crop["harvest"]) + 1 / 31
            if start < end:  # росте в межах одного року
                bars.append({"year": index + 1, "crop": crop_id, "name": crop["name"], "kind": crop["kind"], "start": start, "end": end})
            else:  # озима або покривна: посіяли восени попереднього року
                previous = (index - 1) % n + 1
                bars.append({"year": previous, "crop": crop_id, "name": crop["name"], "kind": crop["kind"], "start": start, "end": 13})
                bars.append({"year": index + 1, "crop": crop_id, "name": crop["name"], "kind": crop["kind"], "start": 1, "end": end})
    return bars


def covered_share(years: list[list[str]]) -> float:
    """Частка місяців, коли на полі щось росте (0..1).
    Місяць вважаємо вкритим, якщо культури стоять на полі хоча б половину місяця."""
    bars = calendar(years)
    covered = 0
    for year in range(1, len(years) + 1):
        for month in range(1, 13):
            overlap = sum(max(0, min(b["end"], month + 1) - max(b["start"], month)) for b in bars if b["year"] == year)
            if overlap >= 0.5:
                covered += 1
    return covered / (12 * len(years))


# ---------- Генерація стратегій ----------

def _mains(years):
    return [c for crops in years for c in crops if CROPS[c]["kind"] == "main"]


def _has_winter_crop(crops):
    return any(_month(CROPS[c]["plant"]) > _month(CROPS[c]["harvest"]) for c in crops)


def label(years) -> str:
    parts = []
    for crops in years:
        mains = [CROPS[c]["name"] for c in crops if CROPS[c]["kind"] == "main"]
        parts.append(" + ".join(mains))
    text = " → ".join(parts)
    covers = sorted({CROPS[c]["name"].replace(" (cover)", "") for crops in years for c in crops if CROPS[c]["kind"] == "cover"})
    return text + (" + " + ", ".join(covers).lower() + " cover" if covers else "")


def add_cover_crop(years):
    """A: у кожен рік без озимої культури додаємо озиме жито як покривну."""
    return [crops if _has_winter_crop(crops) else ["cereal_rye"] + crops for crops in years]


def add_small_grain_and_legume(years, field_gdd):
    """B: додаємо рік з культурою, якої бракує (пшениця, соя або овес)."""
    present = set(_mains(years))
    for new_crop in ("winter_wheat", "soybean", "oats"):
        if new_crop not in present and CROPS[new_crop]["gdd_need"] <= field_gdd:
            break
    result = [list(crops) for crops in years] + [[new_crop]]
    if new_crop == "winter_wheat" and not _has_winter_crop(result[0]):
        result[0] = ["clover"] + result[0]  # конюшина після пшениці до наступної весни
    return result


def drought_tolerant(years, field_gdd, livestock):
    """C: для тваринництва — люцерна; інакше замінюємо найбільш вологолюбну культуру."""
    if livestock:
        return [list(crops) for crops in years] + [["alfalfa"], ["alfalfa"]]
    mains = _mains(years)
    thirsty = max(mains, key=water_need)
    swap = DROUGHT_SWAP.get(thirsty)
    if swap and CROPS[swap]["gdd_need"] <= field_gdd and swap not in mains:
        if len(years) == 1:  # монокультура: чергуємо стару культуру з новою, а не міняємо одну на одну
            return [[swap], list(years[0])]
        return [[swap if c == thirsty else c for c in crops] for crops in years]
    return [list(crops) for crops in years] + [["sorghum" if "sorghum" not in mains else "sunflower"]]


# ---------- Бали ----------

def season_rain(climate, scenario):
    return {"dry": climate["dry_year_rain_mm"], "wet": climate["wet_year_rain_mm"]}.get(scenario, climate["season_rain_mm"])


def soil_storage_mm(soil) -> float:
    """Скільки води ґрунт може запасти в метровому шарі: AWC (см/см) x 100 см x 10 = мм."""
    awc = (soil or {}).get("water_capacity_cm_per_cm") or 0.15
    return awc * 1000


def score(years, field, scenario, constraints) -> dict:
    climate, soil = field["climate"], field.get("soil") or {}
    rain = season_rain(climate, scenario)
    cover = covered_share(years)
    mains = _mains(years)
    cover_years = sum(1 for crops in years if any(CROPS[c]["kind"] == "cover" for c in crops)) / len(years)

    # Вода 1: скільки води сівозміна споживає за рік (FAO, мм). 400 мм = 100 балів, 1200 мм = 0
    yearly_need = mean(sum(water_need(c) for c in crops) for crops in years)
    water = 100 - (yearly_need - 400) / 8
    # Вода 2: чи вистачає опадів сезону + запасу в ґрунті головній культурі (без зрошення)
    if not constraints.get("irrigation"):
        available = rain + soil_storage_mm(soil)
        deficit = mean(max(0, water_need(c) - available) for c in mains)
        water -= deficit / 5

    # Здоров'я ґрунту: рештки + бобові (азот) + покриття поля
    legume_years = sum(1 for crops in years if any(CROPS[c]["n_fixing"] for c in crops)) / len(years)
    residue = mean(attr(c, "residue") for c in mains)
    soil_health = residue * 8 + legume_years * 30 + cover * 30

    # Ерозія: чим довше поле вкрите, тим краще; на схилі й при зливах це важливіше
    risk = 1 + (soil.get("slope_pct") or 0) / 10 + climate["heavy_rain_days_25mm"] / 20
    erosion = 100 - (1 - cover) * 60 * risk

    # Розрив циклу шкідників: скільки різних родин культур у сівозміні
    families = len({CROPS[c]["family"] for crops in years for c in crops})
    pest_break = {1: 20, 2: 60, 3: 80}.get(families, 95)

    # Дохід: справжні ціни NASS ($1000/acre = 100 балів), якщо є; інакше оцінка команди.
    # Мінус витрати на покривні культури і техніку для зернових.
    revenue = (field.get("revenue") or {}).get("revenue_per_acre", {})
    income = mean(revenue[c] / 10 if c in revenue else attr(c, "income") * 20 for c in mains)
    income -= cover_years * COVER_CROP_INCOME_PENALTY
    if not constraints.get("small_grain_equipment") and any(CROPS[c]["small_grain"] for c in mains):
        income -= 10  # треба орендувати або купити техніку

    # Погодна стійкість: посуха (FAO) і спека (оцінка); у сухий рік посуха важить удвічі більше
    drought = mean(TOLERANCE[CROPS[c]["drought_sensitivity"]] for c in mains)
    heat = mean(attr(c, "heat_tolerance") for c in mains)
    climate_risk = ((drought * 2 + heat) / 3 if scenario == "dry" else (drought + heat) / 2) * 20

    scores = {"water": water, "soil_health": soil_health, "erosion": erosion,
              "pest_break": pest_break, "income": income, "climate_risk": climate_risk}
    return {k: round(max(0, min(100, v))) for k, v in scores.items()}


def total(scores, priorities) -> int:
    weights = {"water": priorities.get("water", 3), "soil_health": priorities.get("soil", 3),
               "erosion": priorities.get("erosion", 3), "income": priorities.get("income", 3),
               "pest_break": 3, "climate_risk": 3}
    return round(sum(scores[k] * w for k, w in weights.items()) / sum(weights.values()))


# ---------- Пояснення ----------

def _evidence(field, current_years, scenario):
    climate, soil, sat = field["climate"], field.get("soil") or {}, field.get("satellite")
    bare_now = round((1 - covered_share(current_years)) * 12)
    dry_year = climate["year_types"]["dry"][0]
    thirsty = max(_mains(current_years), key=water_need)
    low, high = CROPS[thirsty]["water_need_mm"]
    items = [
        {"text": f"Field is bare about {bare_now} months a year in the current rotation", "source": "USDA CDL + crop calendar", "confidence": "Model"},
        {"text": f"{CROPS[thirsty]['name']} needs {low}–{high} mm of water per season; this field gets {season_rain(climate, scenario)} mm in May–Sep plus about {round(soil_storage_mm(soil))} mm stored in the soil",
         "source": "FAO + NASA POWER + SSURGO", "confidence": "Reference"},
        {"text": f"{climate['heavy_rain_days_25mm']} days a year with more than 25 mm of rain", "source": "NASA POWER", "confidence": "Model"},
        {"text": f"Dry years like {dry_year} brought {climate['dry_year_rain_mm']} mm in May–Sep (typical: {climate['season_rain_mm']} mm)", "source": "NASA POWER", "confidence": "Model"},
    ]
    if soil:
        items.append({"text": f"{soil['name']} soil: {soil['organic_matter_pct']}% organic matter, {soil['slope_pct']}% slope", "source": "USDA SSURGO", "confidence": "Measured"})
    revenue = (field.get("revenue") or {}).get("revenue_per_acre", {})
    known = [c for c in dict.fromkeys(_mains(current_years)) if c in revenue]
    if known:
        text = ", ".join(f"{CROPS[c]['name'].lower()} ${revenue[c]}" for c in known)
        items.append({"text": f"Typical gross income per acre in {field['revenue']['state']}: {text} (state yield × US price, 2020+)",
                      "source": "USDA NASS", "confidence": "Measured"})
    if sat and sat.get("smap_season_soil"):
        driest = min(sat["smap_season_soil"], key=lambda r: r["value"])
        items.append({"text": f"Satellite soil moisture was lowest in {driest['year']}: {driest['value']} m³/m³ in May–Sep (root zone)", "source": "NASA SMAP", "confidence": "Measured"})
    return items


def explain(kind, years, current_years, field, scenario) -> dict:
    bare_now = round((1 - covered_share(current_years)) * 12)
    bare_new = round((1 - covered_share(years)) * 12)
    dry_year = field["climate"]["year_types"]["dry"][0]
    texts = {
        "current": {
            "why": "This is what the field has grown in recent years, detected from USDA Cropland Data Layer maps.",
            "benefits": ["Known equipment, markets and workflow"],
            "gaps": ["Satellite crop maps can mislabel single fields — please confirm"],
            "check_locally": ["Is this rotation detected correctly?"],
        },
        "cover": {
            "why": f"Adding a winter cover crop cuts bare soil from about {bare_now} to {bare_new} months a year, when heavy rain hits uncovered ground.",
            "benefits": ["Less soil loss in spring storms", "More organic matter over time", "Roots improve water infiltration"],
            "gaps": ["We do not know your seeding equipment or herbicide program", "Cover crop seed costs vary by region"],
            "check_locally": ["Cover crop termination timing before planting", "Spring water use by the cover crop in dry years", "Possible yield drag for the crop planted right after rye"],
        },
        "diverse": {
            "why": "A third crop breaks pest and disease cycles and adds a legume or small grain that feeds the soil.",
            "benefits": ["Breaks pest cycles", "Spreads work and risk across the year", "Clover adds nitrogen for the next crop"],
            "gaps": ["Local prices and buyers for the added crop"],
            "check_locally": ["Equipment for small grains", "Grain storage and markets nearby"],
        },
        "drought": {
            "why": f"Crops that need less water and are less sensitive to drought (FAO) hold up better in dry years like {dry_year}.",
            "benefits": ["Lower water demand", "Better drought and heat tolerance"],
            "gaps": ["Market price and contracts for the new crop"],
            "check_locally": ["Seed varieties suited to your area", "Feed or grain buyers within hauling distance"],
        },
        "forage": {
            "why": "Alfalfa grows deep roots, fixes nitrogen and gives forage for livestock.",
            "benefits": ["Forage for your animals", "Deep roots and nitrogen for the next crop"],
            "gaps": ["Hay prices and storage"],
            "check_locally": ["Alfalfa needs 800–1600 mm of water per season (FAO) — check irrigation"],
        },
    }
    return {**texts[kind], "evidence": _evidence(field, current_years, scenario)}


# ---------- Головна функція ----------

def build_strategies(field, priorities, constraints, scenario="normal") -> list[dict]:
    current = [[c] for c in field["current_rotation"]["pattern"] if c in CROPS]
    if not current:
        current = [["corn"], ["soybean"]]  # якщо CDL нічого не знайшов — типова сівозміна
    gdd = field["climate"]["gdd_base10"]
    options = [
        ("current", "Current", current),
        ("cover", "A", add_cover_crop(current)),
        ("diverse", "B", add_small_grain_and_legume(current, gdd)),
        ("forage" if constraints.get("livestock") else "drought", "C", drought_tolerant(current, gdd, constraints.get("livestock"))),
    ]
    result = []
    for kind, letter, years in options:
        scores = score(years, field, scenario, constraints)
        result.append({
            "id": letter,
            "is_current": kind == "current",
            "name": label(years),
            "years": years,
            "total_score": total(scores, priorities),
            "scores": scores,
            "bare_months_per_year": round((1 - covered_share(years)) * 12),
            "calendar": calendar(years),
            "explanation": explain(kind, years, current, field, scenario),
        })
    best = max(result, key=lambda s: s["total_score"])
    for strategy in result:
        strategy["best_match"] = strategy is best
    return result
