import geopandas as gpd
import folium
from folium import plugins
import os
import json
import re
import webbrowser
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point

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
    """Очищает и восстанавливает валидность геометрии, преобразуя GeometryCollection в Polygon/MultiPolygon.
    
    Безопасно обрабатывает None, пустые геометрии, некорректные кольца и вложенные GeometryCollection.
    """
    if geom is None:
        return None
    try:
        if geom.is_empty:
            return geom
    except Exception:
        return None

    try:
        if not geom.is_valid:
            try:
                from shapely.validation import make_valid
                geom = make_valid(geom)
            except Exception:
                try:
                    geom = geom.buffer(0)
                except Exception:
                    pass
    except Exception:
        try:
            geom = geom.buffer(0)
        except Exception:
            pass

    if geom is None:
        return None

    try:
        if geom.is_empty:
            return geom
    except Exception:
        return None

    # Распаковка разнородной коллекции (GeometryCollection)
    if getattr(geom, 'geom_type', '') == 'GeometryCollection':
        try:
            from shapely.ops import unary_union
            sub_geoms = []
            for g in getattr(geom, 'geoms', []):
                if g is not None:
                    try:
                        if not g.is_empty:
                            cg = clean_geom(g)
                            if cg is not None and not cg.is_empty:
                                sub_geoms.append(cg)
                    except Exception:
                        pass

            polys = [g for g in sub_geoms if g.geom_type in ['Polygon', 'MultiPolygon']]
            if polys:
                geom = unary_union(polys)
            else:
                lines = [g for g in sub_geoms if g.geom_type in ['LineString', 'MultiLineString']]
                if lines:
                    geom = unary_union(lines)
                else:
                    points = [g for g in sub_geoms if g.geom_type in ['Point', 'MultiPoint']]
                    if points:
                        geom = unary_union(points)
        except Exception:
            pass

    try:
        if geom is not None and not geom.is_empty and not geom.is_valid:
            try:
                from shapely.validation import make_valid
                geom = make_valid(geom)
            except Exception:
                geom = geom.buffer(0)
    except Exception:
        pass

    return geom

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, 'public', 'maps')
os.makedirs(MAPS_DIR, exist_ok=True)

REGIONS_CONFIG = {
    'rostov': {
        'path': os.path.join(BASE_DIR, 'Py_Geo', 'shape', 'rostov'),
        'title': 'Ростовская область',
        'center': [47.5, 40.5],
        'zoom': 8,
        'output': os.path.join(MAPS_DIR, 'rostov_quiz_map.html'),
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
        'output': os.path.join(MAPS_DIR, 'krasnodar_quiz_map.html'),
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
        'output': os.path.join(MAPS_DIR, 'russia_quiz_map.html'),
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

CARTO_KEY = os.environ.get('CARTO_KEY', 'cb1_3wsm_1_6bdccfe40c07a69c4fce7b68')

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

KNOWN_POPULATION = {
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

KNOWN_ECONOMY = {
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
            default_out = os.path.join(MAPS_DIR, f"{self.slug}_quiz_map.html")
            self.output_filename = cfg.get('output', default_out)
            self.center = cfg['center']
            self.zoom = cfg['zoom']
        else:
            self.region_name = str(region_name or region_key or 'Регион').strip()
            self.is_rf = is_rf
            self.ru_title = REGION_TRANSLATIONS.get(self.region_name, self.region_name)
            self.slug = slugify_name(self.region_name)
            self.output_filename = os.path.join(MAPS_DIR, f"{self.slug}_quiz_map.html")
            self.center = [55.75, 37.61]
            self.zoom = 7

        self.title = f"Интерактивный атлас: {self.ru_title}"

        self.input_districts = region_districts
        self.input_rivers = clipped_rivers
        self.input_lakes = clipped_lakes
        self.input_cities = clipped_cities

        # Расчет центра и масштаба по границам геометрии
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

        self.map = folium.Map(
            location=self.center,
            zoom_start=self.zoom,
            control_scale=True,
            tiles=None,
            width='100%',
            height='100%'
        )

        if not self.is_rf and not self.cfg and self.input_districts is not None and not self.input_districts.empty:
            bounds = self.input_districts.total_bounds
            self.map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        folium.TileLayer(
            tiles=f'https://basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}',
            name='Carto Voyager',
            attr='© OpenStreetMap contributors, © CARTO',
            control=True,
            show=True
        ).add_to(self.map)

        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            name='Спутник (Esri)',
            attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            control=True,
            show=False
        ).add_to(self.map)

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
        """Корректирует координаты восточнее 180-го меридиана (Чукотка, о. Врангеля и др.) для корректного отображения в Leaflet.
        
        Точки намеренно НЕ сдвигаются (чтобы маркеры не улетали за край карты).
        """
        if geom is None:
            return None
        try:
            if geom.is_empty:
                return geom
        except Exception:
            return geom

        # Если геометрия невалидна, предварительно восстанавливаем ее
        try:
            if not geom.is_valid:
                geom = clean_geom(geom)
                if geom is None or geom.is_empty:
                    return geom
        except Exception:
            pass

        try:
            g_type = getattr(geom, 'geom_type', '')
            if g_type == 'Polygon':
                exterior = [(x + 360 if x < 0 else x, y) for x, y in geom.exterior.coords]
                interiors = [[(x + 360 if x < 0 else x, y) for x, y in interior.coords] for interior in geom.interiors]
                new_poly = Polygon(exterior, interiors)
                return clean_geom(new_poly) if not new_poly.is_valid else new_poly
            elif g_type == 'MultiPolygon':
                fixed_parts = []
                for p in geom.geoms:
                    if p is not None and not p.is_empty:
                        fixed_p = self._fix_antimeridian(p)
                        if fixed_p is not None and not fixed_p.is_empty:
                            if fixed_p.geom_type == 'Polygon':
                                fixed_parts.append(fixed_p)
                            elif fixed_p.geom_type == 'MultiPolygon':
                                fixed_parts.extend([sub for sub in fixed_p.geoms if not sub.is_empty])
                return MultiPolygon(fixed_parts) if fixed_parts else geom
            elif g_type == 'LineString':
                return LineString([(x + 360 if x < 0 else x, y) for x, y in geom.coords])
            elif g_type == 'MultiLineString':
                fixed_lines = []
                for ls in geom.geoms:
                    if ls is not None and not ls.is_empty:
                        fixed_ls = self._fix_antimeridian(ls)
                        if fixed_ls is not None and not fixed_ls.is_empty:
                            if fixed_ls.geom_type == 'LineString':
                                fixed_lines.append(fixed_ls)
                            elif fixed_ls.geom_type == 'MultiLineString':
                                fixed_lines.extend([sub for sub in fixed_ls.geoms if not sub.is_empty])
                return MultiLineString(fixed_lines) if fixed_lines else geom
            elif g_type == 'GeometryCollection':
                from shapely.geometry import GeometryCollection
                fixed_coll = [self._fix_antimeridian(g) for g in geom.geoms if g is not None and not g.is_empty]
                return clean_geom(GeometryCollection(fixed_coll)) if fixed_coll else geom
            elif g_type in ['Point', 'MultiPoint']:
                # Точки не смещаются за 180 меридиан для корректного отображения маркеров в Leaflet
                return geom
        except Exception:
            pass

        return geom

    def _safe_to_crs(self, gdf):
        if gdf is None or gdf.empty:
            return gdf

        if 'geometry' not in gdf.columns:
            return gdf

        gdf = gdf.dropna(subset=['geometry']).copy()
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
        if gdf.empty:
            return gdf

        def _is_degree_bounds(bounds):
            if bounds is None or len(bounds) < 4:
                return False
            import numpy as np
            if any(np.isnan(val) or np.isinf(val) for val in bounds):
                return False
            minx, miny, maxx, maxy = bounds
            return (-360.0 <= minx <= 360.0) and (-90.0 <= miny <= 90.0) and (-360.0 <= maxx <= 360.0) and (-90.0 <= maxy <= 90.0)

        try:
            if gdf.crs:
                crs_str = str(gdf.crs).upper()
                if 'EPSG:4326' not in crs_str and '4326' not in crs_str:
                    gdf = gdf.to_crs('EPSG:4326')
            else:
                b = gdf.total_bounds
                if _is_degree_bounds(b):
                    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                else:
                    try:
                        gdf = gdf.set_crs('EPSG:3857', allow_override=True).to_crs('EPSG:4326')
                    except Exception:
                        gdf = gdf.set_crs('EPSG:4326', allow_override=True)
        except Exception:
            try:
                b = gdf.total_bounds
                if _is_degree_bounds(b):
                    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                else:
                    try:
                        gdf = gdf.set_crs('EPSG:3857', allow_override=True).to_crs('EPSG:4326')
                    except Exception:
                        gdf = gdf.set_crs('EPSG:4326', allow_override=True)
            except Exception:
                pass

        gdf = gdf.dropna(subset=['geometry'])
        try:
            bounds = gdf.bounds
            gdf = gdf[~bounds.isna().any(axis=1)]
        except Exception:
            pass

        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        try:
            gdf['geometry'] = gdf['geometry'].apply(clean_geom)
        except Exception:
            pass

        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]

        # Нормализация координат полигонов восточнее 180 меридиана
        try:
            gdf.geometry = gdf.geometry.apply(self._fix_antimeridian)
        except Exception:
            pass

        # Упрощение полигонов для масштаба РФ
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
        
        # Фильтр региональных столиц
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

            # Фильтрация точек вне территории РФ
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

    def _estimate_metrics(self, name, area_sq_km=0):
        """Оценивает численность населения и объем ВРП района/субъекта по справочникам или площади (DRY)."""
        search_name = str(name or '').lower().replace('\u0301', '').replace('e', 'е').replace('ё', 'е').strip()
        area_sq_km = float(area_sq_km or 0)

        population = None
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

        return population, grp

    def _calculate_neighbors_data(self):
        if self.districts_gdf is None or len(self.districts_gdf) == 0:
            return []

        valid_gdf = self.districts_gdf[self.districts_gdf.geometry.is_valid & ~self.districts_gdf.geometry.is_empty].copy()
        valid_gdf = valid_gdf[valid_gdf['display_name'] != ''].copy()
        
        try:
            # Проекция EPSG:6933 для расчета площадей без искажений
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

        # Поиск смежных полигонов через sindex
        valid_rows = [(idx, row.geometry, str(row['display_name'])) for idx, row in valid_gdf.iterrows()]
        gdf_search = gpd.GeoDataFrame(geometry=[geom for _, geom, _ in valid_rows])
        sindex = gdf_search.sindex if (hasattr(gdf_search, 'sindex') and gdf_search.sindex is not None) else None

        for pos, (idx, current_geom, current_name) in enumerate(valid_rows):
            buffered_geom = current_geom.buffer(0.005)
            neighbor_names = []

            c_positions = None
            if sindex is not None:
                try:
                    c_positions = sorted(sindex.query(buffered_geom, predicate='intersects'))
                except Exception:
                    c_positions = None

            if c_positions is not None:
                for c_pos in c_positions:
                    if c_pos < len(valid_rows):
                        _, other_geom, other_name = valid_rows[c_pos]
                        if other_name != current_name and other_name.strip() and other_geom.intersects(buffered_geom):
                            neighbor_names.append(other_name)
            else:
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

            area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if (idx in metric_gdf.index and metric_gdf.loc[idx].geometry is not None and not metric_gdf.loc[idx].geometry.is_empty) else 0

            population, grp = self._estimate_metrics(current_name, area_sq_km)

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

            district_list = []
            for idx, row in valid_districts.iterrows():
                if row.geometry is not None and not row.geometry.is_empty:
                    d_name = str(row.get('NL_NAME_2') or row.get('display_name') or row.get('NAME_2') or row.get('NAME_RU') or row.get('NAME') or f"Район {idx}")
                    district_list.append((idx, row.geometry, d_name))

            district_neighbors_map = {}
            gdf_district_search = gpd.GeoDataFrame(geometry=[geom for _, geom, _ in district_list])
            sindex = gdf_district_search.sindex if (hasattr(gdf_district_search, 'sindex') and gdf_district_search.sindex is not None) else None

            for pos, (idx, geom, d_name) in enumerate(district_list):
                b_geom = geom.buffer(0.006)
                n_ids = []
                n_names = []

                c_positions = None
                if sindex is not None:
                    try:
                        c_positions = sorted(sindex.query(b_geom, predicate='intersects'))
                    except Exception:
                        c_positions = None

                if c_positions is not None:
                    for c_pos in c_positions:
                        if c_pos < len(district_list):
                            other_idx, other_geom, other_name = district_list[c_pos]
                            if other_idx != idx and other_geom.intersects(b_geom):
                                n_ids.append(f"dist_{other_idx}")
                                n_names.append(other_name)
                else:
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

        self.region_metadata = {
            "REGION_BOUNDS": region_bounds,
            "EMBEDDED_DISTRICTS": districts_data,
            "EMBEDDED_CENTERS": centers_data,
            "EMBEDDED_NEIGHBORS": neighbors_data,
            "EMBEDDED_RIVERS": rivers_data,
            "EMBEDDED_PUZZLE_DATA": puzzle_districts,
            "REGION_OUTLINE_GEOJSON": region_outline_geojson
        }

        map_basename = os.path.basename(self.output_filename)
        server_ctx = {
            "region": self.region_key or self.slug,
            "title": self.ru_title,
            "center": self.center,
            "zoom": self.zoom,
            "map_url": f"public/maps/{map_basename}",
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

        branding_data = {}
        branding_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'branding.json')
        if os.path.exists(branding_path):
            try:
                with open(branding_path, 'r', encoding='utf-8') as f:
                    branding_data = json.load(f)
            except Exception:
                pass
        brand_org_short = branding_data.get('org_short') or branding_data.get('university_short') or 'ЮФУ'
        brand_sub_title = branding_data.get('sub_title') or branding_data.get('org_name') or 'Институт наук о Земле ЮФУ'

        self.map.get_root().header.add_child(folium.Element(
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">\n'
            '<meta name="theme-color" content="#2563EB">\n'
            '<meta name="apple-mobile-web-app-capable" content="yes">\n'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
        ))

        self.map.get_root().html.add_child(folium.Element(f"<script>{dynamic_js}\n{quiz_js}</script>"))

        quiz_html = f'''
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
        <meta name="theme-color" content="#2563EB">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="stylesheet" href="/public/map.css">
        <!-- OVERLAY LOADER ПЕРВИЧНОЙ ЗАГРУЗКИ КАРТЫ -->
        <div id="map-loader" class="map-loader-overlay">
            <div class="map-loader-content">
                <div class="map-loader-spinner"></div>
                <div class="map-loader-title">Загрузка геоданных...</div>
                <div class="map-loader-subtitle">Подготовка пространственных слоев и номенклатуры</div>
            </div>
        </div>

        <div class="top-nav-buttons" id="top-nav-panel">
            <button id="mobile-menu-btn" class="nav-top-btn mobile-only-btn" onclick="toggleMobileMenu()" aria-label="Открыть меню">
                <span style="font-size: 20px;">☰</span>
            </button>
            <a href="index.html" class="btn btn-secondary nav-top-btn" title="Вернуться к выбору региона"><span>🏠</span> <span>На главную</span></a>
            <button class="btn btn-secondary nav-top-btn reset-map-btn" onclick="resetMapView()" title="Показать всю карту">
                <span>🌍</span> <span>Вся карта</span>
            </button>
            <button class="btn btn-secondary nav-top-btn duel-top-btn" onclick="openDuelModal()" title="Мультиплеер 1 на 1 в реальном времени">
                <span>⚔️</span> <span>Дуэль</span>
            </button>
            <button class="btn btn-secondary nav-top-btn admin-btn" onclick="window.open('/admin', '_blank')" title="Панель преподавателя">
                <span>👨‍🏫</span> <span>Кабинет</span>
            </button>
            <button id="auth-top-btn" class="btn btn-primary nav-top-btn auth-btn" onclick="goToMainAuth()" title="Авторизация через главное меню">
                <span>🎓</span> <span>Войти через Главное меню</span>
            </button>
            <div id="student-profile-badge" class="student-badge" style="display: none;" onclick="openStudentProfileModal()" title="Личный кабинет и витрина достижений">
                <div class="badge-avatar">🎓</div>
                <div class="badge-info">
                    <span id="student-badge-name" class="badge-name">Студент</span>
                    <span id="student-badge-group" class="badge-group">Группа</span>
                </div>
                <button onclick="event.stopPropagation(); logoutStudent()" class="badge-logout" title="Выйти">&times;</button>
            </div>
            <button class="btn btn-secondary nav-top-btn leaderboard-top-btn" onclick="showLeaderboard()" title="Глобальная таблица лидеров и профиль"><span>🏆</span> <span>Рейтинг</span></button>
            <button class="btn btn-secondary help-circle-btn" onclick="openWelcomeModal()" title="О проекте и справка">?</button>
        </div>

        <div id="mobile-nav-overlay" class="mobile-nav-overlay" style="display: none;">
            <div class="mobile-nav-menu">
                <div class="mobile-nav-header">
                    <div class="mobile-nav-title">Навигация</div>
                    <button onclick="toggleMobileMenu()" class="mobile-nav-close">×</button>
                </div>
                
                <div class="mobile-nav-profile" id="mobile-nav-profile-container" style="display: none;">
                    <div class="mobile-nav-avatar">🎓</div>
                    <div class="mobile-nav-user-info">
                        <div class="mobile-nav-name" id="mobile-nav-name">Студент</div>
                        <div class="mobile-nav-group" id="mobile-nav-group">Группа</div>
                    </div>
                    <button onclick="logoutStudent()" class="mobile-nav-logout" title="Выйти">🚪</button>
                </div>

                <div class="mobile-nav-list">
                    <a href="index.html" class="mobile-nav-item">
                        <span class="nav-icon">🏠</span> На главную
                    </a>
                    <button onclick="resetMapView(); toggleMobileMenu();" class="mobile-nav-item">
                        <span class="nav-icon">🌍</span> Вся карта
                    </button>
                    <button onclick="openDuelModal(); toggleMobileMenu();" class="mobile-nav-item">
                        <span class="nav-icon">⚔️</span> Дуэль
                    </button>
                    <button onclick="window.open('/admin', '_blank')" class="mobile-nav-item">
                        <span class="nav-icon">👨‍🏫</span> Кабинет преподавателя
                    </button>
                    
                    <div id="mobile-nav-auth-btn" class="mobile-nav-item" style="cursor:pointer;" onclick="goToMainAuth()">
                        <span class="nav-icon">🎓</span> Войти через главное меню
                    </div>

                    <button onclick="showLeaderboard(); toggleMobileMenu();" class="mobile-nav-item">
                        <span class="nav-icon">🏆</span> Рейтинг
                    </button>
                    <button onclick="openWelcomeModal(); toggleMobileMenu();" class="mobile-nav-item">
                        <span class="nav-icon">❓</span> О проекте и справка
                    </button>
                </div>
            </div>
        </div>

        <div id="quiz-controls" class="app-card">
            <!-- ЭКЗАМЕНАЦИОННЫЙ ИНФОРМАЦИОННЫЙ БЛОК ВВЕРХУ БОКОВОЙ ПАНЕЛИ -->
            <div id="exam-sidebar-header" class="exam-sidebar-bar" style="display: none;">
                <div class="exam-sidebar-top">
                    <div class="exam-sidebar-status">
                        <span class="exam-sidebar-dot"></span>
                        <span class="exam-sidebar-title">🛡️ ЭКЗАМЕН • ANTI-CHEAT</span>
                    </div>
                    <div class="exam-sidebar-timer-box">
                        <span class="exam-sidebar-timer-icon">⏳</span>
                        <span id="exam-sidebar-timer" class="exam-sidebar-timer-text">10:00</span>
                    </div>
                </div>
                <div class="exam-sidebar-meta">
                    <div class="exam-sidebar-student">Студент: <b id="exam-sidebar-student-name">Студент</b></div>
                    <div class="exam-sidebar-group">Группа: <b id="exam-sidebar-group-name">{brand_org_short}</b></div>
                </div>
                <div class="timer-track exam-timer-track">
                    <div id="timer-bar"></div>
                </div>
            </div>

            <div class="panel-header">
                <div class="panel-header-bar">
                    <div class="panel-institution-badge">{brand_sub_title}</div>
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
                <div class="section-divider-title">
                    Обучающий режим
                </div>
                <div class="study-pick-grid">
                    <button onclick="startStudyMode('districts')" class="btn btn-study-action">🗺️ Территории</button>
                    <button onclick="startStudyMode('rivers')" class="btn btn-study-action">🌊 Реки</button>
                    <button onclick="startStudyMode('centers')" class="btn btn-study-action">📍 Центры</button>
                </div>

                <div class="section-divider-title section-divider-spaced">
                    Проверка знаний (Викторины)
                </div>

                <div class="btn-group-vertical">
                    <button onclick="openAdaptiveModal()" class="btn btn-block" 
                            id="btn-open-adaptive" 
                            style="background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%) !important; 
                                   color: #FFFFFF !important; border: 1px solid rgba(255,255,255,0.15) !important; 
                                   box-shadow: 0 4px 14px rgba(236,72,153,0.3) !important;">
                        <span>🎯 Адаптивный тест</span>
                    </button>

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
                <div class="btn-group-vertical mt-8">
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
                    <div class="puzzle-header-row">
                        <h4 class="puzzle-title">
                            <span>🧩</span> <span>Собери регион</span>
                        </h4>
                        <span id="puzzle-timer-text" class="puzzle-timer">⏱ 00:00</span>
                    </div>

                    <div class="puzzle-progress-wrap">
                        <div class="puzzle-progress-labels">
                            <span id="puzzle-progress-text">Собрано: 0 из 0</span>
                            <span id="puzzle-percent-text">0%</span>
                        </div>
                        <div class="puzzle-progress-track">
                            <div id="puzzle-progress-bar" style="width: 0%;"></div>
                        </div>
                    </div>

                    <div class="puzzle-stats-row">
                        <span>Ошибок: <b id="puzzle-mistakes-text" class="text-danger">0</b></span>
                        <span>Точность: <b id="puzzle-accuracy-text" class="text-success">100%</b></span>
                    </div>
                </div>

                <div id="puzzle-active-piece-card" class="puzzle-target-card" draggable="true" title="Перетащите эту деталь на карту">
                    <div class="puzzle-card-header">
                        <span class="puzzle-piece-label">
                            Текущая деталь:
                        </span>
                        <span id="puzzle-active-badge" class="puzzle-type-badge">район</span>
                    </div>

                    <div id="puzzle-active-preview" class="puzzle-active-preview-wrap">
                        <!-- SVG силуэт активного района -->
                    </div>

                    <div id="puzzle-active-name" class="puzzle-active-name">
                        Загрузка...
                    </div>
                    <div id="puzzle-active-info" class="puzzle-active-info">
                        Центр: — | Площадь: —
                    </div>
                    <div class="puzzle-drag-hint">
                        🖐️ Перетащите силуэт на карту или кликните по слоту
                    </div>
                </div>

                <div class="puzzle-tray-header">
                    <span class="puzzle-tray-title">Силуэты деталей (выберите любую):</span>
                    <button onclick="skipCurrentPuzzlePiece()" class="btn btn-secondary btn-sm btn-puzzle-skip" title="Пропустить и взять следующую деталь">
                        ⏭ Другая
                    </button>
                </div>

                <div id="puzzle-tray-container" class="puzzle-tray-list">
                    <!-- Список районов в случайном порядке -->
                </div>

                <div class="btn-group-vertical mt-10">
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
            <div id="results-mode" class="text-center" style="display: none;">
                <h4 class="results-header-title">Результаты теста</h4>
                <div id="results-content">
                </div>
                <div class="btn-group-vertical mt-12">
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
                    <div class="welcome-feature" onclick="selectModeFromWelcome('study')" title="Запустить режим обучения номенклатуре">
                        <div class="feature-icon icon-study">🎓</div>
                        <div class="feature-content">
                            <h4>Режим обучения (Номенклатура)</h4>
                            <p>Пошаговое изучение номенклатуры: территорий, русел рек и административных центров с автофокусом карты.</p>
                        </div>
                    </div>
                    <div class="welcome-feature" onclick="selectModeFromWelcome('rivers')" title="Запустить викторину по гидрографии">
                        <div class="feature-icon icon-rivers">🌊</div>
                        <div class="feature-content">
                            <h4>Гидрография</h4>
                            <p>Викторина по главным водным артериям региона. Карта фокусируется на русле реки и предлагает варианты ответа.</p>
                        </div>
                    </div>
                    <div class="welcome-feature" onclick="selectModeFromWelcome('puzzle')" title="Собрать регион из деталей пазла">
                        <div class="feature-icon icon-puzzle">🧩</div>
                        <div class="feature-content">
                            <h4>Топологический пазл</h4>
                            <p>Интерактивная сборка контура региона из силуэтов муниципальных образований без координатной сетки.</p>
                        </div>
                    </div>
                    <div class="welcome-feature" onclick="selectModeFromWelcome('centers')" title="Найти центры на карте">
                        <div class="feature-icon icon-centers">🎯</div>
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

        <div id="adaptive-modal" class="welcome-overlay" style="display: none;">
            <div class="welcome-card" style="max-width: 520px;">
                <div class="welcome-badge" style="background: linear-gradient(135deg, #EC4899, #8B5CF6); color: white;">🎯 Персональный подбор</div>
                <h2 class="welcome-title mb-6">Адаптивный тест</h2>
                <p class="welcome-subtitle mb-16">
                    Алгоритм подберёт вопросы приоритетно на те объекты, где вы чаще всего ошибаетесь.
                </p>

                <div id="adaptive-preview-box" style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 18px;">
                    <div id="adaptive-loading-state" style="text-align: center; color: #64748B; font-size: 13px; padding: 12px;">
                        ⏳ Анализируем вашу статистику...
                    </div>
                    <div id="adaptive-content-state" style="display: none;">
                        <!-- Заполняется динамически -->
                    </div>
                </div>

                <div class="form-group mb-14 text-left">
                    <label style="font-weight: 700; font-size: 13px; color: #1E293B; display: block; margin-bottom: 6px;">
                        Тип вопросов:
                    </label>
                    <select id="adaptive-type-select" class="exam-select">
                        <option value="district">🗺️ Силуэты районов</option>
                        <option value="center">📍 Административные центры</option>
                        <option value="river">🌊 Реки</option>
                    </select>
                </div>

                <div style="display: flex; gap: 12px; margin-bottom: 14px;">
                    <div class="form-group flex-1 text-left">
                        <label style="font-weight: 700; font-size: 13px; color: #1E293B; display: block; margin-bottom: 6px;">
                            Количество вопросов:
                        </label>
                        <select id="adaptive-count-select" class="exam-select">
                            <option value="10">10 вопросов</option>
                            <option value="15" selected>15 вопросов</option>
                            <option value="20">20 вопросов</option>
                        </select>
                    </div>
                </div>

                <div class="exam-rules-box" style="background: #F0FDF4; border-color: #BBF7D0;">
                    <div style="font-size: 12px; color: #166534; line-height: 1.5;">
                        <b>Как это работает:</b> вопросы выбираются из пулов weak/medium/strong 
                        пропорционально 60/30/10. Чем чаще ошибаетесь на объекте — тем чаще 
                        он попадается. Обычный тест — все объекты равновероятно.
                    </div>
                </div>

                <div style="display: flex; gap: 10px; margin-top: 18px;">
                    <button onclick="closeAdaptiveModal()" class="btn btn-secondary" style="flex: 1; padding: 10px;">Отмена</button>
                    <button onclick="startAdaptiveTest()" class="btn btn-primary" style="flex: 2; padding: 10px; font-size: 14px; background: linear-gradient(135deg, #EC4899, #8B5CF6) !important;">
                        🚀 Начать адаптивный тест
                    </button>
                </div>
            </div>
        </div>

        <!-- МОДАЛЬНОЕ ОКНО НАСТРОЙКИ КОНТРОЛЬНОЙ РАБОТЫ (ЭКЗАМЕНА) -->
        <div id="exam-setup-modal" class="welcome-overlay" style="display: none;">
            <div class="welcome-card modal-md">
                <div class="welcome-badge badge-exam-gradient">{brand_org_short} Экзамен</div>
                <h2 class="welcome-title mb-6">📝 Режим контрольной работы</h2>
                <p class="welcome-subtitle mb-16">Аттестационное тестирование студентов {brand_sub_title}</p>
                
                <div class="exam-setup-form">
                    <div class="form-group mb-14 text-left">
                        <label class="exam-form-label">Категория вопросов:</label>
                        <select id="exam-category-select" class="exam-select">
                            <option value="mixed">🔀 Комплексный экзамен (все категории)</option>
                            <option value="districts">🗺️ Номенклатура районов (по силуэту)</option>
                            <option value="rivers">🌊 Гидрография (русла рек региона)</option>
                            <option value="centers">📍 Административные центры (поиск на карте)</option>
                            <option value="neighbors">🔗 Топология смежности (районы-соседи)</option>
                            <option value="puzzle">🧩 Топологический пазл (Собрать регион)</option>
                        </select>
                    </div>

                    <div class="exam-form-row">
                        <div class="form-group flex-1">
                            <label class="exam-form-label">Количество вопросов:</label>
                            <select id="exam-count-select" class="exam-select">
                                <option value="10">10 вопросов</option>
                                <option value="15" selected>15 вопросов (стандарт)</option>
                                <option value="20">20 вопросов</option>
                                <option value="25">25 вопросов</option>
                            </select>
                        </div>
                        <div class="form-group flex-1">
                            <label class="exam-form-label">Лимит времени:</label>
                            <select id="exam-time-select" class="exam-select">
                                <option value="5">5 минут</option>
                                <option value="10" selected>10 минут (рекомендуется)</option>
                                <option value="15">15 минут</option>
                                <option value="20">20 минут</option>
                            </select>
                        </div>
                    </div>

                    <div class="exam-rules-box">
                        <div class="exam-rules-title">
                            <span>⚠️</span> <span>Правила экзамена и Anti-cheat:</span>
                        </div>
                        <ul class="exam-rules-list">
                            <li>Запущен общий таймер на всю работу (автозавершение по истечении).</li>
                            <li><b>Запрещено переключать вкладки браузера</b> (фиксируется нарушение).</li>
                            <li>При повторном уходе с вкладки экзамен аннулируется.</li>
                            <li>Подсказки в режиме контрольной отключены.</li>
                            <li>По окончании выдается именной цифровой токен ведомости.</li>
                        </ul>
                    </div>
                </div>

                <div class="modal-actions-row">
                    <button onclick="closeExamModal()" class="btn btn-secondary btn-modal-half">Отмена</button>
                    <button onclick="startExamFromModal()" class="btn btn-exam btn-modal-double">🚀 Начать экзамен</button>
                </div>
            </div>
        </div>

        <!-- МОДАЛЬНОЕ ОКНО ПРЕДУПРЕЖДЕНИЯ ANTI-CHEAT -->
        <div id="anticheat-modal" class="welcome-overlay modal-z-top" style="display: none;">
            <div class="welcome-card modal-sm-danger">
                <div class="modal-big-icon">🚨</div>
                <h3 id="anticheat-title" class="modal-danger-title">ВНИМАНИЕ: Нарушение дисциплины!</h3>
                <div id="anticheat-body" class="anticheat-msg-body">
                    Вы переключились на другую вкладку браузера во время контрольной работы!
                </div>
                <button id="anticheat-confirm-btn" class="btn btn-danger btn-block btn-pad-10">
                    Я понимаю, вернуться к экзамену
                </button>
            </div>
        </div>

        <!-- МОДАЛЬНОЕ ОКНО ПОБЕДЫ В ПАЗЛЕ -->
        <div id="puzzle-victory-modal" class="welcome-overlay modal-z-high" style="display: none;">
            <div class="welcome-card modal-md-success">
                <div class="modal-trophy-icon">🏆</div>
                <div class="welcome-badge badge-success-gradient">Регион успешно собран!</div>
                <h2 id="puzzle-victory-title" class="welcome-title modal-title-compact">Поздравляем с победой!</h2>
                <p id="puzzle-victory-sub" class="welcome-subtitle mb-14">Вы восстановили географическую целостность региона</p>
                
                <div id="puzzle-victory-stats" class="puzzle-victory-stats-card">
                    <!-- Динамическая сводка: Время, Районы, Ошибки, Точность -->
                </div>

                <div class="exam-token-card token-card-spaced">
                    <div class="token-card-title">
                        Цифровой токен сдачи ({brand_org_short})
                    </div>
                    <div class="exam-token-val" id="puzzle-token-display">PUZZLE-XXXX-XXXX</div>
                    <div>
                        <button onclick="copyPuzzleToken()" class="btn btn-secondary btn-sm token-copy-btn">📋 Скопировать код</button>
                    </div>
                    <div class="token-card-caption">
                        Отправьте преподавателю для фиксации практической работы
                    </div>
                </div>

                <div class="modal-buttons-row">
                    <button onclick="restartPuzzleMode()" class="btn btn-secondary btn-flex-9">🔄 Заново</button>
                    <button onclick="closePuzzleVictoryModal()" class="btn btn-primary btn-flex-9">🗺️ К карте</button>
                    <button onclick="exitPuzzleMode()" class="btn btn-danger btn-flex-9">В меню</button>
                </div>
            </div>
        </div>

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

        try:
            metric_gdf = gdf.to_crs('EPSG:6933')
        except Exception:
            metric_gdf = gdf

        populations = []
        for idx, row in gdf.iterrows():
            area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if (idx in metric_gdf.index and metric_gdf.loc[idx].geometry is not None and not metric_gdf.loc[idx].geometry.is_empty) else 0
            population, _ = self._estimate_metrics(row.get('display_name', ''), area_sq_km)
            populations.append(population)

        gdf['population'] = populations

        import numpy as np
        pop_values = sorted([p for p in populations if p and p > 0])
        if not pop_values:
            return

        q_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        thresholds = [float(np.quantile(pop_values, q)) for q in q_levels]

        # Палитра YlOrRd
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
            area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if (idx in metric_gdf.index and metric_gdf.loc[idx].geometry is not None and not metric_gdf.loc[idx].geometry.is_empty) else 0
            _, grp = self._estimate_metrics(row.get('display_name', ''), area_sq_km)
            grps.append(grp)

        gdf['grp'] = grps

        import numpy as np
        grp_values = sorted([g for g in grps if g and g > 0])
        if not grp_values:
            return

        q_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        thresholds = [float(np.quantile(grp_values, q)) for q in q_levels]

        # Палитра Greens
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
        os.makedirs(MAPS_DIR, exist_ok=True)
        if filename is None:
            filename = self.output_filename
        else:
            if not os.path.isabs(filename):
                if not ('public' in filename and 'maps' in filename):
                    filename = os.path.join(MAPS_DIR, os.path.basename(filename))
                else:
                    filename = os.path.join(BASE_DIR, filename)

        out_dir = os.path.dirname(os.path.abspath(filename))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        if not getattr(self, '_choropleth_added', False):
            self.add_choropleth_layer()
        if not getattr(self, '_economy_added', False):
            self.add_economy_layer()
        folium.LayerControl(collapsed=True, position='bottomleft').add_to(self.map)
        self.add_quiz_controls()
        self.add_legend()
        self.add_fullscreen()
        self.map.save(filename)
        print(f"\n{'='*60}")
        print(f"Карта успешно создана: {filename}")
        print(f"{'='*60}")

        with open(filename, 'r', encoding='utf-8') as f:
            html = f.read()

        css_path = os.path.join(BASE_DIR, 'public', 'map.css')
        if not os.path.exists(css_path):
            print("⚠️ ВНИМАНИЕ: public/map.css не найден, стили карты могут не работать!")

        custom_css_js = ""

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
        rel_map_url = f"public/maps/{os.path.basename(filename)}"
        body_attrs = (
            f'data-region="{reg_id}" '
            f'data-region-title="{self.ru_title}" '
            f'data-center-lat="{self.center[0]}" '
            f'data-center-lng="{self.center[1]}" '
            f'data-zoom="{self.zoom}" '
            f'data-map-url="{rel_map_url}"'
        )
        if '<body' in html:
            if 'data-region="' in html:
                html = re.sub(r'data-region="[^"]*"', f'data-region="{reg_id}"', html, count=1)
                html = re.sub(r'data-region-title="[^"]*"', f'data-region-title="{self.ru_title}"', html, count=1)
                html = re.sub(r'data-center-lat="[^"]*"', f'data-center-lat="{self.center[0]}"', html, count=1)
                html = re.sub(r'data-center-lng="[^"]*"', f'data-center-lng="{self.center[1]}"', html, count=1)
                html = re.sub(r'data-zoom="[^"]*"', f'data-zoom="{self.zoom}"', html, count=1)
                html = re.sub(r'data-map-url="[^"]*"', f'data-map-url="{rel_map_url}"', html, count=1)
            else:
                html = re.sub(r'<body([^>]*)>', rf'<body\1 {body_attrs}>', html, count=1)

        if '</body>' in html:
            html = html.replace('</body>', my_attribution_html + '</body>', 1)
        else:
            html += my_attribution_html

        CHUNK_SIZE = 1024 * 1024
        for attempt in range(3):
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for i in range(0, len(html), CHUNK_SIZE):
                        f.write(html[i:i + CHUNK_SIZE])
                break
            except OSError:
                if attempt == 2:
                    raise
                import time
                time.sleep(0.3)

        meta_filename = os.path.join(out_dir, f"{self.slug}_meta.json")
        try:
            with open(meta_filename, 'w', encoding='utf-8') as f:
                json.dump(getattr(self, 'region_metadata', {}), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

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

    if target in REGIONS_CONFIG or target in ['rf', 'российская федерация', 'россия']:
        key = 'russia' if target in ['rf', 'российская федерация', 'россия'] else target
        is_server = os.environ.get("RENDER") is not None or os.environ.get("PORT") is not None
        out = build_configured_region(key, open_browser=not is_server)
        generated_files.append((REGIONS_CONFIG[key]['title'], out))

    elif target is None and not do_all:
        print("\n⚙️  Запуск в стандартном режиме: генерация 3 ключевых карт (Ростов, Краснодар, РФ)...")
        for key in ['rostov', 'krasnodar', 'russia']:
            try:
                out = build_configured_region(key, open_browser=False)
                generated_files.append((REGIONS_CONFIG[key]['title'], out))
            except Exception as e:
                print(f" ❌ Ошибка при сборке {key}: {e}")

    else:
        if do_all:
            print("\n⚙️  Генерация ключевых детальных карт...")
            for key in ['rostov', 'krasnodar', 'russia']:
                try:
                    out = build_configured_region(key, open_browser=False)
                    generated_files.append((REGIONS_CONFIG[key]['title'], out))
                except Exception as e:
                    print(f" ❌ Ошибка при сборке {key}: {e}")

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

try:
    from server import app
except Exception:
    app = None
