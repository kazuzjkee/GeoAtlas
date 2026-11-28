import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = BASE_DIR / "public" / "dictionary.json"


def test_dictionary_json_structure_uniqueness_and_links():
    assert DICT_PATH.exists(), "public/dictionary.json must exist"
    data = json.loads(DICT_PATH.read_text(encoding="utf-8"))

    categories = data["categories"]
    terms = data["terms"]
    assert len(categories) == 6
    assert len(terms) >= 240

    cat_ids = {c["id"] for c in categories}
    seen_ids = set()
    seen_slugs = set()
    seen_titles = set()

    for t in terms:
        assert t["category"] in cat_ids
        for field in (
            "id", "slug", "title", "category_name",
            "short_def", "academic_def", "simple_explanation",
            "practical_use", "example",
        ):
            assert isinstance(t.get(field), str) and t[field].strip(), f"Missing {field} in {t.get('slug')}"
        assert isinstance(t.get("sources"), list) and len(t["sources"]) >= 1
        assert t["id"] not in seen_ids
        assert t["slug"] not in seen_slugs
        assert t["title"].strip().lower() not in seen_titles
        seen_ids.add(t["id"])
        seen_slugs.add(t["slug"])
        seen_titles.add(t["title"].strip().lower())

    for t in terms:
        for rel in t.get("related", []):
            assert rel in seen_slugs, f"Broken related link: {t['slug']} -> {rel}"

    # Verify key slugs linked from GeoAtlas passports & maps
    for required_slug in (
        "estestvennyy-prirost",
        "plotnost-naseleniya",
        "chislennost-naseleniya",
        "oktmo",
        "proekciya-albersa",
        "geojson",
        "topojson",
    ):
        assert required_slug in seen_slugs


def test_dictionary_routes_public_access(anon_client):
    r_page = anon_client.get("/dictionary")
    assert r_page.status_code == 200
    assert "Географический словарь" in r_page.text

    r_term = anon_client.get("/dictionary/estestvennyy-prirost")
    assert r_term.status_code == 200

    r_api = anon_client.get("/api/dictionary")
    assert r_api.status_code == 200
    body = r_api.json()
    assert body["metadata"]["total_categories"] == 6
    assert len(body["terms"]) >= 240

    r_static = anon_client.get("/public/dictionary.json")
    assert r_static.status_code == 200
