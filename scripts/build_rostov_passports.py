"""
Reproducible ETL for GeoAtlas — Geographical Passport of Rostov Oblast (Stage 1).

Builds `public/maps/rostov_passports.json` from:
1. Local top-level municipal boundaries (`Py_Geo/shape/rostov/raion.shp`, 55 MO, OSM / ODbL).
2. Rosstat BDMO processed datasets (`v20260928`) published by "Если быть точным" (CC BY 4.0).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SHP_PATH = BASE_DIR / "Py_Geo" / "shape" / "rostov" / "raion.shp"
DEFAULT_OUTPUT_PATH = BASE_DIR / "public" / "maps" / "rostov_passports.json"

# Local Albers Equal-Area projection centered on Rostov Oblast for accurate km^2 area calculation
ROSTOV_EQUAL_AREA_CRS = (
    "+proj=aea +lat_1=44 +lat_2=50 +lat_0=47 +lon_0=41 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

DATASET_VERSION = "v20260928"
DATASET_UPDATED_AT = "2026-09-28"

INDICATORS_SPEC: List[Dict[str, Any]] = [
    {
        "key": "population_avg",
        "code": "41.8112013",
        "name": "Среднегодовая численность постоянного населения",
        "unit": "Человек",
        "url": "https://storage.yandexcloud.net/tochno-st-catalog/Rosstat/data_bdmo_118_v20260928/indicators/section41/data_Y48112013_112_v20260928.zip",
        "slice_filters": {},
        "is_nominal": False,
        "allow_negative": False,
    },
    {
        "key": "births",
        "code": "31.8112003",
        "name": "Число родившихся (без мертворожденных)",
        "unit": "Человек",
        "url": "https://storage.yandexcloud.net/tochno-st-catalog/Rosstat/data_bdmo_118_v20260928/indicators/section31/data_Y48112003_112_v20260928.zip",
        "slice_filters": {},
        "is_nominal": False,
        "allow_negative": False,
    },
    {
        "key": "deaths",
        "code": "31.8112001",
        "name": "Число умерших",
        "unit": "Человек",
        "url": "https://storage.yandexcloud.net/tochno-st-catalog/Rosstat/data_bdmo_118_v20260928/indicators/section31/data_Y48112001_112_v20260928.zip",
        "slice_filters": {},
        "is_nominal": False,
        "allow_negative": False,
    },
    {
        "key": "investments_per_capita",
        "code": "41.8109003",
        "name": "Объем инвестиций в основной капитал (за исключением бюджетных средств) в расчете на одного человека",
        "unit": "Рубль",
        "url": "https://storage.yandexcloud.net/tochno-st-catalog/Rosstat/data_bdmo_118_v20260928/indicators/section41/data_Y48109003_112_v20260928.zip",
        "slice_filters": {},
        "is_nominal": True,
        "allow_negative": False,
    },
    {
        "key": "agriculture_output",
        "code": "7.8007010",
        "name": "Продукция сельского хозяйства (в фактически действовавших ценах)",
        "unit": "Тысяча рублей",
        "url": "https://storage.yandexcloud.net/tochno-st-catalog/Rosstat/data_bdmo_118_v20260928/indicators/section7/data_Y48007010_112_v20260928.zip",
        "slice_filters": {"kategor": "Хозяйства всех категорий"},
        "is_nominal": True,
        "allow_negative": False,
    },
    {
        "key": "housing_commissioned",
        "code": "37.8010001",
        "name": "Введено в действие жилых домов",
        "unit": "Квадратный метр общей площади",
        "url": "https://storage.yandexcloud.net/tochno-st-catalog/Rosstat/data_bdmo_118_v20260928/indicators/section37/data_Y48010001_112_v20260928.zip",
        "slice_filters": {},
        "is_nominal": False,
        "allow_negative": False,
    },
]


def normalize_oktmo8(raw_oktmo: Any) -> str:
    digits = "".join(ch for ch in str(raw_oktmo or "").strip() if ch.isdigit())
    return digits[:8]


def parse_numeric_value(raw_val: Any) -> Optional[float]:
    if raw_val is None:
        return None
    text = str(raw_val).strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    if not text or text.lower() in {"na", "nan", "null", "-", "—"}:
        return None
    val = float(text)
    if val.is_integer():
        return int(val)
    return round(val, 2)


def classify_territory_type(name: str) -> str:
    low = name.lower()
    if "городской округ" in low:
        return "Городской округ"
    if "район" in low:
        return "Муниципальный район"
    return "Муниципальное образование"


def load_rostov_territories(shp_path: Path = DEFAULT_SHP_PATH) -> Dict[str, Dict[str, Any]]:
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf_eq = gdf.to_crs(ROSTOV_EQUAL_AREA_CRS)

    territories: Dict[str, Dict[str, Any]] = {}
    for idx, row in gdf.iterrows():
        ok8 = normalize_oktmo8(row.get("oktmo"))
        if len(ok8) != 8:
            raise ValueError(f"Invalid OKTMO in shapefile row {idx}: {row.get('oktmo')!r}")
        if ok8 in territories:
            raise ValueError(f"Duplicate OKTMO in shapefile: {ok8}")
        name = str(row.get("NAME") or "").strip()
        area_km2 = round(float(gdf_eq.loc[idx, "geometry"].area) / 1_000_000.0, 2)
        territories[ok8] = {
            "oktmo": ok8,
            "name": name,
            "type": classify_territory_type(name),
            "area_km2": area_km2,
            "indicators": {},
        }

    if len(territories) != 55:
        raise ValueError(f"Expected 55 top-level Rostov territories, found {len(territories)}")
    return territories


def _load_zip_bytes(url: str, cache_dir: Optional[Path] = None) -> bytes:
    filename = url.rsplit("/", 1)[-1]
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached = cache_dir / filename
        if cached.exists() and cached.stat().st_size > 0:
            return cached.read_bytes()

    req = urllib.request.Request(url, headers={"User-Agent": "GeoAtlas-ETL/1.5"})
    data = urllib.request.urlopen(req, timeout=60).read()
    if cache_dir is not None:
        (cache_dir / filename).write_bytes(data)
    return data


def parse_indicator_zip(
    zip_bytes: bytes,
    spec: Dict[str, Any],
    valid_oktmos: set[str],
) -> Tuple[Dict[str, Dict[str, Optional[float]]], str]:
    """Extracts {oktmo8: {year_str: value_or_None}} for top-level Rostov MO."""
    series_by_oktmo: Dict[str, Dict[str, Optional[float]]] = {ok: {} for ok in valid_oktmos}
    observed_unit = spec["unit"]

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV file found in archive for {spec['code']}")
        with zf.open(csv_names[0]) as cf:
            reader = csv.DictReader(io.TextIOWrapper(cf, encoding="utf-8", errors="replace"), delimiter=";")
            for row in reader:
                reg = (row.get("region_name") or "").strip().lower()
                ok_raw = str(row.get("oktmo") or "").strip()
                if "ростовск" not in reg and not ok_raw.startswith("60"):
                    continue
                mun_level = (row.get("mun_level") or "").strip()
                if mun_level != "Муниципальное образование верхнего уровня":
                    continue

                # Apply deterministic slice filters (e.g. kategor='Хозяйства всех категорий')
                skip = False
                for col, expected in spec.get("slice_filters", {}).items():
                    if (row.get(col) or "").strip() != expected:
                        skip = True
                        break
                if skip:
                    continue

                ok8 = normalize_oktmo8(ok_raw)
                if ok8 not in valid_oktmos:
                    raise ValueError(f"Unexpected top-level Rostov OKTMO {ok8} ({row.get('municipality')}) in {spec['code']}")

                year = str(row.get("year") or "").strip()
                if not year.isdigit():
                    continue

                if year in series_by_oktmo[ok8]:
                    raise ValueError(f"Duplicate observation for ({ok8}, {spec['code']}, {year})")

                val = parse_numeric_value(row.get("indicator_value"))
                if val is not None and not spec.get("allow_negative", False) and val < 0:
                    raise ValueError(f"Unexpected negative value {val} for ({ok8}, {spec['code']}, {year})")

                row_unit = (row.get("indicator_unit") or "").strip()
                if row_unit:
                    observed_unit = row_unit
                series_by_oktmo[ok8][year] = val

    return series_by_oktmo, observed_unit


def build_passports(
    shp_path: Path = DEFAULT_SHP_PATH,
    cache_dir: Optional[Path] = None,
    zip_overrides: Optional[Dict[str, bytes]] = None,
) -> Dict[str, Any]:
    territories = load_rostov_territories(shp_path)
    valid_oktmos = set(territories.keys())
    indicators_meta: Dict[str, Dict[str, Any]] = {}

    for spec in INDICATORS_SPEC:
        key = spec["key"]
        if zip_overrides and key in zip_overrides:
            zbytes = zip_overrides[key]
        else:
            zbytes = _load_zip_bytes(spec["url"], cache_dir=cache_dir)

        by_oktmo, observed_unit = parse_indicator_zip(zbytes, spec, valid_oktmos)
        if observed_unit != spec["unit"]:
            raise ValueError(f"Unit mismatch for {spec['code']}: expected {spec['unit']!r}, got {observed_unit!r}")

        all_years = sorted({y for s in by_oktmo.values() for y in s.keys()})
        latest_year = all_years[-1] if all_years else None
        covered_latest = sum(
            1 for ok in valid_oktmos
            if latest_year and by_oktmo[ok].get(latest_year) is not None
        )

        for ok in valid_oktmos:
            sorted_series = {y: by_oktmo[ok][y] for y in sorted(by_oktmo[ok].keys())}
            non_null_years = [y for y, v in sorted_series.items() if v is not None]
            t_latest_y = non_null_years[-1] if non_null_years else None
            t_latest_v = sorted_series[t_latest_y] if t_latest_y else None
            territories[ok]["indicators"][key] = {
                "latest_year": int(t_latest_y) if t_latest_y else None,
                "latest_value": t_latest_v,
                "series": sorted_series,
            }

        indicators_meta[key] = {
            "code": spec["code"],
            "name": spec["name"],
            "unit": spec["unit"],
            "years": [int(y) for y in all_years],
            "latest_year": int(latest_year) if latest_year else None,
            "coverage_latest": covered_latest,
            "total_territories": len(valid_oktmos),
            "is_nominal": bool(spec["is_nominal"]),
            "slice_filters": spec["slice_filters"],
            "source_url": spec["url"],
        }

    # Derived indicators: population_density & natural_growth
    density_years = set()
    growth_years = set()
    for ok, t in territories.items():
        area = t["area_km2"]
        pop_series = t["indicators"]["population_avg"]["series"]
        dens_series: Dict[str, Optional[float]] = {}
        for y, pval in pop_series.items():
            dval = round(float(pval) / area, 2) if (pval is not None and area > 0) else None
            dens_series[y] = dval
            if dval is not None:
                density_years.add(y)
        d_non_null = [y for y, v in dens_series.items() if v is not None]
        d_ly = d_non_null[-1] if d_non_null else None
        t["indicators"]["population_density"] = {
            "latest_year": int(d_ly) if d_ly else None,
            "latest_value": dens_series[d_ly] if d_ly else None,
            "series": dens_series,
        }

        b_series = t["indicators"]["births"]["series"]
        d_series = t["indicators"]["deaths"]["series"]
        g_series: Dict[str, Optional[int]] = {}
        for y in sorted(set(b_series.keys()) | set(d_series.keys())):
            bv, dv = b_series.get(y), d_series.get(y)
            gv = int(bv - dv) if (bv is not None and dv is not None) else None
            g_series[y] = gv
            if gv is not None:
                growth_years.add(y)
        g_non_null = [y for y, v in g_series.items() if v is not None]
        g_ly = g_non_null[-1] if g_non_null else None
        t["indicators"]["natural_growth"] = {
            "latest_year": int(g_ly) if g_ly else None,
            "latest_value": g_series[g_ly] if g_ly else None,
            "series": g_series,
        }

    dens_sorted = sorted(density_years)
    growth_sorted = sorted(growth_years)
    indicators_meta["population_density"] = {
        "code": "DERIVED:41.8112013/AREA",
        "name": "Плотность населения (расчётная)",
        "unit": "Человек на кв. км",
        "years": [int(y) for y in dens_sorted],
        "latest_year": int(dens_sorted[-1]) if dens_sorted else None,
        "coverage_latest": sum(1 for t in territories.values() if t["indicators"]["population_density"]["latest_value"] is not None),
        "total_territories": len(valid_oktmos),
        "is_nominal": False,
        "derived_formula": "population_avg / area_km2",
    }
    indicators_meta["natural_growth"] = {
        "code": "DERIVED:31.8112003-31.8112001",
        "name": "Естественный прирост (убыль) населения (расчётный)",
        "unit": "Человек",
        "years": [int(y) for y in growth_sorted],
        "latest_year": int(growth_sorted[-1]) if growth_sorted else None,
        "coverage_latest": sum(1 for t in territories.values() if t["indicators"]["natural_growth"]["latest_value"] is not None),
        "total_territories": len(valid_oktmos),
        "is_nominal": False,
        "derived_formula": "births - deaths",
    }

    sorted_territories = {ok: territories[ok] for ok in sorted(territories.keys())}
    return {
        "metadata": {
            "region": "Ростовская область",
            "region_code": "60",
            "total_territories": len(sorted_territories),
            "dataset_version": DATASET_VERSION,
            "updated_at": DATASET_UPDATED_AT,
            "license": "CC BY 4.0",
            "attribution": "«Муниципальная статистика России с 2005 года» // Росстат; обработка: «Если быть точным», 2024. URL: https://doi.org/10.48612/tochno/bdmo",
            "catalog_url": "https://tochno.st/datasets/bdmo",
            "geometry_source": "Py_Geo/shape/rostov/raion.shp (OpenStreetMap, ODbL 1.0)",
            "area_projection": ROSTOV_EQUAL_AREA_CRS,
            "missing_value_policy": "Пропущенные значения сохраняются как null (не заменяются нулями).",
            "monetary_values_note": "Денежные показатели (инвестиции на душу и продукция сельского хозяйства) приведены в номинальных ценах соответствующих лет без дефлирования.",
            "indicators": indicators_meta,
        },
        "territories": sorted_territories,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GeoAtlas Rostov Oblast municipal passports JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--cache-dir", type=Path, default=None)
    args = parser.parse_args()

    payload = build_passports(cache_dir=args.cache_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = args.output.stat().st_size / 1024.0
    print(f"Wrote {args.output} ({size_kb:.1f} KB), territories={payload['metadata']['total_territories']}")
    for k, meta in payload["metadata"]["indicators"].items():
        print(f"  {k}: latest={meta['latest_year']}, coverage={meta['coverage_latest']}/{meta['total_territories']}")


if __name__ == "__main__":
    main()
