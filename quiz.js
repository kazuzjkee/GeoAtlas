
const EMBEDDED_DISTRICTS = [{"name": "Азовский район"}, {"name": "городской округ Азов"}, {"name": "городской округ Батайск"}, {"name": "Аксайский район"}, {"name": "Куйбышевский район"}, {"name": "Багаевский район"}, {"name": "городской округ Ростов-на-Дону"}, {"name": "городской округ Волгодонск"}, {"name": "Матвеево-Курганский район"}, {"name": "Неклиновский район"}, {"name": "Заветинский район"}, {"name": "Мясниковский район"}, {"name": "Ремонтненский район"}, {"name": "Песчанокопский район"}, {"name": "Родионово-Несветайский район"}, {"name": "городской округ Таганрог"}, {"name": "Белокалитвинский район"}, {"name": "Верхнедонской район"}, {"name": "Боковский район"}, {"name": "Весёловский район"}, {"name": "Кагальницкий район"}, {"name": "городской округ Новочеркасск"}, {"name": "городской округ Донецк"}, {"name": "Тарасовский район"}, {"name": "Зимовниковский район"}, {"name": "Сальский район"}, {"name": "Зерноградский район"}, {"name": "городской округ Гуково"}, {"name": "Кашарский район"}, {"name": "Шолоховский район"}, {"name": "Октябрьский район"}, {"name": "Дубовский район"}, {"name": "Усть-Донецкий район"}, {"name": "городской округ Шахты"}, {"name": "Каменский район"}, {"name": "городской округ Зверево"}, {"name": "Красносулинский район"}, {"name": "Семикаракорский район"}, {"name": "Миллеровский район"}, {"name": "городской округ Новошахтинск"}, {"name": "Егорлыкский район"}, {"name": "Морозовский район"}, {"name": "Константиновский район"}, {"name": "Обливский район"}, {"name": "Чертковский район"}, {"name": "Пролетарский район"}, {"name": "Орловский район"}, {"name": "Советский район"}, {"name": "Тацинский район"}, {"name": "городской округ Каменск-Шахтинский"}, {"name": "Целинский район"}, {"name": "Цимлянский район"}, {"name": "Милютинский район"}, {"name": "Мартыновский район"}, {"name": "Волгодонской район"}];
const EMBEDDED_CENTERS = [{"name": "Белая Калитва", "lat": 48.17517779999999, "lon": 40.790212399999994}, {"name": "Константиновск", "lat": 47.582352, "lon": 41.097083999999995}, {"name": "Усть-Донецкий", "lat": 47.640223999999996, "lon": 40.868748000000004}, {"name": "Чертково", "lat": 49.3799696, "lon": 40.1495138}, {"name": "Багаевская", "lat": 47.321434, "lon": 40.382903999999996}, {"name": "Весёлый", "lat": 47.0855153, "lon": 40.7458265}, {"name": "Покровское", "lat": 47.414280000000005, "lon": 38.896759}, {"name": "Родионово-Несветайская", "lat": 47.6135406, "lon": 39.70125289999999}, {"name": "Советская", "lat": 49.009204999999994, "lon": 42.12024699999999}, {"name": "Романовская", "lat": 47.541866, "lon": 42.021465}, {"name": "Казанская", "lat": 49.793972000000004, "lon": 41.13895}, {"name": "Пролетарск", "lat": 46.70016100000001, "lon": 41.724079}, {"name": "Кагальницкая", "lat": 46.879551000000006, "lon": 40.145775}, {"name": "Целина", "lat": 46.533634000000006, "lon": 41.028214000000006}, {"name": "Егорлыкская", "lat": 46.563081399999994, "lon": 40.64950449999999}, {"name": "Дубовское", "lat": 47.411167, "lon": 42.76422500000001}, {"name": "Аксай", "lat": 47.268696000000006, "lon": 39.861362}, {"name": "Большая Мартыновка", "lat": 47.271027000000004, "lon": 41.667885}, {"name": "Самарское", "lat": 46.937504000000004, "lon": 39.690974999999995}, {"name": "Обливская", "lat": 48.536387999999995, "lon": 42.499114999999996}, {"name": "Глубокий", "lat": 48.5242932, "lon": 40.326010999999994}, {"name": "Миллерово", "lat": 48.9196264, "lon": 40.391853999999995}, {"name": "Сальск", "lat": 46.476668999999994, "lon": 41.54100800000001}, {"name": "Вёшенская", "lat": 49.628994000000006, "lon": 41.725105}, {"name": "Кашары", "lat": 49.036998999999994, "lon": 41.008044999999996}, {"name": "Тацинская", "lat": 48.193871, "lon": 41.280865000000006}, {"name": "Цимлянск", "lat": 47.650585, "lon": 42.098232}, {"name": "Каменоломни", "lat": 47.6692096, "lon": 40.2052904}, {"name": "Зерноград", "lat": 46.84484499999999, "lon": 40.304813}, {"name": "Ремонтное", "lat": 46.56118000000001, "lon": 43.656048}, {"name": "Заветное", "lat": 47.117554, "lon": 43.888069}, {"name": "Милютинская", "lat": 48.627880000000005, "lon": 41.669490999999994}, {"name": "Зимовники", "lat": 47.148918, "lon": 42.46497}, {"name": "Чалтырь", "lat": 47.283455000000004, "lon": 39.501518000000004}, {"name": "Морозовск", "lat": 48.352379000000006, "lon": 41.828762}, {"name": "Матвеев Курган", "lat": 47.568459000000004, "lon": 38.86194199999999}, {"name": "Орловский", "lat": 46.869868999999994, "lon": 42.05186499999999}, {"name": "Красный Сулин", "lat": 47.891552, "lon": 40.071899}, {"name": "Куйбышево", "lat": 47.811755100000006, "lon": 38.90832500000001}, {"name": "Тарасовский", "lat": 48.725920599999995, "lon": 40.364463199999996}, {"name": "Семикаракорск", "lat": 47.516392999999994, "lon": 40.8122575}, {"name": "Боковская", "lat": 49.228859, "lon": 41.834742999999996}, {"name": "Песчанокопское", "lat": 46.184349000000005, "lon": 41.084557}];
const EMBEDDED_NEIGHBORS = [{"name": "Азовский район", "center": "Райцентр", "area": 6131, "population": 122620, "neighbors": ["городской округ Азов", "городской округ Батайск", "Кагальницкий район", "Неклиновский район", "городской округ Ростов-на-Дону", "Мясниковский район"]}, {"name": "городской округ Азов", "center": "Райцентр", "area": 142, "population": 2840, "neighbors": ["Азовский район"]}, {"name": "городской округ Батайск", "center": "Райцентр", "area": 173, "population": 3460, "neighbors": ["городской округ Ростов-на-Дону", "Аксайский район", "Азовский район", "Кагальницкий район"]}, {"name": "Аксайский район", "center": "Райцентр", "area": 2511, "population": 50220, "neighbors": ["городской округ Батайск", "Октябрьский район", "городской округ Новочеркасск", "Кагальницкий район", "Багаевский район", "Родионово-Несветайский район", "городской округ Ростов-на-Дону", "Мясниковский район"]}, {"name": "Куйбышевский район", "center": "Райцентр", "area": 1930, "population": 38600, "neighbors": ["Матвеево-Курганский район", "Родионово-Несветайский район"]}, {"name": "Багаевский район", "center": "Райцентр", "area": 2062, "population": 41240, "neighbors": ["Октябрьский район", "Аксайский район", "Семикаракорский район", "Кагальницкий район", "Весёловский район", "Зерноградский район", "Усть-Донецкий район"]}, {"name": "городской округ Ростов-на-Дону", "center": "г. Ростов-на-Дону (Областной центр)", "area": 772, "population": 15440, "neighbors": ["Аксайский район", "Азовский район", "Мясниковский район", "городской округ Батайск"]}, {"name": "городской округ Волгодонск", "center": "Райцентр", "area": 404, "population": 8080, "neighbors": ["Дубовский район", "Цимлянский район", "Волгодонской район"]}, {"name": "Матвеево-Курганский район", "center": "Райцентр", "area": 3750, "population": 75000, "neighbors": ["Родионово-Несветайский район", "Куйбышевский район", "Неклиновский район"]}, {"name": "Неклиновский район", "center": "Райцентр", "area": 4509, "population": 90180, "neighbors": ["Матвеево-Курганский район", "Азовский район", "Родионово-Несветайский район", "городской округ Таганрог", "Мясниковский район"]}, {"name": "Заветинский район", "center": "Райцентр", "area": 10126, "population": 202520, "neighbors": ["Зимовниковский район", "Ремонтненский район", "Дубовский район"]}, {"name": "Мясниковский район", "center": "Райцентр", "area": 1925, "population": 38500, "neighbors": ["Аксайский район", "Азовский район", "Неклиновский район", "Родионово-Несветайский район", "городской округ Ростов-на-Дону"]}, {"name": "Ремонтненский район", "center": "Райцентр", "area": 7965, "population": 159300, "neighbors": ["Зимовниковский район", "Заветинский район", "Орловский район"]}, {"name": "Песчанокопский район", "center": "Райцентр", "area": 3921, "population": 78420, "neighbors": ["Целинский район", "Сальский район"]}, {"name": "Родионово-Несветайский район", "center": "Райцентр", "area": 3408, "population": 68160, "neighbors": ["Матвеево-Курганский район", "Куйбышевский район", "Октябрьский район", "Аксайский район", "Неклиновский район", "Красносулинский район", "Мясниковский район", "городской округ Новошахтинск"]}, {"name": "городской округ Таганрог", "center": "Райцентр", "area": 184, "population": 3680, "neighbors": ["Неклиновский район"]}, {"name": "Белокалитвинский район", "center": "Райцентр", "area": 5979, "population": 119580, "neighbors": ["Константиновский район", "Октябрьский район", "Тарасовский район", "Тацинский район", "Каменский район", "Красносулинский район", "Милютинский район", "Усть-Донецкий район"]}, {"name": "Верхнедонской район", "center": "Райцентр", "area": 6400, "population": 128000, "neighbors": ["Кашарский район", "Чертковский район", "Боковский район", "Шолоховский район"]}, {"name": "Боковский район", "center": "Райцентр", "area": 4480, "population": 89600, "neighbors": ["Кашарский район", "Советский район", "Верхнедонской район", "Шолоховский район"]}, {"name": "Весёловский район", "center": "Райцентр", "area": 2913, "population": 58260, "neighbors": ["Сальский район", "Семикаракорский район", "Багаевский район", "Пролетарский район", "Зерноградский район"]}, {"name": "Кагальницкий район", "center": "Райцентр", "area": 2938, "population": 58760, "neighbors": ["городской округ Батайск", "Аксайский район", "Азовский район", "Багаевский район", "Зерноградский район"]}, {"name": "городской округ Новочеркасск", "center": "Райцентр", "area": 279, "population": 5580, "neighbors": ["Аксайский район", "Октябрьский район"]}, {"name": "городской округ Донецк", "center": "Райцентр", "area": 253, "population": 5060, "neighbors": ["Каменский район"]}, {"name": "Тарасовский район", "center": "Райцентр", "area": 6340, "population": 126800, "neighbors": ["Кашарский район", "Миллеровский район", "Каменский район", "Милютинский район", "Белокалитвинский район"]}, {"name": "Зимовниковский район", "center": "Райцентр", "area": 10855, "population": 217100, "neighbors": ["Мартыновский район", "Ремонтненский район", "Орловский район", "Заветинский район", "Дубовский район", "Волгодонской район"]}, {"name": "Сальский район", "center": "Райцентр", "area": 7494, "population": 149880, "neighbors": ["Целинский район", "Весёловский район", "Песчанокопский район", "Пролетарский район", "Зерноградский район"]}, {"name": "Зерноградский район", "center": "Райцентр", "area": 5731, "population": 114620, "neighbors": ["Целинский район", "Сальский район", "Егорлыкский район", "Кагальницкий район", "Багаевский район", "Весёловский район"]}, {"name": "городской округ Гуково", "center": "Райцентр", "area": 80, "population": 1600, "neighbors": ["Красносулинский район"]}, {"name": "Кашарский район", "center": "Райцентр", "area": 7312, "population": 146240, "neighbors": ["Верхнедонской район", "Боковский район", "Чертковский район", "Миллеровский район", "Тарасовский район", "Советский район", "Милютинский район"]}, {"name": "Шолоховский район", "center": "Райцентр", "area": 6036, "population": 120720, "neighbors": ["Верхнедонской район", "Боковский район"]}, {"name": "Октябрьский район", "center": "Райцентр", "area": 4362, "population": 87240, "neighbors": ["Аксайский район", "городской округ Шахты", "городской округ Новочеркасск", "Багаевский район", "Родионово-Несветайский район", "Красносулинский район", "Усть-Донецкий район", "городской округ Новошахтинск", "Белокалитвинский район"]}, {"name": "Дубовский район", "center": "Райцентр", "area": 8747, "population": 174940, "neighbors": ["Зимовниковский район", "Заветинский район", "Цимлянский район", "Волгодонской район", "городской округ Волгодонск"]}, {"name": "Усть-Донецкий район", "center": "Райцентр", "area": 2560, "population": 51200, "neighbors": ["Константиновский район", "Октябрьский район", "Семикаракорский район", "Багаевский район", "Белокалитвинский район"]}, {"name": "городской округ Шахты", "center": "Райцентр", "area": 354, "population": 7080, "neighbors": ["Красносулинский район", "Октябрьский район"]}, {"name": "Каменский район", "center": "Райцентр", "area": 5819, "population": 116380, "neighbors": ["городской округ Донецк", "Тарасовский район", "городской округ Каменск-Шахтинский", "Красносулинский район", "Белокалитвинский район"]}, {"name": "городской округ Зверево", "center": "Райцентр", "area": 71, "population": 1420, "neighbors": ["Красносулинский район"]}, {"name": "Красносулинский район", "center": "Райцентр", "area": 4752, "population": 95040, "neighbors": ["Октябрьский район", "городской округ Зверево", "городской округ Шахты", "городской округ Каменск-Шахтинский", "Каменский район", "Родионово-Несветайский район", "городской округ Гуково", "городской округ Новошахтинск", "Белокалитвинский район"]}, {"name": "Семикаракорский район", "center": "Райцентр", "area": 3056, "population": 61120, "neighbors": ["Мартыновский район", "Константиновский район", "Весёловский район", "Волгодонской район", "Багаевский район", "Пролетарский район", "Усть-Донецкий район"]}, {"name": "Миллеровский район", "center": "Райцентр", "area": 7520, "population": 150400, "neighbors": ["Чертковский район", "Тарасовский район", "Кашарский район"]}, {"name": "городской округ Новошахтинск", "center": "Райцентр", "area": 310, "population": 6200, "neighbors": ["Родионово-Несветайский район", "Красносулинский район", "Октябрьский район"]}, {"name": "Егорлыкский район", "center": "Райцентр", "area": 3122, "population": 62440, "neighbors": ["Целинский район", "Зерноградский район"]}, {"name": "Морозовский район", "center": "Райцентр", "area": 5731, "population": 114620, "neighbors": ["Константиновский район", "Цимлянский район", "Обливский район", "Тацинский район", "Милютинский район"]}, {"name": "Константиновский район", "center": "Райцентр", "area": 4838, "population": 96760, "neighbors": ["Морозовский район", "Семикаракорский район", "Белокалитвинский район", "Цимлянский район", "Тацинский район", "Волгодонской район", "Усть-Донецкий район"]}, {"name": "Обливский район", "center": "Райцентр", "area": 4617, "population": 92340, "neighbors": ["Советский район", "Морозовский район", "Милютинский район"]}, {"name": "Чертковский район", "center": "Райцентр", "area": 6461, "population": 129220, "neighbors": ["Кашарский район", "Верхнедонской район", "Миллеровский район"]}, {"name": "Пролетарский район", "center": "Райцентр", "area": 5864, "population": 117280, "neighbors": ["Мартыновский район", "Орловский район", "Сальский район", "Семикаракорский район", "Весёловский район"]}, {"name": "Орловский район", "center": "Райцентр", "area": 7144, "population": 142880, "neighbors": ["Мартыновский район", "Зимовниковский район", "Ремонтненский район", "Пролетарский район"]}, {"name": "Советский район", "center": "Райцентр", "area": 3009, "population": 60180, "neighbors": ["Кашарский район", "Обливский район", "Боковский район", "Милютинский район"]}, {"name": "Тацинский район", "center": "Райцентр", "area": 5418, "population": 108360, "neighbors": ["Морозовский район", "Милютинский район", "Константиновский район", "Белокалитвинский район"]}, {"name": "городской округ Каменск-Шахтинский", "center": "Райцентр", "area": 359, "population": 7180, "neighbors": ["Красносулинский район", "Каменский район"]}, {"name": "Целинский район", "center": "Райцентр", "area": 4509, "population": 90180, "neighbors": ["Зерноградский район", "Песчанокопский район", "Егорлыкский район", "Сальский район"]}, {"name": "Цимлянский район", "center": "Райцентр", "area": 5653, "population": 113060, "neighbors": ["Константиновский район", "Морозовский район", "Дубовский район", "Волгодонской район", "городской округ Волгодонск"]}, {"name": "Милютинский район", "center": "Райцентр", "area": 4850, "population": 97000, "neighbors": ["Морозовский район", "Кашарский район", "Тарасовский район", "Обливский район", "Тацинский район", "Советский район", "Белокалитвинский район"]}, {"name": "Мартыновский район", "center": "Райцентр", "area": 4164, "population": 83280, "neighbors": ["Зимовниковский район", "Орловский район", "Семикаракорский район", "Волгодонской район", "Пролетарский район"]}, {"name": "Волгодонской район", "center": "Райцентр", "area": 2996, "population": 59920, "neighbors": ["Мартыновский район", "Зимовниковский район", "Константиновский район", "Семикаракорский район", "Дубовский район", "Цимлянский район", "городской округ Волгодонск"]}];
const EMBEDDED_RIVERS = [{"name": "Сал", "length": 771.2}, {"name": "Дон", "length": 739.6}, {"name": "Чир", "length": 474.9}, {"name": "Калитва", "length": 470.8}, {"name": "Кагальник", "length": 375.6}, {"name": "Быстрая", "length": 359.3}, {"name": "Маныч", "length": 358.5}, {"name": "Северский Донец", "length": 330.2}, {"name": "Джурак-Сал", "length": 323.3}, {"name": "Кундрючья", "length": 321.1}, {"name": "Миус", "length": 240.7}, {"name": "Егорлык", "length": 227.5}, {"name": "Тузлов", "length": 217.6}, {"name": "Большой Гашун", "length": 206.0}, {"name": "Малая Куберле", "length": 172.9}, {"name": "Глубокая", "length": 170.3}, {"name": "Кумшак", "length": 166.0}, {"name": "Донской магистральный канал", "length": 163.8}, {"name": "Средний Егорлык", "length": 163.8}, {"name": "Россошь", "length": 151.7}, {"name": "Деркул", "length": 140.5}, {"name": "Большая", "length": 139.4}, {"name": "Мечетка", "length": 134.9}, {"name": "Гнилая", "length": 133.9}, {"name": "Пролетарский канал", "length": 127.9}, {"name": "Берёзовая", "length": 125.2}, {"name": "Верхнесальский канал", "length": 118.9}, {"name": "Ольховая", "length": 116.7}, {"name": "Грушевка", "length": 111.7}, {"name": "Ерик", "length": 111.6}];

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

function clearMarkers() {
    if (clickMarker) { try { clickMarker.remove(); } catch(e) {} clickMarker = null; }
    if (resultMarker) { try { resultMarker.remove(); } catch(e) {} resultMarker = null; }
    if (resultLine) { try { resultLine.remove(); } catch(e) {} resultLine = null; }
}

function resetActiveHighlight(hideRiverCompletely = false) {
    if (highlightedDistrictLayer) {
        try { highlightedDistrictLayer.setStyle({ color: '#2E8B57', weight: 2, fillColor: '#90EE90', fillOpacity: 0.2, dashArray: '5, 5' }); } catch(e) {}
        highlightedDistrictLayer = null;
    }

    if (highlightedRiverLayers && highlightedRiverLayers.length > 0) {
        highlightedRiverLayers.forEach(layer => {
            try {
                if (hideRiverCompletely) {
                    layer.setStyle({ color: 'transparent', weight: 0, opacity: 0 });
                } else {
                    layer.setStyle({ color: '#1E90FF', weight: 2, opacity: 0.8 });
                }
            } catch(e) {}
        });
        highlightedRiverLayers = [];
    }
}

function restoreAllRiverStyles() {
    const map = getMapObject();
    if (!map) return;
    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.geometry && (layer.feature.geometry.type === 'LineString' || layer.feature.geometry.type === 'MultiLineString')) {
            try { layer.setStyle({ color: '#1E90FF', weight: 2, opacity: 0.8 }); } catch(e) {}
        }
    });
}

function resetMapView() {
    const map = getMapObject();
    if (map) {
        try { map.setView([47.23, 39.72], 8); } catch(e) {}
    }
}

function setQuizLayers(quizMode) {
    const layers = document.querySelectorAll('.leaflet-control-layers-overlays label');
    layers.forEach(label => {
        const text = label.textContent.trim();
        const input = label.querySelector('input[type="checkbox"]');
        if (!input) return;

        if (quizMode === 'center') {
            if (text.includes('Реки') || text.includes('Водоемы') || text.includes('Граница')) {
                if (input.checked) input.click();
            }
            if (text.includes('Районы') || text.includes('Райцентры')) {
                if (!input.checked) input.click();
            }
        } else if (quizMode === 'district' || quizMode === 'neighbor') {
            if (text.includes('Реки') || text.includes('Водоемы') || text.includes('Граница') || text.includes('Райцентры')) {
                if (input.checked) input.click();
            }
            if (text.includes('Районы')) {
                if (!input.checked) input.click();
            }
        } else if (quizMode === 'river') {
            if (text.includes('Районы') || text.includes('Райцентры')) {
                if (input.checked) input.click();
            }
            if (text.includes('Реки') || text.includes('Водоемы') || text.includes('Граница')) {
                if (!input.checked) input.click();
            }
        } else {
            if (!input.checked) input.click();
        }
    });
}

function restoreAllLayers() {
    setQuizLayers('normal');
    restoreAllRiverStyles();
}

function disablePopups() {
    if (popupsDisabled) return;
    const style = document.createElement('style');
    style.id = 'disable-popups-style';
    style.textContent = '.leaflet-popup, .leaflet-tooltip { display: none !important; }';
    document.head.appendChild(style);
    popupsDisabled = true;
}

function enablePopups() {
    const style = document.getElementById('disable-popups-style');
    if (style) style.remove();
    popupsDisabled = false;
}

function toggleTimer() {
    const checkbox = document.getElementById('timer-toggle');
    if (checkbox) timerEnabled = checkbox.checked;
}

function startTimer() {
    stopTimer();
    const tb = document.getElementById('timer-bar-container');
    if (!timerEnabled) {
        if (tb) tb.style.display = 'none';
        return;
    }
    if (tb) tb.style.display = 'block';
    timeLeft = QUESTION_TIME_LIMIT;
    updateTimerDisplay();

    questionTimer = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();
        if (timeLeft <= 0) {
            stopTimer();
            handleTimeout();
        }
    }, 1000);
}

function stopTimer() {
    if (questionTimer) {
        clearInterval(questionTimer);
        questionTimer = null;
    }
}

function updateTimerDisplay() {
    const timerText = document.getElementById('timer-text');
    const timerBar = document.getElementById('timer-bar');
    if (timerText) timerText.textContent = `${timeLeft}с`;
    if (timerBar) {
        const percent = Math.max(0, (timeLeft / QUESTION_TIME_LIMIT) * 100);
        timerBar.style.width = `${percent}%`;
        timerBar.style.background = percent > 50 ? '#10B981' : percent > 25 ? '#F59E0B' : '#EF4444';
    }
}

function handleTimeout() {
    if (currentQuestion >= quizData.length) return;
    const question = quizData[currentQuestion];
    showFeedback('Время вышло!', 'error');

    if (question.type === 'district' || question.type === 'neighbor' || question.type === 'river') {
        document.querySelectorAll('.quiz-option').forEach(opt => {
            if (opt.textContent === question.correctAnswer) {
                opt.classList.add('correct');
            }
            opt.disabled = true;
        });
    } else if (question.type === 'center') {
        if (window._clickBlocker) {
            const map = getMapObject();
            try { map.removeLayer(window._clickBlocker); } catch(e) {}
            window._clickBlocker = null;
        }
    }

    setTimeout(() => {
        currentQuestion++;
        showQuestion();
    }, 1800);
}

function startDistrictQuiz() {
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
}

function startCenterQuiz() {
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
}

function startNeighborQuiz() {
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
}

function startRiverQuiz() {
    if (!EMBEDDED_RIVERS || EMBEDDED_RIVERS.length < 4) {
        alert('Недостаточно данных по рекам для запуска викторины');
        return;
    }
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
}

function loadDistrictQuiz() {
    maxPossibleScore = totalQuestions;
    generateDistrictQuestions(EMBEDDED_DISTRICTS);
}

function generateDistrictQuestions(data) {
    quizData = [];
    if (!data || data.length === 0) return;
    for (let i = 0; i < totalQuestions; i++) {
        const correct = data[Math.floor(Math.random() * data.length)];
        const options = [correct.name];
        while (options.length < 4 && options.length < data.length) {
            const wrong = data[Math.floor(Math.random() * data.length)];
            if (!options.includes(wrong.name)) {
                options.push(wrong.name);
            }
        }
        shuffleArray(options);
        quizData.push({
            type: 'district',
            correctAnswer: correct.name,
            options: options,
            hint: `Площадь района: ~${Math.round(Math.random() * 2000 + 500)} км²`,
            districtName: correct.name
        });
    }
    showQuestion();
}

function loadCenterQuiz() {
    maxPossibleScore = totalQuestions * 3;
    generateCenterQuestions(EMBEDDED_CENTERS);
}

function generateCenterQuestions(data) {
    quizData = [];
    if (!data || data.length === 0) return;
    for (let i = 0; i < totalQuestions; i++) {
        const correct = data[Math.floor(Math.random() * data.length)];
        quizData.push({
            type: 'center',
            correctAnswer: correct.name,
            correctLat: correct.lat,
            correctLon: correct.lon,
            hint: `Население: ~${Math.round(Math.random() * 50000 + 10000)} человек`,
            centerName: correct.name
        });
    }
    showQuestion();
}

function loadNeighborQuiz() {
    maxPossibleScore = totalQuestions;
    generateNeighborQuestions(EMBEDDED_NEIGHBORS);
}

function generateNeighborQuestions(data) {
    quizData = [];
    const validPool = data.filter(d => d.neighbors && d.neighbors.length >= 1);
    const allNames = data.map(d => d.name);

    if (validPool.length === 0) {
        alert('Недостаточно данных о топологии районов');
        finishQuizDirectly();
        return;
    }

    for (let i = 0; i < totalQuestions; i++) {
        const current = validPool[Math.floor(Math.random() * validPool.length)];
        const neighbors = [...current.neighbors];
        shuffleArray(neighbors);
        
        let options = [];
        if (neighbors.length >= 3) {
            options = neighbors.slice(0, 3);
        } else {
            options = [...neighbors];
            while (options.length < 3) {
                const dummyNeighbor = allNames[Math.floor(Math.random() * allNames.length)];
                if (!options.includes(dummyNeighbor) && dummyNeighbor !== current.name) {
                    options.push(dummyNeighbor);
                }
            }
        }

        const nonNeighbors = allNames.filter(name => name !== current.name && !current.neighbors.includes(name));
        const wrongNeighbor = nonNeighbors.length > 0 
            ? nonNeighbors[Math.floor(Math.random() * nonNeighbors.length)] 
            : allNames[0];

        options.push(wrongNeighbor);
        shuffleArray(options);

        quizData.push({
            type: 'neighbor',
            districtName: current.name,
            correctAnswer: wrongNeighbor,
            options: options
        });
    }
    showQuestion();
}

function loadRiverQuiz() {
    maxPossibleScore = totalQuestions;
    generateRiverQuestions(EMBEDDED_RIVERS);
}

function generateRiverQuestions(data) {
    quizData = [];
    if (!data || data.length === 0) return;
    const questionsCount = Math.min(totalQuestions, data.length);

    for (let i = 0; i < questionsCount; i++) {
        const correct = data[i % data.length];
        const options = [correct.name];
        while (options.length < 4 && options.length < data.length) {
            const wrong = data[Math.floor(Math.random() * data.length)];
            if (!options.includes(wrong.name)) {
                options.push(wrong.name);
            }
        }
        shuffleArray(options);
        quizData.push({
            type: 'river',
            correctAnswer: correct.name,
            options: options,
            riverName: correct.name,
            hint: `Длина русла в пределах области: ~${correct.length} км`
        });
    }
    shuffleArray(quizData);
    showQuestion();
}

function showQuestion() {
    if (currentQuestion >= quizData.length) {
        stopTimer();
        showResults();
        return;
    }

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

    if (question.type === 'district') {
        if (qTextEl) qTextEl.textContent = 'Угадайте район по очертаниям:';
        question.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        });
        highlightDistrictOnMapByName(question.districtName);

    } else if (question.type === 'neighbor') {
        if (qTextEl) qTextEl.textContent = `С каким районом НЕ граничит ${question.districtName}?`;
        question.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        });
        highlightDistrictOnMapByName(question.districtName);

    } else if (question.type === 'river') {
        if (qTextEl) qTextEl.textContent = 'Какая река подсвечена на карте?';
        question.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        });
        highlightRiverOnMapByName(question.riverName);

    } else if (question.type === 'center') {
        if (qTextEl) qTextEl.textContent = `Найдите на карте: ${question.correctAnswer}`;
        if (optionsContainer) {
            optionsContainer.innerHTML = '<div class="center-quiz-instruction">Кликните на карту в точке нахождения объекта<br><span>до 5 км: +3 очка | до 15 км: +2 | до 30 км: +1</span></div>';
        }
        window.currentQuestionData = question;
        setupMapClickListener(question);
    }

    const hintC = document.getElementById('hint-container');
    if (hintC) hintC.style.display = 'none';
    selectedOption = null;
    startTimer();
}

function selectOption(button, selected, correct) {
    document.querySelectorAll('.quiz-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    button.classList.add('selected');
    selectedOption = selected;
    showConfirmButton();
}

function showConfirmButton() {
    const optionsContainer = document.getElementById('options-container');
    if (!optionsContainer) return;
    const oldButton = document.getElementById('confirm-button');
    if (oldButton) oldButton.remove();

    const confirmButton = document.createElement('button');
    confirmButton.textContent = 'Подтвердить ответ';
    confirmButton.className = 'btn-primary';
    confirmButton.style.marginTop = '10px';
    confirmButton.onclick = checkAnswer;
    confirmButton.id = 'confirm-button';
    optionsContainer.appendChild(confirmButton);
}

function checkAnswer() {
    if (!selectedOption && currentQuiz !== 'center') {
        alert('Пожалуйста, выберите вариант ответа!');
        return;
    }
    stopTimer();
    const question = quizData[currentQuestion];
    const isCorrect = selectedOption === question.correctAnswer;
    
    document.querySelectorAll('.quiz-option').forEach(opt => {
        if (opt.textContent === question.correctAnswer) {
            opt.classList.add('correct');
        }
        if (opt.textContent === selectedOption && !isCorrect) {
            opt.classList.add('incorrect');
        }
        opt.disabled = true;
    });

    const oldButton = document.getElementById('confirm-button');
    if (oldButton) oldButton.remove();

    if (isCorrect) {
        score++;
        showFeedback('Правильно!', 'success');
    } else {
        showFeedback(`Неправильно! Ответ: ${question.correctAnswer}`, 'error');
    }
    updateScore();
    setTimeout(() => {
        currentQuestion++;
        showQuestion();
    }, 1800);
}

function setupMapClickListener(question) {
    const map = getMapObject();
    if (!map) {
        setTimeout(() => setupMapClickListener(question), 500);
        return;
    }

    if (window._clickBlocker) {
        try { map.removeLayer(window._clickBlocker); } catch(e) {}
        window._clickBlocker = null;
    }

    window._clickBlocker = L.rectangle(
        [[-90, -180], [90, 180]],
        { color: 'transparent', fillColor: 'transparent', fillOpacity: 0, weight: 0, interactive: true }
    ).addTo(map);

    window._clickHandler = function(e) {
        handleMapClick(e.latlng.lat, e.latlng.lng, question);
    };

    window._clickBlocker.on('click', window._clickHandler);
}

function getMapObject() {
    let map = window._leaflet_map;
    if (!map || typeof map.eachLayer !== 'function') {
        const mapElement = document.querySelector('.leaflet-container');
        if (mapElement && typeof L !== 'undefined') {
            try {
                const possibleMap = L.DomUtil.get(mapElement);
                if (possibleMap && typeof possibleMap.eachLayer === 'function') {
                    map = possibleMap;
                    window._leaflet_map = map;
                }
            } catch(e) {}
        }
    }
    if (!map || typeof map.eachLayer !== 'function') {
        if (typeof L !== 'undefined' && L.Map) {
            try {
                for (let key in window) {
                    if (window[key] && window[key] instanceof L.Map) {
                        map = window[key];
                        window._leaflet_map = map;
                        break;
                    }
                }
            } catch(e) {}
        }
    }
    return map;
}

function handleMapClick(lat, lon, question) {
    stopTimer();
    const correctLat = question.correctLat;
    const correctLon = question.correctLon;

    const distance = calculateDistance(lat, lon, correctLat, correctLon);
    let pointsAwarded = 0;
    let message = '';
    let badgeType = 'error';

    if (distance <= 5) {
        pointsAwarded = 3;
        message = `Идеально! (${distance.toFixed(1)} км) +3 очка!`;
        badgeType = 'success';
    } else if (distance <= 15) {
        pointsAwarded = 2;
        message = `Хорошо! (${distance.toFixed(1)} км) +2 очка!`;
        badgeType = 'success';
    } else if (distance <= 30) {
        pointsAwarded = 1;
        message = `Близко (${distance.toFixed(1)} км) +1 очко!`;
        badgeType = 'success';
    } else {
        pointsAwarded = 0;
        message = `Мимо! (${distance.toFixed(1)} км от цели)`;
        badgeType = 'error';
    }

    score += pointsAwarded;
    clearMarkers();

    const map = getMapObject();
    if (window._clickBlocker) {
        try {
            if (window._clickHandler) {
                window._clickBlocker.off('click', window._clickHandler);
            }
            map.removeLayer(window._clickBlocker);
        } catch(e) {}
        window._clickBlocker = null;
        window._clickHandler = null;
    }

    const markerColor = pointsAwarded > 0 ? '#10B981' : '#EF4444';

    clickMarker = L.circleMarker([lat, lon], {
        radius: 9,
        color: markerColor,
        fillColor: markerColor,
        fillOpacity: 0.8,
        weight: 2
    }).addTo(map);

    resultMarker = L.circleMarker([correctLat, correctLon], {
        radius: 8,
        color: '#2563EB',
        fillColor: '#2563EB',
        fillOpacity: 0.5,
        weight: 2,
        dashArray: '4, 4'
    }).addTo(map);

    resultLine = L.polyline([[lat, lon], [correctLat, correctLon]], {
        color: markerColor,
        weight: 2.5,
        opacity: 0.8,
        dashArray: '5, 8'
    }).addTo(map);

    map.fitBounds([
        [Math.min(lat, correctLat) - 0.1, Math.min(lon, correctLon) - 0.1],
        [Math.max(lat, correctLat) + 0.1, Math.max(lon, correctLon) + 0.1]
    ]);

    showFeedback(message, badgeType);
    updateScore();

    setTimeout(() => {
        currentQuestion++;
        showQuestion();
    }, 2600);
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a =
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function showFeedback(message, type) {
    const container = document.getElementById('options-container');
    if (!container) return;
    const oldFeedback = document.getElementById('feedback');
    if (oldFeedback) oldFeedback.remove();

    const feedback = document.createElement('div');
    feedback.className = `feedback-box ${type}`;
    feedback.textContent = message;
    feedback.id = 'feedback';
    container.appendChild(feedback);
}

function showHint() {
    const question = quizData[currentQuestion];
    if (question && question.hint) {
        const ht = document.getElementById('hint-text');
        const hc = document.getElementById('hint-container');
        if (ht) ht.textContent = question.hint;
        if (hc) hc.style.display = 'block';
    }
}

function updateScore() {
    const scoreEl = document.getElementById('score');
    const accEl = document.getElementById('accuracy');
    if (scoreEl) scoreEl.textContent = score;
    const currentMax = currentQuiz === 'center' ? (currentQuestion + 1) * 3 : (currentQuestion + 1);
    const accuracy = currentMax > 0 ? Math.round((score / currentMax) * 100) : 0;
    if (accEl) accEl.textContent = `Эффективность: ${accuracy}%`;
}

function highlightDistrictOnMapByName(districtName) {
    let map = getMapObject();
    if (!map || typeof map.eachLayer !== 'function') {
        mapSearchAttempts++;
        if (mapSearchAttempts < MAX_MAP_SEARCH_ATTEMPTS) {
            setTimeout(() => highlightDistrictOnMapByName(districtName), 300);
        }
        return;
    }
    mapSearchAttempts = 0;

    resetActiveHighlight();

    let targetLayer = null;
    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.properties) {
            const props = layer.feature.properties;
            if (props.name === districtName || props.NAME === districtName ||
                props.Название === districtName || props.название === districtName) {
                targetLayer = layer;
            }
        }
    });

    if (targetLayer) {
        highlightedDistrictLayer = targetLayer;
        try {
            targetLayer.setStyle({
                color: '#F59E0B',
                weight: 4,
                fillColor: '#F59E0B',
                fillOpacity: 0.5,
                dashArray: null
            });
            map.fitBounds(targetLayer.getBounds(), {padding: [30, 30]});
        } catch(e) {}
    }
}

function highlightRiverOnMapByName(riverName) {
    let map = getMapObject();
    if (!map || typeof map.eachLayer !== 'function') return;

    resetActiveHighlight(true);

    let targetGroup = L.featureGroup();
    highlightedRiverLayers = [];

    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.properties) {
            const props = layer.feature.properties;
            const pName = props.name || props.NAME || props.Название || props.название || '';
            if (pName.trim() === riverName.trim()) {
                highlightedRiverLayers.push(layer);
                try {
                    layer.setStyle({
                        color: '#EF4444',
                        weight: 5,
                        opacity: 1.0
                    });
                    targetGroup.addLayer(layer);
                } catch(e) {}
            }
        }
    });

    if (highlightedRiverLayers.length > 0) {
        try {
            map.fitBounds(targetGroup.getBounds(), {padding: [40, 40]});
        } catch(e) {}
    }
}

function showDistrictInfoCard(districtName) {
    const district = EMBEDDED_NEIGHBORS.find(d => d.name === districtName);
    if (!district) return;

    const card = document.getElementById('district-info-card');
    if (!card) return;

    highlightDistrictOnMapByName(districtName);

    const neighborsHtml = district.neighbors && district.neighbors.length > 0 
        ? district.neighbors.map(n => `<span class="neighbor-tag" onclick="showDistrictInfoCard('${n}')">${n}</span>`).join('')
        : '<em>Нет данных</em>';

    const popFormatted = district.population 
        ? `${Number(district.population).toLocaleString('ru-RU')} чел.` 
        : 'Нет данных';

    card.innerHTML = `
        <div class="info-card-header">
            <strong>${district.name}</strong>
            <button onclick="closeInfoCard()" class="close-card-btn">&times;</button>
        </div>
        <div class="info-card-body">
            <div class="info-row"><span>Райцентр:</span><strong>${district.center}</strong></div>
            <div class="info-row"><span>Население:</span><strong>~${popFormatted}</strong></div>
            <div class="info-row"><span>Площадь:</span><strong>~${district.area} км²</strong></div>
            <div style="margin-top: 8px;">
                <span style="color: #64748B; font-size: 11px; font-weight: 600;">Граничит с районами:</span>
                <div style="margin-top: 4px; display: flex; flex-wrap: wrap;">${neighborsHtml}</div>
            </div>
        </div>
    `;
    card.style.display = 'block';
}

function closeInfoCard() {
    const card = document.getElementById('district-info-card');
    if (card) card.style.display = 'none';
    resetActiveHighlight();
}

function setupDistrictClickListeners() {
    const map = getMapObject();
    if (!map) {
        setTimeout(setupDistrictClickListeners, 500);
        return;
    }

    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.properties) {
            const props = layer.feature.properties;
            const name = props.name || props.NAME || props.Название || props.название;
            if (name && (props.adm_level || (layer.feature.geometry && layer.feature.geometry.type.includes('Polygon')))) {
                layer.on('click', function(e) {
                    if (currentQuiz === null) {
                        showDistrictInfoCard(name);
                    }
                });
            }
        }
    });
}

function showResults() {
    clearMarkers();
    resetActiveHighlight(true);
    resetMapView();
    restoreAllLayers();
    enablePopups();

    const qm = document.getElementById('quiz-mode');
    const rm = document.getElementById('results-mode');
    if (qm) qm.style.display = 'none';
    if (rm) rm.style.display = 'block';

    const accuracy = maxPossibleScore > 0 ? Math.round((score / maxPossibleScore) * 100) : 0;
    let message = '', emoji = '';
    if (accuracy >= 85) { message = 'Превосходно! Отличное пространственное знание области!'; emoji = '🏆'; }
    else if (accuracy >= 65) { message = 'Хорошо! Вы уверенно ориентируетесь на карте.'; emoji = '👍'; }
    else if (accuracy >= 45) { message = 'Удовлетворительно, рекомендуем повторить номенклатуру.'; emoji = '📚'; }
    else { message = 'Попробуйте ещё раз, практика даст результат!'; emoji = '💪'; }

    const studentInfo = getCurrentStudentInfo();
    const studentLine = studentInfo ? `<p style="margin: 4px 0; font-size: 13px; color: #0284C7;">Студент: <strong>${studentInfo.name}</strong> (${studentInfo.group})</p>` : '';

    const rc = document.getElementById('results-content');
    if (rc) {
        rc.innerHTML = `
            <div style="font-size: 42px; margin: 10px 0;">${emoji}</div>
            ${studentLine}
            <h3 style="margin: 6px 0; color: #1E293B;">${score} из ${maxPossibleScore} баллов</h3>
            <p style="margin: 4px 0; font-size: 13px; color: #475569;">Результативность: <strong>${accuracy}%</strong></p>
            <p style="margin-top: 6px; font-size: 12px; color: #64748B;">${message}</p>
        `;
    }
    saveResult(accuracy);
}

function saveResult(accuracy) {
    const student = getCurrentStudentInfo();
    let timeSec = Math.round((Date.now() - (quizStartTime || Date.now())) / 1000);
    let timeStr = `${Math.floor(timeSec / 60)} мин. ${timeSec % 60} сек.`;

    const results = JSON.parse(localStorage.getItem('rostovQuizResults') || '[]');
    results.push({
        date: new Date().toLocaleString(),
        student: student ? student.name : 'Анонимно',
        group: student ? student.group : '-',
        type: currentQuiz,
        score: score,
        maxScore: maxPossibleScore,
        accuracy: accuracy,
        time_spent: timeStr
    });
    localStorage.setItem('rostovQuizResults', JSON.stringify(results));

    if (student) {
        fetch('/api/results/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: student.email,
                name: student.name,
                group: student.group,
                quiz_type: currentQuiz,
                score: score,
                max_score: maxPossibleScore,
                accuracy: accuracy,
                time_spent: timeStr
            })
        }).catch(e => {});
    }
}

function showLeaderboard() {
    fetch('/api/results/leaderboard')
    .then(res => res.json())
    .then(data => {
        let html = '<div class="welcome-overlay"><div class="welcome-card" style="text-align: center;"><h3>🏆 Таблица лидеров ЮФУ</h3>';
        if (!data || data.length === 0) {
            html += '<p style="color: #64748B; font-size: 13px; margin: 20px 0;">Пока нет результатов. Станьте первыми!</p>';
        } else {
            html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px; margin: 15px 0;">';
            html += '<tr style="background: #F8FAFC; color: #475569;"><th style="padding: 6px; border: 1px solid #E2E8F0;">Студент</th><th style="padding: 6px; border: 1px solid #E2E8F0;">Группа</th><th style="padding: 6px; border: 1px solid #E2E8F0;">Тест</th><th style="padding: 6px; border: 1px solid #E2E8F0;">Баллы</th><th style="padding: 6px; border: 1px solid #E2E8F0;">%</th><th style="padding: 6px; border: 1px solid #E2E8F0;">Время</th></tr>';
            data.forEach(r => {
                html += `<tr><td style="padding: 6px; border: 1px solid #E2E8F0;">${r.name}</td><td style="padding: 6px; border: 1px solid #E2E8F0;">${r.group}</td><td style="padding: 6px; border: 1px solid #E2E8F0;">${r.quiz_type}</td><td style="padding: 6px; border: 1px solid #E2E8F0;"><b>${r.score}/${r.max_score}</b></td><td style="padding: 6px; border: 1px solid #E2E8F0;">${r.accuracy}%</td><td style="padding: 6px; border: 1px solid #E2E8F0;">${r.time_spent}</td></tr>`;
            });
            html += '</table>';
        }
        html += '<button onclick="closeLeaderboardModal()" class="btn-start" style="margin-top: 10px;">Закрыть</button></div></div>';
        
        let div = document.createElement('div');
        div.id = 'leaderboard-modal-container';
        div.innerHTML = html;
        document.body.appendChild(div);
    }).catch(e => alert('Не удалось загрузить таблицу лидеров с сервера'));
}

function closeLeaderboardModal() {
    let el = document.getElementById('leaderboard-modal-container');
    if (el) el.remove();
}

function exitQuiz() {
    if (confirm('Завершить викторину?')) {
        finishQuizDirectly();
    }
}

function finishQuizDirectly() {
    stopTimer();
    const map = getMapObject();
    if (map && window._clickBlocker) {
        try {
            if (window._clickHandler) {
                window._clickBlocker.off('click', window._clickHandler);
            }
            map.removeLayer(window._clickBlocker);
        } catch(e) {}
        window._clickBlocker = null;
        window._clickHandler = null;
    }
    clearMarkers();
    enablePopups();
    resetActiveHighlight(false);
    restoreAllLayers();
    resetMapView();

    resetQuiz();
    const qm = document.getElementById('quiz-mode');
    const rm = document.getElementById('results-mode');
    const nm = document.getElementById('normal-mode');
    if (qm) qm.style.display = 'none';
    if (rm) rm.style.display = 'none';
    if (nm) nm.style.display = 'block';
}

function restartQuiz() {
    resetQuiz();
    resetActiveHighlight(false);
    const rm = document.getElementById('results-mode');
    const qm = document.getElementById('quiz-mode');
    if (rm) rm.style.display = 'none';
    if (qm) qm.style.display = 'block';
    if (currentQuiz === 'district') {
        setQuizLayers('district');
        loadDistrictQuiz();
    } else if (currentQuiz === 'neighbor') {
        setQuizLayers('neighbor');
        loadNeighborQuiz();
    } else if (currentQuiz === 'river') {
        restoreAllRiverStyles();
        setQuizLayers('river');
        loadRiverQuiz();
    } else {
        setQuizLayers('center');
        loadCenterQuiz();
    }
}

function resetQuiz() {
    stopTimer();
    currentQuestion = 0;
    score = 0;
    maxPossibleScore = 0;
    quizData = [];
    selectedOption = null;
    updateScore();
    clearMarkers();
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function closeWelcomeModal() {
    const modal = document.getElementById('welcome-modal');
    if (modal) {
        modal.classList.add('fade-out');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 250);
    }
    const dontShow = document.getElementById('dont-show-welcome');
    if (dontShow && dontShow.checked) {
        localStorage.setItem('rostovMapHideWelcome', 'true');
    }
}

function openWelcomeModal() {
    const modal = document.getElementById('welcome-modal');
    if (modal) {
        modal.classList.remove('fade-out');
        modal.style.display = 'flex';
    }
}

function openAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
    resetAuthForms();
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
}

function resetAuthForms() {
    document.getElementById('auth-step-1').style.display = 'block';
    document.getElementById('auth-step-2').style.display = 'none';
    document.getElementById('auth-error').style.display = 'none';
    document.getElementById('auth-code-input').value = '';
}

async function requestSfeduCode() {
    const email = document.getElementById('auth-email').value.trim();
    const name = document.getElementById('auth-name').value.trim();
    const group = document.getElementById('auth-group').value.trim();
    const errBox = document.getElementById('auth-error');

    if (!email || !name || !group) {
        showAuthError('Заполните все поля');
        return;
    }

    if (!email.toLowerCase().endsWith('@sfedu.ru') && !email.toLowerCase().endsWith('.sfedu.ru')) {
        showAuthError('Разрешены только адреса @sfedu.ru');
        return;
    }

    try {
        const res = await fetch('/api/auth/send-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, full_name: name, group_num: group })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка отправки');

        document.getElementById('auth-step-1').style.display = 'none';
        document.getElementById('auth-step-2').style.display = 'block';
        document.getElementById('auth-target-email').textContent = email;
        errBox.style.display = 'none';
    } catch(e) {
        showAuthError(e.message);
    }
}

async function verifySfeduCode() {
    const email = document.getElementById('auth-email').value.trim();
    const code = document.getElementById('auth-code-input').value.trim();

    if (!code || code.length !== 6) {
        showAuthError('Введите 6-значный код');
        return;
    }

    try {
        const res = await fetch('/api/auth/verify-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, code })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Неверный код');

        localStorage.setItem('sfeduStudent', JSON.stringify(data.user));
        updateStudentHeader();
        closeAuthModal();
    } catch(e) {
        showAuthError(e.message);
    }
}

function showAuthError(msg) {
    const errBox = document.getElementById('auth-error');
    errBox.textContent = msg;
    errBox.style.display = 'block';
}

function logoutStudent() {
    if (confirm('Выйти из профиля студента ЮФУ?')) {
        localStorage.removeItem('sfeduStudent');
        updateStudentHeader();
    }
}

function getCurrentStudentInfo() {
    try {
        const raw = localStorage.getItem('sfeduStudent');
        return raw ? JSON.parse(raw) : null;
    } catch(e) {
        return null;
    }
}

function updateStudentHeader() {
    const student = getCurrentStudentInfo();
    const authBtn = document.getElementById('auth-top-btn');
    const profileBox = document.getElementById('student-profile-badge');

    if (student) {
        if (authBtn) authBtn.style.display = 'none';
        if (profileBox) {
            profileBox.style.display = 'flex';
            document.getElementById('student-badge-name').textContent = student.name;
            document.getElementById('student-badge-group').textContent = `${student.group} | ЮФУ`;
        }
    } else {
        if (authBtn) authBtn.style.display = 'flex';
        if (profileBox) profileBox.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(setupDistrictClickListeners, 1000);
    updateStudentHeader();
    if (!localStorage.getItem('rostovMapHideWelcome')) {
        setTimeout(openWelcomeModal, 400);
    }
});
