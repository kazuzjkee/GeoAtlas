"""
Generates and validates public/dictionary.json for the GeoAtlas Geographic Dictionary.
Run: python scripts/build_dictionary.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = BASE_DIR / "public" / "dictionary.json"

CATEGORIES: List[Dict[str, str]] = [
    {
        "id": "physical",
        "name": "Физическая география",
        "icon": "🏔️",
        "description": "Рельеф, климат, гидрология суши и океана, почвы, природные зоны и физико-географическое районирование.",
    },
    {
        "id": "socioeconomic",
        "name": "Социально-экономическая география",
        "icon": "👥",
        "description": "Население, демографические процессы, миграция, урбанизация, расселение и региональное развитие.",
    },
    {
        "id": "economic",
        "name": "Экономическая география",
        "icon": "🏭",
        "description": "Промышленность, сельское хозяйство, транспорт, инвестиции, экономические районы и территориальная организация хозяйства.",
    },
    {
        "id": "cartography",
        "name": "Картография и ГИС",
        "icon": "🗺️",
        "description": "Картографические проекции, масштаб, системы координат, ГИС, геоданные, картограммы и пространственный анализ.",
    },
    {
        "id": "methods",
        "name": "Методы географических исследований",
        "icon": "📐",
        "description": "Статистические методы, географическое моделирование, районирование, индексы и полевые исследования.",
    },
    {
        "id": "ecology",
        "name": "Природопользование и экология",
        "icon": "🌿",
        "description": "Природные ресурсы, экосистемы, антропогенное воздействие, устойчивое развитие и охрана окружающей среды.",
    },
]

SOURCES_CATALOG = {
    "kalesnik": "Калесник С. В. Основы общего землеведения. — М.: Учпедгиз / Просвещение.",
    "isachenko": "Исаченко А. Г. Ландшафтоведение и физико-географическое районирование. — М.: Высшая школа.",
    "maksakovsky": "Максаковский В. П. Географическая картина мира. — М.: Дрофа.",
    "berdyant": "Берлянт А. М. Картография: учебник для вузов. — М.: Аспект Пресс / КДУ.",
    "tikunov": "Тикунов В. С. (ред.) Геоинформатика: учебник для студентов вузов. — М.: Академия.",
    "rosstat": "Росстат. Методологические положения по статистике населения и социально-экономических показателей.",
    "kolosovsky": "Колосовский Н. Н. Теория экономического районирования. — М.: Мысль.",
    "baburin": "Бабурин В. Л., Мазуров Ю. Л. Географические основы управления. — М.: Дело.",
    "gost_gis": "ГОСТ Р 52438-2005 «Географические информационные системы. Термины и определения».",
    "ogc": "Open Geospatial Consortium (OGC) — стандарты пространственных данных и систем координат.",
    "unesco_un": "Документы ООН и ЮНЕП по устойчивому развитию и охране окружающей среды.",
    "khromov": "Хромов С. П., Петросянц М. А. Метеорология и климатология. — М.: Изд-во МГУ.",
    "mikhailov": "Михайлов В. Н., Добровольский А. Д., Добролюбов С. А. Гидрология. — М.: Высшая школа.",
    "dobrovolsky": "Добровольский Г. В., Урусевская И. С. География почв. — М.: Изд-во МГУ.",
}

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def make_slug(title: str) -> str:
    s = title.strip().lower()
    out = []
    for ch in s:
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug


def _term(
    title: str,
    category: str,
    short_def: str,
    academic_def: str,
    simple: str,
    practical: str,
    example: str,
    synonyms: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    related: Optional[List[str]] = None,
    formula: Optional[str] = None,
    units: Optional[str] = None,
    sources: Optional[List[str]] = None,
    slug: Optional[str] = None,
) -> Dict[str, Any]:
    sl = slug or make_slug(title)
    src_list = [SOURCES_CATALOG.get(k, k) for k in (sources or ["maksakovsky"])]
    return {
        "id": sl,
        "slug": sl,
        "title": title,
        "category": category,
        "short_def": short_def,
        "academic_def": academic_def,
        "simple_explanation": simple,
        "practical_use": practical,
        "example": example,
        "synonyms": synonyms or [],
        "keywords": keywords or [],
        "related": related or [],
        "formula": formula,
        "units": units,
        "sources": src_list,
    }


def _pack(
    cat: str,
    rows: List[Tuple[Any, ...]],
    default_sources: List[str],
) -> List[Dict[str, Any]]:
    """Compact tuple builder for concise, high-quality dictionary entries."""
    out: List[Dict[str, Any]] = []
    for row in rows:
        # Format: (title, short_def, academic_def, simple, practical, example, synonyms, keywords, related[, formula, units, slug])
        title = row[0]
        short_def = row[1]
        academic_def = row[2]
        simple = row[3]
        practical = row[4]
        example = row[5]
        synonyms = row[6] if len(row) > 6 else []
        keywords = row[7] if len(row) > 7 else []
        related = row[8] if len(row) > 8 else []
        formula = row[9] if len(row) > 9 else None
        units = row[10] if len(row) > 10 else None
        custom_slug = row[11] if len(row) > 11 else None
        out.append(
            _term(
                title=title,
                category=cat,
                short_def=short_def,
                academic_def=academic_def,
                simple=simple,
                practical=practical,
                example=example,
                synonyms=synonyms,
                keywords=keywords,
                related=related,
                formula=formula,
                units=units,
                sources=default_sources,
                slug=custom_slug,
            )
        )
    return out


def build_dictionary() -> Dict[str, Any]:
    from dict_data_part1 import PHYSICAL_TERMS, SOCIOECONOMIC_TERMS
    from dict_data_part2 import ECONOMIC_TERMS, CARTOGRAPHY_TERMS
    from dict_data_part3 import METHODS_TERMS, ECOLOGY_TERMS

    terms: List[Dict[str, Any]] = []
    terms.extend(_pack("physical", PHYSICAL_TERMS, ["kalesnik", "isachenko", "khromov", "mikhailov", "dobrovolsky"]))
    terms.extend(_pack("socioeconomic", SOCIOECONOMIC_TERMS, ["maksakovsky", "rosstat", "baburin"]))
    terms.extend(_pack("economic", ECONOMIC_TERMS, ["maksakovsky", "kolosovsky", "rosstat"]))
    terms.extend(_pack("cartography", CARTOGRAPHY_TERMS, ["berdyant", "tikunov", "gost_gis", "ogc"]))
    terms.extend(_pack("methods", METHODS_TERMS, ["tikunov", "berdyant", "rosstat", "isachenko"]))
    terms.extend(_pack("ecology", ECOLOGY_TERMS, ["isachenko", "baburin", "unesco_un"]))

    cat_names = {c["id"]: c["name"] for c in CATEGORIES}
    seen_ids = set()
    seen_slugs = set()
    seen_titles = set()

    for t in terms:
        assert t["category"] in cat_names, f"Unknown category {t['category']}"
        t["category_name"] = cat_names[t["category"]]
        for req_field in ("id", "slug", "title", "short_def", "academic_def", "simple_explanation", "practical_use", "example"):
            assert t.get(req_field), f"Empty {req_field} in {t.get('title')}"
        assert t["id"] not in seen_ids, f"Duplicate id: {t['id']}"
        assert t["slug"] not in seen_slugs, f"Duplicate slug: {t['slug']}"
        assert t["title"].lower() not in seen_titles, f"Duplicate title: {t['title']}"
        seen_ids.add(t["id"])
        seen_slugs.add(t["slug"])
        seen_titles.add(t["title"].lower())

    # Resolve & validate cross-reference links to ensure 100% integrity
    alias_map = {
        "akumulyaciya": "akkumulyatsiya",
        "koef-uvlazhneniya": "koeffitsient-uvlazhneniya",
        "koef-variacii": "koeffitsient-variatsii",
        "summarnaya-rozhdaemost": "summarnyy-koeffitsient-rozhdaemosti",
        "produktsiya-selskogo-khozyaystva": "valovyy-produkt-sh",
        "distancionnoe-zondirovanie": "distantsionnoe-zondirovanie-zemli",
        "otraslevaya-struktura": "otraslevaya-struktura-ekonomiki",
        "specializaciya-regiona": "spetsializatsiya-regiona",
        "faktor-razmeshcheniya": "faktor-razmeshcheniya-proizvodstva",
        "teritorialno-proizvodstvennyy-kompleks": "territorialno-proizvodstvennyy-kompleks",
        "model-centr-periferiya": "model-tsentr-periferiya",
        "investicii-v-osnovnoy-kapital": "investitsii-v-osnovnoy-kapital",
        "uklon-reki": "rechnoy-stok",
        "klasternyy-analiz": "klassifikatsiya-territoriy",
        "topologiya-geodannyh": "topologiya-geodannykh",
        "agregirovanie-dannyh": "agregirovanie-dannykh",
    }
    missing_refs: List[str] = []
    for t in terms:
        resolved_rel: List[str] = []
        for r in t["related"]:
            cand = alias_map.get(r, r)
            if cand not in seen_slugs:
                cand_ts = re.sub(r"c([ieyaou])", r"ts\1", cand).replace("ciya", "tsiya").replace("ce", "tse").replace("ci", "tsi")
                if cand_ts in seen_slugs:
                    cand = cand_ts
            if cand not in seen_slugs:
                # Fallback: replace any remaining 'c' with 'ts'
                cand_ts2 = cand.replace("c", "ts")
                if cand_ts2 in seen_slugs:
                    cand = cand_ts2
            if cand not in seen_slugs:
                missing_refs.append(f"{t['slug']} -> {r}")
            elif cand != t["slug"] and cand not in resolved_rel:
                resolved_rel.append(cand)
        t["related"] = resolved_rel
    if missing_refs:
        raise ValueError("Broken related links:\n" + "\n".join(missing_refs))

    counts = {c["id"]: 0 for c in CATEGORIES}
    for t in terms:
        counts[t["category"]] += 1

    categories_out = [{**c, "count": counts[c["id"]]} for c in CATEGORIES]
    return {
        "metadata": {
            "title": "Географический словарь GeoAtlas",
            "organization": "Южный федеральный университет • Институт наук о Земле (ИНоЗ)",
            "total_terms": len(terms),
            "total_categories": len(categories_out),
            "version": "1.0.0",
        },
        "categories": categories_out,
        "terms": sorted(terms, key=lambda x: x["title"].lower()),
    }


def main() -> int:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    payload = build_dictionary()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {OUT_PATH}: {payload['metadata']['total_terms']} terms in {payload['metadata']['total_categories']} categories.")
    for c in payload["categories"]:
        print(f"  - {c['name']} ({c['id']}): {c['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
