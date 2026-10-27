import geopandas as gpd
import folium
from folium import plugins
import os
import json
import webbrowser
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point

# ==========================================
# КОНФИГУРАЦИЯ И ТРАНСЛИТЕРАЦИЯ
# ==========================================
BASE_SHP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Py_Geo', 'shape', 'russia_unified')

REGION_TRANSLATIONS = {
    'Adygey': 'Республика Адыгея', 'Altay': 'Алтайский край', 'Amur': 'Амурская область',
    "Arkhangel'sk": 'Архангельская область', "Astrakhan'": 'Астраханская область',
    'Bashkortostan': 'Республика Башкортостан', 'Belgorod': 'Белгородская область',
    'Bryansk': 'Брянская область', 'Buryat': 'Республика Бурятия', 'Chechnya': 'Чеченская Республика',
    'Chelyabinsk': 'Челябинская область', 'Chukot': 'Чукотский автономный округ',
    'Chuvash': 'Чувашская Республика', 'City of St. Petersburg': 'Санкт-Петербург',
    'Dagestan': 'Республика Дагестан', 'Gorno-Altay': 'Республика Алтай',
    'Ingush': 'Республика Ингушетия', 'Irkutsk': 'Иркутская область',
    'Ivanovo': 'Ивановская область', 'Kabardin-Balkar': 'Кабардино-Балкарская Республика',
    'Kaliningrad': 'Калининградская область', 'Kalmyk': 'Республика Калмыкия',
    'Kaluga': 'Калужская область', 'Kamchatka': 'Камчатский край',
    'Karachay-Cherkess': 'Карачаево-Черкесская Республика', 'Karelia': 'Республика Карелия',
    'Kemerovo': 'Кемеровская область', 'Khabarovsk': 'Хабаровский край',
    'Khakass': 'Республика Хакасия', 'Khanty-Mansiy': 'Ханты-Мансийский АО',
    'Kirov': 'Кировская область', 'Komi': 'Республика Коми', 'Kostroma': 'Костромская область',
    'Krasnodar': 'Краснодарский край', 'Krasnoyarsk': 'Красноярский край',
    'Kurgan': 'Курганская область', 'Kursk': 'Курская область',
    'Leningrad': 'Ленинградская область', 'Lipetsk': 'Липецкая область',
    'Maga Buryatdan': 'Магаданская область', 'Mariy-El': 'Республика Марий Эл',
    'Mordovia': 'Республика Мордовия', 'Moscow City': 'Москва', 'Moskva': 'Московская область',
    'Murmansk': 'Мурманская область', 'Nenets': 'Ненецкий автономный округ',
    'Nizhegorod': 'Нижегородская область', 'North Ossetia': 'Республика Северная Осетия',
    'Novgorod': 'Новгородская область', 'Novosibirsk': 'Новосибирская область',
    'Omsk': 'Омская область', 'Orel': 'Орловская область', 'Orenburg': 'Оренбургская область',
    'Penza': 'Пензенская область', "Perm'": 'Пермский край', "Primor'ye": 'Приморский край',
    'Pskov': 'Псковская область', 'Rostov': 'Ростовская область', "Ryazan'": 'Рязанская область',
    'Sakha': 'Республика Саха (Якутия)', 'Sakhalin': 'Сахалинская область',
    'Samara': 'Самарская область', 'Saratov': 'Саратовская область',
    'Smolensk': 'Смоленская область', "Stavropol'": 'Ставропольский край',
    'Sverdlovsk': 'Свердловская область', 'Tambov': 'Тамбовская область',
    'Tatarstan': 'Республика Татарстан', 'Tomsk': 'Томская область',
    'Tula': 'Тульская область', 'Tuva': 'Республика Тыва', "Tver'": 'Тверская область',
    "Tyumen'": 'Тюменская область', 'Udmurt': 'Удмуртская Республика',
    "Ul'yanovsk": 'Ульяновская область', 'Vladimir': 'Владимирская область',
    'Volgograd': 'Волгоградская область', 'Vologda': 'Вологодская область',
    'Voronezh': 'Воронежская область', 'Yamal-Nenets': 'Ямало-Ненецкий АО',
    "Yaroslavl'": 'Ярославская область', 'Yevrey': 'Еврейская автономная область',
    "Zabaykal'ye": 'Забайкальский край'
}

DISTRICT_TRANSLATIONS = {
    'Sasovskiy': 'Сасовский район',
    'Sasovo': 'Сасово',
    'Eysk': 'Ейск',
    'Elets': 'Елец',
    'Ioshkar-Ola': 'Йошкар-Ола',
    'Khimki': 'Химки',
    'Dolgoprudny': 'Долгопрудный',
    'Dzerzinski': 'Дзержинский',
    "Egor'evsk": 'Егорьевск',
    'Elektrostahl': 'Электросталь',
    'Karasnoarmesyk': 'Красноармейск',
    'Kraznoznamensk': 'Краснознаменск',
    'Molodyozhny': 'Молодёжный',
    'Petrovsky': 'Петровский',
    'Protvino': 'Протвино',
    'Pushchino': 'Пущино',
    'Roshal': 'Рошаль',
    'Shcherbinka': 'Щербинка',
    'Voskhod': 'Восход',
    'Zhukovsky': 'Жуковский',
    'Eveno-Bytantayskiy rayon': 'Эвено-Бытантайский улус',
    "Oktyabr'sk": 'Октябрьск',
    'Zhigulevsk': 'Жигулёвск',
    'Budennovsk': 'Будённовск',
    'Essentuki': 'Ессентуки',
    'Efremov': 'Ефремов',
    'Raduga': 'Радужный',
    'Primorskiy': 'Приморский район',
    'Kinel-Cherk': 'Кинель-Черкасский район',
    'Central': 'Центральный АО',
    'Eastern': 'Восточный АО',
    'North-Eastern': 'Северо-Восточный АО',
    'Northern': 'Северный АО',
    'South-Eastern': 'Юго-Восточный АО',
    'South-Western': 'Юго-Западный АО',
    'Southern': 'Южный АО',
    'Western': 'Западный АО',
    'Zelenogradsky': 'Зеленоградский АО'
}

def slugify_name(text):
    import re
    text = str(text).strip()
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    res = []
    for ch in text.lower():
        if ch in translit_map:
            res.append(translit_map[ch])
        elif ch.isalnum():
            res.append(ch)
        elif ch in [' ', '-', '_']:
            res.append('_')
    slug = ''.join(res)
    slug = re.sub(r'_+', '_', slug).strip('_')
    custom_slugs = {
        'rostov': 'rostov', 'krasnodar': 'krasnodar',
        'city_of_st_petersburg': 'spb', 'moscow_city': 'moscow',
        'moskva': 'moscow_oblast'
    }
    return custom_slugs.get(slug, slug or 'region')

def clean_geom(geom):
    """Очищает и восстанавливает валидность геометрии, преобразуя GeometryCollection в Polygon/MultiPolygon."""
    if geom is None or geom.is_empty:
        return geom
    if not geom.is_valid:
        try:
            from shapely.validation import make_valid
            geom = make_valid(geom)
        except Exception:
            try:
                geom = geom.buffer(0)
            except Exception:
                pass
    if geom.geom_type == 'GeometryCollection':
        from shapely.ops import unary_union
        polys = [g for g in geom.geoms if g.geom_type in ['Polygon', 'MultiPolygon']]
        if polys:
            geom = unary_union(polys)
        else:
            lines = [g for g in geom.geoms if g.geom_type in ['LineString', 'MultiLineString']]
            if lines:
                geom = unary_union(lines)
    return geom

# ==========================================
# ГИБРИДНАЯ КОНФИГУРАЦИЯ РЕГИОНОВ (ДЕТАЛЬНЫЕ КАРТЫ)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REGIONS_CONFIG = {
    'rostov': {
        'path': os.path.join(BASE_DIR, 'Py_Geo', 'shape', 'rostov'),
        'title': 'Ростовская область',
        'center': [47.5, 40.5],
        'zoom': 8,
        'output': 'rostov_quiz_map.html',
        'is_rf': False,
        'files': {
            'districts': 'raion.shp',
            'district_centers': 'raicentr.shp',
            'rivers': 'water-line.shp',
            'water_bodies': 'water-polygon.shp'
        }
    },
    'krasnodar': {
        'path': os.path.join(BASE_DIR, 'Py_Geo', 'shape', 'krasnodar'),
        'title': 'Краснодарский край',
        'center': [45.2, 39.0],
        'zoom': 8,
        'output': 'krasnodar_quiz_map.html',
        'is_rf': False,
        'files': {
            'districts': 'boundary-3857.shp',
            'district_centers': 'City-3857.shp',
            'rivers': 'water-line.shp',
            'water_bodies': 'water-polygon.shp'
        }
    },
    'russia': {
        'path': os.path.join(BASE_DIR, 'Py_Geo', 'shape', 'russia'),
        'title': 'Российская Федерация',
        'center': [63.0, 95.0],
        'zoom': 3,
        'output': 'russia_quiz_map.html',
        'is_rf': True,
        'files': {
            'districts': 'gadm41_RUS_1.shp',
            'district_centers': 'Cities.shp',
            'rivers': 'Rivers.shp',
            'water_bodies': 'Lakes.shp'
        }
    }
}

ACTIVE_REGION = 'russia'

CARTO_KEY = 'cb1_3wsm_1_6bdccfe40c07a69c4fce7b68'

STYLES = {
    'districts': {
        'color': '#2E8B57',
        'weight': 2,
        'fillColor': '#90EE90',
        'fillOpacity': 0.25,
        'dashArray': '5, 5'
    },
    'rivers': {
        'color': '#0284C7',
        'weight': 2.5,
        'opacity': 0.9
    },
    'water_bodies': {
        'color': '#0284C7',
        'weight': 1,
        'fillColor': '#38BDF8',
        'fillOpacity': 0.65
    }
}

LAYER_NAMES = {
    'districts': 'Территории',
    'rivers': 'Реки',
    'water_bodies': 'Водоемы'
}

# ==========================================
# ОБЪЕДИНЕННАЯ БАЗА ДАННЫХ НАСЕЛЕНИЯ
# ==========================================
KNOWN_POPULATION = {
    # 1. Города федерального значения и составные / специфичные основы (ДОЛЖНЫ идти ДО общих корней)
    'санкт-петербург': 5597763,
    'петербург': 5597763,
    'севастопол': 561374,
    'московск': 8594454,
    'москв': 13104177,
    'ростов-на-дону': 1140000,
    'ростов': 4132800,
    'краснодарск': 5833000,
    'краснодар': 1100000,
    'приморско-ахтар': 59000,   # Должен идти ДО 'примор'
    'усть-лабин': 105000,       # Должен идти ДО 'лабин' и 'абин'
    'лабин': 97000,             # Должен идти ДО 'абин' ('л-абин-ский')
    'абинск': 98000,
    'красноармей': 105000,      # Должен идти ДО 'ейск' ('красноарм-ейск-ий')
    'матвеево-курган': 39000,   # Должен идти ДО 'курган'
    'курганин': 104000,         # Должен идти ДО 'курган'
    'курган': 760000,
    'усть-донец': 28000,        # Должен идти ДО 'донецк'
    'донецк': 46000,
    'волгодонской': 33000,      # Должен идти ДО 'волгодонск'
    'волгодонск': 168000,
    'каменск-шахтинск': 86000,  # Должен идти ДО 'каменск'
    'каменск': 41000,
    'азовск': 106000,           # Должен идти ДО 'азов'
    'азов': 81000,
    'сахалин': 460000,          # Должен идти ДО 'саха'
    'саха': 997565,
    'якут': 997565,
    'алтайск': 2130000,         # Должен идти ДО 'алтай'
    'алтай': 210000,
    'костром': 570000,          # Должен идти ДО 'омск' ('костр-омск-ая')
    'томск': 1050000,           # Должен идти ДО 'омск' ('т-омск-ая')
    'омск': 1830000,
    'ямал': 512000,             # Должен идти ДО 'ненец' (Ямало-Ненецкий)
    'янао': 512000,
    'ненец': 42000,
    'чечен': 1500000,           # Должен идти ДО 'ингуш'
    'ингуш': 520000,
    'ленинградская область': 2000000, # Должен идти ДО 'ленинград' (район в крае)
    'орловская область': 700000,      # Должен идти ДО 'орлов' (район в области)
    'орел': 700000,
    'калининград': 1030000,     # Должен идти ДО 'калинин' (район в крае)

    # 2. Сибирь, Север и Дальний Восток (по основам)
    'иркут': 2340000,
    'краснояр': 2846000,
    'хабаров': 1278000,
    'камчат': 288000,
    'чукот': 47500,
    'магадан': 134000,
    'мурман': 660000,
    'забайкал': 984000,
    'примор': 1820000,
    'амур': 750000,
    'свердлов': 4239161,
    'бурят': 970000,
    'тыва': 337000,
    'тува': 337000,
    'хакас': 530000,
    'новосиб': 2790000,
    'кемеров': 2550000,
    'тюмен': 1600000,
    'хмао': 1720000,
    'ханты': 1720000,
    'еврей': 147000,
    'врей': 147000,
    'коми': 720000,
    'карел': 523000,

    # 3. Поволжье, Урал, Центр, Северо-Запад, Юг, Кавказ (по основам)
    'башкорт': 4077600,
    'татар': 4001625,
    'челябин': 3396739,
    'нижегород': 3060335,
    'самар': 3128043,
    'волгоград': 2450000,
    'саратов': 2380000,
    'воронеж': 2270000,
    'перм': 2500000,
    'архангель': 1000000,
    'вологод': 1130000,
    'псков': 585000,
    'новгород': 575000,
    'твер': 1200000,
    'ярослав': 1190000,
    'иванов': 910000,
    'владимир': 1320000,
    'рязан': 1080000,
    'тульск': 1470000,
    'калуж': 1070000,
    'смолен': 870000,
    'брянск': 1150000,
    'курск': 1060000,
    'белгород': 1500000,
    'липецк': 1120000,
    'тамбов': 960000,
    'пензен': 1240000,
    'ульянов': 1180000,
    'мордов': 770000,
    'чуваш': 1170000,
    'марий': 670000,
    'удмурт': 1440000,
    'киров': 1130000,
    'оренбург': 1840000,
    'астрахан': 950000,
    'калмык': 265000,
    'дагестан': 3200000,
    'осетия': 680000,
    'осетин': 680000,
    'кабардин': 900000,
    'карача': 468000,
    'адыге': 498000,
    'ставропол': 2890000,

    # 4. Районы и города Ростовской области (по основам)
    'таганрог': 245000, 'шахты': 226000,
    'новочеркасск': 163000, 'батайск': 126000, 'новошахтинск': 103000,
    'гуково': 62000, 'зверево': 19000,
    'аксай': 121000, 'белокалитвин': 91000, 'сальск': 101000, 'мясников': 52000,
    'красносулин': 74000, 'миллеров': 63000, 'морозов': 37000, 'зерноград': 51000,
    'семикаракор': 48000, 'октябрьск': 70000, 'неклинов': 87000,
    'багаев': 33000, 'константинов': 31000, 'цимлян': 33000, 'шолохов': 25000,
    'чертков': 30000, 'тацин': 34000, 'орлов': 36000, 'пролетар': 33000,
    'песчанокоп': 27000, 'ремонтнен': 17000, 'заветин': 15000,
    'дубов': 21000, 'зимовников': 34000, 'кагальниц': 28000, 'кашар': 22000,
    'куйбышев': 13000, 'мартынов': 34000, 'милютин': 12000, 'облив': 17000,
    'родионово-несветай': 22000, 'советск': 6000, 'тарасов': 27000,
    'целин': 29000, 'боков': 14000, 'верхнедон': 17000, 'веселов': 25000, 'егорлык': 34000,

    # 5. Краснодарский край (Городские округа и районы по основам)
    'сочи': 430000, 'новороссийск': 340000, 'армавир': 208000,
    'анапа': 205000, 'геленджик': 116000, 'горячий ключ': 69000,
    'апшерон': 98000, 'белоглин': 29000, 'белоречен': 108000,
    'брюховец': 50000, 'выселк': 59000, 'гулькевич': 98000, 'динск': 147000,
    'ейск': 136000, 'кавказ': 121000, 'калинин': 50000, 'канев': 104000,
    'коренов': 86000, 'крылов': 35000, 'крымск': 133000,
    'кущев': 65000, 'ленинград': 63000,
    'мостов': 70000, 'новокубан': 87000, 'новопокров': 42000, 'отраднен': 70000,
    'павлов': 67000, 'северск': 122000, 'славян': 132000,
    'старомин': 40000, 'тбилис': 48000, 'темрюк': 124000, 'тимашев': 105000,
    'тихорец': 114000, 'туапсин': 128000, 'успен': 40000,
    'щербинов': 35000
}


# ==========================================
# ОБЪЕДИНЕННАЯ БАЗА ДАННЫХ ЭКОНОМИКИ (ВРП, млрд руб.)
# ==========================================
KNOWN_ECONOMY = {
    # 1. Города федерального значения и составные / специфичные основы (ДОЛЖНЫ идти ДО общих корней)
    'санкт-петербург': 7300,
    'петербург': 7300,
    'севастопол': 240,
    'московск': 7100,
    'москв': 24400,
    'ростов-на-дону': 650,
    'ростов': 2200,
    'краснодарск': 3500,
    'краснодар': 950,
    'приморско-ахтар': 35,       # Должен идти ДО 'примор'
    'усть-лабин': 45,           # Должен идти ДО 'лабин' и 'абин'
    'лабин': 40,                 # Должен идти ДО 'абин'
    'абинск': 42,
    'красноармей': 48,          # Должен идти ДО 'ейск'
    'матвеево-курган': 22,       # Должен идти ДО 'курган'
    'курганин': 45,             # Должен идти ДО 'курган'
    'курган': 310,
    'усть-донец': 18,            # Должен идти ДО 'донецк'
    'донецк': 25,
    'волгодонской': 24,          # Должен идти ДО 'волгодонск'
    'волгодонск': 120,
    'каменск-шахтинск': 55,      # Должен идти ДО 'каменск'
    'каменск': 25,
    'азовск': 45,               # Должен идти ДО 'азов'
    'азов': 50,
    'сахалин': 1300,             # Должен идти ДО 'саха'
    'саха': 1800,
    'якут': 1800,
    'алтайск': 850,              # Должен идти ДО 'алтай'
    'алтай': 70,
    'костром': 240,              # Должен идти ДО 'омск'
    'томск': 650,                # Должен идти ДО 'омск'
    'омск': 850,
    'ямал': 4300,                # Должен идти ДО 'ненец'
    'янао': 4300,
    'ненец': 390,
    'чечен': 280,                # Должен идти ДО 'ингуш'
    'ингуш': 85,
    'ленинградская область': 1600,
    'орловская область': 320,
    'орел': 320,
    'калининград': 700,

    # 2. Субъекты РФ (по основам)
    'хмао': 5900,
    'ханты': 5900,
    'татар': 3300,
    'свердлов': 3200,
    'краснояр': 3100,
    'башкорт': 2100,
    'самар': 2100,
    'челябин': 2100,
    'нижегород': 2000,
    'иркут': 1900,
    'кемеров': 1800,
    'новосиб': 1700,
    'перм': 1700,
    'тюмен': 1400,
    'примор': 1300,
    'оренбург': 1300,
    'воронеж': 1250,
    'белгород': 1200,
    'волгоград': 1100,
    'саратов': 1050,
    'ставропол': 1000,
    'хабаров': 950,
    'тульск': 950,
    'дагестан': 850,
    'мурман': 850,
    'удмурт': 850,
    'липецк': 800,
    'вологод': 800,
    'коми': 780,
    'архангель': 750,
    'астрахан': 700,
    'ярослав': 680,
    'калуж': 650,
    'курск': 650,
    'владимир': 650,
    'твер': 550,
    'амур': 550,
    'пензен': 550,
    'рязан': 550,
    'ульянов': 500,
    'брянск': 480,
    'забайкал': 450,
    'смолен': 450,
    'киров': 450,
    'чуваш': 420,
    'тамбов': 420,
    'карел': 380,
    'бурят': 350,
    'камчат': 340,
    'новгород': 340,
    'мордов': 330,
    'хакас': 320,
    'иванов': 320,
    'магадан': 280,
    'псков': 240,
    'марий': 240,
    'северная осетия': 210,
    'осетия': 210,
    'осетин': 210,
    'кабардин': 220,
    'адыге': 180,
    'чукот': 160,
    'карача': 120,
    'калмык': 110,
    'тыва': 90,
    'тува': 90,
    'еврей': 75,
    'врей': 75,

    # 3. Районы и города Ростовской области
    'таганрог': 140, 'шахты': 110,
    'новочеркасск': 95, 'батайск': 75, 'новошахтинск': 50,
    'гуково': 28, 'зверево': 15,
    'аксай': 80, 'белокалитвин': 45, 'сальск': 45, 'мясников': 35,
    'красносулин': 42, 'миллеров': 38, 'морозов': 25, 'зерноград': 32,
    'семикаракор': 28, 'октябрьск': 40, 'неклинов': 45,
    'багаев': 20, 'константинов': 20, 'цимлян': 24, 'шолохов': 18,
    'чертков': 20, 'тацин': 22, 'орлов': 24, 'пролетар': 22,
    'песчанокоп': 18, 'ремонтнен': 14, 'заветин': 12,
    'дубов': 15, 'зимовников': 24, 'кагальниц': 20, 'кашар': 16,
    'куйбышев': 10, 'мартынов': 24, 'милютин': 10, 'облив': 12,
    'родионово-несветай': 16, 'советск': 6, 'тарасов': 18,
    'целин': 20, 'боков': 11, 'верхнедон': 12, 'веселов': 16, 'егорлык': 22,

    # 4. Краснодарский край (Городские округа и районы)
    'новороссийск': 280, 'сочи': 240, 'армавир': 90,
    'анапа': 85, 'геленджик': 65, 'горячий ключ': 35,
    'апшерон': 45, 'белоглин': 20, 'белоречен': 55,
    'брюховец': 30, 'выселк': 35, 'гулькевич': 50, 'динск': 75,
    'ейск': 70, 'кавказ': 65, 'калинин': 30, 'канев': 55,
    'коренов': 45, 'крылов': 22, 'крымск': 65,
    'кущев': 40, 'ленинград': 38,
    'мостов': 35, 'новокубан': 45, 'новопокров': 25, 'отраднен': 35,
    'павлов': 38, 'северск': 60, 'славян': 70,
    'старомин': 25, 'тбилис': 28, 'темрюк': 75, 'тимашев': 65,
    'тихорец': 60, 'туапсин': 80, 'туапсе': 80, 'успен': 24,
    'щербинов': 22
}


class InteractiveAtlas:
    def __init__(self, region_key=None, region_name=None, region_districts=None, clipped_rivers=None, clipped_lakes=None, clipped_cities=None, is_rf=False):
        # Автоматическое определение: передан ли region_key или region_name
        cfg = None
        if isinstance(region_key, str) and region_key.lower() in REGIONS_CONFIG:
            self.region_key = region_key.lower()
            cfg = REGIONS_CONFIG[self.region_key]
        elif isinstance(region_name, str) and region_name.lower() in REGIONS_CONFIG:
            self.region_key = region_name.lower()
            cfg = REGIONS_CONFIG[self.region_key]
        elif region_key in ['rf', 'Российская Федерация', 'россия']:
            self.region_key = 'russia'
            cfg = REGIONS_CONFIG['russia']
        elif region_name in ['rf', 'Российская Федерация', 'россия']:
            self.region_key = 'russia'
            cfg = REGIONS_CONFIG['russia']
        else:
            self.region_key = None

        self.cfg = cfg
        if cfg:
            self.ru_title = cfg['title']
            self.region_name = cfg['title']
            self.is_rf = cfg.get('is_rf', False)
            self.slug = self.region_key
            self.output_filename = cfg.get('output', f"{self.slug}_quiz_map.html")
            self.center = cfg['center']
            self.zoom = cfg['zoom']
        else:
            self.region_name = str(region_name or region_key or 'Регион').strip()
            self.is_rf = is_rf
            self.ru_title = REGION_TRANSLATIONS.get(self.region_name, self.region_name)
            self.slug = slugify_name(self.region_name)
            self.output_filename = f"{self.slug}_quiz_map.html"
            self.center = [55.75, 37.61]
            self.zoom = 7

        self.title = f"Интерактивный атлас: {self.ru_title}"

        self.input_districts = region_districts
        self.input_rivers = clipped_rivers
        self.input_lakes = clipped_lakes
        self.input_cities = clipped_cities

        # Вычисляем индивидуальный центр и zoom карты через total_bounds (для нарезанных регионов)
        if not self.cfg and self.input_districts is not None and not self.input_districts.empty:
            bounds = self.input_districts.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2.0
            center_lon = (bounds[0] + bounds[2]) / 2.0
            self.center = [center_lat, center_lon]
            lat_diff = abs(bounds[3] - bounds[1])
            lon_diff = abs(bounds[2] - bounds[0])
            max_diff = max(lat_diff, lon_diff)
            if max_diff > 25: self.zoom = 4
            elif max_diff > 12: self.zoom = 5
            elif max_diff > 6: self.zoom = 6
            elif max_diff > 3: self.zoom = 7
            elif max_diff > 1.5: self.zoom = 8
            else: self.zoom = 9

        # Инициализируем карту без жестко привязанной подложки, добавляем 3 переключаемые подложки
        self.map = folium.Map(
            location=self.center,
            zoom_start=self.zoom,
            control_scale=True,
            tiles=None,
            width='100%',
            height='100%'
        )

        # Фит границ только для локальных нарезанных регионов (не для РФ, чтобы не ломать начальный масштаб)
        if not self.is_rf and not self.cfg and self.input_districts is not None and not self.input_districts.empty:
            bounds = self.input_districts.total_bounds
            self.map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # 1. Светлая подложка (Carto Voyager) - по умолчанию
        folium.TileLayer(
            tiles=f'https://basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}',
            name='Carto Voyager',
            attr='© OpenStreetMap contributors, © CARTO',
            control=True,
            show=True
        ).add_to(self.map)

        # 2. Спутниковая подложка (Esri World Imagery)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            name='Спутник (Esri)',
            attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            control=True,
            show=False
        ).add_to(self.map)

        # 3. Темная тема (CartoDB dark_matter)
        folium.TileLayer(
            tiles=f'https://basemaps.cartocdn.com/rastertiles/dark_all/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}',
            name='Темная тема (Carto)',
            attr='© OpenStreetMap contributors, © CARTO',
            control=True,
            show=False
        ).add_to(self.map)

        self.districts_gdf = None
        self.centers_gdf = None
        self.rivers_gdf = None

    def _fix_antimeridian(self, geom):
        if geom is None or geom.is_empty or not geom.is_valid:
            return geom
            
        try:
            if geom.geom_type == 'Polygon':
                exterior = [(x + 360 if x < 0 else x, y) for x, y in geom.exterior.coords]
                interiors = [[(x + 360 if x < 0 else x, y) for x, y in interior.coords] for interior in geom.interiors]
                return Polygon(exterior, interiors)
            elif geom.geom_type == 'MultiPolygon':
                return MultiPolygon([self._fix_antimeridian(p) for p in geom.geoms])
            elif geom.geom_type == 'LineString':
                return LineString([(x + 360 if x < 0 else x, y) for x, y in geom.coords])
            elif geom.geom_type == 'MultiLineString':
                return MultiLineString([self._fix_antimeridian(ls) for ls in geom.geoms])
            elif geom.geom_type == 'Point':
                # Точки НЕ сдвигаем за 180 меридиан, иначе в Leaflet маркеры улетают за пределы карты
                return geom
        except Exception:
            pass
            
        return geom

    # БРОНЕБОЙНЫЙ ПРЕДОХРАНИТЕЛЬ CRS
    def _safe_to_crs(self, gdf):
        if gdf is None or gdf.empty:
            return gdf
            
        try:
            if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            elif not gdf.crs:
                b = gdf.total_bounds
                if (-360 <= b[0] <= 360) and (-90 <= b[1] <= 90) and (-360 <= b[2] <= 360) and (-90 <= b[3] <= 90):
                    gdf = gdf.set_crs('EPSG:4326')
                else:
                    gdf = gdf.set_crs('EPSG:3857').to_crs('EPSG:4326')
        except Exception as e:
            b = gdf.total_bounds
            is_degrees = (-360 <= b[0] <= 360) and (-90 <= b[1] <= 90) and (-360 <= b[2] <= 360) and (-90 <= b[3] <= 90)
            
            if is_degrees:
                gdf = gdf.set_crs('EPSG:4326', allow_override=True)
            else:
                try:
                    gdf = gdf.set_crs('EPSG:3857', allow_override=True).to_crs('EPSG:4326')
                except Exception:
                    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                    
        # Очистка и восстановление геометрии
        gdf = gdf.dropna(subset=['geometry'])
        bounds = gdf.bounds
        gdf = gdf[~bounds.isna().any(axis=1)]
        gdf = gdf[~gdf.geometry.is_empty]
        try:
            gdf['geometry'] = gdf['geometry'].apply(clean_geom)
        except Exception:
            pass
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        
        # Фикс Чукотки и территорий за 180 меридианом
        try:
            gdf.geometry = gdf.geometry.apply(self._fix_antimeridian)
        except Exception:
            pass
        
        # Упрощение полигонов: ТОЛЬКО для карты всей России (для сохранения компактного размера)
        if getattr(self, 'is_rf', False) or getattr(self, 'region_key', '') == 'russia':
            try:
                gdf.geometry = gdf.geometry.simplify(0.015, preserve_topology=True)
            except Exception:
                pass
                
        return gdf

    def _load_gdf(self, source, layer_key):
        """Загружает GeoDataFrame из переданного объекта, пути файла или из REGIONS_CONFIG / input_*."""
        if isinstance(source, gpd.GeoDataFrame):
            return source.copy()
        if isinstance(source, str) and source and os.path.exists(source):
            return gpd.read_file(source)
        if source is None and self.cfg and layer_key:
            fname = self.cfg.get('files', {}).get(layer_key)
            if fname:
                fpath = os.path.join(self.cfg['path'], fname)
                if os.path.exists(fpath):
                    return gpd.read_file(fpath)
        input_map = {
            'districts': self.input_districts,
            'rivers': self.input_rivers,
            'water_bodies': self.input_lakes,
            'district_centers': self.input_cities
        }
        fallback = input_map.get(layer_key)
        if isinstance(fallback, gpd.GeoDataFrame) and not fallback.empty:
            return fallback.copy()
        return None

    def _extract_valid_name(self, row, preferred_order=None):
        if preferred_order is None:
            if getattr(self, 'is_rf', False) or getattr(self, 'region_key', '') == 'russia':
                preferred_order = ['NL_NAME_1', 'NAME_1', 'NAME_RU', 'NAME_RWIN', 'NAME', 'name', 'REGION_NAM']
            else:
                preferred_order = ['NAME_RU', 'NAME', 'NL_NAME_2', 'NAME_2', 'NL_NAME_1', 'NAME_1', 'name']

        for col in preferred_order:
            if col in row.index and row[col] is not None:
                val = str(row[col]).strip()
                if val and val.lower() not in ['none', 'nan', 'null', '', 'na', 'n/a', '<null>']:
                    val = val.replace('\u0301', '').strip()
                    if val.endswith(')') and '(' not in val:
                        val = val.rstrip(')').strip()
                    if val in DISTRICT_TRANSLATIONS:
                        return DISTRICT_TRANSLATIONS[val]
                    if val in REGION_TRANSLATIONS:
                        return REGION_TRANSLATIONS[val]
                    translations = {
                        'Moscow City': 'Москва', 'Moskva': 'Московская область', 'Moscow': 'Москва',
                        'Saint Petersburg': 'Санкт-Петербург', 'St. Petersburg': 'Санкт-Петербург',
                        'Sankt-Peterburg': 'Санкт-Петербург', 'City of St. Petersburg': 'Санкт-Петербург',
                        'Sevastopol': 'Севастополь', 'Sevastopol City': 'Севастополь'
                    }
                    return translations.get(val, val)
        return ''

    def _clean_river_name(self, name):
        if not name or str(name).lower() in ['none', 'nan', 'null', '']:
            return ''
        n = str(name).strip().replace('река ', '').replace('р. ', '').replace('р.', '').replace('"', '').strip()
        for key in ['Маныч', 'Северский Донец', 'Калитва', 'Тузлов', 'Сал', 'Волга', 'Обь', 'Енисей', 'Лена', 'Амур', 'Кубань']:
            if key in n:
                return key
        return n

    def add_districts(self, gdf=None):
        gdf = self._load_gdf(gdf, 'districts')
        if gdf is None or gdf.empty:
            return None
        
        gdf = gdf.copy()
        gdf = self._safe_to_crs(gdf)
        if gdf is None or gdf.empty:
            return None
        
        gdf['display_name'] = gdf.apply(lambda r: self._extract_valid_name(r), axis=1)
        gdf['display_name'] = gdf['display_name'].apply(lambda n: n if n else self.ru_title)
        
        # МАГИЧЕСКАЯ МЕТКА: отделяет территории от гидрографии
        gdf['is_district_layer'] = 1
        self.districts_gdf = gdf

        tooltip = folium.GeoJsonTooltip(
            fields=['display_name'],
            aliases=[''],
            style="background: white; border: 1px solid #CBD5E1; padding: 4px 8px; font-weight: 700; font-size: 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);"
        )

        folium.GeoJson(
            gdf,
            name=LAYER_NAMES['districts'],
            style_function=lambda x: STYLES['districts'],
            tooltip=tooltip,
            interactive=True
        ).add_to(self.map)
        return gdf

    def add_water_bodies(self, gdf=None):
        gdf = self._load_gdf(gdf, 'water_bodies')
        if gdf is None or gdf.empty:
            return None
        
        gdf = gdf.copy()
        gdf = self._safe_to_crs(gdf)
        if gdf is None or gdf.empty:
            return None

        def extract_lake_name(row):
            for col in ['name_ru', 'NAME_RU', 'name', 'NAME', 'name_en']:
                if col in row.index and row[col] is not None:
                    v = str(row[col]).strip()
                    if v and v.lower() not in ['none', 'nan', 'null', '']:
                        return v
            return 'Водоем'

        gdf['display_name'] = gdf.apply(extract_lake_name, axis=1)

        tooltip = folium.GeoJsonTooltip(
            fields=['display_name'],
            aliases=[''],
            style="background: white; border: 1px solid #CBD5E1; padding: 4px 8px; font-weight: 700; font-size: 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);"
        )

        folium.GeoJson(
            gdf,
            name=LAYER_NAMES['water_bodies'],
            style_function=lambda x: STYLES['water_bodies'],
            tooltip=tooltip,
            interactive=True
        ).add_to(self.map)
        return gdf

    def add_rivers(self, gdf=None):
        gdf = self._load_gdf(gdf, 'rivers')
        if gdf is None or gdf.empty:
            return None
        
        gdf = gdf.copy()
        for col in ['waterway', 'WATERWAY']:
            if col in gdf.columns:
                gdf = gdf[gdf[col].astype(str).str.lower().isin(['river', 'stream', 'canal', 'waterway', 'drain'])]
                break

        if 'TYPE' in gdf.columns:
            gdf = gdf[gdf['TYPE'].astype(str).str.lower().isin(['река', 'протока', 'канал', 'river'])]
                    
        gdf = self._safe_to_crs(gdf)
        if gdf is None or gdf.empty:
            return None

        def extract_river_name(row):
            for col in ['name_ru', 'NAME_RU', 'name', 'NAME', 'name_en']:
                if col in row.index and row[col] is not None:
                    v = str(row[col]).strip()
                    if v and v.lower() not in ['none', 'nan', 'null', '']:
                        return v
            return ''

        gdf['raw_name'] = gdf.apply(extract_river_name, axis=1)
        gdf['clean_name'] = gdf['raw_name'].apply(self._clean_river_name)

        named = gdf[gdf['clean_name'] != '']
        if not named.empty:
            named = named.dissolve(by='clean_name').reset_index()
        unnamed = gdf[gdf['clean_name'] == ''].copy()
        unnamed['clean_name'] = 'Водоток'

        if named.empty:
            all_rivers = unnamed
        elif unnamed.empty:
            all_rivers = named
        else:
            all_rivers = gpd.pd.concat([named, unnamed], ignore_index=True)

        if all_rivers.empty:
            return None

        all_rivers['display_name'] = all_rivers['clean_name']
        self.rivers_gdf = all_rivers

        tooltip = folium.GeoJsonTooltip(
            fields=['display_name'],
            aliases=[''],
            style="background: white; border: 1px solid #CBD5E1; padding: 4px 8px; font-weight: 700; font-size: 12px; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);"
        )

        folium.GeoJson(
            all_rivers,
            name=LAYER_NAMES['rivers'],
            style_function=lambda x: STYLES['rivers'],
            tooltip=tooltip,
            interactive=True
        ).add_to(self.map)

        return all_rivers

    def add_district_centers(self, gdf=None):
        gdf = self._load_gdf(gdf, 'district_centers')
        if gdf is None or gdf.empty:
            return None
        
        gdf = gdf.copy()
        
        # 1. Если есть колонка CAPITAL (как в Cities.shp для РФ) — оставляем только столицы регионов
        if 'CAPITAL' in gdf.columns:
            gdf = gdf[gdf['CAPITAL'].astype(str).str.strip().str.lower().isin(['c', 'с'])].copy()

        gdf = self._safe_to_crs(gdf)
        if gdf is None or gdf.empty:
            return None
        
        def get_city_name(row):
            for col in ['NAME_RWIN', 'NAME_RU', 'name_ru', 'NAME', 'name', 'NAME_EN', 'name_en', 'CITY_NAME']:
                if col in row.index and row[col] is not None:
                    val = str(row[col]).strip()
                    if val and val.lower() not in ['none', 'nan', 'null', '']:
                        return val
            return ''

        gdf['clean_name'] = gdf.apply(get_city_name, axis=1)

        point_gdf = gdf[gdf.geometry.type == 'Point']
        if len(point_gdf) == 0:
            point_gdf = gdf.copy()
            point_gdf['geometry'] = point_gdf.geometry.centroid

        feature_group = folium.FeatureGroup(name="Центры")
        valid_indices = []

        for idx, row in point_gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            lon = float(geom.x if hasattr(geom, 'x') else geom.centroid.x)
            lat = float(geom.y if hasattr(geom, 'y') else geom.centroid.y)

            # Строгая фильтрация координат: точка должна лежать в пределах территории РФ
            if not (19.0 <= lon <= 180.0 and 41.0 <= lat <= 82.0):
                continue

            valid_indices.append(idx)
            name = row['clean_name'] or f"Центр {idx}"
            status = str(row.get('STATUS', row.get('FEATURECLA', row.get('OFFICIAL_S', row.get('place', 'город'))))).replace('ru:', '')
            if status in ['city', 'Admin-1 capital']: status = 'центр региона'
            elif status == 'town': status = 'город'
            elif status == 'village': status = 'село/поселок'

            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{name}</b><br>Тип: {status}",
                tooltip=name,
                icon=folium.Icon(color='orange', icon='star', prefix='fa')
            ).add_to(feature_group)

        feature_group.add_to(self.map)
        self.centers_gdf = point_gdf.loc[valid_indices].copy() if valid_indices else point_gdf
        return self.centers_gdf

    def _calculate_neighbors_data(self):
        if self.districts_gdf is None or len(self.districts_gdf) == 0:
            return []

        valid_gdf = self.districts_gdf[self.districts_gdf.geometry.is_valid & ~self.districts_gdf.geometry.is_empty].copy()
        valid_gdf = valid_gdf[valid_gdf['display_name'] != ''].copy()
        
        try:
            # Цилиндрическая равновеликая проекция (Cylindrical Equal-Area) без искажения площадей
            metric_gdf = valid_gdf.to_crs('EPSG:6933')
        except Exception:
            metric_gdf = valid_gdf
            
        neighbors_data = []

        centers_wgs = None
        if self.centers_gdf is not None and not self.centers_gdf.empty:
            try:
                centers_wgs = self.centers_gdf.to_crs('EPSG:4326')
            except Exception:
                centers_wgs = self.centers_gdf

        for idx, row in valid_gdf.iterrows():
            current_geom = row.geometry
            current_name = str(row['display_name'])
            buffered_geom = current_geom.buffer(0.005)
            intersecting_rows = valid_gdf[valid_gdf.geometry.intersects(buffered_geom)]
            neighbor_names = [str(n) for n in intersecting_rows['display_name'].tolist() if str(n) != current_name and str(n).strip()]
            
            center_name = "Административный центр"
            if centers_wgs is not None and not centers_wgs.empty:
                matched_c = centers_wgs[centers_wgs.geometry.within(current_geom)]
                if not matched_c.empty:
                    c_val = matched_c.iloc[0].get('clean_name') or matched_c.iloc[0].get('NAME_RWIN') or matched_c.iloc[0].get('NAME_RU') or matched_c.iloc[0].get('NAME') or ''
                    status = matched_c.iloc[0].get('STATUS', matched_c.iloc[0].get('OFFICIAL_S', ''))
                    status_clean = str(status).replace('ru:', '') if status else ''
                    center_name = f"{c_val} ({status_clean})" if status_clean else str(c_val)

            area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if idx in metric_gdf.index else 0

            # === УМНЫЙ ПОИСК НАСЕЛЕНИЯ ===
            population = None
            search_name = current_name.lower().replace('\u0301', '').replace('e', 'е').replace('ё', 'е')
            
            for key, val in KNOWN_POPULATION.items():
                if key in search_name:
                    population = val
                    break
                    
            if population is None:
                if 'область' in search_name:
                    population = int(area_sq_km * 20)
                elif 'республика' in search_name:
                    population = int(area_sq_km * 10)
                elif 'край' in search_name:
                    population = int(area_sq_km * 5)
                elif 'округ' in search_name or 'аок' in search_name:
                    population = int(area_sq_km * 1)
                else:
                    population = int(area_sq_km * 25)

            # === УМНЫЙ ПОИСК / РАСЧЕТ ВРП (ЭКОНОМИКА) ===
            grp = None
            for key, val in KNOWN_ECONOMY.items():
                if key in search_name:
                    grp = float(val)
                    break

            if grp is None:
                if population == 0:
                    grp = 0.0
                elif population > 500_000:
                    grp = round(population * 1.2 / 1000, 1)
                else:
                    grp = round(population * 0.85 / 1000, 1)
            else:
                grp = round(grp, 1)

            neighbors_data.append({
                'name': current_name,
                'center': center_name,
                'area': area_sq_km,
                'population': population,
                'grp': grp,
                'neighbors': list(set(neighbor_names))
            })
        return neighbors_data

    def _extract_rivers_data(self):
        if self.rivers_gdf is None or len(self.rivers_gdf) == 0:
            return []
        
        named_rivers = self.rivers_gdf[
            (self.rivers_gdf['clean_name'] != '') & 
            (self.rivers_gdf['clean_name'] != 'Водоток')
        ].copy()

        if named_rivers.empty:
            return []

        try:
            from pyproj import Geod
            geod = Geod(ellps='WGS84')

            def unshift_geom(geom):
                if geom is None or geom.is_empty:
                    return geom
                def fix_coords(coords):
                    return [(x - 360 if x > 180 else (x + 360 if x < -180 else x), y) for x, y in coords]
                if geom.geom_type == 'LineString':
                    return LineString(fix_coords(geom.coords))
                elif geom.geom_type == 'MultiLineString':
                    return MultiLineString([LineString(fix_coords(ls.coords)) for ls in geom.geoms])
                return geom

            lengths = []
            for _, r in named_rivers.iterrows():
                geom = r.geometry
                if geom is None or geom.is_empty:
                    lengths.append(0.0)
                else:
                    try:
                        clean_g = unshift_geom(geom)
                        l_km = round(geod.geometry_length(clean_g) / 1000.0, 1)
                        lengths.append(l_km)
                    except Exception:
                        lengths.append(0.0)
            named_rivers['length_km'] = lengths
        except Exception:
            try:
                metric_rivers = named_rivers.to_crs('EPSG:6933')
                named_rivers['length_km'] = (metric_rivers.geometry.length / 1000).round(1)
            except Exception:
                named_rivers['length_km'] = 0.0
            
        top_rivers = named_rivers.sort_values(by='length_km', ascending=False).head(35)
        return [{"name": str(r['clean_name']), "length": float(r['length_km'])} for _, r in top_rivers.iterrows()]

    def add_quiz_controls(self):
        neighbors_data = self._calculate_neighbors_data()
        rivers_data = self._extract_rivers_data()
        districts_data = [{"name": d['name']} for d in neighbors_data if d['name'].strip()]
        centers_data = []
        if self.centers_gdf is not None:
            for idx, row in self.centers_gdf.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue
                lon = float(geom.x if hasattr(geom, 'x') else geom.centroid.x)
                lat = float(geom.y if hasattr(geom, 'y') else geom.centroid.y)
                if not (19.0 <= lon <= 180.0 and 41.0 <= lat <= 82.0):
                    continue
                st = str(row.get('STATUS', row.get('OFFICIAL_S', 'город'))).replace('ru:', '')
                name = row.get('clean_name') or row.get('NAME_RWIN') or row.get('NAME') or f"Центр {idx}"
                centers_data.append({
                    "name": str(name),
                    "status": st,
                    "lat": lat,
                    "lon": lon
                })

        if self.districts_gdf is not None and not self.districts_gdf.empty:
            bounds = self.districts_gdf.total_bounds
            region_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
        else:
            region_bounds = [[self.center[0]-1, self.center[1]-1], [self.center[0]+1, self.center[1]+1]]

        puzzle_districts = []
        region_outline_geojson = None

        if self.districts_gdf is not None and not self.districts_gdf.empty:
            import shapely.geometry
            valid_districts = self.districts_gdf[self.districts_gdf.geometry.is_valid & ~self.districts_gdf.geometry.is_empty].copy()
            valid_districts = valid_districts[valid_districts['display_name'] != ''].copy()

            try:
                if hasattr(valid_districts, 'union_all'):
                    region_union = valid_districts.union_all()
                else:
                    region_union = valid_districts.unary_union
                if region_union is not None and not region_union.is_empty:
                    simplified_union = region_union.simplify(0.003, preserve_topology=True)
                    region_outline_geojson = shapely.geometry.mapping(simplified_union)
            except Exception:
                region_outline_geojson = None

            neighbor_lookup = {d['name']: d for d in neighbors_data}

            # Топологический расчет соседства районов для режима конструктора
            district_list = []
            for idx, row in valid_districts.iterrows():
                if row.geometry is not None and not row.geometry.is_empty:
                    d_name = str(row.get('NL_NAME_2') or row.get('display_name') or row.get('NAME_2') or row.get('NAME_RU') or row.get('NAME') or f"Район {idx}")
                    district_list.append((idx, row.geometry, d_name))

            district_neighbors_map = {}
            for idx, geom, d_name in district_list:
                b_geom = geom.buffer(0.006)
                n_ids = []
                n_names = []
                for other_idx, other_geom, other_name in district_list:
                    if other_idx != idx and other_geom.intersects(b_geom):
                        n_ids.append(f"dist_{other_idx}")
                        n_names.append(other_name)
                n_info = neighbor_lookup.get(d_name, {})
                for ext_name in n_info.get('neighbors', []):
                    if ext_name and ext_name not in n_names:
                        n_names.append(str(ext_name))
                district_neighbors_map[idx] = {
                    "neighbor_ids": n_ids,
                    "neighbor_names": n_names
                }

            for idx, row in valid_districts.iterrows():
                geom = row.geometry
                if geom is None or geom.is_empty:
                    continue

                d_name = str(row.get('NL_NAME_2') or row.get('display_name') or row.get('NAME_2') or row.get('NAME_RU') or row.get('NAME') or f"Район {idx}")

                try:
                    simp_geom = geom.simplify(0.002, preserve_topology=True)
                    if simp_geom is None or simp_geom.is_empty:
                        simp_geom = geom
                except Exception:
                    simp_geom = geom

                geojson_geom = shapely.geometry.mapping(simp_geom)
                centroid = geom.centroid
                c_lat = round(float(centroid.y), 5)
                c_lon = round(float(centroid.x), 5)
                b = geom.bounds
                bounds = [[round(b[1], 5), round(b[0], 5)], [round(b[3], 5), round(b[2], 5)]]

                n_info = neighbor_lookup.get(d_name, {})
                center_info = n_info.get('center', '')
                area_info = n_info.get('area', 0)
                n_map = district_neighbors_map.get(idx, {"neighbor_ids": [], "neighbor_names": []})

                puzzle_districts.append({
                    "id": f"dist_{idx}",
                    "name": d_name,
                    "center": center_info,
                    "area": area_info,
                    "centroid": [c_lat, c_lon],
                    "bounds": bounds,
                    "geojson": geojson_geom,
                    "neighbor_ids": n_map["neighbor_ids"],
                    "neighbors": n_map["neighbor_names"]
                })

        server_ctx = {
            "region": self.region_key or self.slug,
            "title": self.ru_title,
            "center": self.center,
            "zoom": self.zoom,
            "map_url": self.output_filename,
            "is_rf": getattr(self, 'is_rf', False)
        }
        server_ctx_json = json.dumps(server_ctx, ensure_ascii=False)

        dynamic_js = f'''
const REGION_BOUNDS = {json.dumps(region_bounds)};
const EMBEDDED_DISTRICTS = {json.dumps(districts_data, ensure_ascii=False)};
const EMBEDDED_CENTERS = {json.dumps(centers_data, ensure_ascii=False)};
const EMBEDDED_NEIGHBORS = {json.dumps(neighbors_data, ensure_ascii=False)};
const EMBEDDED_RIVERS = {json.dumps(rivers_data, ensure_ascii=False)};
const EMBEDDED_PUZZLE_DATA = {json.dumps(puzzle_districts, ensure_ascii=False)};
const REGION_OUTLINE_GEOJSON = {json.dumps(region_outline_geojson, ensure_ascii=False)};
const SERVER_REGION_CONTEXT = {server_ctx_json};
window.SERVER_REGION_CONTEXT = SERVER_REGION_CONTEXT;
window.currentRegionKey = {json.dumps(self.region_key or self.slug)};
window.currentRegionTitle = {json.dumps(self.ru_title)};
window.serverMapCenter = {json.dumps(self.center)};
window.serverMapZoom = {self.zoom};
'''

        quiz_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quiz.js')
        with open(quiz_js_path, 'r', encoding='utf-8') as f:
            quiz_js = f.read()

        self.map.get_root().html.add_child(folium.Element(f"<script>{dynamic_js}\n{quiz_js}</script>"))

        quiz_html = f'''
        <div class="top-nav-buttons" id="top-nav-panel">
            <button class="btn btn-secondary nav-top-btn reset-map-btn" onclick="resetMapView()" title="Показать всю карту">
                <span>🌍 Вся карта</span>
            </button>
            <button class="btn btn-secondary nav-top-btn admin-btn" onclick="window.open('/admin', '_blank')" title="Панель преподавателя">
                <span>📊 Преподавателю</span>
            </button>
            <button id="auth-top-btn" class="btn btn-primary nav-top-btn auth-btn" onclick="goToMainAuth()" title="Авторизация через главное меню">
                <span>🎓 Войти через Главное меню</span>
            </button>
            <div id="student-profile-badge" class="student-badge" style="display: none;">
                <div class="badge-avatar">🎓</div>
                <div class="badge-info">
                    <span id="student-badge-name" class="badge-name">Студент</span>
                    <span id="student-badge-group" class="badge-group">Группа</span>
                </div>
                <button onclick="logoutStudent()" class="badge-logout" title="Выйти">&times;</button>
            </div>
            <button class="btn btn-secondary nav-top-btn leaderboard-top-btn" onclick="showLeaderboard()" title="Глобальная таблица лидеров и профиль">🏆 Топ лидеров</button>
            <button class="btn btn-secondary help-circle-btn" onclick="openWelcomeModal()" title="О проекте и справка">?</button>
        </div>

        <div id="quiz-controls" class="app-card">
            <div class="panel-header">
                <div class="panel-header-bar">
                    <div class="panel-institution-badge">ЮФУ • Институт наук о Земле</div>
                    <button id="panel-collapse-btn" class="mobile-collapse-trigger btn-icon" onclick="togglePanelCollapse()" aria-label="Свернуть/развернуть панель" title="Свернуть панель к карте">
                        <svg class="collapse-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                </div>
                <h3>Учебно-картографический атлас</h3>
            </div>

            <!-- ГЛАВНОЕ МЕНЮ -->
            <div id="normal-mode">
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; margin: 0 0 6px 0; text-align: center;">
                    Обучающий режим
                </div>
                <div class="study-pick-grid">
                    <button onclick="startStudyMode('districts')" class="btn btn-study-action">🗺️ Территории</button>
                    <button onclick="startStudyMode('rivers')" class="btn btn-study-action">🌊 Реки</button>
                    <button onclick="startStudyMode('centers')" class="btn btn-study-action">📍 Центры</button>
                </div>

                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; margin: 12px 0 6px 0; text-align: center;">
                    Проверка знаний (Викторины)
                </div>

                <div class="btn-group-vertical">
                    <button onclick="openExamModal()" class="btn btn-exam btn-block" id="btn-open-exam">
                        <span>📝 Экзамен</span>
                    </button>

                    <button onclick="startPuzzleMode()" class="btn btn-puzzle btn-block" id="btn-start-puzzle">
                        <span>🧩 Собрать пазл</span>
                    </button>

                    <button onclick="startDistrictQuiz()" class="btn btn-district btn-block" id="btn-start-district">
                        <span>🗺️ Угадать силуэт</span>
                    </button>

                    <button onclick="startNeighborQuiz()" class="btn btn-neighbor btn-block" id="btn-start-neighbor">
                        <span>🔗 Топология</span>
                    </button>

                    <button onclick="startRiverQuiz()" class="btn btn-river btn-block" id="btn-start-river">
                        <span>🌊 Определение реки</span>
                    </button>

                    <button onclick="startCenterQuiz()" class="btn btn-center btn-block" id="btn-start-center">
                        <span>📍 Поиск центра</span>
                    </button>
                </div>

                <div class="timer-setting-box">
                    <label class="checkbox-container">
                        <input type="checkbox" id="timer-toggle" onchange="toggleTimer()">
                        <span>Включить таймер (20с на ответ)</span>
                    </label>
                </div>

                <div id="district-info-card" class="district-info-box">
                </div>

                <div class="hint-small">
                    Кликните на любой район на карте для вывода гео-справки
                </div>
            </div>

            <!-- РЕЖИМ ОБУЧЕНИЯ (МУЛЬТИКАТЕГОРИИ) -->
            <div id="study-mode" style="display: none;">
                <div class="study-category-bar">
                    <button id="study-tab-districts" onclick="switchStudyCategory('districts')" class="study-cat-tab">🗺️ Территории</button>
                    <button id="study-tab-rivers" onclick="switchStudyCategory('rivers')" class="study-cat-tab">🌊 Реки</button>
                    <button id="study-tab-centers" onclick="switchStudyCategory('centers')" class="study-cat-tab">📍 Центры</button>
                </div>

                <div class="study-status-header">
                    <h4>Режим изучения</h4>
                    <span id="study-counter-val">1 / 55</span>
                </div>

                <div id="study-content-box" class="study-card-body">
                </div>

                <div class="study-nav-grid">
                    <button onclick="prevStudyItem()" class="btn btn-secondary">← Назад</button>
                    <button onclick="nextStudyItem()" class="btn btn-primary">Вперед →</button>
                </div>
                <div class="btn-group-vertical" style="margin-top: 8px;">
                    <button onclick="randomStudyItem()" class="btn btn-secondary btn-block">
                        🎲 Случайный объект
                    </button>
                    <button onclick="exitStudyMode()" class="btn btn-danger btn-block">
                        Выйти в меню
                    </button>
                </div>
            </div>

            <!-- РЕЖИМ ПАЗЛА (СОБЕРИ РЕГИОН) -->
            <div id="puzzle-mode" style="display: none;">
                <div class="puzzle-header">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="margin: 0; font-size: 15px; color: #0F172A; display: flex; align-items: center; gap: 6px;">
                            <span>🧩</span> <span>Собери регион</span>
                        </h4>
                        <span id="puzzle-timer-text" style="font-weight: 800; font-size: 13px; color: #0284C7;">⏱ 00:00</span>
                    </div>

                    <div class="puzzle-progress-wrap">
                        <div style="display: flex; justify-content: space-between; font-size: 11.5px; font-weight: 700; color: #475569; margin-bottom: 4px;">
                            <span id="puzzle-progress-text">Собрано: 0 из 0</span>
                            <span id="puzzle-percent-text">0%</span>
                        </div>
                        <div class="puzzle-progress-track">
                            <div id="puzzle-progress-bar" style="width: 0%;"></div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748B; margin-top: 6px; padding: 0 2px;">
                        <span>Ошибок: <b id="puzzle-mistakes-text" style="color: #EF4444;">0</b></span>
                        <span>Точность: <b id="puzzle-accuracy-text" style="color: #10B981;">100%</b></span>
                    </div>
                </div>

                <div id="puzzle-active-piece-card" class="puzzle-target-card" draggable="true" title="Перетащите эту деталь на карту">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 10px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">
                            Текущая деталь:
                        </span>
                        <span id="puzzle-active-badge" class="puzzle-type-badge">район</span>
                    </div>

                    <div id="puzzle-active-preview" class="puzzle-active-preview-wrap">
                        <!-- SVG силуэт активного района -->
                    </div>

                    <div id="puzzle-active-name" style="font-size: 15px; font-weight: 800; color: #0F172A; margin-bottom: 2px; text-align: center;">
                        Загрузка...
                    </div>
                    <div id="puzzle-active-info" style="font-size: 11px; color: #475569; margin-bottom: 6px; text-align: center;">
                        Центр: — | Площадь: —
                    </div>
                    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 5px 8px; font-size: 11px; color: #166534; font-weight: 600; text-align: center;">
                        🖐️ Перетащите силуэт на карту или кликните по слоту
                    </div>
                </div>

                <div style="margin: 10px 0 6px 0; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; font-weight: 700; color: #334155;">Силуэты деталей (выберите любую):</span>
                    <button onclick="skipCurrentPuzzlePiece()" class="btn btn-secondary btn-sm btn-puzzle-skip" title="Пропустить и взять следующую деталь">
                        ⏭ Другая
                    </button>
                </div>

                <div id="puzzle-tray-container" class="puzzle-tray-list">
                    <!-- Список районов в случайном порядке -->
                </div>

                <div class="btn-group-vertical" style="margin-top: 10px;">
                    <button onclick="hintPuzzleSlot()" class="btn btn-warning btn-block" id="puzzle-hint-btn">
                        💡 Подсказка (-1 попытка)
                    </button>
                    <button onclick="exitPuzzleMode()" class="btn btn-danger btn-block">
                        Завершить сборку
                    </button>
                </div>
            </div>

            <!-- РЕЖИМ ТЕСТИРОВАНИЯ (QUIZ) -->
            <div id="quiz-mode" style="display: none;">
                <div class="quiz-status-header">
                    <h4 id="quiz-title">Викторина</h4>
                    <div id="quiz-progress">Вопрос: <span id="current-question">1</span>/<span id="total-questions">10</span></div>
                </div>

                <div id="timer-bar-container" class="exam-proctor-panel" style="display: none; margin-bottom: 12px;">
                    <div class="exam-panel-top">
                        <div class="exam-status-badge">
                            <span class="exam-status-dot"></span>
                            <span id="exam-proctor-status-text">Контроль Anti-Cheat</span>
                        </div>
                        <div class="exam-timer-wrapper">
                            <span class="exam-timer-icon">⏳</span>
                            <span id="timer-text" class="exam-timer-display">10:00</span>
                        </div>
                    </div>
                    <div class="timer-track">
                        <div id="timer-bar"></div>
                    </div>
                </div>

                <div id="question-container">
                    <p id="question-text" class="question-text">Загрузка вопроса...</p>

                    <div id="options-container">
                    </div>

                    <div id="hint-container" class="hint-container">
                        <strong>Подсказка:</strong> <span id="hint-text"></span>
                    </div>
                </div>

                <div class="score-card">
                    <div>Баллы: <span id="score">0</span></div>
                    <div class="score-sub" id="accuracy">Эффективность: 0%</div>
                </div>

                <div class="btn-group-vertical">
                    <button onclick="showHint()" id="hint-button" class="btn btn-warning btn-block" style="display: none;">
                        💡 Подсказка
                    </button>
                    <button onclick="exitQuiz()" class="btn btn-danger btn-block">
                        Завершить викторину
                    </button>
                </div>
            </div>

            <!-- ЭКРАН РЕЗУЛЬТАТОВ -->
            <div id="results-mode" style="display: none; text-align: center;">
                <h4 style="color: #10B981; margin: 0 0 10px 0; font-size: 15px;">Результаты теста</h4>
                <div id="results-content">
                </div>
                <div class="btn-group-vertical" style="margin-top: 12px;">
                    <button onclick="closeResultsAndReturnToMenu()" class="btn btn-primary btn-block">
                        В главное меню
                    </button>
                </div>
            </div>
        </div>

        <div id="welcome-modal" class="welcome-overlay" style="display: none;">
            <div class="welcome-card">
                <div class="welcome-badge">Географический атлас</div>
                <h2 class="welcome-title">{self.title}</h2>
                <p class="welcome-subtitle">Интерактивный картографический комплекс и система тестирования пространственных знаний</p>
                
                <div class="welcome-grid">
                    <div class="welcome-feature" onclick="selectModeFromWelcome('study')" style="cursor: pointer;" title="Запустить режим обучения номенклатуре">
                        <div class="feature-icon" style="background: #E8F5E9; color: #2E7D32;">🎓</div>
                        <div class="feature-content">
                            <h4>Режим обучения (Номенклатура)</h4>
                            <p>Пошаговое изучение номенклатуры: территорий, русел рек и административных центров с автофокусом карты.</p>
                        </div>
                    </div>
                    <div class="welcome-feature" onclick="selectModeFromWelcome('rivers')" style="cursor: pointer;" title="Запустить викторину по гидрографии">
                        <div class="feature-icon" style="background: #E0F2FE; color: #0284C7;">🌊</div>
                        <div class="feature-content">
                            <h4>Гидрография</h4>
                            <p>Викторина по главным водным артериям региона. Карта фокусируется на русле реки и предлагает варианты ответа.</p>
                        </div>
                    </div>
                    <div class="welcome-feature" onclick="selectModeFromWelcome('puzzle')" style="cursor: pointer;" title="Собрать регион из деталей пазла">
                        <div class="feature-icon" style="background: #E0F7FA; color: #00796B;">🧩</div>
                        <div class="feature-content">
                            <h4>Топологический пазл</h4>
                            <p>Интерактивная сборка контура региона из силуэтов муниципальных образований без координатной сетки.</p>
                        </div>
                    </div>
                    <div class="welcome-feature" onclick="selectModeFromWelcome('centers')" style="cursor: pointer;" title="Найти центры на карте">
                        <div class="feature-icon" style="background: #EFF6FF; color: #1D4ED8;">🎯</div>
                        <div class="feature-content">
                            <h4>Поиск центров с точностью</h4>
                            <p>Проверка топографической ориентации. Укажите кликом центр на карте и получите баллы в зависимости от погрешности.</p>
                        </div>
                    </div>
                </div>

                <div class="welcome-footer">
                    <label class="welcome-checkbox">
                        <input type="checkbox" id="dont-show-welcome">
                        <span>Больше не показывать при входе</span>
                    </label>
                    <button onclick="closeWelcomeModal()" class="btn btn-primary btn-start">Начать работу с картой</button>
                </div>
            </div>
        </div>

        <!-- МОДАЛЬНОЕ ОКНО НАСТРОЙКИ КОНТРОЛЬНОЙ РАБОТЫ (ЭКЗАМЕНА) -->
        <div id="exam-setup-modal" class="welcome-overlay" style="display: none;">
            <div class="welcome-card" style="max-width: 480px;">
                <div class="welcome-badge" style="background: linear-gradient(135deg, #7C3AED, #4F46E5); color: white;">ЮФУ Экзамен</div>
                <h2 class="welcome-title" style="margin-bottom: 6px;">📝 Режим контрольной работы</h2>
                <p class="welcome-subtitle" style="margin-bottom: 16px;">Аттестационное тестирование студентов Института наук о Земле ЮФУ</p>
                
                <div class="exam-setup-form">
                    <div class="form-group" style="margin-bottom: 14px; text-align: left;">
                        <label style="font-weight: 700; font-size: 13px; color: #1E293B; display: block; margin-bottom: 6px;">Категория вопросов:</label>
                        <select id="exam-category-select" class="exam-select">
                            <option value="mixed">🔀 Комплексный экзамен (все категории)</option>
                            <option value="districts">🗺️ Номенклатура районов (по силуэту)</option>
                            <option value="rivers">🌊 Гидрография (русла рек региона)</option>
                            <option value="centers">📍 Административные центры (поиск на карте)</option>
                            <option value="neighbors">🔗 Топология смежности (районы-соседи)</option>
                            <option value="puzzle">🧩 Топологический пазл (Собрать регион)</option>
                        </select>
                    </div>

                    <div style="display: flex; gap: 12px; margin-bottom: 14px; text-align: left;">
                        <div class="form-group" style="flex: 1;">
                            <label style="font-weight: 700; font-size: 13px; color: #1E293B; display: block; margin-bottom: 6px;">Количество вопросов:</label>
                            <select id="exam-count-select" class="exam-select">
                                <option value="10">10 вопросов</option>
                                <option value="15" selected>15 вопросов (стандарт)</option>
                                <option value="20">20 вопросов</option>
                                <option value="25">25 вопросов</option>
                            </select>
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label style="font-weight: 700; font-size: 13px; color: #1E293B; display: block; margin-bottom: 6px;">Лимит времени:</label>
                            <select id="exam-time-select" class="exam-select">
                                <option value="5">5 минут</option>
                                <option value="10" selected>10 минут (рекомендуется)</option>
                                <option value="15">15 минут</option>
                                <option value="20">20 минут</option>
                            </select>
                        </div>
                    </div>

                    <div class="exam-rules-box">
                        <div style="font-size: 13px; font-weight: 700; color: #991B1B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                            <span>⚠️</span> <span>Правила экзамена и Anti-cheat:</span>
                        </div>
                        <ul style="margin: 0; padding-left: 18px; font-size: 11.5px; color: #7F1D1D; line-height: 1.5;">
                            <li>Запущен общий таймер на всю работу (автозавершение по истечении).</li>
                            <li><b>Запрещено переключать вкладки браузера</b> (фиксируется нарушение).</li>
                            <li>При повторном уходе с вкладки экзамен аннулируется.</li>
                            <li>Подсказки в режиме контрольной отключены.</li>
                            <li>По окончании выдается именной цифровой токен ведомости.</li>
                        </ul>
                    </div>
                </div>

                <div style="display: flex; gap: 10px; margin-top: 18px;">
                    <button onclick="closeExamModal()" class="btn btn-secondary" style="flex: 1; padding: 10px;">Отмена</button>
                    <button onclick="startExamFromModal()" class="btn btn-exam" style="flex: 2; padding: 10px; font-size: 14px;">🚀 Начать экзамен</button>
                </div>
            </div>
        </div>

        <!-- МОДАЛЬНОЕ ОКНО ПРЕДУПРЕЖДЕНИЯ ANTI-CHEAT -->
        <div id="anticheat-modal" class="welcome-overlay" style="display: none; z-index: 11000;">
            <div class="welcome-card" style="max-width: 440px; border-top: 4px solid #DC2626; animation: shakeAnim 0.3s ease;">
                <div style="font-size: 34px; text-align: center; margin-bottom: 6px;">🚨</div>
                <h3 id="anticheat-title" style="margin: 0 0 10px 0; color: #991B1B; text-align: center; font-size: 17px;">ВНИМАНИЕ: Нарушение дисциплины!</h3>
                <div id="anticheat-body" style="font-size: 13px; color: #334155; line-height: 1.5; margin-bottom: 18px; text-align: center;">
                    Вы переключились на другую вкладку браузера во время контрольной работы!
                </div>
                <button id="anticheat-confirm-btn" class="btn btn-danger btn-block" style="padding: 10px; font-size: 13px;">
                    Я понимаю, вернуться к экзамену
                </button>
            </div>
        </div>

        <!-- МОДАЛЬНОЕ ОКНО ПОБЕДЫ В ПАЗЛЕ -->
        <div id="puzzle-victory-modal" class="welcome-overlay" style="display: none; z-index: 10500;">
            <div class="welcome-card" style="max-width: 480px; text-align: center; border-top: 4px solid #10B981;">
                <div style="font-size: 38px; margin-bottom: 6px;">🏆</div>
                <div class="welcome-badge" style="background: linear-gradient(135deg, #10B981, #059669); color: white;">Регион успешно собран!</div>
                <h2 id="puzzle-victory-title" class="welcome-title" style="margin: 8px 0 4px 0; font-size: 20px;">Поздравляем с победой!</h2>
                <p id="puzzle-victory-sub" class="welcome-subtitle" style="margin-bottom: 14px;">Вы восстановили географическую целостность региона</p>
                
                <div id="puzzle-victory-stats" style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px; margin-bottom: 14px; text-align: left;">
                    <!-- Динамическая сводка: Время, Районы, Ошибки, Точность -->
                </div>

                <div class="exam-token-card" style="margin: 10px 0 14px 0;">
                    <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">
                        Цифровой токен сдачи (ЮФУ)
                    </div>
                    <div class="exam-token-val" id="puzzle-token-display">PUZZLE-XXXX-XXXX</div>
                    <div>
                        <button onclick="copyPuzzleToken()" class="btn btn-secondary btn-sm token-copy-btn">📋 Скопировать код</button>
                    </div>
                    <div style="font-size: 11px; color: #94A3B8; margin-top: 6px;">
                        Отправьте преподавателю для фиксации практической работы
                    </div>
                </div>

                <div style="display: flex; gap: 8px;">
                    <button onclick="restartPuzzleMode()" class="btn btn-secondary" style="flex: 1; padding: 9px;">🔄 Заново</button>
                    <button onclick="closePuzzleVictoryModal()" class="btn btn-primary" style="flex: 1; padding: 9px;">🗺️ К карте</button>
                    <button onclick="exitPuzzleMode()" class="btn btn-danger" style="flex: 1; padding: 9px;">В меню</button>
                </div>
            </div>
        </div>

        <style>
        /* ========================================================
           ЕДИНАЯ СИСТЕМА КНОПОК И ЭЛЕМЕНТОВ УПРАВЛЕНИЯ (DESIGN SYSTEM)
           ======================================================== */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-family: inherit;
            font-size: 13px;
            font-weight: 600;
            line-height: 1.4;
            letter-spacing: -0.1px;
            padding: 9px 16px;
            border-radius: 10px;
            border: 1px solid transparent;
            cursor: pointer;
            text-decoration: none;
            user-select: none;
            box-sizing: border-box;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            white-space: nowrap;
        }}

        .btn:hover {{
            transform: translateY(-1.5px);
            filter: brightness(1.04);
        }}

        .btn:active {{
            transform: translateY(0.5px) scale(0.985);
        }}

        .btn:focus-visible {{
            outline: 2px solid #2563EB;
            outline-offset: 2px;
        }}

        /* 1. Главные действия (Основной приоритет) */
        .btn-primary {{
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28) !important;
        }}
        .btn-primary:hover {{
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.38) !important;
        }}

        /* 2. Конструктивные действия и фичи (Пазл, Сохранение, Успех) */
        .btn-success, .btn-puzzle {{
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.28) !important;
        }}
        .btn-success:hover, .btn-puzzle:hover {{
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.38) !important;
        }}

        /* 3. Экзаменационный режим */
        .btn-exam {{
            background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.28) !important;
        }}
        .btn-exam:hover {{
            box-shadow: 0 6px 20px rgba(124, 58, 237, 0.38) !important;
        }}

        /* 4. Второстепенные действия (Вспомогательный приоритет) */
        .btn-secondary {{
            background: #FFFFFF !important;
            color: #334155 !important;
            border: 1px solid #CBD5E1 !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        }}
        .btn-secondary:hover {{
            background: #F8FAFC !important;
            color: #0F172A !important;
            border-color: #94A3B8 !important;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
        }}

        /* 5. Деструктивные / Завершающие действия */
        .btn-danger {{
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.25) !important;
        }}
        .btn-danger:hover {{
            box-shadow: 0 6px 18px rgba(239, 68, 68, 0.35) !important;
        }}

        /* 6. Подсказки и предупреждения */
        .btn-warning {{
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25) !important;
        }}
        .btn-warning:hover {{
            box-shadow: 0 6px 18px rgba(245, 158, 11, 0.35) !important;
        }}

        /* Предметные кнопки викторин */
        .btn-study-action {{
            background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
            color: #FFFFFF !important;
            box-shadow: 0 3px 10px rgba(99, 102, 241, 0.25) !important;
            padding: 8px 6px !important;
            font-size: 11.5px !important;
            border-radius: 8px !important;
        }}
        .btn-study-action:hover {{
            box-shadow: 0 5px 14px rgba(99, 102, 241, 0.35) !important;
        }}

        .btn-district {{
            background: linear-gradient(135deg, #0D9488, #0F766E) !important;
            color: #FFFFFF !important;
            box-shadow: 0 3px 10px rgba(13, 148, 136, 0.25) !important;
            border-radius: 8px !important;
        }}
        .btn-district:hover {{
            box-shadow: 0 5px 14px rgba(13, 148, 136, 0.35) !important;
        }}

        .btn-neighbor {{
            background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
            color: #FFFFFF !important;
            box-shadow: 0 3px 10px rgba(37, 99, 235, 0.25) !important;
            border-radius: 8px !important;
        }}
        .btn-neighbor:hover {{
            box-shadow: 0 5px 14px rgba(37, 99, 235, 0.35) !important;
        }}

        .btn-river {{
            background: linear-gradient(135deg, #0EA5E9, #0284C7) !important;
            color: #FFFFFF !important;
            box-shadow: 0 3px 10px rgba(14, 165, 233, 0.25) !important;
            border-radius: 8px !important;
        }}
        .btn-river:hover {{
            box-shadow: 0 5px 14px rgba(14, 165, 233, 0.35) !important;
        }}

        .btn-center {{
            background: linear-gradient(135deg, #475569, #334155) !important;
            color: #FFFFFF !important;
            box-shadow: 0 3px 10px rgba(51, 65, 85, 0.25) !important;
            border-radius: 8px !important;
        }}
        .btn-center:hover {{
            box-shadow: 0 5px 14px rgba(51, 65, 85, 0.35) !important;
        }}

        .btn-confirm, #confirm-button {{
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
            font-size: 13.5px !important;
            font-weight: 700 !important;
            line-height: 1.4 !important;
            letter-spacing: -0.1px !important;
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
            box-sizing: border-box !important;
            margin-top: 10px !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            text-align: center !important;
            white-space: normal !important;
            min-height: 44px !important;
        }}
        .btn-confirm:hover, #confirm-button:hover {{
            transform: translateY(-1.5px) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.42) !important;
            filter: brightness(1.05) !important;
        }}
        .btn-confirm:active, #confirm-button:active {{
            transform: translateY(0.5px) scale(0.985) !important;
        }}

        /* Модификаторы размеров */
        .btn-sm {{
            padding: 6px 12px !important;
            font-size: 11.5px !important;
            border-radius: 8px !important;
        }}

        .btn-block {{
            width: 100% !important;
            display: flex !important;
        }}

        /* Вертикальные контейнеры кнопок (монолитный Flexbox-блок с gap) */
        .btn-group-vertical {{
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            width: 100% !important;
        }}

        .btn-group-vertical > .btn,
        .btn-group-vertical > button {{
            width: 100% !important;
            margin: 0 !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            justify-content: center !important;
            text-align: center !important;
            min-height: 44px !important;
            box-sizing: border-box !important;
        }}

        /* Скрытие стандартной навигации в режиме экзамена (Kiosk Mode) */
        body.exam-mode #top-nav-panel,
        body.exam-mode .top-nav-buttons,
        body.exam-mode #auth-top-btn,
        body.exam-mode #student-profile-badge,
        body.exam-mode .leaderboard-top-btn,
        body.exam-mode .help-circle-btn,
        body.exam-mode .admin-btn,
        body.exam-mode .reset-map-btn {{
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }}

        body.exam-mode #quiz-controls,
        body.exam-mode .app-card {{
            top: 66px !important;
            max-height: calc(100vh - 80px) !important;
        }}

        body.exam-mode .leaflet-top {{
            top: 62px !important;
        }}

        /* Фиолетовая статус-панель экзамена (Kiosk Bar) */
        .exam-kiosk-bar {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 52px !important;
            z-index: 99999 !important;
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%) !important;
            color: #FFFFFF !important;
            border-bottom: 2px solid #8B5CF6 !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding: 0 20px !important;
            box-sizing: border-box !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }}

        .exam-kiosk-bar .kiosk-left {{
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }}

        .exam-kiosk-bar .kiosk-dot {{
            width: 10px !important;
            height: 10px !important;
            border-radius: 50% !important;
            background: #EF4444 !important;
            box-shadow: 0 0 10px #EF4444 !important;
            animation: syncPulse 1.5s infinite !important;
        }}

        .exam-kiosk-bar .kiosk-title {{
            font-size: 13.5px !important;
            font-weight: 700 !important;
            letter-spacing: 0.02em !important;
        }}

        .exam-kiosk-bar .kiosk-meta {{
            font-size: 11.5px !important;
            color: #CBD5E1 !important;
        }}

        .exam-kiosk-bar .kiosk-right {{
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }}

        .exam-kiosk-bar .kiosk-timer-box {{
            background: rgba(15, 23, 42, 0.75) !important;
            padding: 6px 14px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
        }}

        .exam-kiosk-bar .kiosk-timer-text {{
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 16px !important;
            font-weight: 800 !important;
            color: #FBBF24 !important;
            letter-spacing: 0.5px !important;
        }}

        /* Кнопка-иконка / закрытие */
        .btn-icon, .close-card-btn {{
            width: 32px !important;
            height: 32px !important;
            padding: 0 !important;
            border-radius: 8px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 16px !important;
            background: #F1F5F9 !important;
            border: 1px solid #E2E8F0 !important;
            color: #64748B !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            line-height: 1 !important;
        }}
        .btn-icon:hover, .close-card-btn:hover {{
            background: #E2E8F0 !important;
            color: #0F172A !important;
            transform: translateY(-1.5px) !important;
        }}
        .btn-icon:active, .close-card-btn:active {{
            transform: translateY(0.5px) !important;
        }}

        /* Кнопки верхней панели */
        .top-nav-buttons {{
            position: fixed;
            top: 14px;
            right: 330px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: opacity 0.25s ease, transform 0.25s ease;
        }}

        .nav-top-btn {{
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
            padding: 8px 14px !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #1E293B !important;
            cursor: pointer !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }}
        .nav-top-btn:hover {{
            transform: translateY(-1.5px) !important;
            background: #FFFFFF !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        }}
        .nav-top-btn:active {{
            transform: translateY(0.5px) scale(0.985) !important;
        }}

        .reset-map-btn {{
            color: #1D4ED8 !important;
            border-color: #BFDBFE !important;
            background: #EFF6FF !important;
        }}
        .admin-btn {{
            background: #F0FDF4 !important;
            border-color: #BBF7D0 !important;
            color: #166534 !important;
        }}
        .leaderboard-top-btn {{
            background: #FFFBEB !important;
            border-color: #FDE68A !important;
            color: #B45309 !important;
        }}

        .help-circle-btn {{
            width: 36px !important;
            height: 36px !important;
            border-radius: 10px !important;
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid #CBD5E1 !important;
            color: #334155 !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
        }}
        .help-circle-btn:hover {{
            background: #FFFFFF !important;
            border-color: #94A3B8 !important;
            color: #0F172A !important;
            transform: translateY(-1.5px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        }}
        .help-circle-btn:active {{
            transform: translateY(0.5px) !important;
        }}

        .student-badge {{
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(8px);
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            padding: 4px 10px 4px 6px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        }}
        .badge-avatar {{
            width: 26px;
            height: 26px;
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
        }}
        .badge-info {{ display: flex; flex-direction: column; text-align: left; }}
        .badge-name {{ font-size: 11.5px; font-weight: 700; color: #1E293B; line-height: 1.2; }}
        .badge-group {{ font-size: 10px; color: #64748B; }}
        .badge-logout {{
            background: none;
            border: none;
            font-size: 16px;
            color: #94A3B8;
            cursor: pointer;
            margin-left: 4px;
            line-height: 1;
            border-radius: 4px;
            transition: all 0.15s ease;
        }}
        .badge-logout:hover {{ color: #DC2626; background: #FEE2E2; }}

        .panel-header-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
            margin-bottom: 6px;
        }}

        .panel-institution-badge {{
            font-size: 10px;
            font-weight: 800;
            color: #1E40AF;
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            padding: 3px 8px;
            border-radius: 6px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            text-align: left;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .exam-select {{
            width: 100%;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            font-size: 13px;
            font-weight: 600;
            color: #1E293B;
            background: #FFFFFF;
            font-family: inherit;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            outline: none;
            cursor: pointer;
            transition: border-color 0.15s;
        }}
        .exam-select:focus {{
            border-color: #2563EB;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
        }}

        .exam-rules-box {{
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 10px;
            padding: 12px 14px;
            text-align: left;
        }}

        .exam-token-card {{
            background: #F8FAFC;
            border: 1.5px dashed #CBD5E1;
            border-radius: 10px;
            padding: 14px;
            margin: 12px 0 10px 0;
            text-align: center;
        }}
        .exam-token-val {{
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #1E1B4B;
            background: #FFFFFF;
            padding: 6px 14px;
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            display: inline-block;
            margin: 8px 0;
            user-select: all;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        @keyframes shakeAnim {{
            0%, 100% {{ transform: translateX(0); }}
            20%, 60% {{ transform: translateX(-5px); }}
            40%, 80% {{ transform: translateX(5px); }}
        }}

        .puzzle-header {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 10px;
        }}

        .puzzle-progress-track {{
            width: 100%;
            height: 7px;
            background: #E2E8F0;
            border-radius: 4px;
            overflow: hidden;
        }}

        #puzzle-progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #10B981, #059669);
            border-radius: 4px;
            transition: width 0.3s ease;
        }}

        .puzzle-target-card {{
            background: #FFFFFF;
            border: 1.5px solid #2563EB;
            border-radius: 12px;
            padding: 10px 12px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.1);
            transition: all 0.2s ease;
            cursor: grab;
        }}

        .puzzle-target-card:active, .puzzle-target-card.dragging {{
            cursor: grabbing;
            opacity: 0.6;
            border-style: dashed;
        }}

        .puzzle-target-card.shake {{
            animation: shakeAnim 0.35s ease;
            border-color: #DC2626 !important;
        }}

        .puzzle-active-preview-wrap {{
            width: 100%;
            height: 90px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 6px;
            background: #F8FAFC;
            border: 1.5px dashed #CBD5E1;
            border-radius: 8px;
            padding: 4px;
            box-sizing: border-box;
        }}

        .puzzle-type-badge {{
            font-size: 9px;
            font-weight: 700;
            color: #1D4ED8;
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            padding: 2px 7px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}

        .puzzle-tray-list {{
            max-height: 290px;
            overflow-y: auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
            gap: 8px;
            padding: 8px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
        }}

        .puzzle-silhouette-card {{
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 9px;
            padding: 6px 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            cursor: grab;
            user-select: none;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            position: relative;
            height: 102px;
            box-sizing: border-box;
        }}

        .puzzle-silhouette-card:hover {{
            border-color: #2563EB;
            background: #F8FAFC;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.16);
        }}

        .puzzle-silhouette-card.active {{
            border-color: #1D4ED8;
            background: #EFF6FF;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25);
            transform: translateY(-1px);
        }}

        .puzzle-silhouette-card.dragging {{
            opacity: 0.35;
            cursor: grabbing;
            transform: scale(0.96);
            border-style: dashed;
        }}

        .puzzle-card-badge {{
            font-size: 8px;
            font-weight: 700;
            color: #64748B;
            background: #F1F5F9;
            padding: 1px 5px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            white-space: nowrap;
            max-width: 90%;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center;
        }}

        .puzzle-card-badge.neighbor-ready {{
            background: #DCFCE7 !important;
            color: #166534 !important;
            border: 1px solid #86EFAC;
            font-weight: 800;
        }}

        .puzzle-silhouette-card.neighbor-connectable {{
            border-color: #86EFAC;
            background: #F0FDF4;
        }}

        .puzzle-silhouette-card.neighbor-connectable:hover {{
            border-color: #059669;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2);
        }}

        .puzzle-silhouette-card.active .puzzle-card-badge {{
            background: #DBEAFE;
            color: #1E40AF;
        }}

        .puzzle-card-svg-wrap {{
            width: 100%;
            height: 54px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .puzzle-svg-shape {{
            width: 100%;
            height: 100%;
            display: block;
            filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.05));
            transition: transform 0.15s ease;
        }}

        .puzzle-silhouette-card:hover .puzzle-svg-shape {{
            transform: scale(1.05);
        }}

        .puzzle-card-caption {{
            font-size: 9.5px;
            font-weight: 700;
            color: #334155;
            text-align: center;
            line-height: 1.15;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 96%;
        }}

        .puzzle-drop-active {{
            box-shadow: inset 0 0 0 3px #10B981, 0 0 20px rgba(16, 185, 129, 0.35) !important;
            transition: box-shadow 0.2s ease;
        }}

        #puzzle-drag-ghost, .puzzle-drag-ghost-active {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            pointer-events: none !important;
            z-index: 999999 !important;
            will-change: transform !important;
            opacity: 0.92 !important;
            filter: drop-shadow(0 8px 24px rgba(37, 99, 235, 0.45)) !important;
            user-select: none !important;
            transform-origin: 0 0 !important;
        }}

        .puzzle-placed-label {{
            background: transparent;
            border: none;
            text-align: center;
        }}
        .leaflet-tooltip {{
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
            padding: 5px 10px !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1) !important;
            white-space: nowrap !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 12px !important;
            font-weight: 700 !important;
            color: #1E293B !important;
            line-height: 1.2 !important;
        }}

        .leaflet-tooltip table {{
            margin: 0 !important;
            border-collapse: collapse !important;
        }}
        .leaflet-tooltip table th {{
            display: none !important;
        }}
        .leaflet-tooltip table td {{
            padding: 0 !important;
            margin: 0 !important;
            text-align: center !important;
        }}

        .lb-main-tabs {{
            display: flex;
            background: #F1F5F9;
            padding: 3px;
            border-radius: 8px;
            margin-bottom: 12px;
            gap: 4px;
            border: 1px solid #E2E8F0;
        }}
        .lb-tab-btn {{
            flex: 1;
            background: transparent;
            border: none;
            padding: 7px 10px;
            font-size: 12px;
            font-weight: 700;
            color: #64748B;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .lb-tab-btn.active {{
            background: #FFFFFF;
            color: #0F172A;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            border: 1px solid #CBD5E1;
        }}

        .lb-content-fade {{
            transition: opacity 0.15s ease-in-out, transform 0.15s ease-in-out;
            opacity: 1;
            transform: translateY(0);
        }}
        .fade-anim {{
            opacity: 0;
            transform: translateY(4px);
        }}

        .lb-filters {{
            display: flex;
            gap: 6px;
            justify-content: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }}
        .lb-filter-chip {{
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 11.5px;
            font-weight: 600;
            color: #475569;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .lb-filter-chip:hover {{ background: #F8FAFC; }}
        .lb-filter-chip.active {{
            background: #2563EB;
            color: white;
            border-color: #2563EB;
        }}

        .lb-table-wrap {{
            max-height: 300px;
            overflow-y: auto;
            border-radius: 8px;
            border: 1px solid #CBD5E1;
        }}
        .lb-styled-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            text-align: center;
        }}
        .lb-styled-table th {{
            background: #F8FAFC;
            color: #475569;
            padding: 8px 6px;
            border-bottom: 1px solid #E2E8F0;
            position: sticky;
            top: 0;
            z-index: 2;
        }}
        .lb-styled-table td {{
            padding: 7px 6px;
            border-bottom: 1px solid #F1F5F9;
            color: #334155;
        }}
        .lb-styled-table tr:hover {{ background: #F8FAFC; }}

        .auth-card {{
            background: #FFFFFF;
            border-radius: 14px;
            max-width: 440px;
            width: 100%;
            padding: 24px 26px;
            border: 1px solid #CBD5E1;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            box-sizing: border-box;
            animation: welcomeIn 0.25s ease-out;
        }}

        .auth-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 12px;
            margin-bottom: 14px;
        }}
        .auth-header h3 {{ margin: 0; font-size: 15px; color: #0F172A; }}

        .auth-error {{
            background: #FEE2E2;
            color: #B91C1C;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            margin-bottom: 12px;
            border: 1px solid #FCA5A5;
        }}

        .form-group {{
            margin-bottom: 12px;
            text-align: left;
        }}
        .form-group label {{
            display: block;
            font-size: 11.5px;
            color: #475569;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .auth-input {{
            width: 100%;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #CBD5E1;
            font-size: 13px;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.15s;
        }}
        .auth-input:focus {{ border-color: #2563EB; }}
        .code-input {{
            text-align: center;
            letter-spacing: 5px;
            font-size: 19px;
            font-weight: 700;
            color: #1D4ED8;
            font-family: 'JetBrains Mono', Consolas, monospace;
        }}

        .welcome-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.55);
            backdrop-filter: blur(4px);
            z-index: 20000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            transition: opacity 0.2s ease;
        }}
        .welcome-overlay.fade-out {{
            opacity: 0;
            pointer-events: none;
        }}

        .welcome-card {{
            background: #FFFFFF;
            border-radius: 16px;
            max-width: 640px;
            width: 100%;
            padding: 26px 30px;
            border: 1px solid #CBD5E1;
            box-shadow: 0 16px 44px rgba(15, 23, 42, 0.18);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            position: relative;
            animation: welcomeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            max-height: calc(100vh - 40px);
            overflow-y: auto;
            box-sizing: border-box;
        }}

        @keyframes welcomeIn {{
            from {{ opacity: 0; transform: scale(0.97) translateY(8px); }}
            to {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}

        .welcome-badge {{
            display: inline-block;
            background: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .welcome-title {{
            margin: 0 0 6px 0;
            font-size: 23px;
            color: #0F172A;
            font-weight: 800;
            letter-spacing: -0.3px;
        }}

        .welcome-subtitle {{
            margin: 0 0 20px 0;
            font-size: 13.5px;
            color: #64748B;
            line-height: 1.45;
        }}

        .welcome-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 22px;
        }}

        .welcome-feature {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 12px 14px;
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }}

        .feature-icon {{
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
            border: 1px solid rgba(0, 0, 0, 0.06);
        }}

        .feature-content h4 {{
            margin: 0 0 3px 0;
            font-size: 13px;
            color: #1E293B;
            font-weight: 700;
        }}

        .feature-content p {{
            margin: 0;
            font-size: 11.5px;
            color: #64748B;
            line-height: 1.35;
        }}

        .welcome-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 16px;
            border-top: 1px solid #E2E8F0;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .welcome-checkbox {{
            display: flex;
            align-items: center;
            font-size: 12px;
            color: #64748B;
            cursor: pointer;
            user-select: none;
        }}

        .welcome-checkbox input {{
            margin-right: 8px;
            cursor: pointer;
        }}

        .app-card {{
            position: fixed;
            top: 14px;
            right: 14px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(12px);
            padding: 16px;
            border-radius: 14px;
            box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.1), 0 4px 12px -2px rgba(15, 23, 42, 0.05);
            width: 300px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            border: 1px solid rgba(226, 232, 240, 0.9);
            max-height: calc(100vh - 28px);
            overflow-y: auto;
            box-sizing: border-box;
            transition: max-height 0.25s cubic-bezier(0.16, 1, 0.3, 1), padding 0.25s ease;
        }}

        .panel-header {{
            text-align: center;
            margin-bottom: 12px;
        }}
        .panel-header h3 {{
            margin: 0;
            color: #0F172A;
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.2px;
        }}

        .study-pick-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 6px;
            margin-bottom: 8px;
        }}

        .study-category-bar {{
            display: flex;
            background: #F1F5F9;
            padding: 3px;
            border-radius: 8px;
            margin-bottom: 10px;
            gap: 4px;
            border: 1px solid #E2E8F0;
        }}
        .study-cat-tab {{
            flex: 1;
            border: none;
            background: transparent;
            font-size: 11px;
            font-weight: 700;
            padding: 6px 2px;
            border-radius: 6px;
            color: #64748B;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .study-cat-tab.active {{
            background: #FFFFFF;
            color: #2563EB;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            border: 1px solid #CBD5E1;
        }}

        .study-status-header {{
            background: linear-gradient(135deg, #6366F1, #4F46E5);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
        }}
        .study-status-header h4 {{ margin: 0; font-size: 12.5px; font-weight: 700; }}
        #study-counter-val {{ font-size: 11.5px; font-weight: 700; background: rgba(255,255,255,0.22); padding: 2px 7px; border-radius: 6px; }}

        .study-card-body {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
        }}
        .study-title {{
            margin: 0 0 8px 0;
            font-size: 14.5px;
            color: #1E293B;
            font-weight: 800;
            text-align: center;
            border-bottom: 1px solid #CBD5E1;
            padding-bottom: 6px;
        }}
        .study-nav-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
        }}

        .timer-setting-box {{
            margin: 8px 0;
            padding: 8px 10px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
        }}

        .checkbox-container {{
            display: flex;
            align-items: center;
            font-size: 12px;
            cursor: pointer;
            color: #334155;
            user-select: none;
        }}

        .checkbox-container input {{
            margin-right: 8px;
            cursor: pointer;
        }}

        .hint-small {{
            margin-top: 8px;
            padding: 8px;
            background: #F1F5F9;
            border-radius: 6px;
            font-size: 11px;
            color: #64748B;
            text-align: center;
            line-height: 1.3;
        }}

        .district-info-box {{
            display: none;
            margin-top: 10px;
            padding: 12px;
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 10px;
        }}

        .info-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #86EFAC;
            padding-bottom: 5px;
            margin-bottom: 7px;
        }}

        .info-card-header strong {{
            color: #166534;
            font-size: 13.5px;
        }}

        .info-row {{
            display: flex;
            justify-content: space-between;
            font-size: 11.5px;
            margin-bottom: 4px;
            color: #334155;
        }}
        .info-row span {{ color: #64748B; }}

        .neighbor-tag {{
            display: inline-block;
            background: #DCFCE7;
            color: #15803D;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            margin: 2px;
            cursor: pointer;
            border: 1px solid #BBF7D0;
            transition: all 0.15s ease;
        }}
        .neighbor-tag:hover {{
            background: #BBF7D0;
            transform: translateY(-1px);
        }}

        .quiz-status-header {{
            background: linear-gradient(135deg, #2563EB, #1D4ED8);
            color: white;
            padding: 9px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
        }}
        .quiz-status-header h4 {{ margin: 0; font-size: 13px; font-weight: 700; }}
        #quiz-progress {{ font-size: 11px; opacity: 0.9; margin-top: 2px; }}

        /* ==================== ПРЕМИАЛЬНЫЙ ВИДЖЕТ ТАЙМЕРА И ПРОКТОРИНГА ==================== */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

        .exam-proctor-panel {{
            background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #1E293B 100%);
            border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: 12px;
            padding: 10px 14px;
            margin-bottom: 12px;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.28), 0 1px 3px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            box-sizing: border-box;
            transition: all 0.3s ease;
        }}

        .exam-panel-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .exam-status-badge {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 700;
            color: #CBD5E1;
            letter-spacing: 0.3px;
            text-transform: uppercase;
        }}

        .exam-status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10B981;
            box-shadow: 0 0 8px #10B981;
            animation: proctorDotPulse 1.8s infinite;
        }}

        @keyframes proctorDotPulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.25); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}

        .exam-timer-wrapper {{
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(15, 23, 42, 0.7);
            padding: 4px 10px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}

        .exam-timer-icon {{
            font-size: 13px;
        }}

        .exam-timer-display, #timer-text {{
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 15px !important;
            font-weight: 800 !important;
            color: #38BDF8 !important;
            letter-spacing: 0.5px !important;
        }}

        .timer-track {{
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.12);
            border-radius: 999px;
            overflow: hidden;
        }}

        #timer-bar {{
            width: 100%;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #8B5CF6, #38BDF8);
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.4);
            transition: width 1s linear, background 0.3s;
        }}

        .timer-flex {{
            display: flex;
            justify-content: space-between;
            font-size: 11.5px;
            color: #CBD5E1;
            margin-bottom: 4px;
        }}

        .question-text {{
            font-size: 13px;
            font-weight: 700;
            color: #1E293B;
            margin: 0 0 10px 0;
            text-align: center;
            line-height: 1.4;
        }}

        .quiz-option {{
            display: block;
            width: 100%;
            padding: 9px 12px;
            margin: 6px 0;
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            cursor: pointer;
            font-size: 12.5px;
            color: #334155;
            text-align: left;
            transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
            box-sizing: border-box;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }}
        .quiz-option:hover {{
            background: #F1F5F9;
            border-color: #94A3B8;
            transform: translateY(-1px);
        }}
        .quiz-option.selected {{
            border-color: #2563EB !important;
            background: #EFF6FF !important;
            color: #1D4ED8 !important;
            font-weight: 600;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
        }}
        .quiz-option.correct {{
            background: #DCFCE7 !important;
            border-color: #86EFAC !important;
            color: #15803D !important;
            font-weight: 600;
        }}
        .quiz-option.incorrect {{
            background: #FEE2E2 !important;
            border-color: #FCA5A5 !important;
            color: #B91C1C !important;
        }}

        .center-quiz-instruction {{
            padding: 10px;
            background: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 8px;
            color: #475569;
            text-align: center;
            font-size: 11.5px;
            line-height: 1.4;
        }}
        .center-quiz-instruction span {{
            font-size: 11px;
            color: #64748B;
            display: block;
            margin-top: 4px;
        }}

        .feedback-box {{
            padding: 9px 12px;
            border-radius: 8px;
            margin-top: 10px;
            text-align: center;
            font-weight: 700;
            font-size: 12.5px;
        }}
        .feedback-box.success {{ background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }}
        .feedback-box.error {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }}

        .hint-container {{
            background: #FEF3C7;
            border: 1px solid #FDE68A;
            border-radius: 8px;
            padding: 8px 10px;
            margin-top: 8px;
            font-size: 11.5px;
            color: #92400E;
            line-height: 1.3;
        }}

        .score-card {{
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            padding: 8px 12px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
            font-weight: 700;
            font-size: 12.5px;
            color: #1E293B;
        }}
        .score-sub {{ font-size: 11px; color: #64748B; font-weight: 500; margin-top: 2px; }}

        /* Кнопка сворачивания панели: по умолчанию (десктоп >= 1024px) полностью скрыта */
        .mobile-collapse-trigger {{
            display: none !important;
        }}

        /* АДАПТИВНОСТЬ: мобильные экраны и планшеты (< 1024px) */
        @media (max-width: 1023.98px) {{
            .mobile-collapse-trigger {{
                display: inline-flex !important;
                width: 28px !important;
                height: 28px !important;
                min-width: 28px !important;
                border-radius: 8px !important;
                background: #F1F5F9 !important;
                border: 1px solid #CBD5E1 !important;
                color: #475569 !important;
                padding: 0 !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
                transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
                line-height: 1 !important;
            }}
            .mobile-collapse-trigger:hover {{
                background: #E2E8F0 !important;
                color: #0F172A !important;
            }}
            .mobile-collapse-trigger .collapse-icon {{
                transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            }}
            .app-card.collapsed .mobile-collapse-trigger .collapse-icon {{
                transform: rotate(180deg);
            }}

            .top-nav-buttons {{
                top: 8px;
                left: 8px;
                right: 8px;
                justify-content: flex-end;
                gap: 5px;
            }}
            .nav-top-btn, .help-circle-btn {{
                padding: 6px 9px !important;
                font-size: 11px !important;
                height: 32px !important;
            }}
            .help-circle-btn {{
                width: 32px !important;
                font-size: 14px !important;
            }}

            .app-card {{
                position: fixed;
                top: auto;
                bottom: 0;
                right: 0;
                left: 0;
                width: 100%;
                border-radius: 16px 16px 0 0;
                max-height: 52vh;
                padding: 12px 14px;
                z-index: 1001;
                box-shadow: 0 -6px 24px rgba(0,0,0,0.14);
            }}

            .app-card.collapsed {{
                max-height: 52px;
                overflow: hidden;
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.98);
            }}
            .app-card.collapsed > *:not(.panel-header) {{
                display: none !important;
            }}
            .app-card.collapsed .panel-header h3 {{
                display: none;
            }}
            .app-card.collapsed .panel-header {{
                margin-bottom: 0;
            }}

            body.ui-collapsed #top-nav-panel {{
                opacity: 0 !important;
                pointer-events: none !important;
                transform: translateY(-20px);
            }}
            body.ui-collapsed .leaflet-control-layers {{
                opacity: 0 !important;
                pointer-events: none !important;
            }}

            .leaflet-bottom.leaflet-left {{
                bottom: 54vh !important;
                margin-left: 6px !important;
            }}
            .leaflet-control-layers {{
                border-radius: 8px !important;
                background: rgba(255, 255, 255, 0.98) !important;
                border: 1px solid #CBD5E1 !important;
                transition: opacity 0.25s ease;
            }}

            div[style*="top: 14px; left: 60px;"] {{
                display: none !important;
            }}
        }}

        /* ДЕСКТОП: >= 1024px — панель строго зафиксирована в развернутом виде, кнопка скрыта */
        @media (min-width: 1024px) {{
            .mobile-collapse-trigger {{
                display: none !important;
            }}
            .app-card {{
                position: fixed !important;
                top: 14px !important;
                right: 14px !important;
                width: 300px !important;
                max-height: calc(100vh - 28px) !important;
                overflow-y: auto !important;
            }}
            .app-card.collapsed > * {{
                display: block !important;
            }}
        }}
        </style>
        '''
        self.map.get_root().html.add_child(folium.Element(quiz_html))

    def add_choropleth_layer(self):
        """Аналитический слой: раскраска районов по численности населения (Choropleth)."""
        if self.districts_gdf is None or self.districts_gdf.empty:
            print("Внимание: Нет данных о районах для Choropleth-слоя.")
            return

        gdf = self.districts_gdf.copy()
        gdf['is_district_layer'] = 0
        gdf['is_choropleth'] = 1

        # --- Вычисляем население для каждого полигона ---
        try:
            metric_gdf = gdf.to_crs('EPSG:6933')
        except Exception:
            metric_gdf = gdf

        populations = []
        for idx, row in gdf.iterrows():
            name = str(row.get('display_name', '')).lower().replace('\u0301', '').replace('e', 'е').replace('ё', 'е')
            population = None

            for key, val in KNOWN_POPULATION.items():
                if key in name:
                    population = val
                    break

            if population is None:
                # Если субъект РФ не найден в словаре по корню, возвращаем 0 (серый полигон)
                
                    area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if idx in metric_gdf.index else 0
                    if 'область' in name:
                        population = int(area_sq_km * 20)
                    elif 'республика' in name:
                        population = int(area_sq_km * 10)
                    elif 'край' in name:
                        population = int(area_sq_km * 5)
                    elif 'округ' in name or 'аок' in name:
                        population = int(area_sq_km * 1)
                    else:
                        population = int(area_sq_km * 25)

            populations.append(population)

        gdf['population'] = populations

        # --- Рассчитываем границы для 6-ступенчатого градиента ---
        import numpy as np
        pop_values = sorted([p for p in populations if p and p > 0])
        if not pop_values:
            return

        # 6 квантильных интервалов для плавного распределения цветов
        q_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        thresholds = [float(np.quantile(pop_values, q)) for q in q_levels]

        # Палитра ColorBrewer YlOrRd: светло-желтый -> янтарный -> оранжевый -> темно-красный
        colors = ['#FFFFCC', '#FED976', '#FEB24C', '#FD8D3C', '#E31A1C', '#800026']

        def get_color(pop):
            if pop is None or pop <= 0:
                return '#E2E8F0'
            if len(pop_values) == 1:
                return colors[2]
            if pop <= thresholds[1]:
                return colors[0]
            elif pop <= thresholds[2]:
                return colors[1]
            elif pop <= thresholds[3]:
                return colors[2]
            elif pop <= thresholds[4]:
                return colors[3]
            elif pop <= thresholds[5]:
                return colors[4]
            else:
                return colors[5]

        def style_function(feature):
            pop = feature['properties'].get('population', 0)
            return {
                'color': '#475569',
                'weight': 1.5,
                'fillColor': get_color(pop),
                'fillOpacity': 0.72,
                'dashArray': None
            }

        def highlight_function(feature):
            return {
                'weight': 3,
                'color': '#0F172A',
                'fillOpacity': 0.90
            }

        # Форматирование отображаемого населения
        gdf['pop_display'] = gdf['population'].apply(
            lambda p: f"{p:,.0f} чел.".replace(',', ' ') if (p and p > 0) else 'Нет данных'
        )

        tooltip = folium.GeoJsonTooltip(
            fields=['display_name', 'pop_display'],
            aliases=['Территория:', 'Население:'],
            style="background: white; border: 1px solid #CBD5E1; padding: 6px 10px; "
                  "font-weight: 700; font-size: 12px; border-radius: 6px; "
                  "box-shadow: 0 2px 8px rgba(0,0,0,0.12);"
        )

        folium.GeoJson(
            gdf,
            name='Население',
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=tooltip,
            show=False,           # Отдельный отключаемый слой (выключен по умолчанию)
            interactive=True
        ).add_to(self.map)

        self._choropleth_added = True
        print(f"  ✓ Choropleth-слой населения добавлен ({len(pop_values)} полигонов)")

    def add_economy_layer(self):
        """Аналитический слой: раскраска районов по объему ВРП (Choropleth)."""
        if self.districts_gdf is None or self.districts_gdf.empty:
            print("Внимание: Нет данных о районах для слоя ВРП (Экономика).")
            return

        gdf = self.districts_gdf.copy()
        gdf['is_district_layer'] = 0
        gdf['is_choropleth'] = 1
        gdf['is_economy'] = 1

        try:
            metric_gdf = gdf.to_crs('EPSG:6933')
        except Exception:
            metric_gdf = gdf

        grps = []
        for idx, row in gdf.iterrows():
            name = str(row.get('display_name', '')).lower().replace('\u0301', '').replace('e', 'е').replace('ё', 'е')
            
            # Население для резервного расчета
            population = None
            for key, val in KNOWN_POPULATION.items():
                if key in name:
                    population = val
                    break

            if population is None:
                
                    area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if idx in metric_gdf.index else 0
                    if 'область' in name:
                        population = int(area_sq_km * 20)
                    elif 'республика' in name:
                        population = int(area_sq_km * 10)
                    elif 'край' in name:
                        population = int(area_sq_km * 5)
                    elif 'округ' in name or 'аок' in name:
                        population = int(area_sq_km * 1)
                    else:
                        population = int(area_sq_km * 25)

            # ВРП
            grp = None
            for key, val in KNOWN_ECONOMY.items():
                if key in name:
                    grp = float(val)
                    break

            if grp is None:
                if population == 0:
                    grp = 0.0
                elif population > 500_000:
                    grp = round(population * 1.2 / 1000, 1)
                else:
                    grp = round(population * 0.85 / 1000, 1)
            else:
                grp = round(grp, 1)

            grps.append(grp)

        gdf['grp'] = grps

        import numpy as np
        grp_values = sorted([g for g in grps if g and g > 0])
        if not grp_values:
            return

        # 6 квантильных интервалов для плавного распределения цветов
        q_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        thresholds = [float(np.quantile(grp_values, q)) for q in q_levels]

        # 6-ступенчатая зеленая палитра ColorBrewer Greens: от светло-зеленого к темно-зеленому
        colors = ['#EDF8E9', '#BAE4B3', '#74C476', '#31A354', '#006D2C', '#005A32']

        def get_color(g):
            if g is None or g <= 0:
                return '#E2E8F0'
            if len(grp_values) == 1:
                return colors[2]
            if g <= thresholds[1]:
                return colors[0]
            elif g <= thresholds[2]:
                return colors[1]
            elif g <= thresholds[3]:
                return colors[2]
            elif g <= thresholds[4]:
                return colors[3]
            elif g <= thresholds[5]:
                return colors[4]
            else:
                return colors[5]

        def style_function(feature):
            g = feature['properties'].get('grp', 0)
            return {
                'color': '#334155',
                'weight': 1.5,
                'fillColor': get_color(g),
                'fillOpacity': 0.72,
                'dashArray': None
            }

        def highlight_function(feature):
            return {
                'weight': 3,
                'color': '#064E3B',
                'fillOpacity': 0.90
            }

        # Форматирование отображаемого ВРП
        gdf['grp_display'] = gdf['grp'].apply(
            lambda g: f"{g:,.1f} млрд ₽".replace(',', ' ').replace('.', ',') if (g and g > 0) else 'Нет данных'
        )

        tooltip = folium.GeoJsonTooltip(
            fields=['display_name', 'grp_display'],
            aliases=['Территория:', 'ВРП:'],
            style="background: white; border: 1px solid #CBD5E1; padding: 6px 10px; "
                  "font-weight: 700; font-size: 12px; border-radius: 6px; "
                  "box-shadow: 0 2px 8px rgba(0,0,0,0.12);"
        )

        folium.GeoJson(
            gdf,
            name='Экономика (ВРП)',
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=tooltip,
            show=False,           # Отдельный отключаемый слой (выключен по умолчанию)
            interactive=True
        ).add_to(self.map)

        self._economy_added = True
        print(f"  ✓ Слой экономической аналитики (ВРП) добавлен ({len(grp_values)} полигонов)")

    def add_legend(self):
        legend_html = f'''
        <div style="
            position: fixed;
            top: 14px; left: 60px;
            width: 220px;
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            padding: 12px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            color: #334155;
        ">
            <h4 style="margin: 0 0 10px 0; color: #1E293B; font-size: 13.5px; font-weight: 700;">Легенда карты</h4>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <i class="fa fa-star" style="color: #FF9800; font-size: 12px; margin-right: 8px;"></i>
                <span>Центры</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <div style="width: 18px; height: 3px; background: #2E8B57; margin-right: 8px; border-radius: 2px;"></div>
                <span>Границы</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <div style="width: 18px; height: 3px; background: #0284C7; margin-right: 8px; border-radius: 2px;"></div>
                <span>Реки</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 18px; height: 14px; background: #38BDF8; border: 1px solid #0284C7; margin-right: 8px; opacity: 0.8; border-radius: 2px;"></div>
                <span>Водоемы</span>
            </div>
            <div id="choropleth-legend-block" style="display: none; border-top: 1px solid #E2E8F0; padding-top: 8px; margin-top: 6px;">
                <div style="font-size: 11.5px; font-weight: 700; color: #1E293B; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between;">
                    <span>📊 Население районов</span>
                </div>
                <div style="display: flex; height: 11px; border-radius: 4px; overflow: hidden; margin-bottom: 4px; border: 1px solid #CBD5E1;">
                    <div style="flex: 1; background: #FFFFCC;" title="Мин."></div>
                    <div style="flex: 1; background: #FED976;"></div>
                    <div style="flex: 1; background: #FEB24C;"></div>
                    <div style="flex: 1; background: #FD8D3C;"></div>
                    <div style="flex: 1; background: #E31A1C;"></div>
                    <div style="flex: 1; background: #800026;" title="Макс."></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 9.5px; color: #64748B;">
                    <span>Меньше</span>
                    <span>Больше</span>
                </div>
            </div>
            <div id="economy-legend-block" style="display: none; border-top: 1px solid #E2E8F0; padding-top: 8px; margin-top: 6px;">
                <div style="font-size: 11.5px; font-weight: 700; color: #1E293B; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between;">
                    <span>💰 ВРП (Экономика)</span>
                </div>
                <div style="display: flex; height: 11px; border-radius: 4px; overflow: hidden; margin-bottom: 4px; border: 1px solid #CBD5E1;">
                    <div style="flex: 1; background: #EDF8E9;" title="Мин."></div>
                    <div style="flex: 1; background: #BAE4B3;"></div>
                    <div style="flex: 1; background: #74C476;"></div>
                    <div style="flex: 1; background: #31A354;"></div>
                    <div style="flex: 1; background: #006D2C;"></div>
                    <div style="flex: 1; background: #005A32;" title="Макс."></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 9.5px; color: #64748B;">
                    <span>Меньше</span>
                    <span>Больше</span>
                </div>
            </div>
            <div style="border-top: 1px solid #E2E8F0; padding-top: 8px; font-size: 11px; color: #94A3B8; text-align: center;">
                {self.title}
            </div>
        </div>

        <script>
        (function() {{
            function syncChoroplethLegend() {{
                const labels = document.querySelectorAll('.leaflet-control-layers-overlays label');
                let isPopChecked = false;
                let isEconChecked = false;
                labels.forEach(label => {{
                    const inp = label.querySelector('input[type="checkbox"]');
                    if (label.textContent.includes('Население') || label.textContent.includes('Choropleth')) {{
                        if (inp && inp.checked) isPopChecked = true;
                    }}
                    if (label.textContent.includes('Экономика') || label.textContent.includes('ВРП')) {{
                        if (inp && inp.checked) isEconChecked = true;
                    }}
                }});
                const popBlock = document.getElementById('choropleth-legend-block');
                if (popBlock) {{
                    popBlock.style.display = isPopChecked ? 'block' : 'none';
                }}
                const econBlock = document.getElementById('economy-legend-block');
                if (econBlock) {{
                    econBlock.style.display = isEconChecked ? 'block' : 'none';
                }}
            }}

            window.addEventListener('load', function() {{
                const ctrl = document.querySelector('.leaflet-control-layers');
                if (ctrl) {{
                    ctrl.addEventListener('change', syncChoroplethLegend);
                }}
                syncChoroplethLegend();
            }});
        }})();
        </script>
        '''
        self.map.get_root().html.add_child(folium.Element(legend_html))

    def add_minimap(self):
        minimap = plugins.MiniMap(toggle_display=True)
        self.map.add_child(minimap)

    def add_fullscreen(self):
        plugins.Fullscreen().add_to(self.map)

    def save(self, filename=None, open_browser=False):
        if filename is None:
            filename = self.output_filename
        if not getattr(self, '_choropleth_added', False):
            self.add_choropleth_layer()
        if not getattr(self, '_economy_added', False):
            self.add_economy_layer()
        folium.LayerControl(collapsed=False, position='bottomleft').add_to(self.map)
        self.add_quiz_controls()
        self.add_legend()
        self.add_fullscreen()
        self.map.save(filename)
        print(f"\n{'='*60}")
        print(f"Карта успешно создана: {filename}")
        print(f"{'='*60}")

        with open(filename, 'r', encoding='utf-8') as f:
            html = f.read()

        custom_css_js = """
        <style>
        path:focus,
        path:focus-visible,
        svg:focus,
        .leaflet-container :focus,
        .leaflet-interactive:focus,
        .leaflet-pane path:focus {
            outline: none !important;
        }

        .leaflet-control-attribution {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            width: 0 !important;
            height: 0 !important;
            overflow: hidden !important;
        }

        .my-attribution {
            position: fixed;
            bottom: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.95);
            padding: 4px 10px;
            font-size: 11px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #64748B;
            z-index: 10000;
            border-top-left-radius: 6px;
            box-shadow: 0 -1px 4px rgba(0,0,0,0.06);
            pointer-events: auto;
        }
        .my-attribution a {
            color: #2563EB;
            text-decoration: none;
        }
        .my-attribution a:hover {
            text-decoration: underline;
        }

        .leaflet-control-layers {
            border-radius: 10px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12) !important;
            border: 1px solid rgba(0,0,0,0.08) !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 12.5px !important;
            color: #334155 !important;
        }

        .leaflet-control-layers::before {
            content: "Слои карты";
            display: block;
            font-weight: 700;
            margin-bottom: 6px;
            color: #1E293B;
            font-size: 13px;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 4px;
        }

        .leaflet-control-layers-base label {
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin-bottom: 3px !important;
            cursor: pointer !important;
            font-size: 11.5px !important;
        }

        .leaflet-control-layers-separator {
            border-top: 1px solid #E2E8F0 !important;
            margin: 6px 0 !important;
        }

        .chart-tab-group {
            display: inline-flex;
            gap: 2px;
            background: #E2E8F0;
            padding: 2px;
            border-radius: 6px;
        }

        .chart-tab {
            border: none;
            background: transparent;
            font-size: 9.5px;
            font-weight: 700;
            color: #475569;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .chart-tab.active {
            background: #ffffff;
            color: #0F172A;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        </style>
        """

        my_attribution_html = """
        <div class="my-attribution">
            © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors, © <a href="https://carto.com/attributions" target="_blank">CARTO</a>
        </div>
        """

        chart_js_cdn = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
        if '</head>' in html:
            html = html.replace('</head>', chart_js_cdn + '\n' + custom_css_js + '</head>', 1)
        else:
            html = custom_css_js + html

        reg_id = self.region_key or self.slug
        body_attrs = (
            f'data-region="{reg_id}" '
            f'data-region-title="{self.ru_title}" '
            f'data-center-lat="{self.center[0]}" '
            f'data-center-lng="{self.center[1]}" '
            f'data-zoom="{self.zoom}" '
            f'data-map-url="{self.output_filename}"'
        )
        if '<body' in html:
            if 'data-region="' in html:
                html = re.sub(r'data-region="[^"]*"', f'data-region="{reg_id}"', html, count=1)
                html = re.sub(r'data-region-title="[^"]*"', f'data-region-title="{self.ru_title}"', html, count=1)
                html = re.sub(r'data-center-lat="[^"]*"', f'data-center-lat="{self.center[0]}"', html, count=1)
                html = re.sub(r'data-center-lng="[^"]*"', f'data-center-lng="{self.center[1]}"', html, count=1)
                html = re.sub(r'data-zoom="[^"]*"', f'data-zoom="{self.zoom}"', html, count=1)
                html = re.sub(r'data-map-url="[^"]*"', f'data-map-url="{self.output_filename}"', html, count=1)
            else:
                html = re.sub(r'<body([^>]*)>', rf'<body\1 {body_attrs}>', html, count=1)

        if '</body>' in html:
            html = html.replace('</body>', my_attribution_html + '</body>', 1)
        else:
            html += my_attribution_html

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        if open_browser:
            try:
                webbrowser.open(f'file://{os.path.abspath(filename)}')
            except Exception:
                pass

        return filename

def generate_region_map(region_name, region_districts, clipped_rivers=None, clipped_lakes=None, clipped_cities=None, open_browser=False):
    atlas = InteractiveAtlas(
        region_name=region_name,
        region_districts=region_districts,
        clipped_rivers=clipped_rivers,
        clipped_lakes=clipped_lakes,
        clipped_cities=clipped_cities
    )
    atlas.add_districts()
    atlas.add_water_bodies()
    atlas.add_rivers()
    atlas.add_district_centers()
    output_file = atlas.save(open_browser=open_browser)
    return output_file


def build_configured_region(region_key, open_browser=False):
    if region_key not in REGIONS_CONFIG:
        raise ValueError(f"Unknown region key: {region_key}")
    cfg = REGIONS_CONFIG[region_key]
    print(f"\n🗺️  Сборка детальной карты: {cfg['title']} ({region_key})...")
    atlas = InteractiveAtlas(region_key=region_key)
    atlas.add_districts()
    atlas.add_water_bodies()
    atlas.add_rivers()
    atlas.add_district_centers()
    output_file = atlas.save(open_browser=open_browser)
    return output_file


def main():
    import sys
    print("=" * 65)
    print("  🚀 GEOATLAS: ГИБРИДНЫЙ КАРТОГРАФИЧЕСКИЙ ДВИЖОК")
    print("=" * 65)

    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    flags = [a for a in sys.argv[1:] if a.startswith('-')]
    do_all = '--all' in flags

    target = args[0].lower() if args else None

    generated_files = []

    # 1. Если указан конкретный регион из REGIONS_CONFIG (rostov, krasnodar, russia/rf)
    if target in REGIONS_CONFIG or target in ['rf', 'российская федерация', 'россия']:
        key = 'russia' if target in ['rf', 'российская федерация', 'россия'] else target
        out = build_configured_region(key, open_browser=True)
        generated_files.append((REGIONS_CONFIG[key]['title'], out))

    # 2. Если аргументов нет (запуск по умолчанию): строим 3 базовые детальные карты!
    elif target is None and not do_all:
        print("\n⚙️  Запуск в стандартном режиме: генерация 3 ключевых карт (Ростов, Краснодар, РФ)...")
        for key in ['rostov', 'krasnodar', 'russia']:
            try:
                out = build_configured_region(key, open_browser=False)
                generated_files.append((REGIONS_CONFIG[key]['title'], out))
            except Exception as e:
                print(f" ❌ Ошибка при сборке {key}: {e}")

    # 3. Если передан фильтр для нарезки из russia_unified или флаг --all:
    else:
        # Сначала строим 3 детальные карты, если флаг --all
        if do_all:
            print("\n⚙️  Генерация ключевых детальных карт...")
            for key in ['rostov', 'krasnodar', 'russia']:
                try:
                    out = build_configured_region(key, open_browser=False)
                    generated_files.append((REGIONS_CONFIG[key]['title'], out))
                except Exception as e:
                    print(f" ❌ Ошибка при сборке {key}: {e}")

        # Читаем unified shapefiles для остальных регионов
        base_shp_dir = os.path.join(BASE_DIR, 'Py_Geo', 'shape', 'russia_unified')
        districts_shp = os.path.join(base_shp_dir, 'districts.shp')
        rivers_shp = os.path.join(base_shp_dir, 'rivers.shp')
        lakes_shp = os.path.join(base_shp_dir, 'lakes.shp')
        cities_shp = os.path.join(base_shp_dir, 'cities.shp')

        if os.path.exists(districts_shp):
            print("\n📦 Загрузка единых SHP-файлов для автоматической нарезки регионов...")
            districts = gpd.read_file(districts_shp)
            rivers = gpd.read_file(rivers_shp) if os.path.exists(rivers_shp) else None
            lakes = gpd.read_file(lakes_shp) if os.path.exists(lakes_shp) else None
            cities = gpd.read_file(cities_shp) if os.path.exists(cities_shp) else None

            if 'NAME_2' in districts.columns:
                districts = districts[districts['NAME_2'].astype(str).str.lower() != 'water body'].copy()
            districts['geometry'] = districts['geometry'].apply(clean_geom)

            if districts.crs is None or districts.crs.to_string() != 'EPSG:4326':
                districts = districts.to_crs('EPSG:4326') if districts.crs else districts.set_crs('EPSG:4326')
            if rivers is not None and rivers.crs != districts.crs:
                rivers = rivers.to_crs(districts.crs)
            if lakes is not None and lakes.crs != districts.crs:
                lakes = lakes.to_crs(districts.crs)
            if cities is not None and cities.crs != districts.crs:
                cities = cities.to_crs(districts.crs)

            region_col = 'NAME_1'
            unique_regions = [r for r in districts[region_col].dropna().unique() if str(r).strip()]

            if target:
                matched = [
                    r for r in unique_regions
                    if target in str(r).lower() or target in slugify_name(r).lower() or target in REGION_TRANSLATIONS.get(r, '').lower()
                ]
                if matched:
                    unique_regions = matched

            # Исключаем Ростов и Краснодар из нарезки, так как у них свои детальные шейпы
            if not target:
                unique_regions = [r for r in unique_regions if slugify_name(r) not in ['rostov', 'krasnodar']]

            for idx, region_name in enumerate(unique_regions, 1):
                ru_name = REGION_TRANSLATIONS.get(region_name, region_name)
                print(f"[{idx}/{len(unique_regions)}] Нарезка региона: {ru_name} ('{region_name}')...", end="", flush=True)
                try:
                    reg_districts = districts[districts[region_col] == region_name].copy()
                    if reg_districts.empty:
                        print(" Пропущен")
                        continue
                    boundary = reg_districts.union_all() if hasattr(reg_districts, 'union_all') else reg_districts.unary_union
                    boundary = clean_geom(boundary)

                    c_rivers = gpd.clip(rivers, boundary) if rivers is not None else None
                    c_lakes = gpd.clip(lakes, boundary) if lakes is not None else None
                    c_cities = gpd.clip(cities, boundary) if cities is not None else None

                    out = generate_region_map(region_name, reg_districts, c_rivers, c_lakes, c_cities, open_browser=bool(target))
                    generated_files.append((ru_name, out))
                    print(f" ✓ {out}")
                except Exception as e:
                    print(f" ❌ Ошибка: {e}")

    print("\n" + "=" * 65)
    print(f"  🎉 УСПЕШНО СГЕНЕРИРОВАНО КАРТ: {len(generated_files)}")
    print("=" * 65)
    return generated_files


if __name__ == "__main__":
    main()


# ==========================================
# ЭКСПОРТ FASTAPI ДЛЯ RENDER / UVICORN
# ==========================================
try:
    from server import app
except Exception:
    app = None
