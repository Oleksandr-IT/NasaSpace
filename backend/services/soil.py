"""USDA SSURGO через Soil Data Access: ґрунт у точці поля.

Це ті самі дані, що показує Web Soil Survey. Ключ не потрібен.
Документація: https://sdmdataaccess.sc.egov.usda.gov/
"""
import requests

SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

# Беремо головний компонент ґрунту (найбільший відсоток) і його верхній шар (глибина 0 см)
QUERY = """
SELECT TOP 1 l.areaname, mu.muname, c.compname, c.comppct_r, c.slope_r, c.hydgrp, c.drainagecl,
       h.om_r, h.awc_r, h.kwfact, h.sandtotal_r, h.claytotal_r
FROM legend l
JOIN mapunit mu ON mu.lkey = l.lkey
JOIN component c ON c.mukey = mu.mukey
LEFT JOIN chorizon h ON h.cokey = c.cokey AND h.hzdept_r = 0
WHERE mu.mukey IN (SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT({lon} {lat})'))
  AND c.majcompflag = 'Yes'
ORDER BY c.comppct_r DESC
"""


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_soil(lat: float, lon: float) -> dict | None:
    body = {"format": "JSON+COLUMNNAME", "query": QUERY.format(lat=lat, lon=lon)}
    response = requests.post(SDA_URL, json=body, timeout=60)
    response.raise_for_status()
    table = response.json().get("Table")
    if not table or len(table) < 2:
        return None  # точка поза зйомкою SSURGO (вода, місто тощо)
    row = dict(zip(table[0], table[1]))
    return {
        "source": "USDA SSURGO",
        "area": row["areaname"],
        "map_unit": row["muname"],
        "name": row["compname"],
        "slope_pct": _number(row["slope_r"]),
        "hydro_group": row["hydgrp"],
        "drainage": row["drainagecl"],
        "organic_matter_pct": _number(row["om_r"]),
        "water_capacity_cm_per_cm": _number(row["awc_r"]),
        "k_factor": _number(row["kwfact"]),  # схильність до водної ерозії, 0.02–0.69
        "sand_pct": _number(row["sandtotal_r"]),
        "clay_pct": _number(row["claytotal_r"]),
    }
