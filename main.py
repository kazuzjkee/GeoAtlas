import geopandas as gpd
import folium
from folium import plugins
import os
import json
import webbrowser

BASE_PATH = 'Py_Geo/shape/'

SHAPEFILES = {
    'districts': 'raion.shp',
    'district_centers': 'raicentr.shp',
    'rivers': 'water-line.shp',
    'water_bodies': 'water-polygon.shp'
}

STYLES = {
    'districts': {
        'color': '#2E8B57',
        'weight': 2,
        'fillColor': '#90EE90',
        'fillOpacity': 0.2,
        'dashArray': '5, 5'
    },
    'rivers': {
        'color': '#1E90FF',
        'weight': 2,
        'opacity': 0.8
    },
    'water_bodies': {
        'color': '#87CEEB',
        'weight': 1,
        'fillColor': '#87CEEB',
        'fillOpacity': 0.6
    }
}

LAYER_NAMES = {
    'districts': 'Районы',
    'rivers': 'Реки',
    'water_bodies': 'Водоемы'
}

POPUP_PREFIXES = {
    'districts': 'Район:',
    'rivers': 'Река:',
    'water_bodies': 'Водоем:'
}

MAP_CENTER = [47.23, 39.72]
INITIAL_ZOOM = 8
CARTO_KEY = 'cb1_3wsm_1_6bdccfe40c07a69c4fce7b68'

KNOWN_POPULATION = {
    'Ростов-на-Дону': 1140000, 'Таганрог': 245000, 'Шахты': 226000, 'Волгодонск': 168000,
    'Новочеркасск': 163000, 'Батайск': 126000, 'Новошахтинск': 103000, 'Каменск-Шахтинский': 86000,
    'Азов': 81000, 'Гуково': 62000, 'Донецк': 46000, 'Зверево': 19000, 'Аксайский': 121000,
    'Азовский': 106000, 'Белокалитвинский': 91000, 'Сальский': 101000, 'Мясниковский': 52000,
    'Красносулинский': 74000, 'Миллеровский': 63000, 'Морозовский': 37000, 'Зерноградский': 51000,
    'Семикаракорский': 48000, 'Октябрьский': 70000, 'Неклиновский': 87000, 'Каменский': 41000,
    'Багаевский': 33000, 'Константиновский': 31000, 'Цимлянский': 33000, 'Шолоховский': 25000,
    'Чертковский': 30000, 'Тацинский': 34000, 'Орловский': 36000, 'Пролетарский': 33000,
    'Матвеево-Курганский': 39000, 'Песчанокопский': 27000, 'Ремонтненский': 17000, 'Заветинский': 15000,
    'Дубовский': 21000, 'Зимовниковский': 34000, 'Кагальницкий': 28000, 'Кашарский': 22000,
    'Куйбышевский': 13000, 'Мартыновский': 34000, 'Милютинский': 12000, 'Обливский': 17000,
    'Родионово-Несветайский': 22000, 'Советский': 6000, 'Тарасовский': 27000, 'Усть-Донецкий': 28000,
    'Целинский': 29000, 'Боковский': 14000, 'Верхнедонской': 17000, 'Веселовский': 25000, 'Волгодонской': 33000
}


class RostovMap:
    def __init__(self):
        self.map = folium.Map(
            location=MAP_CENTER,
            zoom_start=INITIAL_ZOOM,
            control_scale=True,
            tiles=f'https://basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}.png?key={CARTO_KEY}',
            attr='© OpenStreetMap contributors, © CARTO',
            width='100%',
            height='100%'
        )
        self.districts_gdf = None
        self.centers_gdf = None
        self.rivers_gdf = None

    def _detect_name_field(self, gdf):
        possible_names = ['name', 'NAME', 'Name', 'Название', 'название', 'title', 'Title', 'TITLE', 'наименование', 'adm_name']
        for field in possible_names:
            if field in gdf.columns:
                return field
        for col in gdf.columns:
            if col != 'geometry' and gdf[col].dtype == 'object':
                sample = gdf[col].iloc[0] if len(gdf) > 0 else ''
                if isinstance(sample, str) and sample.strip():
                    return col
        return None

    def add_layer(self, shp_path, layer_key, with_id=False, simplify_tolerance=None, interactive=True):
        print(f"Загружаю слой: {LAYER_NAMES.get(layer_key, layer_key)}...")
        try:
            gdf = gpd.read_file(shp_path)
            if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')

            if simplify_tolerance is not None:
                gdf['geometry'] = gdf.geometry.simplify(tolerance=simplify_tolerance, preserve_topology=True)
                gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()]

            name_field = self._detect_name_field(gdf)
            popup_fields = [name_field] if name_field else []
            prefix = POPUP_PREFIXES.get(layer_key, 'Название:')

            popup = None
            tooltip = None

            if interactive and popup_fields:
                popup = folium.GeoJsonPopup(fields=popup_fields, aliases=[prefix] * len(popup_fields), localize=True)
                tooltip = folium.GeoJsonTooltip(fields=popup_fields, aliases=[prefix] * len(popup_fields), style="background-color: white; padding: 6px;")

            kwargs = {'id': name_field} if with_id and name_field else {}

            folium.GeoJson(
                gdf,
                name=LAYER_NAMES.get(layer_key, layer_key),
                style_function=lambda x, s=STYLES[layer_key]: s,
                popup=popup,
                tooltip=tooltip,
                interactive=interactive,
                **kwargs
            ).add_to(self.map)

            print(f"  Загружено: {len(gdf)} объектов")
            return gdf
        except Exception as e:
            print(f"  Ошибка загрузки: {e}")
            return None

    def add_districts(self, shp_path):
        self.districts_gdf = self.add_layer(shp_path, 'districts', with_id=True, interactive=True)
        return self.districts_gdf

    def add_rivers(self, shp_path):
        self.rivers_gdf = self.add_layer(shp_path, 'rivers', simplify_tolerance=0.001)
        return self.rivers_gdf

    def add_water_bodies(self, shp_path):
        return self.add_layer(shp_path, 'water_bodies', simplify_tolerance=0.001)

    def add_district_centers(self, shp_path):
        print("Загружаю райцентры...")
        try:
            gdf = gpd.read_file(shp_path)
            if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            self.centers_gdf = gdf
            name_field = self._detect_name_field(gdf)

            point_gdf = gdf[gdf.geometry.type == 'Point']
            if len(point_gdf) == 0:
                point_gdf = gdf.copy()
                point_gdf['geometry'] = point_gdf.geometry.centroid

            feature_group = folium.FeatureGroup(name="Райцентры")
            for idx, row in point_gdf.iterrows():
                lon, lat = (row.geometry.x, row.geometry.y) if hasattr(row.geometry, 'x') else (row.geometry.centroid.x, row.geometry.centroid.y)
                name = str(row[name_field]) if name_field and name_field in row else f"Центр {idx}"
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>{name}</b><br>Тип: Райцентр",
                    tooltip=name,
                    icon=folium.Icon(color='orange', icon='star', prefix='fa')
                ).add_to(feature_group)

            feature_group.add_to(self.map)
            print(f"  Загружено: {len(point_gdf)} объектов")
        except Exception as e:
            print(f"  Ошибка загрузки райцентров: {e}")

    def _calculate_neighbors_data(self):
        if self.districts_gdf is None or len(self.districts_gdf) == 0:
            return []
        name_field = self._detect_name_field(self.districts_gdf)
        if not name_field:
            return []

        valid_gdf = self.districts_gdf[self.districts_gdf.geometry.is_valid & ~self.districts_gdf.geometry.is_empty].copy()
        metric_gdf = valid_gdf.to_crs('EPSG:3857')
        neighbors_data = []

        for idx, row in valid_gdf.iterrows():
            current_geom = row.geometry
            current_name = str(row[name_field])
            buffered_geom = current_geom.buffer(0.005)
            intersecting_rows = valid_gdf[valid_gdf.geometry.intersects(buffered_geom)]
            neighbor_names = [str(n) for n in intersecting_rows[name_field].tolist() if str(n) != current_name]
            
            center_name = "г. Ростов-на-Дону (Областной центр)" if 'Ростов-на-Дону' in current_name else "Райцентр"
            area_sq_km = int(metric_gdf.loc[idx].geometry.area / 1_000_000) if idx in metric_gdf.index else 500

            population = None
            for key, val in KNOWN_POPULATION.items():
                if key in current_name:
                    population = val
                    break
            if population is None:
                population = int(area_sq_km * 20)

            neighbors_data.append({
                'name': current_name,
                'center': center_name,
                'area': area_sq_km,
                'population': population,
                'neighbors': list(set(neighbor_names))
            })
        return neighbors_data

    def _extract_rivers_data(self):
        if self.rivers_gdf is None or len(self.rivers_gdf) == 0:
            return []
        name_field = self._detect_name_field(self.rivers_gdf)
        if not name_field:
            return []

        valid_rivers = self.rivers_gdf[self.rivers_gdf[name_field].notnull() & (self.rivers_gdf[name_field] != '')].copy()
        valid_rivers['clean_name'] = valid_rivers[name_field].astype(str).str.strip()
        valid_rivers = valid_rivers[valid_rivers['clean_name'].str.len() > 2]
        dissolved = valid_rivers.dissolve(by='clean_name').reset_index()
        metric_rivers = dissolved.to_crs('EPSG:3857')
        dissolved['length_km'] = (metric_rivers.geometry.length / 1000).round(1)
        top_rivers = dissolved.sort_values(by='length_km', ascending=False).head(30)

        return [{"name": str(r['clean_name']), "length": float(r['length_km'])} for _, r in top_rivers.iterrows()]

    def export_quiz_data(self, output_dir='quiz_data'):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if self.districts_gdf is not None:
            name_field = self._detect_name_field(self.districts_gdf)
            data = [{"id": int(idx), "name": str(row[name_field])} for idx, row in self.districts_gdf.iterrows() if name_field and name_field in row]
            with open(os.path.join(output_dir, 'districts.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        if self.centers_gdf is not None:
            name_field = self._detect_name_field(self.centers_gdf)
            data = []
            for idx, row in self.centers_gdf.iterrows():
                if name_field and name_field in row:
                    lon, lat = (row.geometry.x, row.geometry.y) if hasattr(row.geometry, 'x') else (row.geometry.centroid.x, row.geometry.centroid.y)
                    data.append({"id": int(idx), "name": str(row[name_field]), "lat": lat, "lon": lon})
            with open(os.path.join(output_dir, 'centers.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def add_quiz_controls(self):
        neighbors_data = self._calculate_neighbors_data()
        rivers_data = self._extract_rivers_data()
        districts_data = [{"name": d['name']} for d in neighbors_data]
        centers_data = []
        if self.centers_gdf is not None:
            c_field = self._detect_name_field(self.centers_gdf)
            for _, row in self.centers_gdf.iterrows():
                lon, lat = (row.geometry.x, row.geometry.y) if hasattr(row.geometry, 'x') else (row.geometry.centroid.x, row.geometry.centroid.y)
                centers_data.append({"name": str(row[c_field]) if c_field else "Центр", "lat": lat, "lon": lon})

        js_code = f'''
const EMBEDDED_DISTRICTS = {json.dumps(districts_data, ensure_ascii=False)};
const EMBEDDED_CENTERS = {json.dumps(centers_data, ensure_ascii=False)};
const EMBEDDED_NEIGHBORS = {json.dumps(neighbors_data, ensure_ascii=False)};
const EMBEDDED_RIVERS = {json.dumps(rivers_data, ensure_ascii=False)};

let currentQuiz = null;
let currentQuestion = 0;
let score = 0;
let maxPossibleScore = 0;
let totalQuestions = 10;
let quizData = [];
let selectedOption = null;
let mapSearchAttempts = 0;
const MAX_MAP_SEARCH_ATTEMPTS = 50;
let clickMarker = null;
let resultMarker = null;
let resultLine = null;
let popupsDisabled = false;
let highlightedDistrictLayer = null;
let highlightedRiverLayers = [];

let timerEnabled = false;
let questionTimer = null;
const QUESTION_TIME_LIMIT = 20;
let timeLeft = QUESTION_TIME_LIMIT;
let quizStartTime = 0;

function clearMarkers() {{
    if (clickMarker) {{ try {{ clickMarker.remove(); }} catch(e) {{}} clickMarker = null; }}
    if (resultMarker) {{ try {{ resultMarker.remove(); }} catch(e) {{}} resultMarker = null; }}
    if (resultLine) {{ try {{ resultLine.remove(); }} catch(e) {{}} resultLine = null; }}
}}

function resetActiveHighlight(hideRiverCompletely = false) {{
    if (highlightedDistrictLayer) {{
        try {{ highlightedDistrictLayer.setStyle({{ color: '#2E8B57', weight: 2, fillColor: '#90EE90', fillOpacity: 0.2, dashArray: '5, 5' }}); }} catch(e) {{}}
        highlightedDistrictLayer = null;
    }}

    if (highlightedRiverLayers && highlightedRiverLayers.length > 0) {{
        highlightedRiverLayers.forEach(layer => {{
            try {{
                if (hideRiverCompletely) {{
                    layer.setStyle({{ color: 'transparent', weight: 0, opacity: 0 }});
                }} else {{
                    layer.setStyle({{ color: '#1E90FF', weight: 2, opacity: 0.8 }});
                }}
            }} catch(e) {{}}
        }});
        highlightedRiverLayers = [];
    }}
}}

function restoreAllRiverStyles() {{
    const map = getMapObject();
    if (!map) return;
    map.eachLayer(function(layer) {{
        if (layer.feature && layer.feature.geometry && (layer.feature.geometry.type === 'LineString' || layer.feature.geometry.type === 'MultiLineString')) {{
            try {{ layer.setStyle({{ color: '#1E90FF', weight: 2, opacity: 0.8 }}); }} catch(e) {{}}
        }}
    }});
}}

function resetMapView() {{
    const map = getMapObject();
    if (map) {{
        try {{ map.setView([{MAP_CENTER[0]}, {MAP_CENTER[1]}], {INITIAL_ZOOM}); }} catch(e) {{}}
    }}
}}

function setQuizLayers(quizMode) {{
    const layers = document.querySelectorAll('.leaflet-control-layers-overlays label');
    layers.forEach(label => {{
        const text = label.textContent.trim();
        const input = label.querySelector('input[type="checkbox"]');
        if (!input) return;

        if (quizMode === 'center') {{
            if (text.includes('Реки') || text.includes('Водоемы')) {{
                if (input.checked) input.click();
            }}
            if (text.includes('Районы') || text.includes('Райцентры')) {{
                if (!input.checked) input.click();
            }}
        }} else if (quizMode === 'district' || quizMode === 'neighbor') {{
            if (text.includes('Реки') || text.includes('Водоемы') || text.includes('Райцентры')) {{
                if (input.checked) input.click();
            }}
            if (text.includes('Районы')) {{
                if (!input.checked) input.click();
            }}
        }} else if (quizMode === 'river') {{
            if (text.includes('Районы') || text.includes('Райцентры')) {{
                if (input.checked) input.click();
            }}
            if (text.includes('Реки') || text.includes('Водоемы')) {{
                if (!input.checked) input.click();
            }}
        }} else {{
            if (!input.checked) input.click();
        }}
    }});
}}

function restoreAllLayers() {{
    setQuizLayers('normal');
    restoreAllRiverStyles();
}}

function disablePopups() {{
    if (popupsDisabled) return;
    const style = document.createElement('style');
    style.id = 'disable-popups-style';
    style.textContent = '.leaflet-popup, .leaflet-tooltip {{ display: none !important; }}';
    document.head.appendChild(style);
    popupsDisabled = true;
}}

function enablePopups() {{
    const style = document.getElementById('disable-popups-style');
    if (style) style.remove();
    popupsDisabled = false;
}}

function toggleTimer() {{
    const checkbox = document.getElementById('timer-toggle');
    if (checkbox) timerEnabled = checkbox.checked;
}}

function startTimer() {{
    stopTimer();
    const tb = document.getElementById('timer-bar-container');
    if (!timerEnabled) {{
        if (tb) tb.style.display = 'none';
        return;
    }}
    if (tb) tb.style.display = 'block';
    timeLeft = QUESTION_TIME_LIMIT;
    updateTimerDisplay();

    questionTimer = setInterval(() => {{
        timeLeft--;
        updateTimerDisplay();
        if (timeLeft <= 0) {{
            stopTimer();
            handleTimeout();
        }}
    }}, 1000);
}}

function stopTimer() {{
    if (questionTimer) {{
        clearInterval(questionTimer);
        questionTimer = null;
    }}
}}

function updateTimerDisplay() {{
    const timerText = document.getElementById('timer-text');
    const timerBar = document.getElementById('timer-bar');
    if (timerText) timerText.textContent = `${{timeLeft}}с`;
    if (timerBar) {{
        const percent = Math.max(0, (timeLeft / QUESTION_TIME_LIMIT) * 100);
        timerBar.style.width = `${{percent}}%`;
        timerBar.style.background = percent > 50 ? '#10B981' : percent > 25 ? '#F59E0B' : '#EF4444';
    }}
}}

function handleTimeout() {{
    if (currentQuestion >= quizData.length) return;
    const question = quizData[currentQuestion];
    showFeedback('Время вышло!', 'error');

    if (question.type === 'district' || question.type === 'neighbor' || question.type === 'river') {{
        document.querySelectorAll('.quiz-option').forEach(opt => {{
            if (opt.textContent === question.correctAnswer) {{
                opt.classList.add('correct');
            }}
            opt.disabled = true;
        }});
    }} else if (question.type === 'center') {{
        if (window._clickBlocker) {{
            const map = getMapObject();
            try {{ map.removeLayer(window._clickBlocker); }} catch(e) {{}}
            window._clickBlocker = null;
        }}
    }}

    setTimeout(() => {{
        currentQuestion++;
        showQuestion();
    }}, 1800);
}}

function startDistrictQuiz() {{
    currentQuiz = 'district';
    quizStartTime = Date.now();
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers('district');
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('quiz-title').textContent = 'Угадай район по очертаниям';
    document.getElementById('hint-button').style.display = 'block';
    loadDistrictQuiz();
}}

function startCenterQuiz() {{
    currentQuiz = 'center';
    quizStartTime = Date.now();
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers('center');
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('quiz-title').textContent = 'Найди райцентр на карте';
    document.getElementById('hint-button').style.display = 'block';
    loadCenterQuiz();
}}

function startNeighborQuiz() {{
    currentQuiz = 'neighbor';
    quizStartTime = Date.now();
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers('neighbor');
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('quiz-title').textContent = 'Районы-соседи';
    document.getElementById('hint-button').style.display = 'none';
    loadNeighborQuiz();
}}

function startRiverQuiz() {{
    if (!EMBEDDED_RIVERS || EMBEDDED_RIVERS.length < 4) {{
        alert('Недостаточно данных по рекам для запуска викторины');
        return;
    }}
    currentQuiz = 'river';
    quizStartTime = Date.now();
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    restoreAllRiverStyles();
    disablePopups();
    setQuizLayers('river');
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('quiz-title').textContent = 'Угадай реку по руслу';
    document.getElementById('hint-button').style.display = 'block';
    loadRiverQuiz();
}}

function loadDistrictQuiz() {{
    maxPossibleScore = totalQuestions;
    generateDistrictQuestions(EMBEDDED_DISTRICTS);
}}

function generateDistrictQuestions(data) {{
    quizData = [];
    if (!data || data.length === 0) return;
    for (let i = 0; i < totalQuestions; i++) {{
        const correct = data[Math.floor(Math.random() * data.length)];
        const options = [correct.name];
        while (options.length < 4 && options.length < data.length) {{
            const wrong = data[Math.floor(Math.random() * data.length)];
            if (!options.includes(wrong.name)) {{
                options.push(wrong.name);
            }}
        }}
        shuffleArray(options);
        quizData.push({{
            type: 'district',
            correctAnswer: correct.name,
            options: options,
            hint: `Площадь района: ~${{Math.round(Math.random() * 2000 + 500)}} км²`,
            districtName: correct.name
        }});
    }}
    showQuestion();
}}

function loadCenterQuiz() {{
    maxPossibleScore = totalQuestions * 3;
    generateCenterQuestions(EMBEDDED_CENTERS);
}}

function generateCenterQuestions(data) {{
    quizData = [];
    if (!data || data.length === 0) return;
    for (let i = 0; i < totalQuestions; i++) {{
        const correct = data[Math.floor(Math.random() * data.length)];
        quizData.push({{
            type: 'center',
            correctAnswer: correct.name,
            correctLat: correct.lat,
            correctLon: correct.lon,
            hint: `Население: ~${{Math.round(Math.random() * 50000 + 10000)}} человек`,
            centerName: correct.name
        }});
    }}
    showQuestion();
}}

function loadNeighborQuiz() {{
    maxPossibleScore = totalQuestions;
    generateNeighborQuestions(EMBEDDED_NEIGHBORS);
}}

function generateNeighborQuestions(data) {{
    quizData = [];
    const validPool = data.filter(d => d.neighbors && d.neighbors.length >= 1);
    const allNames = data.map(d => d.name);

    if (validPool.length === 0) {{
        alert('Недостаточно данных о топологии районов');
        finishQuizDirectly();
        return;
    }}

    for (let i = 0; i < totalQuestions; i++) {{
        const current = validPool[Math.floor(Math.random() * validPool.length)];
        const neighbors = [...current.neighbors];
        shuffleArray(neighbors);
        
        let options = [];
        if (neighbors.length >= 3) {{
            options = neighbors.slice(0, 3);
        }} else {{
            options = [...neighbors];
            while (options.length < 3) {{
                const dummyNeighbor = allNames[Math.floor(Math.random() * allNames.length)];
                if (!options.includes(dummyNeighbor) && dummyNeighbor !== current.name) {{
                    options.push(dummyNeighbor);
                }}
            }}
        }}

        const nonNeighbors = allNames.filter(name => name !== current.name && !current.neighbors.includes(name));
        const wrongNeighbor = nonNeighbors.length > 0 
            ? nonNeighbors[Math.floor(Math.random() * nonNeighbors.length)] 
            : allNames[0];

        options.push(wrongNeighbor);
        shuffleArray(options);

        quizData.push({{
            type: 'neighbor',
            districtName: current.name,
            correctAnswer: wrongNeighbor,
            options: options
        }});
    }}
    showQuestion();
}}

function loadRiverQuiz() {{
    maxPossibleScore = totalQuestions;
    generateRiverQuestions(EMBEDDED_RIVERS);
}}

function generateRiverQuestions(data) {{
    quizData = [];
    if (!data || data.length === 0) return;
    const questionsCount = Math.min(totalQuestions, data.length);

    for (let i = 0; i < questionsCount; i++) {{
        const correct = data[i % data.length];
        const options = [correct.name];
        while (options.length < 4 && options.length < data.length) {{
            const wrong = data[Math.floor(Math.random() * data.length)];
            if (!options.includes(wrong.name)) {{
                options.push(wrong.name);
            }}
        }}
        shuffleArray(options);
        quizData.push({{
            type: 'river',
            correctAnswer: correct.name,
            options: options,
            riverName: correct.name,
            hint: `Длина русла в пределах области: ~${{correct.length}} км`
        }});
    }}
    shuffleArray(quizData);
    showQuestion();
}}

function showQuestion() {{
    if (currentQuestion >= quizData.length) {{
        stopTimer();
        showResults();
        return;
    }}

    clearMarkers();
    resetActiveHighlight(currentQuiz === 'river');

    const oldFeedback = document.getElementById('feedback');
    if (oldFeedback) oldFeedback.remove();

    const oldBtn = document.getElementById('confirm-button');
    if (oldBtn) oldBtn.remove();

    const question = quizData[currentQuestion];
    const cqEl = document.getElementById('current-question');
    const tqEl = document.getElementById('total-questions');
    const qTextEl = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');

    if (cqEl) cqEl.textContent = currentQuestion + 1;
    if (tqEl) tqEl.textContent = quizData.length;
    if (optionsContainer) optionsContainer.innerHTML = '';

    if (question.type === 'district') {{
        if (qTextEl) qTextEl.textContent = 'Угадайте район по очертаниям:';
        question.options.forEach(option => {{
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        }});
        highlightDistrictOnMapByName(question.districtName);

    }} else if (question.type === 'neighbor') {{
        if (qTextEl) qTextEl.textContent = `С каким районом НЕ граничит ${{question.districtName}}?`;
        question.options.forEach(option => {{
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        }});
        highlightDistrictOnMapByName(question.districtName);

    }} else if (question.type === 'river') {{
        if (qTextEl) qTextEl.textContent = 'Какая река подсвечена на карте?';
        question.options.forEach(option => {{
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        }});
        highlightRiverOnMapByName(question.riverName);

    }} else if (question.type === 'center') {{
        if (qTextEl) qTextEl.textContent = `Найдите на карте: ${{question.correctAnswer}}`;
        if (optionsContainer) {{
            optionsContainer.innerHTML = '<div class="center-quiz-instruction">Кликните на карту в точке нахождения объекта<br><span>до 5 км: +3 очка | до 15 км: +2 | до 30 км: +1</span></div>';
        }}
        window.currentQuestionData = question;
        setupMapClickListener(question);
    }}

    const hintC = document.getElementById('hint-container');
    if (hintC) hintC.style.display = 'none';
    selectedOption = null;
    startTimer();
}}

function selectOption(button, selected, correct) {{
    document.querySelectorAll('.quiz-option').forEach(opt => {{
        opt.classList.remove('selected');
    }});
    button.classList.add('selected');
    selectedOption = selected;
    showConfirmButton();
}}

function showConfirmButton() {{
    const optionsContainer = document.getElementById('options-container');
    if (!optionsContainer) return;
    const oldButton = document.getElementById('confirm-button');
    if (oldButton) oldButton.remove();

    const confirmButton = document.createElement('button');
    confirmButton.textContent = '✓ Подтвердить ответ';
    confirmButton.className = 'btn-confirm';
    confirmButton.onclick = checkAnswer;
    confirmButton.id = 'confirm-button';
    optionsContainer.appendChild(confirmButton);
}}

function checkAnswer() {{
    if (!selectedOption && currentQuiz !== 'center') {{
        alert('Пожалуйста, выберите вариант ответа!');
        return;
    }}
    stopTimer();
    const question = quizData[currentQuestion];
    const isCorrect = selectedOption === question.correctAnswer;
    
    document.querySelectorAll('.quiz-option').forEach(opt => {{
        if (opt.textContent === question.correctAnswer) {{
            opt.classList.add('correct');
        }}
        if (opt.textContent === selectedOption && !isCorrect) {{
            opt.classList.add('incorrect');
        }}
        opt.disabled = true;
    }});

    const oldButton = document.getElementById('confirm-button');
    if (oldButton) oldButton.remove();

    if (isCorrect) {{
        score++;
        showFeedback('Правильно!', 'success');
    }} else {{
        showFeedback(`Неправильно! Ответ: ${{question.correctAnswer}}`, 'error');
    }}
    updateScore();
    setTimeout(() => {{
        currentQuestion++;
        showQuestion();
    }}, 1800);
}}

function setupMapClickListener(question) {{
    const map = getMapObject();
    if (!map) {{
        setTimeout(() => setupMapClickListener(question), 500);
        return;
    }}

    if (window._clickBlocker) {{
        try {{ map.removeLayer(window._clickBlocker); }} catch(e) {{}}
        window._clickBlocker = null;
    }}

    window._clickBlocker = L.rectangle(
        [[-90, -180], [90, 180]],
        {{ color: 'transparent', fillColor: 'transparent', fillOpacity: 0, weight: 0, interactive: true }}
    ).addTo(map);

    window._clickHandler = function(e) {{
        handleMapClick(e.latlng.lat, e.latlng.lng, question);
    }};

    window._clickBlocker.on('click', window._clickHandler);
}}

function getMapObject() {{
    let map = window._leaflet_map;
    if (!map || typeof map.eachLayer !== 'function') {{
        const mapElement = document.querySelector('.leaflet-container');
        if (mapElement && typeof L !== 'undefined') {{
            try {{
                const possibleMap = L.DomUtil.get(mapElement);
                if (possibleMap && typeof possibleMap.eachLayer === 'function') {{
                    map = possibleMap;
                    window._leaflet_map = map;
                }}
            }} catch(e) {{}}
        }}
    }}
    if (!map || typeof map.eachLayer !== 'function') {{
        if (typeof L !== 'undefined' && L.Map) {{
            try {{
                for (let key in window) {{
                    if (window[key] && window[key] instanceof L.Map) {{
                        map = window[key];
                        window._leaflet_map = map;
                        break;
                    }}
                }}
            }} catch(e) {{}}
        }}
    }}
    return map;
}}

function handleMapClick(lat, lon, question) {{
    stopTimer();
    const correctLat = question.correctLat;
    const correctLon = question.correctLon;

    const distance = calculateDistance(lat, lon, correctLat, correctLon);
    let pointsAwarded = 0;
    let message = '';
    let badgeType = 'error';

    if (distance <= 5) {{
        pointsAwarded = 3;
        message = `Идеально! (${{distance.toFixed(1)}} км) +3 очка!`;
        badgeType = 'success';
    }} else if (distance <= 15) {{
        pointsAwarded = 2;
        message = `Хорошо! (${{distance.toFixed(1)}} км) +2 очка!`;
        badgeType = 'success';
    }} else if (distance <= 30) {{
        pointsAwarded = 1;
        message = `Близко (${{distance.toFixed(1)}} км) +1 очко!`;
        badgeType = 'success';
    }} else {{
        pointsAwarded = 0;
        message = `Мимо! (${{distance.toFixed(1)}} км от цели)`;
        badgeType = 'error';
    }}

    score += pointsAwarded;
    clearMarkers();

    const map = getMapObject();
    if (window._clickBlocker) {{
        try {{
            if (window._clickHandler) {{
                window._clickBlocker.off('click', window._clickHandler);
            }}
            map.removeLayer(window._clickBlocker);
        }} catch(e) {{}}
        window._clickBlocker = null;
        window._clickHandler = null;
    }}

    const markerColor = pointsAwarded > 0 ? '#10B981' : '#EF4444';

    clickMarker = L.circleMarker([lat, lon], {{
        radius: 9,
        color: markerColor,
        fillColor: markerColor,
        fillOpacity: 0.8,
        weight: 2
    }}).addTo(map);

    resultMarker = L.circleMarker([correctLat, correctLon], {{
        radius: 8,
        color: '#2563EB',
        fillColor: '#2563EB',
        fillOpacity: 0.5,
        weight: 2,
        dashArray: '4, 4'
    }}).addTo(map);

    resultLine = L.polyline([[lat, lon], [correctLat, correctLon]], {{
        color: markerColor,
        weight: 2.5,
        opacity: 0.8,
        dashArray: '5, 8'
    }}).addTo(map);

    map.fitBounds([
        [Math.min(lat, correctLat) - 0.1, Math.min(lon, correctLon) - 0.1],
        [Math.max(lat, correctLat) + 0.1, Math.max(lon, correctLon) + 0.1]
    ]);

    showFeedback(message, badgeType);
    updateScore();

    setTimeout(() => {{
        currentQuestion++;
        showQuestion();
    }}, 2600);
}}

function calculateDistance(lat1, lon1, lat2, lon2) {{
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}}

function showFeedback(message, type) {{
    const container = document.getElementById('options-container');
    if (!container) return;
    const oldFeedback = document.getElementById('feedback');
    if (oldFeedback) oldFeedback.remove();

    const feedback = document.createElement('div');
    feedback.className = `feedback-box ${{type}}`;
    feedback.textContent = message;
    feedback.id = 'feedback';
    container.appendChild(feedback);
}}

function showHint() {{
    const question = quizData[currentQuestion];
    if (question && question.hint) {{
        const ht = document.getElementById('hint-text');
        const hc = document.getElementById('hint-container');
        if (ht) ht.textContent = question.hint;
        if (hc) hc.style.display = 'block';
    }}
}}

function updateScore() {{
    const scoreEl = document.getElementById('score');
    const accEl = document.getElementById('accuracy');
    if (scoreEl) scoreEl.textContent = score;
    const currentMax = currentQuiz === 'center' ? (currentQuestion + 1) * 3 : (currentQuestion + 1);
    const accuracy = currentMax > 0 ? Math.round((score / currentMax) * 100) : 0;
    if (accEl) accEl.textContent = `Эффективность: ${{accuracy}}%`;
}}

function highlightDistrictOnMapByName(districtName) {{
    let map = getMapObject();
    if (!map || typeof map.eachLayer !== 'function') {{
        mapSearchAttempts++;
        if (mapSearchAttempts < MAX_MAP_SEARCH_ATTEMPTS) {{
            setTimeout(() => highlightDistrictOnMapByName(districtName), 300);
        }}
        return;
    }}
    mapSearchAttempts = 0;

    resetActiveHighlight();

    let targetLayer = null;
    map.eachLayer(function(layer) {{
        if (layer.feature && layer.feature.properties) {{
            const props = layer.feature.properties;
            if (props.name === districtName || props.NAME === districtName ||
                props.Название === districtName || props.название === districtName) {{
                targetLayer = layer;
            }}
        }}
    }});

    if (targetLayer) {{
        highlightedDistrictLayer = targetLayer;
        try {{
            targetLayer.setStyle({{
                color: '#F59E0B',
                weight: 4,
                fillColor: '#F59E0B',
                fillOpacity: 0.5,
                dashArray: null
            }});
            map.fitBounds(targetLayer.getBounds(), {{padding: [30, 30]}});
        }} catch(e) {{}}
    }}
}}

function highlightRiverOnMapByName(riverName) {{
    let map = getMapObject();
    if (!map || typeof map.eachLayer !== 'function') return;

    resetActiveHighlight(true);

    let targetGroup = L.featureGroup();
    highlightedRiverLayers = [];

    map.eachLayer(function(layer) {{
        if (layer.feature && layer.feature.properties) {{
            const props = layer.feature.properties;
            const pName = props.name || props.NAME || props.Название || props.название || '';
            if (pName.trim() === riverName.trim()) {{
                highlightedRiverLayers.push(layer);
                try {{
                    layer.setStyle({{
                        color: '#EF4444',
                        weight: 5,
                        opacity: 1.0
                    }});
                    targetGroup.addLayer(layer);
                }} catch(e) {{}}
            }}
        }}
    }});

    if (highlightedRiverLayers.length > 0) {{
        try {{
            map.fitBounds(targetGroup.getBounds(), {{padding: [40, 40]}});
        }} catch(e) {{}}
    }}
}}

function showDistrictInfoCard(districtName) {{
    const district = EMBEDDED_NEIGHBORS.find(d => d.name === districtName);
    if (!district) return;

    const card = document.getElementById('district-info-card');
    if (!card) return;

    highlightDistrictOnMapByName(districtName);

    const neighborsHtml = district.neighbors && district.neighbors.length > 0 
        ? district.neighbors.map(n => `<span class="neighbor-tag" onclick="showDistrictInfoCard('${{n}}')">${{n}}</span>`).join('')
        : '<em>Нет данных</em>';

    const popFormatted = district.population 
        ? `${{Number(district.population).toLocaleString('ru-RU')}} чел.` 
        : 'Нет данных';

    card.innerHTML = `
        <div class="info-card-header">
            <strong>${{district.name}}</strong>
            <button onclick="closeInfoCard()" class="close-card-btn">&times;</button>
        </div>
        <div class="info-card-body">
            <div class="info-row"><span>Райцентр:</span><strong>${{district.center}}</strong></div>
            <div class="info-row"><span>Население:</span><strong>~${{popFormatted}}</strong></div>
            <div class="info-row"><span>Площадь:</span><strong>~${{district.area}} км²</strong></div>
            <div style="margin-top: 8px;">
                <span style="color: #64748B; font-size: 11px; font-weight: 600;">Граничит с районами:</span>
                <div style="margin-top: 4px; display: flex; flex-wrap: wrap;">${{neighborsHtml}}</div>
            </div>
        </div>
    `;
    card.style.display = 'block';
}}

function closeInfoCard() {{
    const card = document.getElementById('district-info-card');
    if (card) card.style.display = 'none';
    resetActiveHighlight();
}}

function setupDistrictClickListeners() {{
    const map = getMapObject();
    if (!map) {{
        setTimeout(setupDistrictClickListeners, 500);
        return;
    }}

    map.eachLayer(function(layer) {{
        if (layer.feature && layer.feature.properties) {{
            const props = layer.feature.properties;
            const name = props.name || props.NAME || props.Название || props.название;
            if (name && (props.adm_level || (layer.feature.geometry && layer.feature.geometry.type.includes('Polygon')))) {{
                layer.off('click');
                layer.on('click', function(e) {{
                    if (currentQuiz === null) {{
                        showDistrictInfoCard(name);
                    }}
                }});
            }}
        }}
    }});
}}

function showResults() {{
    clearMarkers();
    resetActiveHighlight(true);
    resetMapView();
    restoreAllLayers();
    enablePopups();

    currentQuiz = null;
    setTimeout(setupDistrictClickListeners, 500);

    const qm = document.getElementById('quiz-mode');
    const rm = document.getElementById('results-mode');
    if (qm) qm.style.display = 'none';
    if (rm) rm.style.display = 'block';

    const accuracy = maxPossibleScore > 0 ? Math.round((score / maxPossibleScore) * 100) : 0;
    let message = '', emoji = '';
    if (accuracy >= 85) {{ message = 'Превосходно! Отличное пространственное знание области!'; emoji = '🏆'; }}
    else if (accuracy >= 65) {{ message = 'Хорошо! Вы уверенно ориентируетесь на карте.'; emoji = '👍'; }}
    else if (accuracy >= 45) {{ message = 'Удовлетворительно, рекомендуем повторить номенклатуру.'; emoji = '📚'; }}
    else {{ message = 'Попробуйте ещё раз, практика даст результат!'; emoji = '💪'; }}

    const studentInfo = getCurrentStudentInfo();
    const studentLine = studentInfo ? `<p style="margin: 4px 0; font-size: 13px; color: #0284C7;">Студент: <strong>${{studentInfo.name}}</strong> (${{studentInfo.group}})</p>` : '';

    const rc = document.getElementById('results-content');
    if (rc) {{
        rc.innerHTML = `
            <div style="font-size: 42px; margin: 10px 0;">${{emoji}}</div>
            ${{studentLine}}
            <h3 style="margin: 6px 0; color: #1E293B;">${{score}} из ${{maxPossibleScore}} баллов</h3>
            <p style="margin: 4px 0; font-size: 13px; color: #475569;">Результативность: <strong>${{accuracy}}%</strong></p>
            <p style="margin-top: 6px; font-size: 12px; color: #64748B;">${{message}}</p>
        `;
    }}
    saveResult(accuracy);
}}

function saveResult(accuracy) {{
    const student = getCurrentStudentInfo();
    let timeSec = Math.round((Date.now() - (quizStartTime || Date.now())) / 1000);
    let timeStr = `${{Math.floor(timeSec / 60)}} мин. ${{timeSec % 60}} сек.`;

    const results = JSON.parse(localStorage.getItem('rostovQuizResults') || '[]');
    results.push({{
        date: new Date().toLocaleString(),
        student: student ? student.name : 'Анонимно',
        group: student ? student.group : '-',
        type: currentQuiz,
        score: score,
        maxScore: maxPossibleScore,
        accuracy: accuracy,
        time_spent: timeStr
    }});
    localStorage.setItem('rostovQuizResults', JSON.stringify(results));

    if (student) {{
        fetch('/api/results/save', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                email: student.email,
                name: student.name,
                group: student.group,
                quiz_type: currentQuiz,
                score: score,
                max_score: maxPossibleScore,
                accuracy: accuracy,
                time_spent: timeStr
            }})
        }}).catch(e => {{}});
    }}
}}

let globalLeaderboardCache = [];
let currentLbTab = 'global';
let currentLbFilter = 'all';

function showLeaderboard() {{
    fetch('/api/results/leaderboard')
    .then(res => res.json())
    .then(data => {{
        globalLeaderboardCache = data;
        renderLeaderboardModal();
    }}).catch(e => alert('Не удалось загрузить таблицу лидеров с сервера'));
}}

function switchLbTab(tab) {{
    currentLbTab = tab;
    updateLbView();
}}

function switchLbFilter(filter) {{
    currentLbFilter = filter;
    updateLbView();
}}

function renderLeaderboardModal() {{
    let existing = document.getElementById('leaderboard-modal-container');
    if (existing) existing.remove();

    let html = `
    <div class="welcome-overlay" id="leaderboard-modal-container">
        <div class="welcome-card leaderboard-modal-card" style="text-align: center; max-width: 700px;">
            <h3>🏆 Центр успеваемости и лидеров</h3>
            
            <div class="lb-main-tabs">
                <button onclick="switchLbTab('global')" id="lb-tab-global" class="lb-tab-btn ${{currentLbTab==='global'?'active':''}}">🌍 Глобальный топ</button>
                <button onclick="switchLbTab('profile')" id="lb-tab-profile" class="lb-tab-btn ${{currentLbTab==='profile'?'active':''}}">👤 Мой профиль и история</button>
            </div>

            <div id="lb-content-area" class="lb-content-fade">
                ${{getLbContentHtml()}}
            </div>

            <button onclick="closeLeaderboardModal()" class="btn-start" style="margin-top: 16px;">Закрыть</button>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
}}

function updateLbView() {{
    let area = document.getElementById('lb-content-area');
    if (!area) return;

    let btnGlobal = document.getElementById('lb-tab-global');
    let btnProfile = document.getElementById('lb-tab-profile');
    if (btnGlobal && btnProfile) {{
        if (currentLbTab === 'global') {{
            btnGlobal.classList.add('active');
            btnProfile.classList.remove('active');
        }} else {{
            btnProfile.classList.add('active');
            btnGlobal.classList.remove('active');
        }}
    }}

    area.classList.add('fade-anim');
    setTimeout(() => {{
        area.innerHTML = getLbContentHtml();
        area.classList.remove('fade-anim');
    }}, 150);
}}

function getLbContentHtml() {{
    let filtersHtml = `
    <div class="lb-filters">
        <button onclick="switchLbFilter('all')" class="lb-filter-chip ${{currentLbFilter==='all'?'active':''}}">Все тесты</button>
        <button onclick="switchLbFilter('district')" class="lb-filter-chip ${{currentLbFilter==='district'?'active':''}}">Районы</button>
        <button onclick="switchLbFilter('neighbor')" class="lb-filter-chip ${{currentLbFilter==='neighbor'?'active':''}}">Соседи</button>
        <button onclick="switchLbFilter('river')" class="lb-filter-chip ${{currentLbFilter==='river'?'active':''}}">Реки</button>
        <button onclick="switchLbFilter('center')" class="lb-filter-chip ${{currentLbFilter==='center'?'active':''}}">Центры</button>
    </div>`;

    if (currentLbTab === 'global') {{
        let data = globalLeaderboardCache;
        if (currentLbFilter !== 'all') {{
            data = data.filter(r => r.quiz_type === currentLbFilter);
        }}

        if (!data || data.length === 0) {{
            return filtersHtml + '<p style="color: #64748B; font-size: 13px; margin: 25px 0;">Пока нет результатов в этой категории.</p>';
        }}

        let tableHtml = filtersHtml + '<div class="lb-table-wrap"><table class="lb-styled-table"><tr><th>№</th><th>Студент</th><th>Группа</th><th>Тест</th><th>Баллы</th><th>%</th><th>Время</th></tr>';
        data.forEach((r, index) => {{
            tableHtml += `<tr><td>${{index+1}}</td><td>${{r.name}}</td><td>${{r.group}}</td><td>${{r.quiz_type}}</td><td><b>${{r.score}}/${{r.max_score}}</b></td><td>${{r.accuracy}}%</td><td>${{r.time_spent}}</td></tr>`;
        }});
        tableHtml += '</table></div>';
        return tableHtml;
    }} else {{
        let student = getCurrentStudentInfo();
        if (!student) {{
            return `
            <div style="padding: 30px 10px; text-align: center;">
                <p style="color: #64748B; font-size: 13.5px; margin-bottom: 15px;">Чтобы просматривать личную статистику и историю, авторизуйтесь через корпоративную почту ЮФУ.</p>
                <button onclick="closeLeaderboardModal(); openAuthModal();" class="btn-start">Войти через ЮФУ</button>
            </div>`;
        }}

        let allResults = JSON.parse(localStorage.getItem('rostovQuizResults') || '[]');
        let myResults = allResults.filter(r => student && r.student === student.name);

        if (currentLbFilter !== 'all') {{
            myResults = myResults.filter(r => r.type === currentLbFilter);
        }}

        if (myResults.length === 0) {{
            return filtersHtml + `
            <div style="padding: 25px 10px; text-align: center;">
                <p style="font-weight: 700; color: #0369A1; font-size: 14px;">Привет, ${{student.name}} (${{student.group}})!</p>
                <p style="color: #64748B; font-size: 13px; margin-top: 8px;">У вас пока нет сохраненных результатов в выбранной категории.</p>
            </div>`;
        }}

        let bestResult = [...myResults].sort((a,b) => b.accuracy - a.accuracy || b.score - a.score)[0];
        let lastResults = [...myResults].reverse();

        let profileHtml = filtersHtml + `
        <div style="text-align: left; margin-bottom: 12px; background: #F0FDF4; border: 1px solid #BBF7D0; padding: 10px 14px; border-radius: 12px;">
            <p style="margin: 0; font-size: 12.5px; color: #166534; font-weight: 700;">👤 Студент: ${{student.name}}</p>
            <p style="margin: 2px 0 0 0; font-size: 11.5px; color: #15803D;">Группа: ${{student.group}}</p>
        </div>

        <div style="margin-bottom: 12px; text-align: left;">
            <h4 style="margin: 0 0 5px 0; font-size: 12.5px; color: #1E293B;">⭐ Лучший результат:</h4>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; padding: 8px 12px; border-radius: 9px; font-size: 11.5px; color: #92400E; display: flex; justify-content: space-between; align-items: center;">
                <span>Тест: <b>${{bestResult.type}}</b> | Баллы: <b>${{bestResult.score}}/${{bestResult.maxScore}}</b> (${{bestResult.accuracy}}%)</span>
                <span>⏱️ ${{bestResult.time_spent}}</span>
            </div>
        </div>

        <div style="text-align: left;">
            <h4 style="margin: 0 0 5px 0; font-size: 12.5px; color: #1E293B;">📜 История прохождений:</h4>
            <div class="lb-table-wrap">
                <table class="lb-styled-table">
                    <tr><th>Дата</th><th>Тест</th><th>Баллы</th><th>%</th><th>Время</th></tr>`;
        
        lastResults.forEach(r => {{
            profileHtml += `<tr><td>${{r.date}}</td><td>${{r.type}}</td><td><b>${{r.score}}/${{r.maxScore}}</b></td><td>${{r.accuracy}}%</td><td>${{r.time_spent}}</td></tr>`;
        }});

        profileHtml += `</table></div></div>`;
        return profileHtml;
    }}
}}

function closeLeaderboardModal() {{
    let el = document.getElementById('leaderboard-modal-container');
    if (el) el.remove();
}}

function exitQuiz() {{
    if (confirm('Завершить викторину?')) {{
        finishQuizDirectly();
    }}
}}

function finishQuizDirectly() {{
    stopTimer();
    const map = getMapObject();
    if (map && window._clickBlocker) {{
        try {{
            if (window._clickHandler) {{
                window._clickBlocker.off('click', window._clickHandler);
            }}
            map.removeLayer(window._clickBlocker);
        }} catch(e) {{}}
        window._clickBlocker = null;
        window._clickHandler = null;
    }}
    clearMarkers();
    enablePopups();
    resetActiveHighlight(false);
    restoreAllLayers();
    resetMapView();

    currentQuiz = null;
    resetQuiz();
    setTimeout(setupDistrictClickListeners, 300);

    const qm = document.getElementById('quiz-mode');
    const rm = document.getElementById('results-mode');
    const nm = document.getElementById('normal-mode');
    if (qm) qm.style.display = 'none';
    if (rm) rm.style.display = 'none';
    if (nm) nm.style.display = 'block';
}}

function restartQuiz() {{
    resetQuiz();
    resetActiveHighlight(false);
    const rm = document.getElementById('results-mode');
    const qm = document.getElementById('quiz-mode');
    if (rm) rm.style.display = 'none';
    if (qm) qm.style.display = 'block';
    if (currentQuiz === 'district') {{
        setQuizLayers('district');
        loadDistrictQuiz();
    }} else if (currentQuiz === 'neighbor') {{
        setQuizLayers('neighbor');
        loadNeighborQuiz();
    }} else if (currentQuiz === 'river') {{
        restoreAllRiverStyles();
        setQuizLayers('river');
        loadRiverQuiz();
    }} else {{
        setQuizLayers('center');
        loadCenterQuiz();
    }}
}}

function resetQuiz() {{
    stopTimer();
    currentQuestion = 0;
    score = 0;
    maxPossibleScore = 0;
    quizData = [];
    selectedOption = null;
    updateScore();
    clearMarkers();
}}

function shuffleArray(array) {{
    for (let i = array.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }}
}}

function closeWelcomeModal() {{
    const modal = document.getElementById('welcome-modal');
    if (modal) {{
        modal.classList.add('fade-out');
        setTimeout(() => {{
            modal.style.display = 'none';
        }}, 250);
    }}
    const dontShow = document.getElementById('dont-show-welcome');
    if (dontShow && dontShow.checked) {{
        localStorage.setItem('rostovMapHideWelcome', 'true');
    }}
}}

function openWelcomeModal() {{
    const modal = document.getElementById('welcome-modal');
    if (modal) {{
        modal.classList.remove('fade-out');
        modal.style.display = 'flex';
    }}
}}

function openAuthModal() {{
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
    resetAuthForms();
}}

function closeAuthModal() {{
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
}}

function resetAuthForms() {{
    document.getElementById('auth-step-1').style.display = 'block';
    document.getElementById('auth-step-2').style.display = 'none';
    document.getElementById('auth-error').style.display = 'none';
    document.getElementById('auth-code-input').value = '';
}}

async function requestSfeduCode() {{
    const email = document.getElementById('auth-email').value.trim();
    const name = document.getElementById('auth-name').value.trim();
    const group = document.getElementById('auth-group').value.trim();
    const errBox = document.getElementById('auth-error');

    if (!email || !name || !group) {{
        showAuthError('Заполните все поля');
        return;
    }}

    if (!email.toLowerCase().endsWith('@sfedu.ru') && !email.toLowerCase().endsWith('.sfedu.ru')) {{
        showAuthError('Разрешены только адреса @sfedu.ru');
        return;
    }}

    try {{
        const res = await fetch('/api/auth/send-code', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ email, full_name: name, group_num: group }})
        }});
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка отправки кода');

        document.getElementById('auth-step-1').style.display = 'none';
        document.getElementById('auth-step-2').style.display = 'block';
        document.getElementById('auth-target-email').textContent = email;
        errBox.style.display = 'none';

        if (data.dev_code) {{
            alert(`[Демо/ЮФУ] Ваш проверочный код: ${{data.dev_code}}`);
        }}
    }} catch(e) {{
        showAuthError(e.message || 'Ошибка соединения с сервером');
    }}
}}

async function verifySfeduCode() {{
    const email = document.getElementById('auth-email').value.trim();
    const code = document.getElementById('auth-code-input').value.trim();

    if (!code || code.length !== 6) {{
        showAuthError('Введите 6-значный код');
        return;
    }}

    try {{
        const res = await fetch('/api/auth/verify-code', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ email, code }})
        }});
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Неверный код');

        localStorage.setItem('sfeduStudent', JSON.stringify(data.user));
        updateStudentHeader();
        closeAuthModal();
    }} catch(e) {{
        showAuthError(e.message || 'Неверный или просроченный код');
    }}
}}

function showAuthError(msg) {{
    const errBox = document.getElementById('auth-error');
    errBox.textContent = msg;
    errBox.style.display = 'block';
}}

function logoutStudent() {{
    if (confirm('Выйти из профиля студента ЮФУ?')) {{
        localStorage.removeItem('sfeduStudent');
        updateStudentHeader();
    }}
}}

function getCurrentStudentInfo() {{
    try {{
        const raw = localStorage.getItem('sfeduStudent');
        return raw ? JSON.parse(raw) : null;
    }} catch(e) {{
        return null;
    }}
}}

function updateStudentHeader() {{
    const student = getCurrentStudentInfo();
    const authBtn = document.getElementById('auth-top-btn');
    const profileBox = document.getElementById('student-profile-badge');

    if (student) {{
        if (authBtn) authBtn.style.display = 'none';
        if (profileBox) {{
            profileBox.style.display = 'flex';
            document.getElementById('student-badge-name').textContent = student.name;
            document.getElementById('student-badge-group').textContent = `${{student.group}} | ЮФУ`;
        }}
    }} else {{
        if (authBtn) authBtn.style.display = 'flex';
        if (profileBox) profileBox.style.display = 'none';
    }}
}}

document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(setupDistrictClickListeners, 1000);
    updateStudentHeader();
    if (!localStorage.getItem('rostovMapHideWelcome')) {{
        setTimeout(openWelcomeModal, 400);
    }}
}});
'''

        self.map.get_root().html.add_child(folium.Element(f"<script>{js_code}</script>"))

        quiz_html = '''
        <div class="top-nav-buttons">
            <button id="auth-top-btn" class="nav-top-btn auth-btn" onclick="openAuthModal()" title="Вход для студентов ЮФУ">
                <span>🎓 Вход ЮФУ</span>
            </button>
            <div id="student-profile-badge" class="student-badge" style="display: none;">
                <div class="badge-avatar">🎓</div>
                <div class="badge-info">
                    <span id="student-badge-name" class="badge-name">Студент</span>
                    <span id="student-badge-group" class="badge-group">Группа</span>
                </div>
                <button onclick="logoutStudent()" class="badge-logout" title="Выйти">&times;</button>
            </div>
            <button class="nav-top-btn leaderboard-top-btn" onclick="showLeaderboard()" title="Глобальная таблица лидеров и профиль">🏆 Топ лидеров</button>
            <button class="help-circle-btn" onclick="openWelcomeModal()" title="О проекте и справка">?</button>
        </div>

        <div id="quiz-controls" class="app-card">
            <div class="panel-header">
                <h3>Режим обучения</h3>
            </div>

            <div id="normal-mode">
                <button onclick="startDistrictQuiz()" class="btn btn-district">
                    Угадай район по очертаниям
                </button>

                <button onclick="startNeighborQuiz()" class="btn btn-neighbor">
                    Районы-соседи (пространственный тест)
                </button>

                <button onclick="startRiverQuiz()" class="btn btn-river">
                    Угадай реку по руслу
                </button>

                <button onclick="startCenterQuiz()" class="btn btn-center">
                    Найди райцентр на карте
                </button>

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

            <div id="quiz-mode" style="display: none;">
                <div class="quiz-status-header">
                    <h4 id="quiz-title">Викторина</h4>
                    <div id="quiz-progress">Вопрос: <span id="current-question">1</span>/<span id="total-questions">10</span></div>
                </div>

                <div id="timer-bar-container" style="display: none; margin-bottom: 10px;">
                    <div class="timer-flex">
                        <span>Время:</span>
                        <span id="timer-text">20с</span>
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

                <button onclick="exitQuiz()" class="btn btn-danger">
                    Завершить
                </button>

                <button onclick="showHint()" id="hint-button" class="btn btn-warning" style="display: none; margin-top: 6px;">
                    Подсказка
                </button>
            </div>

            <div id="results-mode" style="display: none; text-align: center;">
                <h4 style="color: #10B981; margin: 0 0 10px 0; font-size: 15px;">Результаты теста</h4>
                <div id="results-content">
                </div>
                <button onclick="restartQuiz()" class="btn btn-primary" style="margin-top: 12px;">
                    Пройти заново
                </button>
                <button onclick="finishQuizDirectly()" class="btn btn-danger" style="margin-top: 6px;">
                    Завершить
                </button>
            </div>
        </div>

        <!-- Окно авторизации ЮФУ -->
        <div id="auth-modal" class="welcome-overlay" style="display: none;">
            <div class="auth-card">
                <div class="auth-header">
                    <div>
                        <h3>Вход через профиль ЮФУ</h3>
                        <p style="margin: 2px 0 0 0; font-size: 11.5px; color: #64748B;">Студенческая почта @sfedu.ru</p>
                    </div>
                    <button onclick="closeAuthModal()" class="close-card-btn">&times;</button>
                </div>

                <div id="auth-error" class="auth-error" style="display: none;"></div>

                <div id="auth-step-1">
                    <div class="form-group">
                        <label>Корпоративная почта ЮФУ:</label>
                        <input type="email" id="auth-email" placeholder="ivanov@sfedu.ru" class="auth-input">
                    </div>
                    <div class="form-group">
                        <label>ФИО студента:</label>
                        <input type="text" id="auth-name" placeholder="Иванов Иван Иванович" class="auth-input">
                    </div>
                    <div class="form-group">
                        <label>Академическая группа / Специальность:</label>
                        <input type="text" id="auth-group" placeholder="Геофак, 4 курс" class="auth-input">
                    </div>
                    <button onclick="requestSfeduCode()" class="btn-start" style="width: 100%; margin-top: 14px;">
                        Получить код подтверждения
                    </button>
                </div>

                <div id="auth-step-2" style="display: none;">
                    <p style="font-size: 13px; color: #475569; margin: 0 0 12px 0;">
                        Код верификации отправлен на адрес: <br><strong id="auth-target-email" style="color: #0F172A;"></strong>
                    </p>
                    <div class="form-group">
                        <label>6-значный код:</label>
                        <input type="text" id="auth-code-input" maxlength="6" placeholder="000000" class="auth-input code-input">
                    </div>
                    <button onclick="verifySfeduCode()" class="btn-start" style="width: 100%; margin-top: 14px;">
                        Подтвердить и войти
                    </button>
                    <button onclick="resetAuthForms()" style="background: none; border: none; color: #64748B; font-size: 12px; margin-top: 10px; width: 100%; cursor: pointer;">
                        ← Ввести другой адрес
                    </button>
                </div>
            </div>
        </div>

        <div id="welcome-modal" class="welcome-overlay" style="display: none;">
            <div class="welcome-card">
                <div class="welcome-badge">Географический атлас</div>
                <h2 class="welcome-title">Ростовская область</h2>
                <p class="welcome-subtitle">Интерактивный картографический комплекс и система тестирования пространственных знаний</p>
                
                <div class="welcome-grid">
                    <div class="welcome-feature">
                        <div class="feature-icon" style="background: #E8F5E9; color: #2E7D32;">🗺️</div>
                        <div class="feature-content">
                            <h4>Интерактивная карта</h4>
                            <p>Детальные границы районов, русла рек, водоёмы и райцентры. Кликайте по районам в обычном режиме для просмотра площади, населения и соседей.</p>
                        </div>
                    </div>
                    <div class="welcome-feature">
                        <div class="feature-icon" style="background: #E0F2FE; color: #0284C7;">🌊</div>
                        <div class="feature-content">
                            <h4>Гидрография и номенклатура</h4>
                            <p>Режим викторины по главным водным артериям региона. Карта фокусируется на русле реки и предлагает варианты ответа.</p>
                        </div>
                    </div>
                    <div class="welcome-feature">
                        <div class="feature-icon" style="background: #E0F7FA; color: #00796B;">🧩</div>
                        <div class="feature-content">
                            <h4>Пространственные тесты</h4>
                            <p>Проверка знания топологии границ районов («Районы-соседи») и узнавания силуэтов административных территорий.</p>
                        </div>
                    </div>
                    <div class="welcome-feature">
                        <div class="feature-icon" style="background: #EFF6FF; color: #1D4ED8;">🎯</div>
                        <div class="feature-content">
                            <h4>Поиск центров с точностью</h4>
                            <p>Проверка топографической ориентации. Укажите кликом райцентр на карте и получите баллы в зависимости от погрешности в километрах.</p>
                        </div>
                    </div>
                </div>

                <div class="welcome-footer">
                    <label class="welcome-checkbox">
                        <input type="checkbox" id="dont-show-welcome">
                        <span>Больше не показывать при входе</span>
                    </label>
                    <button onclick="closeWelcomeModal()" class="btn-start">Начать работу с картой</button>
                </div>
            </div>
        </div>

        <style>
        .top-nav-buttons {
            position: fixed;
            top: 14px;
            right: 330px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .nav-top-btn {
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 20px;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 700;
            color: #1E293B;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
            transition: all 0.2s ease;
        }
        .nav-top-btn:hover {
            transform: translateY(-1px);
            background: #ffffff;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
        }

        .leaderboard-top-btn {
            background: linear-gradient(135deg, #FFF7ED, #FFEDD5);
            border-color: #FDBA74;
            color: #C2410C;
        }
        .leaderboard-top-btn:hover {
            background: linear-gradient(135deg, #FFEDD5, #FED7AA);
            color: #9A3412;
        }

        .student-badge {
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(8px);
            border: 1px solid #BAE6FD;
            border-radius: 20px;
            padding: 4px 10px 4px 6px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
        }
        .badge-avatar {
            width: 26px;
            height: 26px;
            background: #E0F2FE;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
        }
        .badge-info { display: flex; flex-direction: column; text-align: left; }
        .badge-name { font-size: 11.5px; font-weight: 700; color: #0369A1; line-height: 1.2; }
        .badge-group { font-size: 10px; color: #64748B; }
        .badge-logout {
            background: none;
            border: none;
            font-size: 16px;
            color: #94A3B8;
            cursor: pointer;
            margin-left: 4px;
            line-height: 1;
        }
        .badge-logout:hover { color: #EF4444; }

        .help-circle-btn {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(0, 0, 0, 0.1);
            color: #334155;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .help-circle-btn:hover {
            transform: scale(1.05);
            background: white;
            color: #10B981;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15);
        }

        .lb-main-tabs {
            display: flex;
            background: #F1F5F9;
            padding: 4px;
            border-radius: 12px;
            margin-bottom: 14px;
            gap: 4px;
        }
        .lb-tab-btn {
            flex: 1;
            background: transparent;
            border: none;
            padding: 8px 12px;
            font-size: 12.5px;
            font-weight: 700;
            color: #64748B;
            border-radius: 9px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .lb-tab-btn.active {
            background: #ffffff;
            color: #0F172A;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .lb-content-fade {
            transition: opacity 0.15s ease-in-out, transform 0.15s ease-in-out;
            opacity: 1;
            transform: translateY(0);
        }
        .fade-anim {
            opacity: 0;
            transform: translateY(6px);
        }

        .lb-filters {
            display: flex;
            gap: 6px;
            justify-content: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }
        .lb-filter-chip {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 5px 12px;
            border-radius: 16px;
            font-size: 11.5px;
            font-weight: 600;
            color: #475569;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .lb-filter-chip:hover { background: #F1F5F9; }
        .lb-filter-chip.active {
            background: #10B981;
            color: white;
            border-color: #10B981;
        }

        .lb-table-wrap {
            max-height: 300px;
            overflow-y: auto;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
        }
        .lb-styled-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            text-align: center;
        }
        .lb-styled-table th {
            background: #F8FAFC;
            color: #475569;
            padding: 8px 6px;
            border-bottom: 1px solid #E2E8F0;
            position: sticky;
            top: 0;
            z-index: 2;
        }
        .lb-styled-table td {
            padding: 7px 6px;
            border-bottom: 1px solid #F1F5F9;
            color: #334155;
        }
        .lb-styled-table tr:hover { background: #F8FAFC; }

        .auth-card {
            background: #ffffff;
            border-radius: 18px;
            max-width: 440px;
            width: 100%;
            padding: 24px 26px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            box-sizing: border-box;
            animation: welcomeIn 0.25s ease-out;
        }

        .auth-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 12px;
            margin-bottom: 14px;
        }
        .auth-header h3 { margin: 0; font-size: 15px; color: #0F172A; }

        .auth-error {
            background: #FEE2E2;
            color: #B91C1C;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            margin-bottom: 12px;
            border: 1px solid #FCA5A5;
        }

        .form-group {
            margin-bottom: 12px;
            text-align: left;
        }
        .form-group label {
            display: block;
            font-size: 11.5px;
            color: #475569;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .auth-input {
            width: 100%;
            padding: 9px 12px;
            border-radius: 8px;
            border: 1.5px solid #CBD5E1;
            font-size: 13px;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.2s;
        }
        .auth-input:focus { border-color: #0284C7; }
        .code-input {
            text-align: center;
            letter-spacing: 6px;
            font-size: 20px;
            font-weight: 800;
            color: #0284C7;
        }

        .welcome-overlay {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.55);
            backdrop-filter: blur(4px);
            z-index: 20000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            transition: opacity 0.25s ease;
        }
        .welcome-overlay.fade-out {
            opacity: 0;
            pointer-events: none;
        }

        .welcome-card {
            background: #ffffff;
            border-radius: 18px;
            max-width: 640px;
            width: 100%;
            padding: 28px 32px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            position: relative;
            animation: welcomeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            max-height: calc(100vh - 40px);
            overflow-y: auto;
            box-sizing: border-box;
        }

        @keyframes welcomeIn {
            from { opacity: 0; transform: scale(0.96) translateY(10px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }

        .welcome-badge {
            display: inline-block;
            background: #DCFCE7;
            color: #15803D;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .welcome-title {
            margin: 0 0 6px 0;
            font-size: 24px;
            color: #0F172A;
            font-weight: 800;
            letter-spacing: -0.4px;
        }

        .welcome-subtitle {
            margin: 0 0 22px 0;
            font-size: 13.5px;
            color: #64748B;
            line-height: 1.45;
        }

        .welcome-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-bottom: 24px;
        }

        .welcome-feature {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 12px 14px;
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }

        .feature-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 17px;
            flex-shrink: 0;
        }

        .feature-content h4 {
            margin: 0 0 3px 0;
            font-size: 13px;
            color: #1E293B;
            font-weight: 700;
        }

        .feature-content p {
            margin: 0;
            font-size: 11.5px;
            color: #64748B;
            line-height: 1.35;
        }

        .welcome-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 16px;
            border-top: 1px solid #E2E8F0;
            flex-wrap: wrap;
            gap: 12px;
        }

        .welcome-checkbox {
            display: flex;
            align-items: center;
            font-size: 12px;
            color: #64748B;
            cursor: pointer;
            user-select: none;
        }

        .welcome-checkbox input {
            margin-right: 8px;
            cursor: pointer;
        }

        .btn-start {
            background: linear-gradient(135deg, #10B981, #059669);
            color: white;
            border: none;
            padding: 10px 22px;
            border-radius: 10px;
            font-size: 13.5px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            transition: all 0.2s ease;
        }
        .btn-start:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
        }

        .app-card {
            position: fixed;
            top: 14px;
            right: 14px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(8px);
            padding: 16px;
            border-radius: 14px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            width: 300px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            border: 1px solid rgba(0, 0, 0, 0.08);
            max-height: calc(100vh - 28px);
            overflow-y: auto;
            box-sizing: border-box;
        }

        .panel-header h3 {
            margin: 0 0 12px 0;
            color: #1E293B;
            text-align: center;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.2px;
        }

        .btn {
            display: block;
            width: 100%;
            border: none;
            padding: 9px 12px;
            margin-bottom: 7px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.06);
            color: white;
            box-sizing: border-box;
        }

        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.12);
        }

        .btn-district { background: linear-gradient(135deg, #10B981, #059669); }
        .btn-neighbor { background: linear-gradient(135deg, #0D9488, #0F766E); }
        .btn-river { background: linear-gradient(135deg, #0EA5E9, #0284C7); }
        .btn-center { background: linear-gradient(135deg, #3B82F6, #2563EB); }
        .btn-primary { background: #10B981; }
        .btn-warning { background: #F59E0B; }
        .btn-danger { background: #EF4444; }

        .btn-confirm {
            display: block;
            width: 100%;
            border: none;
            padding: 10px 14px;
            margin-top: 10px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 700;
            background: linear-gradient(135deg, #2563EB, #1D4ED8);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
            transition: all 0.2s ease;
            box-sizing: border-box;
        }
        .btn-confirm:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
            background: linear-gradient(135deg, #1D4ED8, #1E40AF);
        }

        .timer-setting-box {
            margin: 8px 0;
            padding: 8px 10px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
        }

        .checkbox-container {
            display: flex;
            align-items: center;
            font-size: 12px;
            cursor: pointer;
            color: #334155;
            user-select: none;
        }

        .checkbox-container input {
            margin-right: 8px;
            cursor: pointer;
        }

        .hint-small {
            margin-top: 8px;
            padding: 8px;
            background: #F1F5F9;
            border-radius: 6px;
            font-size: 11px;
            color: #64748B;
            text-align: center;
            line-height: 1.3;
        }

        .district-info-box {
            display: none;
            margin-top: 10px;
            padding: 12px;
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 10px;
        }

        .info-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1.5px solid #86EFAC;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }

        .info-card-header strong {
            color: #166534;
            font-size: 13.5px;
        }

        .close-card-btn {
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            color: #94A3B8;
            line-height: 1;
            padding: 0;
        }
        .close-card-btn:hover { color: #334155; }

        .info-row {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            margin-bottom: 4px;
            color: #334155;
        }
        .info-row span { color: #64748B; }

        .neighbor-tag {
            display: inline-block;
            background: #DCFCE7;
            color: #15803D;
            padding: 3px 7px;
            border-radius: 5px;
            font-size: 11px;
            margin: 2px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .neighbor-tag:hover { background: #BBF7D0; }

        .quiz-status-header {
            background: linear-gradient(135deg, #10B981, #059669);
            color: white;
            padding: 9px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            text-align: center;
        }
        .quiz-status-header h4 { margin: 0; font-size: 13px; font-weight: 700; }
        #quiz-progress { font-size: 11.5px; opacity: 0.9; margin-top: 2px; }

        .timer-flex {
            display: flex;
            justify-content: space-between;
            font-size: 11.5px;
            color: #475569;
            margin-bottom: 4px;
        }
        .timer-track {
            width: 100%;
            height: 6px;
            background: #E2E8F0;
            border-radius: 3px;
            overflow: hidden;
        }
        #timer-bar {
            width: 100%;
            height: 100%;
            background: #10B981;
            transition: width 1s linear, background 0.3s;
        }

        .question-text {
            font-size: 13px;
            font-weight: 700;
            color: #1E293B;
            margin: 0 0 10px 0;
            text-align: center;
            line-height: 1.4;
        }

        .quiz-option {
            display: block;
            width: 100%;
            padding: 9px 12px;
            margin: 5px 0;
            background: #F8FAFC;
            border: 1.5px solid #E2E8F0;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12.5px;
            color: #334155;
            text-align: left;
            transition: all 0.15s ease;
            box-sizing: border-box;
        }
        .quiz-option:hover {
            background: #F1F5F9;
            border-color: #CBD5E1;
        }
        .quiz-option.selected {
            border-color: #3B82F6 !important;
            background: #EFF6FF !important;
            color: #1D4ED8 !important;
            font-weight: 600;
        }
        .quiz-option.correct {
            background: #DCFCE7 !important;
            border-color: #86EFAC !important;
            color: #15803D !important;
            font-weight: 600;
        }
        .quiz-option.incorrect {
            background: #FEE2E2 !important;
            border-color: #FCA5A5 !important;
            color: #B91C1C !important;
        }

        .center-quiz-instruction {
            padding: 10px;
            background: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 8px;
            color: #475569;
            text-align: center;
            font-size: 12px;
            line-height: 1.4;
        }
        .center-quiz-instruction span {
            font-size: 11px;
            color: #64748B;
            display: block;
            margin-top: 4px;
        }

        .feedback-box {
            padding: 9px 12px;
            border-radius: 7px;
            margin-top: 10px;
            text-align: center;
            font-weight: 700;
            font-size: 12.5px;
        }
        .feedback-box.success { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
        .feedback-box.error { background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }

        .hint-container {
            background: #FEF3C7;
            border: 1px solid #FDE68A;
            border-radius: 7px;
            padding: 8px 10px;
            margin-top: 8px;
            font-size: 11.5px;
            color: #92400E;
            line-height: 1.3;
        }

        .score-card {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 8px 12px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
            font-weight: 700;
            font-size: 13px;
            color: #1E293B;
        }
        .score-sub { font-size: 11px; color: #64748B; font-weight: 500; margin-top: 2px; }

        /* ================= MOBILE ADAPTIVE STYLES ================= */
        @media (max-width: 768px) {
            .top-nav-buttons {
                top: 10px;
                right: 10px;
                left: auto;
                gap: 6px;
            }
            .nav-top-btn, .help-circle-btn {
                padding: 6px 10px;
                font-size: 11px;
                height: 32px;
            }
            .help-circle-btn {
                width: 32px;
                font-size: 14px;
            }
            .app-card {
                position: fixed;
                top: auto;
                bottom: 10px;
                right: 10px;
                left: 10px;
                width: auto;
                max-height: 42vh;
                padding: 12px;
                z-index: 1001;
            }
            .welcome-grid {
                grid-template-columns: 1fr;
            }
            .welcome-card, .auth-card {
                padding: 18px 20px;
                max-width: 95vw;
                max-height: 85vh;
            }

            .leaflet-bottom.leaflet-left .leaflet-control-layers {
                border-radius: 8px !important;
                margin-bottom: 46vh !important;
                margin-left: 10px !important;
                background: rgba(255, 255, 255, 0.95) !important;
            }
            .leaflet-control-layers-expanded {
                max-height: 140px;
                overflow-y: auto;
                padding: 6px 10px !important;
                font-size: 11px !important;
            }
            .leaflet-control-layers::before {
                font-size: 11.5px !important;
                padding-bottom: 2px !important;
                margin-bottom: 4px !important;
            }

            div[style*="top: 14px; left: 60px;"] {
                display: none !important;
            }
        }
        </style>
        '''
        self.map.get_root().html.add_child(folium.Element(quiz_html))

    def add_legend(self):
        legend_html = '''
        <div style="
            position: fixed;
            top: 14px; left: 60px;
            width: 220px;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(0,0,0,0.08);
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            padding: 14px;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            color: #334155;
        ">
            <h4 style="margin: 0 0 10px 0; color: #1E293B; font-size: 14px; font-weight: 700;">Легенда карты</h4>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <i class="fa fa-star" style="color: #FF9800; font-size: 12px; margin-right: 8px;"></i>
                <span>Райцентры</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <div style="width: 18px; height: 3px; background: #2E8B57; margin-right: 8px; border-radius: 2px;"></div>
                <span>Границы районов</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 6px;">
                <div style="width: 18px; height: 3px; background: #1E90FF; margin-right: 8px; border-radius: 2px;"></div>
                <span>Реки</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 18px; height: 14px; background: #87CEEB; margin-right: 8px; opacity: 0.6; border-radius: 2px;"></div>
                <span>Водоемы</span>
            </div>
            <div style="border-top: 1px solid #E2E8F0; padding-top: 8px; font-size: 11px; color: #94A3B8; text-align: center;">
                Ростовская область
            </div>
        </div>
        '''
        self.map.get_root().html.add_child(folium.Element(legend_html))

    def add_minimap(self):
        minimap = plugins.MiniMap(toggle_display=True)
        self.map.add_child(minimap)

    def add_fullscreen(self):
        plugins.Fullscreen().add_to(self.map)

    def save(self, filename='rostov_quiz_map.html'):
        self.export_quiz_data()
        folium.LayerControl(collapsed=False, position='bottomleft').add_to(self.map)
        self.add_quiz_controls()
        self.add_legend()
        self.add_fullscreen()
        self.map.save(filename)
        print(f"\n{'='*60}")
        print(f"Карта успешно создана: {filename}")
        print(f"{'='*60}")

        force_map_script = '''
        <script>
        function findMapForce() {
            const mapElement = document.querySelector('.leaflet-container');
            if (mapElement) {
                try {
                    if (typeof L !== 'undefined') {
                        const map = L.DomUtil.get(mapElement);
                        if (map && typeof map.eachLayer === 'function') {
                            window._leaflet_map = map;
                            return true;
                        }
                    }
                } catch(e) {}
            }
            if (window._leaflet_map && typeof window._leaflet_map.eachLayer === 'function') {
                return true;
            }
            return false;
        }

        let attempts = 0;
        const maxAttempts = 30;

        function tryFindMap() {
            attempts++;
            if (findMapForce()) return;
            if (attempts < maxAttempts) setTimeout(tryFindMap, 300);
        }

        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(tryFindMap, 300);
        });
        </script>
        '''
        self.map.get_root().html.add_child(folium.Element(force_map_script))
        self.map.save(filename)

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
        .leaflet-control-attribution::before,
        .leaflet-control-attribution::after {
            display: none !important;
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

        .leaflet-control-layers-base {
            display: none !important;
        }
        </style>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            function hideBasemapUrl() {
                const baseLabels = document.querySelectorAll('.leaflet-control-layers-base label');
                baseLabels.forEach(function(label) {
                    label.style.display = 'none';
                });

                const links = document.querySelectorAll('.leaflet-control-layers a');
                links.forEach(function(link) {
                    if (link.href && (link.href.includes('cartocdn') || link.href.includes('carto'))) {
                        link.style.display = 'none';
                    }
                });

                const spans = document.querySelectorAll('.leaflet-control-layers span');
                spans.forEach(function(span) {
                    if (span.textContent && span.textContent.includes('basemaps')) {
                        span.style.display = 'none';
                    }
                });
            }

            let tries = 0;
            const interval = setInterval(function() {
                tries++;
                hideBasemapUrl();
                if (tries > 30) clearInterval(interval);
            }, 200);

            window.addEventListener('load', function() {
                hideBasemapUrl();
                setTimeout(hideBasemapUrl, 500);
            });
        });
        </script>
        """

        my_attribution_html = """
        <div class="my-attribution">
            © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors, © <a href="https://carto.com/attributions" target="_blank">CARTO</a>
        </div>
        """

        if '</head>' in html:
            html = html.replace('</head>', custom_css_js + '</head>', 1)
        else:
            html = custom_css_js + html

        if '</body>' in html:
            html = html.replace('</body>', my_attribution_html + '</body>', 1)
        else:
            html += my_attribution_html

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        try:
            webbrowser.open(f'file://{os.path.abspath(filename)}')
        except:
            pass

        return filename


def main():
    print("=" * 60)
    print("СОЗДАНИЕ КАРТЫ РОСТОВСКОЙ ОБЛАСТИ С ВИКТОРИНОЙ")
    print("=" * 60)
    print("\nПроверка наличия файлов...")
    for key, filename in SHAPEFILES.items():
        full_path = os.path.join(BASE_PATH, filename)
        if os.path.exists(full_path):
            print(f"  {filename}")
        else:
            print(f"  {filename} - не найден")

    rostov_map = RostovMap()
    rostov_map.add_water_bodies(os.path.join(BASE_PATH, SHAPEFILES['water_bodies']))
    rostov_map.add_rivers(os.path.join(BASE_PATH, SHAPEFILES['rivers']))
    rostov_map.add_districts(os.path.join(BASE_PATH, SHAPEFILES['districts']))
    rostov_map.add_district_centers(os.path.join(BASE_PATH, SHAPEFILES['district_centers']))

    output_file = rostov_map.save('rostov_quiz_map.html')
    print("\nВикторина готова!")
    return output_file


if __name__ == "__main__":
    main()