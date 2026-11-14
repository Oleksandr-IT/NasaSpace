"""NASA POWER: щоденний клімат для точки поля і метрики на його основі.

API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
Ключ не потрібен.
"""
from datetime import date
from statistics import mean, median

import requests

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ["T2M_MAX", "T2M_MIN", "T2M", "PRECTOTCORR", "GWETROOT"]
START_YEAR = 1995
END_YEAR = 2025
MISSING = -999


def fetch_daily(lat: float, lon: float) -> dict:
    """Завантажує щоденні дані за 1995–2025 роки. Повертає {параметр: {"YYYYMMDD": значення}}."""
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": f"{START_YEAR}0101",
        "end": f"{END_YEAR}1231",
        "format": "JSON",
    }
    response = requests.get(POWER_URL, params=params, timeout=120)
    response.raise_for_status()
    return response.json()["properties"]["parameter"]


def _to_days(raw: dict) -> list[dict]:
    """Перетворює відповідь POWER у список днів: [{"date": date, "tmax": .., ...}]."""
    days = []
    for key in raw["T2M"]:
        day = {
            "date": date(int(key[:4]), int(key[4:6]), int(key[6:])),
            "tmax": raw["T2M_MAX"][key],
            "tmin": raw["T2M_MIN"][key],
            "tavg": raw["T2M"][key],
            "rain": raw["PRECTOTCORR"][key],
            "soil": raw["GWETROOT"][key],
        }
        if MISSING not in day.values():
            days.append(day)
    if not days:  # над водою немає даних про ґрунт (GWETROOT = -999)
        raise ValueError("no land data here — the point looks like water")
    return days


def _trend_per_decade(years: list[int], values: list[float], digits: int = 2) -> float:
    """Нахил лінійної регресії (метод найменших квадратів), переведений у «за 10 років»."""
    x_mean, y_mean = mean(years), mean(values)
    top = sum((x - x_mean) * (y - y_mean) for x, y in zip(years, values))
    bottom = sum((x - x_mean) ** 2 for x in years)
    return round(top / bottom * 10, digits) if bottom else 0.0


def _year_stats(days: list[dict]) -> dict:
    """Метрики одного року."""
    spring = [d for d in days if d["date"].month < 7 and d["tmin"] <= 0]
    fall = [d for d in days if d["date"].month >= 7 and d["tmin"] <= 0]
    last_frost = spring[-1]["date"] if spring else None
    first_frost = fall[0]["date"] if fall else None
    season = [d for d in days if 5 <= d["date"].month <= 9]  # травень–вересень
    summer = [d for d in days if 6 <= d["date"].month <= 8]  # червень–серпень
    return {
        "last_frost_doy": last_frost.timetuple().tm_yday if last_frost else None,
        "first_frost_doy": first_frost.timetuple().tm_yday if first_frost else None,
        "frost_free_days": (first_frost - last_frost).days if last_frost and first_frost else None,
        # GDD: сума (середня температура - 10 °C) за квітень–жовтень
        "gdd": sum(max(0, d["tavg"] - 10) for d in days if 4 <= d["date"].month <= 10),
        "season_rain": sum(d["rain"] for d in season),
        "heat_days": sum(1 for d in days if d["tmax"] > 35),
        "heavy_rain_days": sum(1 for d in days if d["rain"] > 25),
        "summer_tmax": mean(d["tmax"] for d in summer),
        "season_soil": mean(d["soil"] for d in season),
    }


def _doy_to_text(doy: float) -> str:
    """Номер дня в році -> 'Apr 28'."""
    day = date.fromordinal(date(2001, 1, 1).toordinal() + round(doy) - 1)
    return day.strftime("%b %d").replace(" 0", " ")


def climate_summary(raw: dict) -> dict:
    """Головна функція: з сирих даних POWER рахує все, що показує екран «Conditions»."""
    days = _to_days(raw)
    years = sorted({d["date"].year for d in days})
    per_year = {y: _year_stats([d for d in days if d["date"].year == y]) for y in years}

    def values(name):
        return [per_year[y][name] for y in years if per_year[y][name] is not None]

    last_frosts = values("last_frost_doy")
    may_5 = date(2001, 5, 5).timetuple().tm_yday
    late_frost_years = sum(1 for doy in last_frosts if doy > may_5)

    # Типовий рік: середнє по кожному місяцю за всі роки
    monthly = []
    for month in range(1, 13):
        month_days = [d for d in days if d["date"].month == month]
        monthly.append({
            "month": month,
            "tavg": round(mean(d["tavg"] for d in month_days), 1),
            "rain_mm": round(sum(d["rain"] for d in month_days) / len(years)),
            "soil_wetness": round(mean(d["soil"] for d in month_days), 2),
        })

    # Типи років за опадами сезону: 20% найсухіших і 20% найвологіших
    by_rain = sorted(years, key=lambda y: per_year[y]["season_rain"])
    n = max(1, len(years) // 5)
    year_types = {"dry": by_rain[:n], "wet": by_rain[-n:]}

    def series(name, digits=1):
        return [{"year": y, "value": round(per_year[y][name], digits)} for y in years]

    # На півдні (Флорида, Техас) заморозків майже немає — тоді сезон без заморозків = весь рік
    frost_years = values("frost_free_days")
    if len(frost_years) >= len(years) / 2:
        frost_free = round(median(frost_years))
        last_frost, first_frost = _doy_to_text(median(last_frosts)), _doy_to_text(median(values("first_frost_doy")))
    else:
        frost_free, last_frost, first_frost = 365, None, None

    return {
        "source": f"NASA POWER {years[0]}-{years[-1]}",
        "years": len(years),
        "frost_free_days": frost_free,
        "last_spring_frost": last_frost,
        "first_fall_frost": first_frost,
        "late_frost_years_per_10": round(late_frost_years / len(years) * 10),
        "gdd_base10": round(median(values("gdd"))),
        "season_rain_mm": round(median(values("season_rain"))),
        "heat_days_35c": round(mean(values("heat_days")), 1),
        "heavy_rain_days_25mm": round(mean(values("heavy_rain_days")), 1),
        "season_soil_wetness": round(mean(values("season_soil")), 2),
        "monthly": monthly,
        "trends": {
            "summer_tmax_c_per_decade": _trend_per_decade(years, values("summer_tmax")),
            "season_rain_mm_per_decade": _trend_per_decade(years, values("season_rain")),
            "soil_wetness_per_decade": _trend_per_decade(years, values("season_soil"), 3),
        },
        "series": {
            "summer_tmax": series("summer_tmax"),
            "season_rain": series("season_rain", 0),
            "season_soil": series("season_soil", 2),
        },
        "year_types": year_types,
        "dry_year_rain_mm": round(mean(per_year[y]["season_rain"] for y in year_types["dry"])),
        "wet_year_rain_mm": round(mean(per_year[y]["season_rain"] for y in year_types["wet"])),
    }
