import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_rostov_passports as etl  # noqa: E402

PASSPORTS_PATH = REPO_ROOT / "public" / "maps" / "rostov_passports.json"
SHP_PATH = REPO_ROOT / "Py_Geo" / "shape" / "rostov" / "raion.shp"


def _make_csv_zip(rows: list[dict], fieldnames: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        sio = io.StringIO()
        writer = csv.DictWriter(sio, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
        zf.writestr("fixture.csv", sio.getvalue().encode("utf-8"))
    return buf.getvalue()


def test_generated_rostov_passports_structure_and_coverage():
    assert PASSPORTS_PATH.exists(), "public/maps/rostov_passports.json must exist"
    data = json.loads(PASSPORTS_PATH.read_text(encoding="utf-8"))

    meta = data["metadata"]
    assert meta["total_territories"] == 55
    assert meta["license"] == "CC BY 4.0"
    assert "Росстат" in meta["attribution"]
    assert "Если быть точным" in meta["attribution"]
    assert "OpenStreetMap" in meta["geometry_source"]
    assert "номинальн" in meta["monetary_values_note"].lower()

    territories = data["territories"]
    assert len(territories) == 55

    # Exact 55 OKTMO match against raion.shp
    gdf = gpd.read_file(SHP_PATH)
    shp_oktmos = {str(ok).strip()[:8] for ok in gdf["oktmo"]}
    assert len(shp_oktmos) == 55
    assert set(territories.keys()) == shp_oktmos

    types = [t["type"] for t in territories.values()]
    assert types.count("Муниципальный район") == 43
    assert types.count("Городской округ") == 12

    expected_units = {
        "population_avg": "Человек",
        "births": "Человек",
        "deaths": "Человек",
        "investments_per_capita": "Рубль",
        "agriculture_output": "Тысяча рублей",
        "housing_commissioned": "Квадратный метр общей площади",
        "population_density": "Человек на кв. км",
        "natural_growth": "Человек",
    }

    for key, unit in expected_units.items():
        ind_meta = meta["indicators"][key]
        assert ind_meta["unit"] == unit
        assert ind_meta["coverage_latest"] == 55
        assert ind_meta["total_territories"] == 55

    non_negative_keys = {
        "population_avg",
        "births",
        "deaths",
        "investments_per_capita",
        "agriculture_output",
        "housing_commissioned",
        "population_density",
    }

    for ok, t in territories.items():
        assert len(ok) == 8 and ok.isdigit()
        assert t["area_km2"] > 0

        for key in expected_units:
            ind = t["indicators"][key]
            assert ind["latest_value"] is not None
            for yr, val in ind["series"].items():
                if val is not None and key in non_negative_keys:
                    assert val >= 0, f"Negative value for {ok}/{key}/{yr}: {val}"

        # Derived consistency: population_density = population_avg / area_km2
        pop_series = t["indicators"]["population_avg"]["series"]
        dens_series = t["indicators"]["population_density"]["series"]
        for yr, pval in pop_series.items():
            if pval is not None:
                assert dens_series[yr] == round(float(pval) / t["area_km2"], 2)

        # Derived consistency: natural_growth = births - deaths
        b_series = t["indicators"]["births"]["series"]
        d_series = t["indicators"]["deaths"]["series"]
        g_series = t["indicators"]["natural_growth"]["series"]
        for yr in set(b_series) & set(d_series):
            if b_series[yr] is not None and d_series[yr] is not None:
                assert g_series[yr] == b_series[yr] - d_series[yr]


def test_etl_fixture_slice_filtering_nulls_and_duplicate_guard():
    territories = etl.load_rostov_territories(SHP_PATH)
    valid_oktmos = sorted(territories.keys())

    base_fields = [
        "region_name", "mun_level", "municipality", "oktmo",
        "year", "indicator_value", "indicator_unit",
    ]
    agri_fields = base_fields + ["kategor"]

    def _build_rows(unit: str, with_kategor: bool = False):
        rows = []
        for i, ok in enumerate(valid_oktmos):
            # Missing value on first MO must stay None, not 0
            val = "" if i == 0 else str(100 + i)
            row = {
                "region_name": "Ростовская область",
                "mun_level": "Муниципальное образование верхнего уровня",
                "municipality": territories[ok]["name"],
                "oktmo": ok,
                "year": "2024",
                "indicator_value": val,
                "indicator_unit": unit,
            }
            if with_kategor:
                row["kategor"] = "Хозяйства всех категорий"
                rows.append(row)
                # Extra category row that must be ignored, not summed
                rows.append({**row, "kategor": "Хозяйства населения (граждане)", "indicator_value": "99999"})
            else:
                rows.append(row)
            # Lower-level settlement row that must be ignored
            rows.append({
                **row,
                "mun_level": "Муниципальное образование нижнего уровня",
                "oktmo": ok[:5] + "405",
                "indicator_value": "777",
                **({"kategor": "Хозяйства всех категорий"} if with_kategor else {}),
            })
        return rows

    overrides = {
        "population_avg": _make_csv_zip(_build_rows("Человек"), base_fields),
        "births": _make_csv_zip(_build_rows("Человек"), base_fields),
        "deaths": _make_csv_zip(_build_rows("Человек"), base_fields),
        "investments_per_capita": _make_csv_zip(_build_rows("Рубль"), base_fields),
        "agriculture_output": _make_csv_zip(_build_rows("Тысяча рублей", with_kategor=True), agri_fields),
        "housing_commissioned": _make_csv_zip(_build_rows("Квадратный метр общей площади"), base_fields),
    }

    res = etl.build_passports(shp_path=SHP_PATH, zip_overrides=overrides)
    first_ok = valid_oktmos[0]
    assert res["territories"][first_ok]["indicators"]["population_avg"]["series"]["2024"] is None
    assert res["territories"][first_ok]["indicators"]["population_density"]["series"]["2024"] is None
    assert res["territories"][valid_oktmos[1]]["indicators"]["agriculture_output"]["series"]["2024"] == 101

    # Duplicate (oktmo, year) in same slice must raise ValueError
    dup_rows = _build_rows("Человек")
    dup_rows.append({**dup_rows[0], "indicator_value": "555"})
    dup_zip = _make_csv_zip(dup_rows, base_fields)
    with pytest.raises(ValueError, match="Duplicate observation"):
        etl.parse_indicator_zip(dup_zip, etl.INDICATORS_SPEC[0], set(valid_oktmos))
