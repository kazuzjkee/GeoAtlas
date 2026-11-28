"""
GeoAtlas — Data Freshness & Quality Monitor.

Centralized registry, local integrity/statistical validation, and lightweight
remote metadata freshness checks without downloading large archives.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent

DATA_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "rostov_passports",
        "name": "Муниципальные паспорта Ростовской области",
        "kind": "passport_json",
        "region": "Ростовская область",
        "local_path": "public/maps/rostov_passports.json",
        "geometry_ref": "Py_Geo/shape/rostov/raion.shp",
        "expected_territories": 55,
        "source": "БД ПМО Росстата / «Если быть точным»",
        "source_url": "https://tochno.st/datasets/bdmo",
        "owner_org": "Росстат; обработка: «Если быть точным»",
        "license": "CC BY 4.0",
        "attribution": "«Муниципальная статистика России с 2005 года» // Росстат; обработка: «Если быть точным», 2024",
        "declared_version": "v20260928",
        "published_at": "2026-09-28",
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "tochno_bdmo",
    },
    {
        "id": "krasnodar_passports",
        "name": "Муниципальные паспорта Краснодарского края",
        "kind": "passport_json",
        "region": "Краснодарский край",
        "local_path": "public/maps/krasnodar_passports.json",
        "geometry_ref": "Py_Geo/shape/krasnodar/boundary-3857.shp",
        "legacy_oktmo_map": {
            "03703000": "03501000",
            "03709000": "03504000",
            "03632000": "03532000",
            "03641000": "03541000",
            "03655000": "03555000",
        },
        "expected_territories": 44,
        "source": "БД ПМО Росстата / «Если быть точным»",
        "source_url": "https://tochno.st/datasets/bdmo",
        "owner_org": "Росстат; обработка: «Если быть точным»",
        "license": "CC BY 4.0",
        "attribution": "«Муниципальная статистика России с 2005 года» // Росстат; обработка: «Если быть точным», 2024",
        "declared_version": "v20260928",
        "published_at": "2026-09-28",
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "tochno_bdmo",
    },
    {
        "id": "rostov_boundaries",
        "name": "Границы муниципальных образований Ростовской области",
        "kind": "shapefile",
        "region": "Ростовская область",
        "local_path": "Py_Geo/shape/rostov/raion.shp",
        "expected_territories": 55,
        "require_oktmo": True,
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/",
        "owner_org": "Сообщество OpenStreetMap",
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "declared_version": "osm-local-2026",
        "published_at": None,
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "static_local",
    },
    {
        "id": "rostov_hydrography",
        "name": "Гидрографическая сеть Ростовской области",
        "kind": "shapefile",
        "region": "Ростовская область",
        "local_path": "Py_Geo/shape/rostov/water-line.shp",
        "expected_territories": None,
        "require_oktmo": False,
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/",
        "owner_org": "Сообщество OpenStreetMap",
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "declared_version": "osm-local-2026",
        "published_at": None,
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "static_local",
    },
    {
        "id": "krasnodar_boundaries",
        "name": "Границы муниципальных образований Краснодарского края",
        "kind": "shapefile",
        "region": "Краснодарский край",
        "local_path": "Py_Geo/shape/krasnodar/boundary-3857.shp",
        "expected_territories": 44,
        "require_oktmo": True,
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/",
        "owner_org": "Сообщество OpenStreetMap",
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "declared_version": "osm-local-2026",
        "published_at": None,
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "static_local",
    },
    {
        "id": "krasnodar_hydrography",
        "name": "Гидрографическая сеть Краснодарского края",
        "kind": "shapefile",
        "region": "Краснодарский край",
        "local_path": "Py_Geo/shape/krasnodar/water-line.shp",
        "expected_territories": None,
        "require_oktmo": False,
        "source": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/",
        "owner_org": "Сообщество OpenStreetMap",
        "license": "ODbL 1.0",
        "attribution": "© OpenStreetMap contributors",
        "declared_version": "osm-local-2026",
        "published_at": None,
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "static_local",
    },
    {
        "id": "russia_unified_boundaries",
        "name": "Границы субъектов Российской Федерации (GADM / OSM)",
        "kind": "shapefile_dir",
        "region": "Российская Федерация",
        "local_path": "Py_Geo/shape/russia_unified",
        "expected_territories": None,
        "source": "GADM / OpenStreetMap",
        "source_url": "https://gadm.org/",
        "owner_org": "GADM / OpenStreetMap",
        "license": "Academic / ODbL 1.0",
        "attribution": "GADM & OpenStreetMap contributors",
        "declared_version": "local-2026",
        "published_at": None,
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "static_local",
    },
    {
        "id": "compiled_maps_metadata",
        "name": "Предкомпилированные метаданные региональных карт",
        "kind": "meta_dir",
        "region": "Все регионы GeoAtlas",
        "local_path": "public/maps",
        "expected_territories": None,
        "source": "GeoAtlas Compiler (main.py)",
        "source_url": "https://geoatlas.sfedu.ru/",
        "owner_org": "GeoAtlas / ИНоЗ ЮФУ",
        "license": "CC BY 4.0 / ODbL 1.0",
        "attribution": "GeoAtlas / ИНоЗ ЮФУ",
        "declared_version": "1.5",
        "published_at": None,
        "last_downloaded_at": "2026-11-28",
        "remote_check_type": "static_local",
    },
]

_REQUIRED_REGISTRY_FIELDS = (
    "id", "name", "region", "local_path", "source", "source_url", "owner_org", "license", "attribution"
)


def compute_sha256(file_path: Path) -> Optional[str]:
    if not file_path.exists() or not file_path.is_file():
        return None
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_oktmo8(raw: Any) -> str:
    digits = "".join(ch for ch in str(raw or "").strip() if ch.isdigit())
    return digits[:8]


def _check_remote_tochno_bdmo(declared_version: str) -> Dict[str, Any]:
    """Lightweight metadata check on https://tochno.st/datasets/bdmo (never downloads archives)."""
    url = "https://tochno.st/datasets/bdmo"
    req = urllib.request.Request(url, headers={"User-Agent": "GeoAtlas-QualityMonitor/1.5"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            html = resp.read(160000).decode("utf-8", errors="replace")
        versions = sorted(set(re.findall(r"v(20\d{6})", html)))
        remote_ver = f"v{versions[-1]}" if versions else None
        if not remote_ver:
            return {
                "freshness_status": "unknown",
                "remote_version": None,
                "newer_available": False,
                "etag": headers.get("etag"),
                "last_modified": headers.get("last-modified"),
                "note": "Версия каталога на странице источника не распознана.",
            }
        if remote_ver > declared_version:
            return {
                "freshness_status": "stale",
                "remote_version": remote_ver,
                "newer_available": True,
                "etag": headers.get("etag"),
                "last_modified": headers.get("last-modified"),
                "note": f"Найдена более новая версия источника: {remote_ver} (текущая {declared_version}).",
            }
        return {
            "freshness_status": "fresh",
            "remote_version": remote_ver,
            "newer_available": False,
            "etag": headers.get("etag"),
            "last_modified": headers.get("last-modified"),
            "note": f"Подтверждена актуальная версия источника: {remote_ver}.",
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "freshness_status": "unknown",
            "remote_version": None,
            "newer_available": False,
            "note": f"Внешний источник временно недоступен ({exc}).",
        }


def _validate_passport_json(
    entry: Dict[str, Any],
    base_dir: Path,
) -> Dict[str, Any]:
    file_path = base_dir / entry["local_path"]
    errors: List[str] = []
    warnings: List[str] = []
    indicator_reports: List[Dict[str, Any]] = []

    if not file_path.exists():
        return {
            "check_result": "fail",
            "errors": [f"Отсутствует файл набора данных: {entry['local_path']}"],
            "warnings": [],
            "indicators": [],
            "latest_stat_year": None,
            "coverage_pct": 0.0,
            "missing_total": 0,
            "generated_at": None,
            "actual_version": None,
            "territory_count": 0,
        }

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "check_result": "fail",
            "errors": [f"Ошибка чтения JSON: {exc}"],
            "warnings": [],
            "indicators": [],
            "latest_stat_year": None,
            "coverage_pct": 0.0,
            "missing_total": 0,
            "generated_at": None,
            "actual_version": None,
            "territory_count": 0,
        }

    meta = payload.get("metadata") or {}
    territories = payload.get("territories") or {}
    actual_version = meta.get("dataset_version")
    generated_at = meta.get("updated_at")

    if entry.get("declared_version") and actual_version and actual_version != entry["declared_version"]:
        warnings.append(
            f"Несовпадение версии: в реестре {entry['declared_version']}, в файле {actual_version}."
        )

    for req_meta in ("license", "attribution", "dataset_version", "updated_at"):
        if not meta.get(req_meta):
            errors.append(f"Отсутствует обязательное метаполе metadata.{req_meta}")

    expected_n = entry.get("expected_territories")
    if expected_n is not None and len(territories) != expected_n:
        errors.append(f"Ожидалось {expected_n} территорий, найдено {len(territories)}")

    # Validate 8-digit OKTMO uniqueness & geometry alignment
    seen_oktmos = set()
    for ok_key, t_obj in territories.items():
        ok8 = _normalize_oktmo8(t_obj.get("oktmo") or ok_key)
        if len(ok8) != 8 or ok8 in seen_oktmos:
            errors.append(f"Некорректный или дублирующий ОКТМО: {ok_key!r}")
        seen_oktmos.add(ok8)

    geom_rel = entry.get("geometry_ref")
    if geom_rel:
        geom_path = base_dir / geom_rel
        if not geom_path.exists():
            warnings.append(f"Связанный файл геометрии не найден: {geom_rel}")
        else:
            try:
                gdf = gpd.read_file(geom_path)
                legacy_map = entry.get("legacy_oktmo_map") or {}
                shp_oktmos = {
                    legacy_map.get(_normalize_oktmo8(ok), _normalize_oktmo8(ok))
                    for ok in gdf["oktmo"]
                }
                if shp_oktmos != seen_oktmos:
                    errors.append(
                        f"Расхождение ОКТМО с геометрией ({len(shp_oktmos)} в SHP vs {len(seen_oktmos)} в JSON)"
                    )
            except Exception as exc:
                warnings.append(f"Не удалось проверить геометрию {geom_rel}: {exc}")

    # Per-indicator checks
    ind_meta_map = meta.get("indicators") or {}
    total_missing = 0
    all_latest_years: List[int] = []
    coverage_values: List[float] = []
    non_negative_keys = {
        "population_avg", "births", "deaths", "investments_per_capita",
        "agriculture_output", "housing_commissioned", "population_density",
    }

    for ind_key, ind_meta in ind_meta_map.items():
        years_list: List[int] = []
        with_data = 0
        missing_latest = 0
        latest_yr = ind_meta.get("latest_year")
        if isinstance(latest_yr, int):
            all_latest_years.append(latest_yr)

        for ok_key, t_obj in territories.items():
            t_ind = (t_obj.get("indicators") or {}).get(ind_key) or {}
            series = t_ind.get("series") or {}
            for yr_str, val in series.items():
                if str(yr_str).isdigit():
                    years_list.append(int(yr_str))
                if val is not None and ind_key in non_negative_keys and float(val) < 0:
                    errors.append(f"Отрицательное значение {val} в {ok_key}/{ind_key}/{yr_str}")
            if latest_yr is not None:
                lv = series.get(str(latest_yr))
                if lv is None:
                    missing_latest += 1
                else:
                    with_data += 1

        # Derived consistency checks
        if ind_key == "natural_growth":
            for ok_key, t_obj in territories.items():
                inds = t_obj.get("indicators") or {}
                bs = (inds.get("births") or {}).get("series") or {}
                ds = (inds.get("deaths") or {}).get("series") or {}
                gs = (inds.get("natural_growth") or {}).get("series") or {}
                for yr_str in set(bs) & set(ds):
                    if bs[yr_str] is not None and ds[yr_str] is not None:
                        if gs.get(yr_str) != bs[yr_str] - ds[yr_str]:
                            errors.append(f"Несогласованный расчёт natural_growth для {ok_key}/{yr_str}")
                            break

        expected_cnt = len(territories) if expected_n is None else expected_n
        cov_pct = round((with_data / expected_cnt) * 100.0, 1) if expected_cnt > 0 else 0.0
        coverage_values.append(cov_pct)
        total_missing += missing_latest
        if missing_latest > 0:
            warnings.append(f"Показатель {ind_key}: пропуски за {latest_yr} г. у {missing_latest} МО")

        indicator_reports.append({
            "key": ind_key,
            "code": ind_meta.get("code", "—"),
            "name": ind_meta.get("name", ind_key),
            "unit": ind_meta.get("unit", "—"),
            "first_year": min(years_list) if years_list else None,
            "latest_year": latest_yr,
            "territories_with_data": with_data,
            "expected_territories": expected_cnt,
            "missing_count": missing_latest,
            "coverage_pct": cov_pct,
            "source": entry["source"],
            "derived_formula": ind_meta.get("derived_formula"),
        })

    avg_cov = round(sum(coverage_values) / len(coverage_values), 1) if coverage_values else 0.0
    check_res = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "check_result": check_res,
        "errors": errors,
        "warnings": warnings,
        "indicators": indicator_reports,
        "latest_stat_year": max(all_latest_years) if all_latest_years else None,
        "coverage_pct": avg_cov,
        "missing_total": total_missing,
        "generated_at": generated_at,
        "actual_version": actual_version,
        "territory_count": len(territories),
    }


def _validate_spatial_entry(entry: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    target = base_dir / entry["local_path"]
    errors: List[str] = []
    warnings: List[str] = []
    territory_count = 0

    if not target.exists():
        return {
            "check_result": "fail",
            "errors": [f"Путь не найден: {entry['local_path']}"],
            "warnings": [],
            "indicators": [],
            "latest_stat_year": None,
            "coverage_pct": 0.0,
            "missing_total": 0,
            "generated_at": None,
            "actual_version": entry.get("declared_version"),
            "territory_count": 0,
        }

    if entry["kind"] == "shapefile":
        try:
            gdf = gpd.read_file(target)
            territory_count = len(gdf)
            exp = entry.get("expected_territories")
            if exp is not None and territory_count != exp:
                errors.append(f"Ожидалось {exp} объектов, найдено {territory_count}")
            if entry.get("require_oktmo"):
                if "oktmo" not in gdf.columns:
                    errors.append("Отсутствует обязательный атрибут oktmo")
                else:
                    null_ok = int(gdf["oktmo"].isna().sum())
                    if null_ok > 0:
                        errors.append(f"Пропущен код ОКТМО у {null_ok} объектов")
        except Exception as exc:
            errors.append(f"Ошибка чтения Shapefile: {exc}")
    elif entry["kind"] == "shapefile_dir":
        shps = list(target.glob("*.shp"))
        territory_count = len(shps)
        if not shps:
            errors.append("В каталоге не найдены файлы .shp")
    elif entry["kind"] == "meta_dir":
        metas = list(target.glob("*_meta.json"))
        territory_count = len(metas)
        if not metas:
            errors.append("Не найдены файлы *_meta.json")

    cov_pct = 100.0 if not errors else 0.0
    return {
        "check_result": "fail" if errors else ("warn" if warnings else "pass"),
        "errors": errors,
        "warnings": warnings,
        "indicators": [],
        "latest_stat_year": None,
        "coverage_pct": cov_pct,
        "missing_total": 0,
        "generated_at": entry.get("last_downloaded_at"),
        "actual_version": entry.get("declared_version"),
        "territory_count": territory_count,
    }


def evaluate_dataset(
    entry: Dict[str, Any],
    base_dir: Path = BASE_DIR,
    check_remote: bool = False,
    remote_checker: Any = None,
) -> Dict[str, Any]:
    missing_meta = [f for f in _REQUIRED_REGISTRY_FIELDS if not entry.get(f)]
    file_path = base_dir / entry["local_path"]
    is_file = file_path.exists() and file_path.is_file()
    size_bytes = file_path.stat().st_size if is_file else (
        sum(f.stat().st_size for f in file_path.rglob("*") if f.is_file()) if file_path.exists() else 0
    )
    sha256 = compute_sha256(file_path) if is_file else None

    if entry["kind"] == "passport_json":
        val_res = _validate_passport_json(entry, base_dir)
    else:
        val_res = _validate_spatial_entry(entry, base_dir)

    if missing_meta:
        val_res["errors"].append(f"Не заполнены обязательные поля реестра: {', '.join(missing_meta)}")
        val_res["check_result"] = "fail"

    # Freshness status (decoupled from check_result & never false 'stale' on network failure)
    remote_info: Dict[str, Any] = {
        "freshness_status": "fresh" if val_res["check_result"] == "pass" else "attention",
        "remote_version": entry.get("declared_version"),
        "newer_available": False,
        "note": "Локальная проверка выполнена без обращения к внешним серверам.",
    }
    if check_remote and entry.get("remote_check_type") == "tochno_bdmo":
        checker = remote_checker or _check_remote_tochno_bdmo
        remote_info = checker(entry.get("declared_version", ""))
        if val_res["check_result"] != "pass" and remote_info["freshness_status"] == "fresh":
            remote_info["freshness_status"] = "attention"
    elif val_res["check_result"] == "fail":
        remote_info["freshness_status"] = "attention"

    return {
        "id": entry["id"],
        "name": entry["name"],
        "kind": entry["kind"],
        "region": entry["region"],
        "local_path": entry["local_path"],
        "source": entry["source"],
        "source_url": entry["source_url"],
        "owner_org": entry["owner_org"],
        "license": entry["license"],
        "attribution": entry["attribution"],
        "declared_version": entry.get("declared_version"),
        "actual_version": val_res["actual_version"],
        "published_at": entry.get("published_at"),
        "last_downloaded_at": entry.get("last_downloaded_at"),
        "generated_at": val_res["generated_at"],
        "last_checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256,
        "size_bytes": size_bytes,
        "territory_count": val_res["territory_count"],
        "expected_territories": entry.get("expected_territories"),
        "latest_stat_year": val_res["latest_stat_year"],
        "coverage_pct": val_res["coverage_pct"],
        "missing_total": val_res["missing_total"],
        "check_result": val_res["check_result"],
        "freshness_status": remote_info["freshness_status"],
        "newer_available": bool(remote_info.get("newer_available", False)),
        "remote_version": remote_info.get("remote_version"),
        "freshness_note": remote_info.get("note", ""),
        "errors": val_res["errors"],
        "warnings": val_res["warnings"],
        "indicators": val_res["indicators"],
    }


def build_quality_report(
    registry: Optional[List[Dict[str, Any]]] = None,
    base_dir: Path = BASE_DIR,
    check_remote: bool = False,
    remote_checker: Any = None,
) -> Dict[str, Any]:
    items = registry if registry is not None else DATA_REGISTRY
    results = [
        evaluate_dataset(entry, base_dir=base_dir, check_remote=check_remote, remote_checker=remote_checker)
        for entry in items
    ]
    passed = sum(1 for r in results if r["check_result"] == "pass")
    warned = sum(1 for r in results if r["check_result"] == "warn")
    failed = sum(1 for r in results if r["check_result"] == "fail")
    stale_count = sum(1 for r in results if r["freshness_status"] == "stale")
    unknown_count = sum(1 for r in results if r["freshness_status"] == "unknown")

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check_remote": bool(check_remote),
        "summary": {
            "total_datasets": len(results),
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "stale": stale_count,
            "unknown": unknown_count,
            "overall_status": "fail" if failed > 0 else ("warn" if warned > 0 or stale_count > 0 else "pass"),
        },
        "datasets": results,
    }


def get_public_sources_summary(base_dir: Path = BASE_DIR) -> Dict[str, Any]:
    """Safe public summary of data sources & update dates without internal paths or infra details."""
    sources: List[Dict[str, Any]] = []
    for entry in DATA_REGISTRY:
        if entry["kind"] not in ("passport_json", "shapefile"):
            continue
        updated_at = entry.get("published_at") or entry.get("last_downloaded_at")
        if entry["kind"] == "passport_json":
            p = base_dir / entry["local_path"]
            if p.exists():
                try:
                    meta = json.loads(p.read_text(encoding="utf-8")).get("metadata") or {}
                    updated_at = meta.get("updated_at") or updated_at
                except Exception:
                    pass
        sources.append({
            "name": entry["name"],
            "region": entry["region"],
            "source": entry["source"],
            "license": entry["license"],
            "updated_at": updated_at,
        })
    return {"sources": sources}
