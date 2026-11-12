var _root = typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this);

var QUESTION_TIME_LIMIT = 20;

class ExamProctorClass {
    #violations = 0;
    #isActive = false;
    #isExam = false;
    #status = 'passed';
    #token = '';
    #category = 'mixed';
    #questionCount = 15;
    #timeLimitMinutes = 10;
    #timeRemaining = 600;
    #globalTimer = null;
    #blurCooldown = false;
    #syncSessionId = null;
    #syncGroupName = null;
    #syncRemainingSec = null;
    #syncHeartbeatTimer = null;
    #syncTeacherId = null;

    get isExam() { return this.#isExam; }
    set isExam(v) { this.#isExam = Boolean(v); }

    get active() { return this.#isActive; }
    enable() { this.#isActive = true; }
    disable() { this.#isActive = false; }

    get violations() { return this.#violations; }
    recordViolation() {
        this.#violations++;
        if (this.#violations >= 2) {
            this.#status = 'cheating_detected';
        } else if (this.#violations === 1) {
            this.#status = 'warning';
        }
        return this.#violations;
    }

    resetViolations(force = false) {
        if (force || !this.#isExam) {
            this.#violations = 0;
            this.#status = 'passed';
        }
    }

    get status() { return this.#status; }
    set status(v) { this.#status = String(v || 'passed'); }

    get token() { return this.#token; }
    set token(v) { this.#token = String(v || ''); }

    get category() { return this.#category; }
    set category(v) { this.#category = v; }

    get questionCount() { return this.#questionCount; }
    set questionCount(v) { this.#questionCount = Number(v) || 15; }

    get timeLimitMinutes() { return this.#timeLimitMinutes; }
    set timeLimitMinutes(v) { this.#timeLimitMinutes = Number(v) || 10; }

    get timeRemaining() { return this.#timeRemaining; }
    set timeRemaining(v) { this.#timeRemaining = Number(v); }

    get globalTimer() { return this.#globalTimer; }
    set globalTimer(v) { this.#globalTimer = v; }

    get blurCooldown() { return this.#blurCooldown; }
    set blurCooldown(v) { this.#blurCooldown = Boolean(v); }

    get syncSessionId() { return this.#syncSessionId; }
    set syncSessionId(v) { this.#syncSessionId = v; }

    get syncGroupName() { return this.#syncGroupName; }
    set syncGroupName(v) { this.#syncGroupName = v; }

    get syncRemainingSec() { return this.#syncRemainingSec; }
    set syncRemainingSec(v) { this.#syncRemainingSec = v; }

    get syncHeartbeatTimer() { return this.#syncHeartbeatTimer; }
    set syncHeartbeatTimer(v) { this.#syncHeartbeatTimer = v; }

    get syncTeacherId() { return this.#syncTeacherId; }
    set syncTeacherId(v) { this.#syncTeacherId = v; }

    reset() {
        this.#isExam = false;
        this.#isActive = false;
        this.#violations = 0;
        this.#status = 'passed';
        this.#token = '';
        this.#globalTimer = null;
        this.#blurCooldown = false;
        this.#syncTeacherId = null;
    }
}

class QuizManagerClass {
    constructor() {
        this.currentQuiz = null;
        this.currentQuestion = 0;
        this.score = 0;
        this.maxPossibleScore = 0;
        this.totalQuestions = 10;
        this.quizData = [];
        this.selectedOption = null;
        this.clickMarker = null;
        this.resultMarker = null;
        this.resultLine = null;
        this.popupsDisabled = false;
        this.highlightedDistrictLayer = null;
        this.highlightedRiverLayers = [];
        this.timerEnabled = false;
        this.questionTimer = null;
        this.timeLeft = QUESTION_TIME_LIMIT;
        this.quizStartTime = 0;
        this.studyCategory = 'districts';
        this.studyQueue = [];
        this.studyIndex = 0;
        this.studyCenterMarker = null;
        this.currentSessionMistakes = [];
        this.currentSessionMistakesDetails = [];
    }

    reset() {
        this.currentSessionMistakes = [];
        this.currentSessionMistakesDetails = [];
        this.currentQuiz = null;
        this.currentQuestion = 0;
        this.score = 0;
        this.maxPossibleScore = 0;
        this.selectedOption = null;
        this.clickMarker = null;
        this.resultMarker = null;
        this.resultLine = null;
        this.popupsDisabled = false;
        this.highlightedDistrictLayer = null;
        this.highlightedRiverLayers = [];
        this.timeLeft = QUESTION_TIME_LIMIT;
    }
}

class PuzzleEngineClass {
    constructor() {
        this.isPuzzleMode = false;
        this.districts = [];
        this.unplacedQueue = [];
        this.activePiece = null;
        this.anchorDistrict = null;
        this.placedDistricts = new Set();
        this.slotLayers = {};
        this.placedMarkers = [];
        this.outlineLayer = null;
        this.timerInterval = null;
        this.startTime = 0;
        this.mistakes = 0;
        this.hintsUsed = 0;
        this.token = '';
        this.savedLayerStyles = [];
    }

    reset() {
        this.isPuzzleMode = false;
        this.districts = [];
        this.unplacedQueue = [];
        this.activePiece = null;
        this.anchorDistrict = null;
        this.placedDistricts.clear();
        this.slotLayers = {};
        this.placedMarkers = [];
        this.outlineLayer = null;
        this.timerInterval = null;
        this.mistakes = 0;
        this.hintsUsed = 0;
        this.token = '';
    }
}

var ExamProctor = _root.ExamProctor || new ExamProctorClass();
var QuizManager = _root.QuizManager || new QuizManagerClass();
var PuzzleEngine = _root.PuzzleEngine || new PuzzleEngineClass();

_root.ExamProctor = ExamProctor;
_root.QuizManager = QuizManager;
_root.PuzzleEngine = PuzzleEngine;

Object.defineProperty(_root, 'currentQuiz', { get() { return QuizManager.currentQuiz; }, set(v) { QuizManager.currentQuiz = v; }, configurable: true });
Object.defineProperty(_root, 'currentQuestion', { get() { return QuizManager.currentQuestion; }, set(v) { QuizManager.currentQuestion = v; }, configurable: true });
Object.defineProperty(_root, 'score', { get() { return QuizManager.score; }, set(v) { QuizManager.score = v; }, configurable: true });
Object.defineProperty(_root, 'maxPossibleScore', { get() { return QuizManager.maxPossibleScore; }, set(v) { QuizManager.maxPossibleScore = v; }, configurable: true });
Object.defineProperty(_root, 'totalQuestions', { get() { return QuizManager.totalQuestions; }, set(v) { QuizManager.totalQuestions = v; }, configurable: true });
Object.defineProperty(_root, 'quizData', { get() { return QuizManager.quizData; }, set(v) { QuizManager.quizData = v; }, configurable: true });
Object.defineProperty(_root, 'selectedOption', { get() { return QuizManager.selectedOption; }, set(v) { QuizManager.selectedOption = v; }, configurable: true });
Object.defineProperty(_root, 'clickMarker', { get() { return QuizManager.clickMarker; }, set(v) { QuizManager.clickMarker = v; }, configurable: true });
Object.defineProperty(_root, 'resultMarker', { get() { return QuizManager.resultMarker; }, set(v) { QuizManager.resultMarker = v; }, configurable: true });
Object.defineProperty(_root, 'resultLine', { get() { return QuizManager.resultLine; }, set(v) { QuizManager.resultLine = v; }, configurable: true });
Object.defineProperty(_root, 'popupsDisabled', { get() { return QuizManager.popupsDisabled; }, set(v) { QuizManager.popupsDisabled = v; }, configurable: true });
Object.defineProperty(_root, 'highlightedDistrictLayer', { get() { return QuizManager.highlightedDistrictLayer; }, set(v) { QuizManager.highlightedDistrictLayer = v; }, configurable: true });
Object.defineProperty(_root, 'highlightedRiverLayers', { get() { return QuizManager.highlightedRiverLayers; }, set(v) { QuizManager.highlightedRiverLayers = v; }, configurable: true });
Object.defineProperty(_root, 'timerEnabled', { get() { return QuizManager.timerEnabled; }, set(v) { QuizManager.timerEnabled = v; }, configurable: true });
Object.defineProperty(_root, 'questionTimer', { get() { return QuizManager.questionTimer; }, set(v) { QuizManager.questionTimer = v; }, configurable: true });
Object.defineProperty(_root, 'timeLeft', { get() { return QuizManager.timeLeft; }, set(v) { QuizManager.timeLeft = v; }, configurable: true });
Object.defineProperty(_root, 'quizStartTime', { get() { return QuizManager.quizStartTime; }, set(v) { QuizManager.quizStartTime = v; }, configurable: true });
Object.defineProperty(_root, 'studyCategory', { get() { return QuizManager.studyCategory; }, set(v) { QuizManager.studyCategory = v; }, configurable: true });
Object.defineProperty(_root, 'studyQueue', { get() { return QuizManager.studyQueue; }, set(v) { QuizManager.studyQueue = v; }, configurable: true });
Object.defineProperty(_root, 'studyIndex', { get() { return QuizManager.studyIndex; }, set(v) { QuizManager.studyIndex = v; }, configurable: true });
Object.defineProperty(_root, 'studyCenterMarker', { get() { return QuizManager.studyCenterMarker; }, set(v) { QuizManager.studyCenterMarker = v; }, configurable: true });
Object.defineProperty(_root, 'currentSessionMistakes', { get() { return QuizManager.currentSessionMistakes; }, set(v) { QuizManager.currentSessionMistakes = v; }, configurable: true });
Object.defineProperty(_root, 'currentSessionMistakesDetails', { get() { return QuizManager.currentSessionMistakesDetails; }, set(v) { QuizManager.currentSessionMistakesDetails = v; }, configurable: true });

Object.defineProperty(_root, 'isExamMode', { get() { return ExamProctor.isExam; }, set(v) { ExamProctor.isExam = Boolean(v); }, configurable: true });
Object.defineProperty(_root, 'examCategory', { get() { return ExamProctor.category; }, set(v) { ExamProctor.category = v; }, configurable: true });
Object.defineProperty(_root, 'examQuestionCount', { get() { return ExamProctor.questionCount; }, set(v) { ExamProctor.questionCount = v; }, configurable: true });
Object.defineProperty(_root, 'examTimeLimitMinutes', { get() { return ExamProctor.timeLimitMinutes; }, set(v) { ExamProctor.timeLimitMinutes = v; }, configurable: true });
Object.defineProperty(_root, 'examTimeRemaining', { get() { return ExamProctor.timeRemaining; }, set(v) { ExamProctor.timeRemaining = v; }, configurable: true });
Object.defineProperty(_root, 'examGlobalTimer', { get() { return ExamProctor.globalTimer; }, set(v) { ExamProctor.globalTimer = v; }, configurable: true });
Object.defineProperty(_root, 'examCheatingViolations', {
    get() { return ExamProctor.violations; },
    set(v) {
        if (v === 0 && !ExamProctor.isExam) {
            ExamProctor.resetViolations();
        }
    },
    configurable: true
});
Object.defineProperty(_root, 'examStatus', { get() { return ExamProctor.status; }, set(v) { ExamProctor.status = v; }, configurable: true });
Object.defineProperty(_root, 'examToken', { get() { return ExamProctor.token; }, set(v) { ExamProctor.token = v; }, configurable: true });
Object.defineProperty(_root, 'antiCheatActive', {
    get() { return ExamProctor.active; },
    set(v) { if (v) ExamProctor.enable(); else ExamProctor.disable(); },
    configurable: true
});
Object.defineProperty(_root, 'blurCooldown', { get() { return ExamProctor.blurCooldown; }, set(v) { ExamProctor.blurCooldown = v; }, configurable: true });
Object.defineProperty(_root, 'currentSyncSessionId', { get() { return ExamProctor.syncSessionId; }, set(v) { ExamProctor.syncSessionId = v; }, configurable: true });
Object.defineProperty(_root, 'currentSyncGroupName', { get() { return ExamProctor.syncGroupName; }, set(v) { ExamProctor.syncGroupName = v; }, configurable: true });
Object.defineProperty(_root, 'currentSyncTeacherId', { get() { return ExamProctor.syncTeacherId; }, set(v) { ExamProctor.syncTeacherId = v; }, configurable: true });
Object.defineProperty(_root, 'syncExamRemainingSec', { get() { return ExamProctor.syncRemainingSec; }, set(v) { ExamProctor.syncRemainingSec = v; }, configurable: true });
Object.defineProperty(_root, 'syncSessionHeartbeatTimer', { get() { return ExamProctor.syncHeartbeatTimer; }, set(v) { ExamProctor.syncHeartbeatTimer = v; }, configurable: true });

Object.defineProperty(_root, 'isPuzzleMode', { get() { return PuzzleEngine.isPuzzleMode; }, set(v) { PuzzleEngine.isPuzzleMode = Boolean(v); }, configurable: true });
Object.defineProperty(_root, 'puzzleDistricts', { get() { return PuzzleEngine.districts; }, set(v) { PuzzleEngine.districts = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleUnplacedQueue', { get() { return PuzzleEngine.unplacedQueue; }, set(v) { PuzzleEngine.unplacedQueue = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleActivePiece', { get() { return PuzzleEngine.activePiece; }, set(v) { PuzzleEngine.activePiece = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleAnchorDistrict', { get() { return PuzzleEngine.anchorDistrict; }, set(v) { PuzzleEngine.anchorDistrict = v; }, configurable: true });
Object.defineProperty(_root, 'puzzlePlacedDistricts', { get() { return PuzzleEngine.placedDistricts; }, set(v) { PuzzleEngine.placedDistricts = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleSlotLayers', { get() { return PuzzleEngine.slotLayers; }, set(v) { PuzzleEngine.slotLayers = v; }, configurable: true });
Object.defineProperty(_root, 'puzzlePlacedMarkers', { get() { return PuzzleEngine.placedMarkers; }, set(v) { PuzzleEngine.placedMarkers = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleOutlineLayer', { get() { return PuzzleEngine.outlineLayer; }, set(v) { PuzzleEngine.outlineLayer = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleTimerInterval', { get() { return PuzzleEngine.timerInterval; }, set(v) { PuzzleEngine.timerInterval = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleStartTime', { get() { return PuzzleEngine.startTime; }, set(v) { PuzzleEngine.startTime = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleMistakes', { get() { return PuzzleEngine.mistakes; }, set(v) { PuzzleEngine.mistakes = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleHintsUsed', { get() { return PuzzleEngine.hintsUsed; }, set(v) { PuzzleEngine.hintsUsed = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleToken', { get() { return PuzzleEngine.token; }, set(v) { PuzzleEngine.token = v; }, configurable: true });
Object.defineProperty(_root, 'puzzleSavedLayerStyles', { get() { return PuzzleEngine.savedLayerStyles; }, set(v) { PuzzleEngine.savedLayerStyles = v; }, configurable: true });

var PUZZLE_PALETTE = [
    '#38BDF8', '#34D399', '#F472B6', '#A78BFA',
    '#FBBF24', '#60A5FA', '#4ADE80', '#FB7185',
    '#818CF8', '#F59E0B', '#2DD4BF', '#C084FC',
    '#E879F9', '#22C55E', '#38BDF8', '#FB923C'
];

function getPuzzlePieceColor(index) {
    return PUZZLE_PALETTE[index % PUZZLE_PALETTE.length];
}

function getDistrictsData() {
    return window._dynamicDistricts || (typeof EMBEDDED_DISTRICTS !== 'undefined' ? EMBEDDED_DISTRICTS : []);
}
function getRiversData() {
    return window._dynamicRivers || (typeof EMBEDDED_RIVERS !== 'undefined' ? EMBEDDED_RIVERS : []);
}
function getCentersData() {
    return window._dynamicCenters || (typeof EMBEDDED_CENTERS !== 'undefined' ? EMBEDDED_CENTERS : []);
}
function getNeighborsData() {
    return window._dynamicNeighbors || (typeof EMBEDDED_NEIGHBORS !== 'undefined' ? EMBEDDED_NEIGHBORS : []);
}
function getPuzzleData() {
    return window._dynamicPuzzleData || (typeof EMBEDDED_PUZZLE_DATA !== 'undefined' ? EMBEDDED_PUZZLE_DATA : []);
}
function getRegionOutlineData() {
    return window._dynamicOutline || (typeof REGION_OUTLINE_GEOJSON !== 'undefined' ? REGION_OUTLINE_GEOJSON : null);
}
function getRegionBoundsData() {
    return window._dynamicBounds || (typeof REGION_BOUNDS !== 'undefined' ? REGION_BOUNDS : null);
}

function initServerRegionContext() {
    let ctx = null;
    if (typeof window !== 'undefined' && window.SERVER_REGION_CONTEXT && typeof window.SERVER_REGION_CONTEXT === 'object') {
        ctx = Object.assign({}, window.SERVER_REGION_CONTEXT);
    } else if (typeof document !== 'undefined') {
        const scriptEl = document.getElementById('server-region-context');
        if (scriptEl && scriptEl.textContent) {
            try {
                ctx = JSON.parse(scriptEl.textContent);
            } catch (e) {}
        }
    }

    if (typeof document !== 'undefined' && document.body && document.body.dataset) {
        const ds = document.body.dataset;
        if (ds.region) {
            ctx = ctx || {};
            ctx.region = ctx.region || ds.region;
            ctx.title = ctx.title || ds.regionTitle;
            if (ds.centerLat && ds.centerLng) {
                ctx.center = ctx.center || [parseFloat(ds.centerLat), parseFloat(ds.centerLng)];
            }
            if (ds.zoom) {
                ctx.zoom = ctx.zoom || parseInt(ds.zoom, 10);
            }
            if (ds.mapUrl) {
                ctx.map_url = ctx.map_url || ds.mapUrl;
            }
        }
    }

    if (ctx && ctx.region) {
        const cleanKey = resolveRegionKey(ctx.region);
        window.SERVER_REGION_CONTEXT = ctx;
        window.currentRegionKey = cleanKey;
        window.currentRegionTitle = ctx.title || getRegionName(cleanKey);
        if (ctx.center) window.serverMapCenter = ctx.center;
        if (ctx.zoom) window.serverMapZoom = ctx.zoom;
        return ctx;
    }
    return null;
}
window.initServerRegionContext = initServerRegionContext;
try { initServerRegionContext(); } catch(e) {}

function resolveRegionKey(raw) {
    let s = raw;
    if (!s) {
        if (typeof window !== 'undefined' && window.SERVER_REGION_CONTEXT && window.SERVER_REGION_CONTEXT.region) {
            s = window.SERVER_REGION_CONTEXT.region;
        } else if (typeof document !== 'undefined' && document.body && document.body.dataset && document.body.dataset.region) {
            s = document.body.dataset.region;
        } else if (typeof window !== 'undefined' && window.currentRegionKey) {
            return window.currentRegionKey;
        }
        if (!s) {
            try {
                const params = new URLSearchParams(window.location.search);
                s = params.get('region') || params.get('map') || '';
            } catch (e) {}
        }
        if (!s && typeof window !== 'undefined' && window.location && window.location.pathname) {
            const pathParts = window.location.pathname.split('/');
            const pageName = (pathParts.pop() || '').toLowerCase();
            if (pageName && pageName !== 'index.html' && pageName !== 'admin.html') {
                s = pageName;
            }
        }
    }
    if (!s) return 'rostov';

    s = String(s).toLowerCase().trim()
        .replace(/_quiz_map\.html$/, '')
        .replace(/\.html$/, '');

    if (s.includes('krasnodar') || s.includes('краснодар')) return 'krasnodar';
    if (s.includes('adygey') || s.includes('адыге')) return 'adygey';
    if (s.includes('volgograd') || s.includes('волгоград')) return 'volgograd';
    if (s.includes('astrakhan') || s.includes('астрахан')) return 'astrakhan';
    if (s.includes('stavropol') || s.includes('ставропол')) return 'stavropol';
    if (s.includes('russia') || s.includes('росси')) return 'russia';
    if (s.includes('dagestan') || s.includes('дагестан')) return 'dagestan';
    if (s.includes('chechnya') || s.includes('чеч')) return 'chechnya';
    if (s.includes('crimea') || s.includes('крым')) return 'crimea';
    if (s.includes('rostov') || s.includes('ростов')) return 'rostov';

    const clean = s.replace(/[^a-z0-9_]/gi, '');
    return clean || 'rostov';
}

function getRegionName(key) {
    const k = resolveRegionKey(key);
    const names = {
        'rostov': 'Ростовская область',
        'krasnodar': 'Краснодарский край',
        'adygey': 'Республика Адыгея',
        'volgograd': 'Волгоградская область',
        'astrakhan': 'Астраханская область',
        'stavropol': 'Ставропольский край',
        'russia': 'Российская Федерация',
        'dagestan': 'Республика Дагестан',
        'chechnya': 'Чеченская Республика',
        'crimea': 'Республика Крым'
    };
    return names[k] || (k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, ' '));
}

function getResultsStorageKey() {
    const reg = window.currentRegionKey || resolveRegionKey(window.location.pathname) || 'rostov';
    return `${reg}_quiz_results`;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function loadRegionData(regionKey) {
    if (!regionKey) return false;
    const resolved = resolveRegionKey(regionKey);
    window.currentRegionKey = resolved;

    const currentFile = (window.location.pathname || '').split('/').pop() || '';
    const targetMapFile = `${resolved}_quiz_map.html`;

        if ((currentFile === targetMapFile || currentFile.includes(resolved)) && typeof EMBEDDED_DISTRICTS !== 'undefined') {
        window._dynamicDistricts = EMBEDDED_DISTRICTS;
        if (typeof EMBEDDED_CENTERS !== 'undefined') window._dynamicCenters = EMBEDDED_CENTERS;
        if (typeof EMBEDDED_NEIGHBORS !== 'undefined') window._dynamicNeighbors = EMBEDDED_NEIGHBORS;
        if (typeof EMBEDDED_RIVERS !== 'undefined') window._dynamicRivers = EMBEDDED_RIVERS;
        if (typeof EMBEDDED_PUZZLE_DATA !== 'undefined') window._dynamicPuzzleData = EMBEDDED_PUZZLE_DATA;
        if (typeof REGION_OUTLINE_GEOJSON !== 'undefined') window._dynamicOutline = REGION_OUTLINE_GEOJSON;
        if (typeof REGION_BOUNDS !== 'undefined') window._dynamicBounds = REGION_BOUNDS;
        return true;
    }

    try {
        const res = await fetch(`/api/region/${resolved}/data`);
        if (res.ok) {
            const data = await res.json();
            if (data && data.status === 'ok') {
                applyRegionDataset(data);
                return true;
            }
        }
    } catch (e) {
        console.warn('API /api/region/ data недоступен, выполняем локальный fallback', e);
    }

        if (currentFile && currentFile !== targetMapFile && !currentFile.includes(resolved)) {
        const search = window.location.search;
        window.location.href = `${targetMapFile}${search}`;
        return true;
    }
    return false;
}

function applyRegionDataset(data) {
    if (!data) return;
    if (data.bounds) window._dynamicBounds = data.bounds;
    if (data.districts) window._dynamicDistricts = data.districts;
    if (data.centers) window._dynamicCenters = data.centers;
    if (data.neighbors) window._dynamicNeighbors = data.neighbors;
    if (data.rivers) window._dynamicRivers = data.rivers;
    if (data.puzzle_data) window._dynamicPuzzleData = data.puzzle_data;
    if (data.outline_geojson) window._dynamicOutline = data.outline_geojson;

    const map = getMapObject();
    if (!map) return;

    if (window._dynamicBounds) {
        try {
            map.fitBounds(window._dynamicBounds, { padding: [20, 20] });
        } catch (e) {}
    }

        if (typeof L !== 'undefined' && data.puzzle_data && Array.isArray(data.puzzle_data)) {
        if (!window._dynamicRegionLayerGroup) {
            window._dynamicRegionLayerGroup = L.layerGroup().addTo(map);
        } else {
            window._dynamicRegionLayerGroup.clearLayers();
        }

        if (data.outline_geojson) {
            try {
                L.geoJSON(data.outline_geojson, {
                    style: {
                        color: '#3B82F6',
                        weight: 3,
                        opacity: 0.9,
                        fillColor: '#60A5FA',
                        fillOpacity: 0.05
                    }
                }).addTo(window._dynamicRegionLayerGroup);
            } catch (e) {}
        }

        data.puzzle_data.forEach(item => {
            if (item && item.geojson) {
                try {
                    const l = L.geoJSON(item.geojson, {
                        style: {
                            color: '#2E8B57',
                            weight: 2,
                            fillColor: '#90EE90',
                            fillOpacity: 0.25,
                            dashArray: '5, 5'
                        }
                    });
                    l.eachLayer(subLayer => {
                        subLayer.feature = {
                            type: 'Feature',
                            properties: {
                                is_district_layer: 1,
                                display_name: item.name,
                                NAME_RU: item.name,
                                NAME_1: item.name,
                                NAME: item.name
                            },
                            geometry: item.geojson
                        };
                        subLayer.on('click', () => {
                            if (currentQuiz === null) {
                                showDistrictInfoCard(item.name);
                            }
                        });
                    });
                    l.addTo(window._dynamicRegionLayerGroup);
                } catch (e) {}
            }
        });
    }
}

function ensureExamKioskTopBar(opts = {}) {
    const student = getCurrentStudentInfo();
    const groupName = opts.groupName || currentSyncGroupName || (student ? student.group : '') || 'ВКР ЮФУ';
    const studentName = (student && student.name) ? student.name : 'Студент';

        const oldBar = document.getElementById('exam-kiosk-top-bar');
    if (oldBar) oldBar.remove();

    const oldBanner = document.getElementById('sync-exam-top-banner');
    if (oldBanner) oldBanner.style.display = 'none';

        let sidebarHeader = document.getElementById('exam-sidebar-header');
    if (!sidebarHeader) {
        const quizControls = document.getElementById('quiz-controls');
        if (quizControls) {
            sidebarHeader = document.createElement('div');
            sidebarHeader.id = 'exam-sidebar-header';
            sidebarHeader.className = 'exam-sidebar-bar';
            quizControls.prepend(sidebarHeader);
        }
    }

    const safeSec = Math.max(0, examTimeRemaining);
    const mins = Math.floor(safeSec / 60);
    const secs = safeSec % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    if (sidebarHeader) {
        sidebarHeader.innerHTML = `
            <div class="exam-sidebar-top">
                <div class="exam-sidebar-status">
                    <span class="exam-sidebar-dot"></span>
                    <span class="exam-sidebar-title">🛡️ ЭКЗАМЕН • ANTI-CHEAT</span>
                </div>
                <div class="exam-sidebar-timer-box">
                    <span style="font-size: 13px;">⏳</span>
                    <span id="exam-sidebar-timer" class="exam-sidebar-timer-text">${timeStr}</span>
                </div>
            </div>
            <div class="exam-sidebar-meta">
                <div class="exam-sidebar-student">Студент: <b id="exam-sidebar-student-name">${escapeHtml(studentName)}</b></div>
                <div class="exam-sidebar-group">Группа: <b id="exam-sidebar-group-name">${escapeHtml(groupName)}</b></div>
            </div>
            <div class="timer-track" style="margin-top: 8px;">
                <div id="timer-bar"></div>
            </div>
        `;
        sidebarHeader.style.display = 'block';
    }

    _cachedTimerElements = null;
}

function removeExamKioskTopBar() {
    const oldBar = document.getElementById('exam-kiosk-top-bar');
    if (oldBar) oldBar.remove();

    const sidebarHeader = document.getElementById('exam-sidebar-header');
    if (sidebarHeader) sidebarHeader.style.display = 'none';

    const oldBanner = document.getElementById('sync-exam-top-banner');
    if (oldBanner) oldBanner.style.display = 'none';

    _cachedTimerElements = null;
}

async function initExamMode(options = {}) {
    currentSessionMistakes = [];
    currentSessionMistakesDetails = [];
    initServerRegionContext();
    const urlParams = new URLSearchParams(window.location.search);

    const regionParam = options.region || options.regionKey || options.regionName || options.region_name || 
                        urlParams.get('region') || urlParams.get('map') || 
                        (window.SERVER_REGION_CONTEXT && (window.SERVER_REGION_CONTEXT.region || window.SERVER_REGION_CONTEXT.title)) ||
                        (typeof document !== 'undefined' && document.body && document.body.dataset && document.body.dataset.region) ||
                        (options.session && (options.session.regionName || options.session.region_name || options.session.mapUrl || options.session.map_url)) ||
                        window.currentRegionKey ||
                        '';

    const targetRegion = resolveRegionKey(regionParam);
    window.currentRegionKey = targetRegion;

    const mode = options.mode || options.category || urlParams.get('mode') || 'mixed';
    const count = options.count || parseInt(urlParams.get('limit') || '15', 10);
    const timeLimit = options.timeLimit || parseInt(urlParams.get('time') || '10', 10);
    const sessionId = options.sessionId || urlParams.get('session_id') || '';
    const groupName = options.groupName || (options.session && (options.session.group_name || options.session.groupName)) || urlParams.get('group') || '';

    if (targetRegion) {
        await loadRegionData(targetRegion);
    }

    document.body.classList.add('exam-mode');
    ensureExamKioskTopBar({
        region: targetRegion,
        groupName: groupName,
        timeLimit: timeLimit,
        category: mode
    });

    startSelectedTestMode(mode, {
        isExam: true,
        count: count,
        timeLimit: timeLimit,
        sessionId: sessionId,
        groupName: groupName,
        region: targetRegion
    });
}
window.initExamMode = initExamMode;

function getMapObject() {
    if (window._leaflet_map) return window._leaflet_map;
    for (let key in window) {
        if (window[key] && window[key]._layers && typeof window[key].eachLayer === 'function') {
            window._leaflet_map = window[key];
            return window._leaflet_map;
        }
    }
    return null;
}

function setBasemapVisible(isVisible) {
    const tilePane = document.querySelector('.leaflet-tile-pane');
    if (tilePane) {
        tilePane.style.visibility = isVisible ? 'visible' : 'hidden';
    }
}

function togglePanelCollapse() {
    const panel = document.getElementById('quiz-controls');
    const btn = document.getElementById('panel-collapse-btn');
    if (!panel) return;
    const isCollapsed = panel.classList.toggle('collapsed');
    document.body.classList.toggle('ui-collapsed', isCollapsed);
    if (btn) {
        btn.setAttribute('aria-expanded', (!isCollapsed).toString());
        btn.title = isCollapsed ? 'Развернуть панель атласа' : 'Свернуть панель к карте';
    }
    // Триггерим ресайз Leaflet чтобы контролы встали правильно
    const map = getMapObject();
    if (map) setTimeout(() => map.invalidateSize(), 320);
}

// Инициализация свайпа по ручке и заголовку
function setupMobileBottomSheetSwipe() {
    const panel = document.getElementById('quiz-controls');
    const header = panel ? panel.querySelector('.panel-header') : null;
    if (!panel || !header) return;
    if (header._swipeBound) return;
    header._swipeBound = true;

    let startY = 0;
    let startTime = 0;
    let isDragging = false;

    function onDown(e) {
        if (window.innerWidth > 1023) return;
        const touch = e.touches ? e.touches[0] : e;
        startY = touch.clientY;
        startTime = Date.now();
        isDragging = true;
    }

    function onMove(e) {
        if (!isDragging) return;
        const touch = e.touches ? e.touches[0] : e;
        const dy = touch.clientY - startY;
        if (Math.abs(dy) > 10 && e.cancelable) {
            e.preventDefault();
        }
    }

    function onUp(e) {
        if (!isDragging) return;
        isDragging = false;
        const touch = e.changedTouches ? e.changedTouches[0] : e;
        const dy = touch.clientY - startY;
        const dt = Date.now() - startTime;
        // Порог: свайп > 40px или быстрый flick (>0.5px/ms)
        const isFastFlick = dt < 300 && Math.abs(dy) > 30;
        if (dy < -40 || (isFastFlick && dy < 0)) {
            panel.classList.remove('collapsed');
            document.body.classList.remove('ui-collapsed');
        } else if (dy > 40 || (isFastFlick && dy > 0)) {
            panel.classList.add('collapsed');
            document.body.classList.add('ui-collapsed');
        }
        const map = getMapObject();
        if (map) setTimeout(() => map.invalidateSize(), 320);
    }

    header.addEventListener('touchstart', onDown, { passive: true });
    header.addEventListener('touchmove', onMove, { passive: false });
    header.addEventListener('touchend', onUp, { passive: true });
    header.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
}
window.setupMobileBottomSheetSwipe = setupMobileBottomSheetSwipe;
window.togglePanelCollapse = togglePanelCollapse;

function toggleMobileMenu() {
    const overlay = document.getElementById('mobile-nav-overlay');
    if (!overlay) return;
    
    const isActive = overlay.classList.contains('active');
    
    if (isActive) {
        overlay.classList.remove('active');
        setTimeout(() => { overlay.style.display = 'none'; }, 300);
    } else {
        // Синхронизируем данные профиля перед открытием
        const student = getCurrentStudentInfo();
        const profileBox = document.getElementById('mobile-nav-profile-container');
        const authBtn = document.getElementById('mobile-nav-auth-btn');
        
        if (student) {
            if (profileBox) {
                profileBox.style.display = 'flex';
                const nameEl = document.getElementById('mobile-nav-name');
                const groupEl = document.getElementById('mobile-nav-group');
                if (nameEl) nameEl.textContent = student.name;
                if (groupEl) groupEl.textContent = student.group;
            }
            if (authBtn) authBtn.style.display = 'none';
        } else {
            if (profileBox) profileBox.style.display = 'none';
            if (authBtn) authBtn.style.display = 'flex';
        }

        overlay.style.display = 'flex';
        // Небольшая задержка для срабатывания CSS transition
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });
    }
}
window.toggleMobileMenu = toggleMobileMenu;

function clearMarkers() {
    if (clickMarker) { try { clickMarker.remove(); } catch(e) {} clickMarker = null; }
    if (resultMarker) { try { resultMarker.remove(); } catch(e) {} resultMarker = null; }
    if (resultLine) { try { resultLine.remove(); } catch(e) {} resultLine = null; }
    if (typeof studyCenterMarker !== 'undefined' && studyCenterMarker) { 
        try { studyCenterMarker.remove(); } catch(e) {} 
        studyCenterMarker = null; 
    }
}

function resetActiveHighlight(hideRiverCompletely = false) {
    if (highlightedDistrictLayer) {
        try {
            highlightedDistrictLayer.setStyle({
                color: '#2E8B57',
                weight: 2,
                fillColor: '#90EE90',
                fillOpacity: 0.25,
                dashArray: '5, 5'
            });
        } catch(e) {}
        highlightedDistrictLayer = null;
    }

    if (highlightedRiverLayers && highlightedRiverLayers.length > 0) {
        highlightedRiverLayers.forEach(layer => {
            try {
                if (hideRiverCompletely) {
                    layer.setStyle({ color: 'transparent', weight: 0, opacity: 0 });
                } else {
                    layer.setStyle({ color: '#0284C7', weight: 2.5, opacity: 0.9 });
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
            try { layer.setStyle({ color: '#0284C7', weight: 2.5, opacity: 0.9 }); } catch(e) {}
        }
    });
}

function resetMapView() {
    const map = getMapObject();
    if (map) {
        const bounds = getRegionBoundsData() || (typeof REGION_BOUNDS !== 'undefined' ? REGION_BOUNDS : null);
        if (bounds) {
            try {
                map.fitBounds(bounds, {padding: [15, 15]});
                return;
            } catch(e) {}
        }
        if (window.serverMapCenter && window.serverMapZoom) {
            try {
                map.setView(window.serverMapCenter, window.serverMapZoom);
                return;
            } catch(e) {}
        }
    }
}

function setQuizLayers(quizMode) {
    try {
        const layers = document.querySelectorAll('.leaflet-control-layers-overlays label');
        layers.forEach(label => {
            const text = label.textContent.trim();
            const input = label.querySelector('input[type="checkbox"]');
            if (!input) return;

                        if (text.includes('Население') || text.includes('Choropleth') || text.includes('Экономика') || text.includes('ВРП')) {
                if (quizMode !== 'normal') {
                    if (input.checked) input.click();
                }
                return;
            }

            if (quizMode === 'center') {
                if (text.includes('Реки') || text.includes('Водоемы')) { if (input.checked) input.click(); }
                if (text.includes('Районы') || text.includes('Райцентры') || text.includes('Территории') || text.includes('Центры')) { if (!input.checked) input.click(); }
            } else if (quizMode === 'district' || quizMode === 'neighbor' || quizMode === 'study_districts') {
                if (text.includes('Реки') || text.includes('Водоемы')) { if (input.checked) input.click(); }
                if (text.includes('Районы') || text.includes('Райцентры') || text.includes('Территории') || text.includes('Центры')) { if (!input.checked) input.click(); }
            } else if (quizMode === 'river' || quizMode === 'study_rivers') {
                if (text.includes('Районы') || text.includes('Райцентры') || text.includes('Территории') || text.includes('Центры')) { if (!input.checked) input.click(); }
                if (text.includes('Реки') || text.includes('Водоемы')) { if (!input.checked) input.click(); }
            } else if (quizMode === 'study_centers') {
                if (text.includes('Реки') || text.includes('Водоемы')) { if (input.checked) input.click(); }
                if (text.includes('Райцентры') || text.includes('Районы') || text.includes('Территории') || text.includes('Центры')) { if (!input.checked) input.click(); }
            } else {
                if (!input.checked) input.click();
            }
        });
    } catch(e) {}
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
    if (isExamMode || !timerEnabled) {
        return;
    }
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

function ensureExamProctorWidgetDOM() {
    // Устаревший виджет #timer-bar-container удален, таймер и Anti-Cheat объединены в #exam-sidebar-header
}

function showExamTimeoutBanner() {
    let banner = document.getElementById('exam-timeout-notification');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'exam-timeout-notification';
        banner.style.cssText = 'position:fixed; top:20px; left:50%; transform:translateX(-50%); background:linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%); color:#FFFFFF; padding:12px 24px; border-radius:12px; font-weight:700; font-size:13.5px; box-shadow:0 12px 32px rgba(0,0,0,0.45); z-index:100002; display:flex; align-items:center; gap:10px; border:1px solid #F87171; animation:slideDownToast 0.3s ease;';
        banner.innerHTML = '<span style="font-size:20px;">⏰</span><span>Время контрольной работы истекло! Ваши ответы зафиксированы и сохранены.</span>';
        document.body.appendChild(banner);
        setTimeout(() => { if (banner) banner.remove(); }, 6000);
    }
}

function startGlobalExamTimer() {
    stopTimer();
    stopGlobalExamTimer();

    ensureExamKioskTopBar();

    // Фиксация абсолютной метки завершения для защиты от засыпания вкладки
    window.examTimerEndTime = Date.now() + (Math.max(1, examTimeRemaining) * 1000);

    updateGlobalExamTimerDisplay();

    examGlobalTimer = setInterval(() => {
        const now = Date.now();
        examTimeRemaining = Math.max(0, Math.round((window.examTimerEndTime - now) / 1000));

        updateGlobalExamTimerDisplay();

        if (examTimeRemaining <= 0) {
            stopGlobalExamTimer();
            handleExamTimeout();
        }
    }, 1000);
}

let _cachedTimerElements = null;
let _prevTimerStr = '';
let _prevStatusText = '';
let _prevTimerPercent = -1;

function resetTimerDOMCache() {
    _cachedTimerElements = null;
    _prevTimerStr = '';
    _prevStatusText = '';
    _prevTimerPercent = -1;
}

function stopGlobalExamTimer() {
    if (examGlobalTimer) {
        clearInterval(examGlobalTimer);
        examGlobalTimer = null;
    }
    resetTimerDOMCache();
}

function updateGlobalExamTimerDisplay() {
    if (!_cachedTimerElements) {
        _cachedTimerElements = {
            timerBar: document.getElementById('timer-bar'),
            sidebarTimer: document.getElementById('exam-sidebar-timer'),
            kioskTimer: document.getElementById('kiosk-timer-display')
        };
    }
    const els = _cachedTimerElements;

    const safeSec = Math.max(0, examTimeRemaining);
    const mins = Math.floor(safeSec / 60);
    const secs = safeSec % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    if (timeStr !== _prevTimerStr) {
        _prevTimerStr = timeStr;
        const kColor = safeSec < 60 ? '#EF4444' : (safeSec < 180 ? '#F59E0B' : '#FBBF24');

        const activeTimer = els.sidebarTimer || document.getElementById('exam-sidebar-timer') || els.kioskTimer;
        if (activeTimer) {
            activeTimer.textContent = timeStr;
            if (activeTimer.style.color !== kColor) activeTimer.style.color = kColor;
        }
    }

    const timerBar = els.timerBar || document.getElementById('timer-bar');
    if (timerBar) {
        const totalSec = Math.max(1, examTimeLimitMinutes * 60);
        const percent = Math.min(100, Math.max(0, Math.round((safeSec / totalSec) * 100)));
        if (percent !== _prevTimerPercent) {
            _prevTimerPercent = percent;
            timerBar.style.width = percent + '%';
            if (percent > 40) {
                timerBar.style.background = 'linear-gradient(90deg, #8B5CF6, #38BDF8)';
                timerBar.style.boxShadow = '0 0 8px rgba(56, 189, 248, 0.4)';
            } else if (percent > 20) {
                timerBar.style.background = 'linear-gradient(90deg, #F59E0B, #FBBF24)';
                timerBar.style.boxShadow = '0 0 8px rgba(245, 158, 11, 0.4)';
            } else {
                timerBar.style.background = 'linear-gradient(90deg, #DC2626, #EF4444)';
                timerBar.style.boxShadow = '0 0 10px rgba(239, 68, 68, 0.7)';
            }
        }
    }
}

function handleExamTimeout() {
    stopGlobalExamTimer();
    stopTimer();

    finishExamEarly(true);

    showExamTimeoutBanner();
}

function enableAntiCheat() {
    antiCheatActive = true;
    document.addEventListener('visibilitychange', handleExamVisibilityChange);
    window.addEventListener('blur', handleExamWindowBlur);
}

function disableAntiCheat() {
    antiCheatActive = false;
    document.removeEventListener('visibilitychange', handleExamVisibilityChange);
    window.removeEventListener('blur', handleExamWindowBlur);
}

function handleExamVisibilityChange() {
    if (!isExamMode || !antiCheatActive) return;
    if (document.hidden) {
        triggerAntiCheatViolation();
    }
}

function handleExamWindowBlur() {
    if (!isExamMode || !antiCheatActive) return;
    if (document.hidden) {
        triggerAntiCheatViolation();
    }
}

function triggerAntiCheatViolation() {
    if (!isExamMode || !antiCheatActive || blurCooldown) return;
    blurCooldown = true;
    setTimeout(() => { blurCooldown = false; }, 2000);

    examCheatingViolations++;

    if (examCheatingViolations === 1) {
        examStatus = 'warning';
        showAntiCheatModal(
            "⚠️ ВНИМАНИЕ: Нарушение регламента!",
            "Зафиксирован уход с вкладки тестирования! Во время контрольной работы переключение на другие вкладки браузера и сторонние программы <b>строго запрещено</b> регламентом Института наук о Земле ЮФУ.<br><br><span style='color:#DC2626; font-weight:700;'>Это ваше первое предупреждение.</span> При повторном переключении попытка будет аннулирована с отметкой о нарушении в ведомости преподавателя.",
            false
        );
    } else if (examCheatingViolations >= 2) {
        examStatus = 'cheating_detected';
        showAntiCheatModal(
            "🚨 ПОДОЗРЕНИЕ НА СПИСЫВАНИЕ!",
            "Зафиксировано <b>повторное переключение вкладок</b>! Контрольная работа принудительно прекращена.<br><br>В журнал преподавателя внесена запись: <b style='color:#DC2626;'>«Подозрение на списывание (нарушение фокуса)»</b>.",
            true
        );
    }
}

function showAntiCheatModal(title, message, isFatal) {
    const modal = document.getElementById('anticheat-modal');
    const titleEl = document.getElementById('anticheat-title');
    const bodyEl = document.getElementById('anticheat-body');
    const btnEl = document.getElementById('anticheat-confirm-btn');

    if (titleEl) titleEl.innerHTML = title;
    if (bodyEl) bodyEl.innerHTML = message;

    if (btnEl) {
        if (isFatal) {
            btnEl.textContent = 'Завершить попытку и зафиксировать результат';
            btnEl.className = 'btn btn-danger';
            btnEl.onclick = () => {
                if (modal) modal.style.display = 'none';
                finishExamEarly(false);
            };
        } else {
            btnEl.textContent = 'Я понимаю, вернуться к контрольной';
            btnEl.className = 'btn btn-warning';
            btnEl.onclick = () => {
                if (modal) modal.style.display = 'none';
            };
        }
    }
    if (modal) modal.style.display = 'flex';
}

function finishExamEarly(isTimeout = false) {
    if (examStatus !== 'cheating_detected') {
        examStatus = isTimeout ? 'timeout' : 'early_finish';
    }
    stopGlobalExamTimer();
    disableAntiCheat();
    document.body.classList.remove('exam-mode');
    removeExamKioskTopBar();
    showResults();
}

function updateTimerDisplay() {
    ensureExamProctorWidgetDOM();
    const timerText = document.getElementById('timer-text');
    const timerBar = document.getElementById('timer-bar');
    const statusText = document.getElementById('exam-proctor-status-text');

    const safeSec = Math.max(0, timeLeft);
    const mins = Math.floor(safeSec / 60);
    const secs = safeSec % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    if (timerText) {
        timerText.textContent = timeStr;
        timerText.classList.add('exam-timer-display');
        timerText.style.color = safeSec <= 5 ? '#EF4444' : '#38BDF8';
    }
    if (statusText) {
        statusText.textContent = 'Таймер вопроса';
        statusText.style.color = '#CBD5E1';
    }
    if (timerBar) {
        const percent = Math.max(0, (safeSec / QUESTION_TIME_LIMIT) * 100);
        timerBar.style.width = `${percent}%`;
        timerBar.style.background = percent > 50 ? 'linear-gradient(90deg, #10B981, #34D399)' : percent > 25 ? 'linear-gradient(90deg, #F59E0B, #FBBF24)' : 'linear-gradient(90deg, #DC2626, #EF4444)';
        timerBar.style.boxShadow = percent <= 25 ? '0 0 8px rgba(239,68,68,0.5)' : 'none';
    }
}

function handleTimeout() {
    if (currentQuestion >= quizData.length) return;
    const question = quizData[currentQuestion];
    showFeedback('Время вышло!', 'error');

    const problematicName = question.correctAnswer || question.districtName || question.riverName || question.name;
    if (problematicName) {
        currentSessionMistakes.push(problematicName);
    }
    if (Array.isArray(currentSessionMistakesDetails)) {
        currentSessionMistakesDetails.push({
            type: question.type || 'district',
            targetName: problematicName,
            correctAnswer: question.correctAnswer || question.districtName || question.riverName || question.name,
            studentAnswer: 'Время вышло (без ответа)',
            questionText: question.text || question.prompt || '',
            questionIndex: currentQuestion + 1,
            districtName: question.districtName || question.correctAnswer || question.name,
            correctLat: question.lat,
            correctLon: question.lon
        });
    }

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

function startStudyMode(category = 'districts') {
    studyCategory = category;
    currentQuiz = 'study';
    setBasemapVisible(true);
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'block';

    updateStudyTabButtons();

    if (category === 'districts') {
        setQuizLayers('study_districts');
        studyQueue = [...getNeighborsData()];
    } else if (category === 'rivers') {
        setQuizLayers('study_rivers');
        restoreAllRiverStyles();
        studyQueue = [...getRiversData()];
    } else if (category === 'centers') {
        setQuizLayers('study_centers');
        studyQueue = [...getCentersData()];
    }

    shuffleArray(studyQueue);
    studyIndex = 0;
    renderStudyItem();
}

function updateStudyTabButtons() {
    const btns = ['districts', 'rivers', 'centers'];
    btns.forEach(b => {
        const el = document.getElementById(`study-tab-${b}`);
        if (el) {
            if (b === studyCategory) el.classList.add('active');
            else el.classList.remove('active');
        }
    });
}

function switchStudyCategory(category) {
    startStudyMode(category);
}

function renderStudyItem() {
    if (!studyQueue || studyQueue.length === 0) return;
    if (studyIndex < 0) studyIndex = 0;
    if (studyIndex >= studyQueue.length) studyIndex = studyQueue.length - 1;

    clearMarkers();
    resetActiveHighlight(studyCategory === 'rivers');

    const item = studyQueue[studyIndex];
    const counterEl = document.getElementById('study-counter-val');
    const contentEl = document.getElementById('study-content-box');
    if (counterEl) counterEl.textContent = `${studyIndex + 1} / ${studyQueue.length}`;

    if (!contentEl) return;

    if (studyCategory === 'districts') {
        const neighborsHtml = item.neighbors && item.neighbors.length > 0
            ? item.neighbors.map(n => `<span class="neighbor-tag" onclick="jumpToStudyItem('${escapeHtml(n)}')">${escapeHtml(n)}</span>`).join('')
            : '<span style="color: #94A3B8; font-size: 11px;">Нет смежных границ</span>';

        const popFormatted = item.population ? `${Number(item.population).toLocaleString('ru-RU')} чел.` : 'Уточняется';

        contentEl.innerHTML = `
            <h3 class="study-title">${escapeHtml(item.name)}</h3>
            <div class="info-row"><span>Центр:</span><strong>${escapeHtml(item.center || '—')}</strong></div>
            <div class="info-row"><span>Население:</span><strong>~${escapeHtml(popFormatted)}</strong></div>
            <div class="info-row"><span>Площадь:</span><strong>~${escapeHtml(item.area)} км²</strong></div>
            <div style="margin-top: 8px;">
                <span style="color: #64748B; font-size: 11px; font-weight: 600;">Граничит:</span>
                <div style="margin-top: 4px; display: flex; flex-wrap: wrap;">${neighborsHtml}</div>
            </div>
        `;
        highlightDistrictOnMapByName(item.name);

    } else if (studyCategory === 'rivers') {
        contentEl.innerHTML = `
            <h3 class="study-title">Река ${escapeHtml(item.name)}</h3>
            <div class="info-row"><span>Тип:</span><strong>Водный объект / Водоток</strong></div>
            <div class="info-row"><span>Протяженность:</span><strong>~${escapeHtml(item.length)} км</strong></div>
            <div class="hint-small" style="margin-top: 8px;">Русло выделено красной линией на карте</div>
        `;
        highlightRiverOnMapByName(item.name);

    } else if (studyCategory === 'centers') {
        contentEl.innerHTML = `
            <h3 class="study-title">${escapeHtml(item.name)}</h3>
            <div class="info-row"><span>Статус:</span><strong>${escapeHtml(item.status || 'центр')}</strong></div>
            <div class="info-row"><span>Координаты:</span><strong>${escapeHtml(item.lat.toFixed(3))}°, ${escapeHtml(item.lon.toFixed(3))}°</strong></div>
            <div class="hint-small" style="margin-top: 8px;">Объект отмечен пульсирующим маркером</div>
        `;
        const map = getMapObject();
        if (map) {
            map.setView([item.lat, item.lon], 11);
            studyCenterMarker = L.circleMarker([item.lat, item.lon], {
                radius: 12,
                color: '#EF4444',
                fillColor: '#F59E0B',
                fillOpacity: 0.9,
                weight: 3
            }).addTo(map);
        }
    }
}

function nextStudyItem() {
    if (studyIndex < studyQueue.length - 1) {
        studyIndex++;
        renderStudyItem();
    } else {
        alert('🎉 Вы просмотрели все объекты в этой категории!');
    }
}

function prevStudyItem() {
    if (studyIndex > 0) {
        studyIndex--;
        renderStudyItem();
    }
}

function randomStudyItem() {
    studyIndex = Math.floor(Math.random() * studyQueue.length);
    renderStudyItem();
}

function jumpToStudyItem(name) {
    const foundIdx = studyQueue.findIndex(d => d.name === name);
    if (foundIdx !== -1) {
        studyIndex = foundIdx;
        renderStudyItem();
    }
}

function exitStudyMode() {
    setBasemapVisible(true);
    clearMarkers();
    resetActiveHighlight(false);
    restoreAllLayers();
    enablePopups();
    resetMapView();
    currentQuiz = null;

    const sm = document.getElementById('study-mode');
    const nm = document.getElementById('normal-mode');
    if (sm) sm.style.display = 'none';
    if (nm) nm.style.display = 'block';
    setTimeout(setupDistrictClickListeners, 300);
}

function openExamModal(preselectedCategory) {
    const m = document.getElementById('exam-setup-modal');
    if (m) {
        if (preselectedCategory) {
            const catSelect = document.getElementById('exam-category-select');
            if (catSelect) {
                const norm = String(preselectedCategory).toLowerCase();
                if (norm === 'rivers' || norm === 'river' || norm.includes('гидрограф') || norm.includes('рек')) {
                    catSelect.value = 'rivers';
                } else if (norm === 'districts' || norm === 'district' || norm.includes('номенклатур') || norm.includes('территори')) {
                    catSelect.value = 'districts';
                } else if (norm === 'puzzle' || norm.includes('пазл')) {
                    catSelect.value = 'puzzle';
                } else if (norm === 'centers' || norm === 'center' || norm.includes('центр')) {
                    catSelect.value = 'centers';
                } else if (norm === 'neighbors' || norm === 'neighbor' || norm.includes('сосед') || norm.includes('тополог')) {
                    catSelect.value = 'neighbors';
                } else {
                    catSelect.value = preselectedCategory;
                }
            }
        }
        m.style.display = 'flex';
    }
}

function closeExamModal() {
    const m = document.getElementById('exam-setup-modal');
    if (m) m.style.display = 'none';
}

var _adaptiveData = null;
var _adaptivePools = null;
var _isAdaptiveQuiz = false;

async function openAdaptiveModal() {
    const m = document.getElementById('adaptive-modal');
    if (!m) return;
    m.style.display = 'flex';

    const loadingState = document.getElementById('adaptive-loading-state');
    const contentState = document.getElementById('adaptive-content-state');
    if (loadingState) loadingState.style.display = 'block';
    if (contentState) contentState.style.display = 'none';

    const student = getCurrentStudentInfo();
    if (!student || !student.email) {
        if (contentState) {
            contentState.innerHTML = `
                <div style="text-align: center; padding: 12px;">
                    <div style="font-size: 32px; margin-bottom: 8px;">⚠️</div>
                    <div style="font-size: 13px; color: #92400E; font-weight: 600; margin-bottom: 4px;">
                        Нужно войти в аккаунт
                    </div>
                    <div style="font-size: 11.5px; color: #64748B;">
                        Адаптив работает только для авторизованных студентов
                    </div>
                </div>
            `;
        }
        if (loadingState) loadingState.style.display = 'none';
        if (contentState) contentState.style.display = 'block';
        return;
    }

    try {
        const res = await fetch(`/api/student/heatmap?email=${encodeURIComponent(student.email)}`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        _adaptiveData = await res.json();
        renderAdaptivePreview(_adaptiveData, student);
    } catch (e) {
        if (contentState) {
            contentState.innerHTML = `
                <div style="text-align: center; padding: 12px;">
                    <div style="font-size: 32px; margin-bottom: 8px;">📭</div>
                    <div style="font-size: 13px; color: #475569; font-weight: 600;">
                        Пока нет данных о ваших ошибках
                    </div>
                    <div style="font-size: 11.5px; color: #64748B; margin-top: 4px;">
                        Пройдите 1-2 обычных теста, чтобы адаптив начал работать
                    </div>
                </div>
            `;
        }
    } finally {
        if (loadingState) loadingState.style.display = 'none';
        if (contentState) contentState.style.display = 'block';
    }
}

function closeAdaptiveModal() {
    const m = document.getElementById('adaptive-modal');
    if (m) m.style.display = 'none';
}

function renderAdaptivePreview(data, student) {
    const byObject = data.by_object || {};
    const totalTests = data.total_tests || 0;
    const objectsCount = Object.keys(byObject).length;

    // Строим пулы
    const weak = [];
    const medium = [];
    const strong = [];

    Object.entries(byObject).forEach(([name, obj]) => {
        if (obj.type && obj.type !== 'district') return; // фильтр по районам
        const acc = obj.accuracy || 0;
        const entry = { name: name, accuracy: acc, errors: obj.errors || 0 };
        if (acc < 60) weak.push(entry);
        else if (acc < 85) medium.push(entry);
        else strong.push(entry);
    });

    // Сортируем weak по возрастанию accuracy (самые плохие — первыми)
    weak.sort((a, b) => a.accuracy - b.accuracy);

    const content = document.getElementById('adaptive-content-state');
    if (!content) return;

    if (totalTests === 0 || objectsCount === 0) {
        content.innerHTML = `
            <div style="text-align: center; padding: 8px;">
                <div style="font-size: 28px; margin-bottom: 8px;">📊</div>
                <div style="font-size: 13px; color: #475569; font-weight: 600; margin-bottom: 4px;">
                    У вас пока нет истории ответов
                </div>
                <div style="font-size: 11.5px; color: #64748B; line-height: 1.5;">
                    Первый адаптивный тест будет обычным (все объекты равновероятно).
                    После него алгоритм запомнит ваши ошибки и начнёт адаптироваться.
                </div>
            </div>
        `;
        return;
    }

    const top3Weak = weak.slice(0, 3).map(w => 
        `<span style="display:inline-block;background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;margin:2px 4px 2px 0;border:1px solid #FCA5A5;">${escapeHtml(w.name)}</span>`
    ).join('');

    content.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-size: 13px; font-weight: 700; color: #0F172A;">
                🎯 Ваши приоритеты
            </div>
            <div style="font-size: 11px; color: #64748B;">
                ${totalTests} тестов • ${objectsCount} объектов
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px;">
            <div style="background: #FEE2E2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 8px; text-align: center;">
                <div style="font-size: 18px; font-weight: 800; color: #991B1B;">${weak.length}</div>
                <div style="font-size: 10px; color: #7F1D1D; font-weight: 600; margin-top: 2px;">слабых</div>
            </div>
            <div style="background: #FEF3C7; border: 1px solid #FDE68A; border-radius: 8px; padding: 8px; text-align: center;">
                <div style="font-size: 18px; font-weight: 800; color: #92400E;">${medium.length}</div>
                <div style="font-size: 10px; color: #78350F; font-weight: 600; margin-top: 2px;">в процессе</div>
            </div>
            <div style="background: #DCFCE7; border: 1px solid #BBF7D0; border-radius: 8px; padding: 8px; text-align: center;">
                <div style="font-size: 18px; font-weight: 800; color: #166534;">${strong.length}</div>
                <div style="font-size: 10px; color: #14532D; font-weight: 600; margin-top: 2px;">освоено</div>
            </div>
        </div>

        ${weak.length > 0 ? `
            <div style="font-size: 11px; color: #64748B; margin-bottom: 4px;">
                Топ проблемных объектов:
            </div>
            <div style="margin-bottom: 8px;">${top3Weak}</div>
        ` : ''}

        <div style="background: rgba(37,99,235,0.08); border: 1px solid rgba(37,99,235,0.2); border-radius: 8px; padding: 8px 10px; font-size: 11px; color: #1E40AF; line-height: 1.4;">
            💡 <b>60%</b> вопросов — на слабые объекты, <b>30%</b> — на средние, <b>10%</b> — на освоенные (для закрепления).
        </div>
    `;
}

async function startAdaptiveTest() {
    const student = getCurrentStudentInfo();
    if (!student || !student.email) {
        alert('Войдите в аккаунт');
        return;
    }

    const typeSelect = document.getElementById('adaptive-type-select');
    const countSelect = document.getElementById('adaptive-count-select');
    const quizType = typeSelect ? typeSelect.value : 'district';
    const count = countSelect ? parseInt(countSelect.value, 10) : 15;

    closeAdaptiveModal();

    // Готовим пулы
    _isAdaptiveQuiz = true;
    _adaptivePools = buildAdaptivePools(_adaptiveData, quizType);

    // Вызываем существующую подготовку UI для типа
    prepareQuizUI(quizType, `🎯 Адаптивный: ${quizType === 'district' ? 'Силуэты' : quizType === 'center' ? 'Центры' : 'Реки'}`, 
                  quizType !== 'center', false);

    // Генерируем вопросы с приоритетом на weak
    generateAdaptiveQuestions(quizType, count);
}

function buildAdaptivePools(heatmapData, quizType) {
    const pools = { weak: [], medium: [], strong: [] };
    
    // Дефолтное распределение 60/30/10
    const byObject = (heatmapData && heatmapData.by_object) || {};
    
    // Группируем по accuracy
    const allObjects = {};
    Object.entries(byObject).forEach(([name, obj]) => {
        if (obj.type && obj.type !== quizType) return;
        allObjects[name] = obj.accuracy || 0;
    });

    // Собираем полный список доступных объектов для типа
    let fullList = [];
    if (quizType === 'district') {
        fullList = (getDistrictsData() || []).map(d => d.name).filter(Boolean);
    } else if (quizType === 'center') {
        fullList = (getCentersData() || []).map(c => c.name).filter(Boolean);
    } else if (quizType === 'river') {
        fullList = (getRiversData() || []).map(r => r.name).filter(Boolean);
    }

    // Распихиваем по пулам
    fullList.forEach(name => {
        const acc = name in allObjects ? allObjects[name] : 100; // не встречался — считаем освоенным
        if (acc < 60) pools.weak.push(name);
        else if (acc < 85) pools.medium.push(name);
        else pools.strong.push(name);
    });

    // Если weak пуст — добавляем из medium половину
    if (pools.weak.length === 0 && pools.medium.length > 0) {
        const half = Math.floor(pools.medium.length / 2);
        pools.weak = pools.medium.slice(0, half);
        pools.medium = pools.medium.slice(half);
    }

    // Если всё ещё пусто — берём strong как fallback
    if (pools.weak.length === 0 && pools.strong.length > 0) {
        const quarter = Math.ceil(pools.strong.length / 4);
        pools.weak = pools.strong.slice(0, quarter);
    }

    console.log('[Adaptive] Pools:', {
        weak: pools.weak.length,
        medium: pools.medium.length,
        strong: pools.strong.length
    });

    return pools;
}

function generateAdaptiveQuestions(quizType, count) {
    quizData = [];
    currentQuestion = 0;
    score = 0;
    maxPossibleScore = 0;

    const pools = _adaptivePools || { weak: [], medium: [], strong: [] };
    const totalAvailable = pools.weak.length + pools.medium.length + pools.strong.length;

    if (totalAvailable < 2) {
        alert('Недостаточно данных для адаптивного теста');
        _isAdaptiveQuiz = false;
        exitQuizDirectly();
        return;
    }

    // Вычисляем целевое количество из каждого пула
    let targetWeak = Math.round(count * 0.6);
    let targetMedium = Math.round(count * 0.3);
    let targetStrong = count - targetWeak - targetMedium;

    // Корректируем если пул меньше цели
    if (pools.weak.length < targetWeak) {
        const diff = targetWeak - pools.weak.length;
        targetWeak = pools.weak.length;
        targetMedium += Math.ceil(diff * 0.75);
        targetStrong += Math.floor(diff * 0.25);
    }
    if (pools.medium.length < targetMedium) {
        const diff = targetMedium - pools.medium.length;
        targetMedium = pools.medium.length;
        targetStrong += diff;
    }
    if (pools.strong.length < targetStrong) {
        targetStrong = pools.strong.length;
    }

    // Добираем недостающее из weak/medium если total < count
    let shortfall = count - (targetWeak + targetMedium + targetStrong);
    while (shortfall > 0 && (pools.weak.length > targetWeak || pools.medium.length > targetMedium)) {
        if (pools.weak.length > targetWeak) { targetWeak++; shortfall--; }
        else if (pools.medium.length > targetMedium) { targetMedium++; shortfall--; }
    }

    // Функция выбора объектов из пула
    function pickFromPool(pool, n) {
        const copy = [...pool];
        shuffleArray(copy);
        return copy.slice(0, n);
    }

    // Собираем выбранные имена
    const selectedNames = [
        ...pickFromPool(pools.weak, targetWeak),
        ...pickFromPool(pools.medium, targetMedium),
        ...pickFromPool(pools.strong, targetStrong)
    ];

    // Перемешиваем итоговый порядок
    shuffleArray(selectedNames);

    // Генерируем вопросы по типу
    if (quizType === 'district') {
        const valid = (getDistrictsData() || []).filter(d => d.name && d.name.trim());
        selectedNames.forEach(name => {
            if (!valid.find(d => d.name === name)) return;
            const options = [name];
            while (options.length < 4 && options.length < valid.length) {
                const wrong = valid[Math.floor(Math.random() * valid.length)];
                if (!options.includes(wrong.name)) options.push(wrong.name);
            }
            shuffleArray(options);
            quizData.push({
                type: 'district',
                correctAnswer: name,
                options: options,
                districtName: name
            });
            maxPossibleScore += 1;
        });
    } else if (quizType === 'center') {
        const valid = (getCentersData() || []).filter(c => c.name && c.name.trim());
        selectedNames.forEach(name => {
            const center = valid.find(c => c.name === name);
            if (!center) return;
            quizData.push({
                type: 'center',
                correctAnswer: name,
                correctLat: center.lat,
                correctLon: center.lon,
                centerName: name
            });
            maxPossibleScore += 3;
        });
    } else if (quizType === 'river') {
        const valid = (getRiversData() || []).filter(r => r.name && r.name.trim());
        selectedNames.forEach(name => {
            if (!valid.find(r => r.name === name)) return;
            const options = [name];
            while (options.length < 4 && options.length < valid.length) {
                const wrong = valid[Math.floor(Math.random() * valid.length)];
                if (!options.includes(wrong.name)) options.push(wrong.name);
            }
            shuffleArray(options);
            quizData.push({
                type: 'river',
                correctAnswer: name,
                options: options,
                riverName: name
            });
            maxPossibleScore += 1;
        });
    }

    if (quizData.length === 0) {
        alert('Не удалось сгенерировать адаптивные вопросы');
        _isAdaptiveQuiz = false;
        exitQuizDirectly();
        return;
    }

    totalQuestions = quizData.length;
    showQuestion();
}

window.openAdaptiveModal = openAdaptiveModal;
window.closeAdaptiveModal = closeAdaptiveModal;
window.startAdaptiveTest = startAdaptiveTest;

function startExamFromModal() {
    const cat = document.getElementById('exam-category-select') ? document.getElementById('exam-category-select').value : 'mixed';
    const cnt = document.getElementById('exam-count-select') ? parseInt(document.getElementById('exam-count-select').value) : 15;
    const tme = document.getElementById('exam-time-select') ? parseInt(document.getElementById('exam-time-select').value) : 10;
    
    closeExamModal();
    startSelectedTestMode(cat, { isExam: true, count: cnt, timeLimit: tme });
}

function selectModeFromWelcome(mode) {
    closeWelcomeModal();
    startSelectedTestMode(mode, { isExam: false });
}

function startSelectedTestMode(mode = 'mixed', options = {}) {
    currentSessionMistakes = [];
    currentSessionMistakesDetails = [];
    const count = options.count || 15;
    const timeLimit = options.timeLimit || 10;
    const isExam = options.isExam !== undefined ? options.isExam : isExamMode;
    const normalized = String(mode).toLowerCase().trim();

    if (normalized === 'puzzle' || normalized.includes('пазл')) {
        if (isExam) {
            isExamMode = true;
            document.body.classList.add('exam-mode');
            ensureExamKioskTopBar({
                region: window.currentRegionKey || '',
                groupName: options.groupName || currentSyncGroupName,
                timeLimit: timeLimit,
                category: 'puzzle'
            });
        }
        startPuzzleMode();
    } else if (normalized === 'rivers' || normalized === 'river' || normalized.includes('гидрограф') || normalized.includes('рек')) {
        if (isExam) {
            startExamQuiz('rivers', count, timeLimit);
        } else {
            startRiverQuiz();
        }
    } else if (normalized === 'districts' || normalized === 'district' || normalized.includes('номенклатур') || normalized.includes('территори') || normalized.includes('силуэт')) {
        if (isExam) {
            startExamQuiz('districts', count, timeLimit);
        } else {
            startDistrictQuiz();
        }
    } else if (normalized === 'centers' || normalized === 'center' || normalized.includes('центр')) {
        if (isExam) {
            startExamQuiz('centers', count, timeLimit);
        } else {
            startCenterQuiz();
        }
    } else if (normalized === 'neighbors' || normalized === 'neighbor' || normalized.includes('сосед') || normalized.includes('тополог')) {
        if (isExam) {
            startExamQuiz('neighbors', count, timeLimit);
        } else {
            startNeighborQuiz();
        }
    } else if (normalized === 'study' || normalized.includes('обучен')) {
        startStudyMode(options.category || 'districts');
    } else {
        startExamQuiz('mixed', count, timeLimit);
    }
}

function startExamQuiz(category = 'mixed', count = 15, timeLimitMinutes = 10) {
    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) exitHeatmapMode();
    isExamMode = true;
    document.body.classList.add('exam-mode');
    ensureExamKioskTopBar({
        region: window.currentRegionKey || '',
        groupName: currentSyncGroupName,
        timeLimit: timeLimitMinutes,
        category: category
    });

    examCategory = category;
    examQuestionCount = count || 15;
    examTimeLimitMinutes = timeLimitMinutes || 10;
    // Строгий расчет: если экзамен синхронный, используется остаток абсолютного серверного времени
    if (currentSyncSessionId && typeof syncExamRemainingSec === 'number' && syncExamRemainingSec > 0) {
        examTimeRemaining = syncExamRemainingSec;
    } else {
        examTimeRemaining = examTimeLimitMinutes * 60;
    }
    ExamProctor.resetViolations(true);
    ExamProctor.status = 'passed';
    ExamProctor.token = '';
    currentQuiz = 'exam_' + category;
    totalQuestions = examQuestionCount;
    currentQuestion = 0;
    score = 0;
    quizStartTime = Date.now();

    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';

    const regName = getRegionName(window.currentRegionKey || '');
    const titles = {
        'mixed': `📝 Комплексный экзамен (${regName})`,
        'districts': `📝 Контрольная: Номенклатура (${regName})`,
        'rivers': `📝 Контрольная: Гидрография (${regName})`,
        'centers': `📝 Контрольная: Центры (${regName})`,
        'neighbors': `📝 Контрольная: Топология (${regName})`
    };
    document.getElementById('quiz-title').textContent = titles[category] || `📝 Контрольная работа (${regName})`;

    const hintBtn = document.getElementById('hint-button');
    if (hintBtn) hintBtn.style.display = 'none';

    if (category === 'districts' || category === 'neighbors') {
        setBasemapVisible(false);
        setQuizLayers('district');
    } else if (category === 'rivers') {
        setBasemapVisible(true);
        restoreAllRiverStyles();
        setQuizLayers('river');
    } else if (category === 'centers') {
        setBasemapVisible(true);
        setQuizLayers('center');
    } else {
        setBasemapVisible(true);
        setQuizLayers('normal');
    }

    enableAntiCheat();
    startGlobalExamTimer();
    generateExamQuestions(category, examQuestionCount);
}

function generateExamQuestions(category, count) {
    quizData = [];
    currentQuestion = 0;
    score = 0;
    maxPossibleScore = 0;

    if (category === 'districts') {
        const valid = (getDistrictsData() || []).filter(d => d.name && d.name.trim() !== '');
        if (valid.length < 2) {
            alert('Недостаточно данных для вопросов по территориям.');
            exitQuizDirectly();
            return;
        }
        for (let i = 0; i < count; i++) {
            const correct = valid[Math.floor(Math.random() * valid.length)];
            const options = [correct.name];
            while (options.length < 4 && options.length < valid.length) {
                const wrong = valid[Math.floor(Math.random() * valid.length)];
                if (!options.includes(wrong.name)) options.push(wrong.name);
            }
            shuffleArray(options);
            quizData.push({
                type: 'district',
                correctAnswer: correct.name,
                options: options,
                districtName: correct.name
            });
            maxPossibleScore += 1;
        }
    } else if (category === 'rivers') {
        const valid = (getRiversData() || []).filter(r => r.name && r.name.trim() !== '');
        if (valid.length < 1) {
            alert('В данном регионе нет рек в базе данных.');
            exitQuizDirectly();
            return;
        }
        for (let i = 0; i < count; i++) {
            const correct = valid[i % valid.length];
            const options = [correct.name];
            while (options.length < 4 && options.length < valid.length) {
                const wrong = valid[Math.floor(Math.random() * valid.length)];
                if (!options.includes(wrong.name)) options.push(wrong.name);
            }
            shuffleArray(options);
            quizData.push({
                type: 'river',
                correctAnswer: correct.name,
                options: options,
                riverName: correct.name
            });
            maxPossibleScore += 1;
        }
        shuffleArray(quizData);
    } else if (category === 'centers') {
        const valid = (getCentersData() || []).filter(c => c.name && c.name.trim() !== '');
        if (valid.length < 1) {
            alert('Недостаточно данных об административных центрах.');
            exitQuizDirectly();
            return;
        }
        for (let i = 0; i < count; i++) {
            const correct = valid[Math.floor(Math.random() * valid.length)];
            quizData.push({
                type: 'center',
                correctAnswer: correct.name,
                correctLat: correct.lat,
                correctLon: correct.lon,
                centerName: correct.name
            });
            maxPossibleScore += 3;
        }
    } else if (category === 'neighbors') {
        const validPool = (getNeighborsData() || []).filter(d => d.name && d.name.trim() !== '' && d.neighbors && d.neighbors.length >= 1);
        const allNames = validPool.map(d => d.name);
        if (validPool.length === 0) {
            alert('Недостаточно данных о топологии.');
            exitQuizDirectly();
            return;
        }
        for (let i = 0; i < count; i++) {
            const current = validPool[Math.floor(Math.random() * validPool.length)];
            const neighbors = [...current.neighbors];
            shuffleArray(neighbors);
            let options = neighbors.slice(0, 3);
            while (options.length < 3) {
                const dummy = allNames[Math.floor(Math.random() * allNames.length)];
                if (!options.includes(dummy) && dummy !== current.name) options.push(dummy);
            }
            const nonNeighbors = allNames.filter(name => name !== current.name && !current.neighbors.includes(name));
            const wrongNeighbor = nonNeighbors.length > 0 ? nonNeighbors[Math.floor(Math.random() * nonNeighbors.length)] : allNames[0];
            options.push(wrongNeighbor);
            shuffleArray(options);
            quizData.push({
                type: 'neighbor',
                districtName: current.name,
                correctAnswer: wrongNeighbor,
                options: options
            });
            maxPossibleScore += 1;
        }
    } else {
        // 'mixed' - сбалансированная комбинация всех доступных типов
        const hasDistricts = getDistrictsData() && getDistrictsData().length >= 2;
        const hasRivers = getRiversData() && getRiversData().length >= 1;
        const hasCenters = getCentersData() && getCentersData().length >= 1;
        const hasNeighbors = getNeighborsData() && getNeighborsData().some(d => d.neighbors && d.neighbors.length >= 1);

        const availableTypes = [];
        if (hasDistricts) availableTypes.push('districts');
        if (hasNeighbors) availableTypes.push('neighbors');
        if (hasRivers) availableTypes.push('rivers');
        if (hasCenters) availableTypes.push('centers');

        if (availableTypes.length === 0) {
            alert('Недостаточно данных для проведения экзамена.');
            exitQuizDirectly();
            return;
        }

        const validDistricts = (getDistrictsData() || []).filter(d => d.name && d.name.trim() !== '');
        const validRivers = (getRiversData() || []).filter(r => r.name && r.name.trim() !== '');
        const validCenters = (getCentersData() || []).filter(c => c.name && c.name.trim() !== '');
        const validNeighborsPool = (getNeighborsData() || []).filter(d => d.name && d.name.trim() !== '' && d.neighbors && d.neighbors.length >= 1);
        const allNeighborNames = validNeighborsPool.map(d => d.name);

        for (let i = 0; i < count; i++) {
            const qType = availableTypes[i % availableTypes.length];
            if (qType === 'districts' && validDistricts.length >= 2) {
                const correct = validDistricts[Math.floor(Math.random() * validDistricts.length)];
                const options = [correct.name];
                while (options.length < 4 && options.length < validDistricts.length) {
                    const wrong = validDistricts[Math.floor(Math.random() * validDistricts.length)];
                    if (!options.includes(wrong.name)) options.push(wrong.name);
                }
                shuffleArray(options);
                quizData.push({
                    type: 'district',
                    correctAnswer: correct.name,
                    options: options,
                    districtName: correct.name
                });
                maxPossibleScore += 1;
            } else if (qType === 'rivers' && validRivers.length >= 1) {
                const correct = validRivers[Math.floor(Math.random() * validRivers.length)];
                const options = [correct.name];
                while (options.length < 4 && options.length < validRivers.length) {
                    const wrong = validRivers[Math.floor(Math.random() * validRivers.length)];
                    if (!options.includes(wrong.name)) options.push(wrong.name);
                }
                shuffleArray(options);
                quizData.push({
                    type: 'river',
                    correctAnswer: correct.name,
                    options: options,
                    riverName: correct.name
                });
                maxPossibleScore += 1;
            } else if (qType === 'centers' && validCenters.length >= 1) {
                const correct = validCenters[Math.floor(Math.random() * validCenters.length)];
                quizData.push({
                    type: 'center',
                    correctAnswer: correct.name,
                    correctLat: correct.lat,
                    correctLon: correct.lon,
                    centerName: correct.name
                });
                maxPossibleScore += 3;
            } else if (qType === 'neighbors' && validNeighborsPool.length >= 1) {
                const current = validNeighborsPool[Math.floor(Math.random() * validNeighborsPool.length)];
                const neighbors = [...current.neighbors];
                shuffleArray(neighbors);
                let options = neighbors.slice(0, 3);
                while (options.length < 3) {
                    const dummy = allNeighborNames[Math.floor(Math.random() * allNeighborNames.length)];
                    if (!options.includes(dummy) && dummy !== current.name) options.push(dummy);
                }
                const nonNeighbors = allNeighborNames.filter(name => name !== current.name && !current.neighbors.includes(name));
                const wrongNeighbor = nonNeighbors.length > 0 ? nonNeighbors[Math.floor(Math.random() * nonNeighbors.length)] : allNeighborNames[0];
                options.push(wrongNeighbor);
                shuffleArray(options);
                quizData.push({
                    type: 'neighbor',
                    districtName: current.name,
                    correctAnswer: wrongNeighbor,
                    options: options
                });
                maxPossibleScore += 1;
            }
        }
        shuffleArray(quizData);
    }

    totalQuestions = quizData.length;
    showQuestion();
}

function startPuzzleMode() {
    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) exitHeatmapMode();
    currentSessionMistakes = [];
    currentSessionMistakesDetails = [];
    if (typeof EMBEDDED_PUZZLE_DATA === 'undefined' || !EMBEDDED_PUZZLE_DATA || EMBEDDED_PUZZLE_DATA.length < 2) {
        alert('Для запуска режима пазла требуются пространственные данные районов этого региона.');
        return;
    }

    const map = getMapObject();
    if (!map) {
        alert('Карта еще не инициализирована. Подождите пару секунд.');
        return;
    }

    currentQuiz = 'puzzle';
    isPuzzleMode = true;

    removePuzzleGhost();
    stopTimer();
    stopGlobalExamTimer();
    disableAntiCheat();
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight(false);
    disablePopups();

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'none';
    const pm = document.getElementById('puzzle-mode');
    if (pm) pm.style.display = 'block';

    setBasemapVisible(false);

    hideAllMapLayersForPuzzle();

    puzzleDistricts = JSON.parse(JSON.stringify(EMBEDDED_PUZZLE_DATA));
    puzzlePlacedDistricts = new Set();
    puzzleSlotLayers = {};
    puzzlePlacedMarkers = [];
    puzzleMistakes = 0;
    puzzleHintsUsed = 0;
    puzzleStartTime = Date.now();

    renderPuzzleRegionOutline();

    const randomIndex = Math.floor(Math.random() * puzzleDistricts.length);
    puzzleAnchorDistrict = puzzleDistricts[randomIndex];

    placeDistrictOnMap(puzzleAnchorDistrict, true);

    puzzleUnplacedQueue = puzzleDistricts.filter(d => d.id !== puzzleAnchorDistrict.id);
    shuffleArray(puzzleUnplacedQueue);

    const initialNeighbor = puzzleUnplacedQueue.find(d => isDistrictNeighborOfPlaced(d)) || puzzleUnplacedQueue[0];
    if (initialNeighbor) {
        setActivePuzzlePiece(initialNeighbor);
    }

    renderPuzzleTray();

    updatePuzzleProgress();

    resetMapView();

    startPuzzleTimer();

    setupPuzzleDropZone();

    showPuzzleFloatingMessage(`⭐ Опорный район: «${puzzleAnchorDistrict.name}» зафиксирован! Присоединяйте соседние районы к нему.`, '#0284C7');
}

function hideAllMapLayersForPuzzle() {
    const map = getMapObject();
    if (!map) return;
    puzzleSavedLayerStyles = [];

    map.eachLayer(function(layer) {
        if (layer.options && layer.options.isPuzzleLayer) return;

        if (layer.feature && layer.setStyle) {
            puzzleSavedLayerStyles.push({
                layer: layer,
                opacity: layer.options.opacity !== undefined ? layer.options.opacity : 1,
                fillOpacity: layer.options.fillOpacity !== undefined ? layer.options.fillOpacity : 0.6
            });
            try {
                layer.setStyle({ opacity: 0, fillOpacity: 0 });
            } catch(e) {}
        } else if (layer instanceof L.Marker || layer instanceof L.CircleMarker) {
            if (layer.setOpacity) {
                puzzleSavedLayerStyles.push({
                    layer: layer,
                    isMarker: true,
                    opacity: 1
                });
                try { layer.setOpacity(0); } catch(e) {}
            }
        }
    });
}

function restoreMapLayersAfterPuzzle() {
    puzzleSavedLayerStyles.forEach(item => {
        try {
            if (item.isMarker && item.layer.setOpacity) {
                item.layer.setOpacity(item.opacity);
            } else if (item.layer.setStyle) {
                item.layer.setStyle({
                    opacity: item.opacity,
                    fillOpacity: item.fillOpacity
                });
            }
        } catch(e) {}
    });
    puzzleSavedLayerStyles = [];
}

function renderPuzzleRegionOutline() {
    const map = getMapObject();
    if (!map) return;

    if (puzzleOutlineLayer) {
        try { map.removeLayer(puzzleOutlineLayer); } catch(e) {}
        puzzleOutlineLayer = null;
    }

    if (typeof REGION_OUTLINE_GEOJSON !== 'undefined' && REGION_OUTLINE_GEOJSON) {
        try {
            puzzleOutlineLayer = L.geoJSON(REGION_OUTLINE_GEOJSON, {
                style: {
                    color: '#334155',
                    weight: 3.0,
                    opacity: 0.9,
                    fillColor: '#F8FAFC',
                    fillOpacity: 0.85,
                    dashArray: null
                },
                interactive: false
            });
            puzzleOutlineLayer.options = puzzleOutlineLayer.options || {};
            puzzleOutlineLayer.options.isPuzzleLayer = true;
            puzzleOutlineLayer.addTo(map);
        } catch(e) {
            console.warn('Не удалось отобразить внешний контур региона:', e);
        }
    }
}

function renderPuzzleSlots() {
    const map = getMapObject();
    if (!map) return;

    for (let id in puzzleSlotLayers) {
        try { map.removeLayer(puzzleSlotLayers[id]); } catch(e) {}
    }
    puzzleSlotLayers = {};
}

function placeDistrictOnMap(district, isAnchor = false) {
    const map = getMapObject();
    if (!map || !district || !district.geojson) return;

    puzzlePlacedDistricts.add(district.id);
    const placedCount = puzzlePlacedDistricts.size;

    if (typeof DuelManager !== 'undefined' && DuelManager.active && !isAnchor) {
        DuelManager.submitPuzzlePiece(placedCount, puzzleMistakes, district.name);
    }
    const pieceColor = isAnchor ? '#2563EB' : getPuzzlePieceColor(placedCount);

    try {
        const layer = L.geoJSON(district.geojson, {
            style: {
                color: isAnchor ? '#1E40AF' : '#0F766E',
                weight: isAnchor ? 3.0 : 2.2,
                opacity: 1,
                fillColor: pieceColor,
                fillOpacity: 0.88,
                dashArray: null
            },
            interactive: false
        });
        layer.options = layer.options || {};
        layer.options.isPuzzleLayer = true;
        layer.options.districtId = district.id;
        layer.addTo(map);
        puzzleSlotLayers[district.id] = layer;

        if (!isAnchor) {
            // Зеленый импульс примагничивания
            layer.setStyle({
                color: '#10B981',
                weight: 4,
                fillColor: '#6EE7B7',
                fillOpacity: 0.95
            });
            setTimeout(() => {
                if (puzzleSlotLayers[district.id]) {
                    puzzleSlotLayers[district.id].setStyle({
                        color: '#0F766E',
                        weight: 2.2,
                        opacity: 1,
                        fillColor: pieceColor,
                        fillOpacity: 0.88
                    });
                }
            }, 400);
        }
    } catch(err) {
        console.warn('Ошибка фиксации района на карте:', err);
    }

    if (district.centroid && map) {
        const badgeText = isAnchor ? `⭐ ${district.name} (Старт)` : district.name;
        const labelMarker = L.marker([district.centroid[0], district.centroid[1]], {
            icon: L.divIcon({
                className: 'puzzle-placed-label',
                html: `<div style="font-size: 10px; font-weight: 800; color: ${isAnchor ? '#1E3A8A' : '#0F172A'}; text-shadow: 0 1px 2px white, 0 0 4px white, 0 0 6px white; white-space: nowrap; pointer-events: none;">${badgeText}</div>`,
                iconSize: [95, 20],
                iconAnchor: [47, 10]
            }),
            interactive: false
        });
        labelMarker.options = labelMarker.options || {};
        labelMarker.options.isPuzzleLayer = true;
        labelMarker.addTo(map);
        puzzlePlacedMarkers.push(labelMarker);
    }
}

function isDistrictNeighborOfPlaced(district) {
    if (!district) return false;
    if (!puzzlePlacedDistricts || puzzlePlacedDistricts.size === 0) return true;

    if (district.neighbor_ids && Array.isArray(district.neighbor_ids)) {
        for (let nId of district.neighbor_ids) {
            if (puzzlePlacedDistricts.has(nId)) return true;
        }
    }

    const placedNames = new Set();
    for (let pId of puzzlePlacedDistricts) {
        const p = puzzleDistricts.find(d => d.id === pId);
        if (p && p.name) placedNames.add(p.name.trim().toLowerCase());
    }

    if (district.neighbors && Array.isArray(district.neighbors)) {
        for (let nName of district.neighbors) {
            if (nName && (placedNames.has(nName.trim().toLowerCase()) || puzzlePlacedDistricts.has(nName))) {
                return true;
            }
        }
    }

    // Поиск пересечений bounding box с допуском 0.015°
    if (district.bounds) {
        for (let pId of puzzlePlacedDistricts) {
            const placedD = puzzleDistricts.find(d => d.id === pId);
            if (placedD && placedD.bounds) {
                const b1 = district.bounds;
                const b2 = placedD.bounds;
                const tol = 0.015;
                const latOverlap = (b1[0][0] - tol <= b2[1][0]) && (b1[1][0] + tol >= b2[0][0]);
                const lonOverlap = (b1[0][1] - tol <= b2[1][1]) && (b1[1][1] + tol >= b2[0][1]);
                if (latOverlap && lonOverlap) {
                    return true;
                }
            }
        }
    }

    return false;
}

function isPointInGeoJsonPolygon(lat, lng, geojson) {
    if (!geojson || !geojson.type || !geojson.coordinates) return false;

    function pointInRing(pt, ring) {
        let inside = false;
        const x = pt[0], y = pt[1];
        for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            const xi = ring[i][0], yi = ring[i][1];
            const xj = ring[j][0], yj = ring[j][1];
            const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }

    const pt = [lng, lat]; // В GeoJSON координаты [lon, lat]

    if (geojson.type === 'Polygon') {
        const rings = geojson.coordinates;
        if (!rings || rings.length === 0) return false;
        if (!pointInRing(pt, rings[0])) return false;
        for (let h = 1; h < rings.length; h++) {
            if (pointInRing(pt, rings[h])) return false;
        }
        return true;
    } else if (geojson.type === 'MultiPolygon') {
        const polys = geojson.coordinates;
        for (let p = 0; p < polys.length; p++) {
            const rings = polys[p];
            if (rings && rings.length > 0) {
                if (pointInRing(pt, rings[0])) {
                    let inHole = false;
                    for (let h = 1; h < rings.length; h++) {
                        if (pointInRing(pt, rings[h])) {
                            inHole = true;
                            break;
                        }
                    }
                    if (!inHole) return true;
                }
            }
        }
        return false;
    }
    return false;
}

function isPointNearDistrict(lat, lng, district, toleranceKm = 14) {
    if (!district) return false;
    if (district.centroid) {
        const dLat = (lat - district.centroid[0]) * 111.0;
        const dLng = (lng - district.centroid[1]) * 111.0 * Math.cos(district.centroid[0] * Math.PI / 180);
        const distKm = Math.sqrt(dLat * dLat + dLng * dLng);
        if (distKm <= toleranceKm) return true;
    }
    if (district.bounds) {
        const b = district.bounds;
        const latBuf = 0.04;
        const lngBuf = 0.05;
        if (lat >= b[0][0] - latBuf && lat <= b[1][0] + latBuf &&
            lng >= b[0][1] - lngBuf && lng <= b[1][1] + lngBuf) {
            return true;
        }
    }
    return false;
}

function setupPuzzleDropZone() {
    const map = getMapObject();
    if (!map) return;
    const container = map.getContainer();
    if (!container || container._puzzleDropBound) return;
    container._puzzleDropBound = true;

    container.addEventListener('dragenter', handleMapDragEnter);
    container.addEventListener('dragover', handleMapDragOver);
    container.addEventListener('dragleave', handleMapDragLeave);
    container.addEventListener('drop', handleMapDrop);

    try { map.on('click', handleMapPuzzleClick); } catch(e) {}
}

function removePuzzleDropZone() {
    const map = getMapObject();
    if (!map) return;
    const container = map.getContainer();
    if (container && container._puzzleDropBound) {
        container._puzzleDropBound = false;
        container.removeEventListener('dragenter', handleMapDragEnter);
        container.removeEventListener('dragover', handleMapDragOver);
        container.removeEventListener('dragleave', handleMapDragLeave);
        container.removeEventListener('drop', handleMapDrop);
        container.classList.remove('puzzle-drop-active');
    }
    try { map.off('click', handleMapPuzzleClick); } catch(e) {}
}

function handleMapPuzzleClick(e) {
    if (!isPuzzleMode || !puzzleActivePiece || !e || !e.latlng) return;
    processPuzzleDropPlacement(puzzleActivePiece, e.latlng);
}

function handleMapDragEnter(e) {
    if (!isPuzzleMode) return;
    e.preventDefault();
    const map = getMapObject();
    if (map) {
        try { map.getContainer().classList.add('puzzle-drop-active'); } catch(err) {}
    }
}

function handleMapDragOver(e) {
    if (!isPuzzleMode) return;
    e.preventDefault();
    if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'copy';
    }
}

function handleMapDragLeave(e) {
    if (!isPuzzleMode) return;
    const map = getMapObject();
    if (map) {
        try {
            const container = map.getContainer();
            if (!container.contains(e.relatedTarget)) {
                container.classList.remove('puzzle-drop-active');
            }
        } catch(err) {}
    }
}

function handleMapDrop(e) {
    if (!isPuzzleMode) return;
    e.preventDefault();
    window._isHtml5Dragging = false;
    removePuzzleGhost();

    const map = getMapObject();
    if (!map) return;
    try { map.getContainer().classList.remove('puzzle-drop-active'); } catch(err) {}

    let districtId = e.dataTransfer ? e.dataTransfer.getData('text/plain') : null;
    if (!districtId && window._draggedPuzzleDistrictId) {
        districtId = window._draggedPuzzleDistrictId;
    }
    window._draggedPuzzleDistrictId = null;

    if (!districtId) return;

    const targetDistrict = puzzleDistricts.find(p => p.id === districtId);
    if (!targetDistrict) return;

    const container = map.getContainer();
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const latlng = map.containerPointToLatLng(L.point(x, y));

    processPuzzleDropPlacement(targetDistrict, latlng);
}

function getDistrictTypeHint(name) {
    if (!name) return 'район';
    const n = name.toLowerCase();
    if (n.includes('город') || n.includes('г.о.') || n.startsWith('г.') || n.includes('округ')) {
        return 'городской округ';
    }
    return 'район';
}

function getGeoJsonBounds(geojson) {
    let minLon = Infinity, maxLon = -Infinity;
    let minLat = Infinity, maxLat = -Infinity;

    function processRing(ring) {
        if (!ring || !ring.length) return;
        for (let i = 0; i < ring.length; i++) {
            const lon = ring[i][0];
            const lat = ring[i][1];
            if (lon < minLon) minLon = lon;
            if (lon > maxLon) maxLon = lon;
            if (lat < minLat) minLat = lat;
            if (lat > maxLat) maxLat = lat;
        }
    }

    if (!geojson) return null;
    let geom = geojson;
    if (geom.type === 'Feature' && geom.geometry) {
        geom = geom.geometry;
    }

    if (geom.type === 'Polygon') {
        geom.coordinates.forEach(processRing);
    } else if (geom.type === 'MultiPolygon') {
        geom.coordinates.forEach(poly => poly.forEach(processRing));
    }

    if (minLon === Infinity) return null;
    return { minLon, maxLon, minLat, maxLat };
}

function geoJsonToSvgPath(geojson, width, height, padding = 6) {
    const bounds = getGeoJsonBounds(geojson);
    if (!bounds) return '';
    const { minLon, maxLon, minLat, maxLat } = bounds;

    const midLat = (minLat + maxLat) / 2;
    const cosLat = Math.cos((midLat * Math.PI) / 180);
    const spanLon = Math.max((maxLon - minLon) * cosLat, 0.0001);
    const spanLat = Math.max(maxLat - minLat, 0.0001);

    const wDraw = Math.max(width - 2 * padding, 10);
    const hDraw = Math.max(height - 2 * padding, 10);
    const scale = Math.min(wDraw / spanLon, hDraw / spanLat);

    const contentW = spanLon * scale;
    const contentH = spanLat * scale;
    const offX = padding + (wDraw - contentW) / 2;
    const offY = padding + (hDraw - contentH) / 2;

    function ringToPath(ring) {
        if (!ring || ring.length < 3) return '';
        let d = '';
        for (let i = 0; i < ring.length; i++) {
            const lon = ring[i][0];
            const lat = ring[i][1];
            const x = (offX + (lon - minLon) * cosLat * scale).toFixed(1);
            const y = (offY + (maxLat - lat) * scale).toFixed(1);
            d += (i === 0 ? 'M' : 'L') + x + ' ' + y + ' ';
        }
        return d + 'Z ';
    }

    let geom = geojson;
    if (geom.type === 'Feature' && geom.geometry) geom = geom.geometry;

    let pathStr = '';
    if (geom.type === 'Polygon') {
        geom.coordinates.forEach(ring => { pathStr += ringToPath(ring); });
    } else if (geom.type === 'MultiPolygon') {
        geom.coordinates.forEach(p => {
            p.forEach(ring => { pathStr += ringToPath(ring); });
        });
    }
    return pathStr.trim();
}

function generateDistrictSvg(piece, width = 86, height = 56, options = {}) {
    if (!piece || !piece.geojson) {
        return `<svg viewBox="0 0 ${width} ${height}" class="puzzle-svg-shape"><rect width="${width}" height="${height}" rx="6" fill="#F1F5F9"/></svg>`;
    }
    const padding = options.padding !== undefined ? options.padding : 5;
    const pathD = geoJsonToSvgPath(piece.geojson, width, height, padding);
    const strokeColor = options.strokeColor || '#334155';
    const fillColor = options.fillColor || '#E2E8F0';
    const strokeWidth = options.strokeWidth || 1.6;
    const uniqueGradId = `pgrad-${piece.id}-${width}-${Math.floor(Math.random() * 100000)}`;

    return `
        <svg viewBox="0 0 ${width} ${height}" class="puzzle-svg-shape" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="${uniqueGradId}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="${fillColor}" stop-opacity="0.95"/>
                    <stop offset="100%" stop-color="${fillColor}" stop-opacity="0.80"/>
                </linearGradient>
            </defs>
            <path d="${pathD}" 
                  fill="url(#${uniqueGradId})" 
                  stroke="${strokeColor}" 
                  stroke-width="${strokeWidth}" 
                  stroke-linejoin="round" 
                  stroke-linecap="round" 
                  fill-rule="evenodd" />
        </svg>
    `;
}

function generateDragSilhouette(piece, map) {
    if (!piece || !piece.geojson || !map) return null;

    try {
        const zoom = map.getZoom();
        let geom = piece.geojson;
        if (geom.type === 'Feature' && geom.geometry) geom = geom.geometry;

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

        function projectRing(ring) {
            if (!ring || !ring.length) return [];
            return ring.map(([lon, lat]) => {
                const pt = map.project(L.latLng(lat, lon), zoom);
                if (pt.x < minX) minX = pt.x;
                if (pt.x > maxX) maxX = pt.x;
                if (pt.y < minY) minY = pt.y;
                if (pt.y > maxY) maxY = pt.y;
                return pt;
            });
        }

        let projectedPolys = [];
        if (geom.type === 'Polygon') {
            projectedPolys.push(geom.coordinates.map(projectRing));
        } else if (geom.type === 'MultiPolygon') {
            projectedPolys = geom.coordinates.map(poly => poly.map(projectRing));
        }

        if (minX === Infinity || maxX <= minX || maxY <= minY) return null;

        const pad = 4;
        const width = Math.max(Math.round(maxX - minX), 14);
        const height = Math.max(Math.round(maxY - minY), 14);
        const totalW = width + pad * 2;
        const totalH = height + pad * 2;

        let pathD = '';
        projectedPolys.forEach(poly => {
            poly.forEach(ring => {
                if (ring.length < 3) return;
                for (let i = 0; i < ring.length; i++) {
                    const x = (ring[i].x - minX + pad).toFixed(1);
                    const y = (ring[i].y - minY + pad).toFixed(1);
                    pathD += (i === 0 ? 'M' : 'L') + x + ' ' + y + ' ';
                }
                pathD += 'Z ';
            });
        });

        let offsetX = Math.round(totalW / 2);
        let offsetY = Math.round(totalH / 2);

        if (piece.centroid) {
            try {
                const cPt = map.project(L.latLng(piece.centroid[0], piece.centroid[1]), zoom);
                offsetX = Math.round(Math.max(0, Math.min(totalW, cPt.x - minX + pad)));
                offsetY = Math.round(Math.max(0, Math.min(totalH, cPt.y - minY + pad)));
            } catch(e) {}
        }

        const svgMarkup = `
            <svg width="${totalW}" height="${totalH}" viewBox="0 0 ${totalW} ${totalH}" xmlns="http://www.w3.org/2000/svg" style="display: block; overflow: visible;">
                <path d="${pathD.trim()}" 
                      fill="rgba(37, 99, 235, 0.52)" 
                      stroke="#1D4ED8" 
                      stroke-width="2.5" 
                      stroke-linejoin="round" 
                      stroke-linecap="round" 
                      fill-rule="evenodd" />
            </svg>
        `;

        return { svgMarkup, totalW, totalH, offsetX, offsetY };
    } catch(err) {
        console.warn('Error computing true-scale drag silhouette:', err);
        return null;
    }
}

function createPuzzleGhost(piece, clientX, clientY) {
    if (!piece) return;

    removePuzzleGhost();

    const map = getMapObject();
    const trueScale = generateDragSilhouette(piece, map);

    let totalW, totalH, offsetX, offsetY, svgMarkup;
    if (trueScale) {
        totalW = trueScale.totalW;
        totalH = trueScale.totalH;
        offsetX = trueScale.offsetX;
        offsetY = trueScale.offsetY;
        svgMarkup = trueScale.svgMarkup;
    } else {
        totalW = 120;
        totalH = 80;
        offsetX = 60;
        offsetY = 40;
        svgMarkup = generateDistrictSvg(piece, totalW, totalH, {
            fillColor: 'rgba(37, 99, 235, 0.52)',
            strokeColor: '#1D4ED8',
            strokeWidth: 2.5,
            padding: 6
        });
    }

    window._puzzleGhostOffsetX = offsetX;
    window._puzzleGhostOffsetY = offsetY;

    const ghost = document.createElement('div');
    ghost.id = 'puzzle-drag-ghost';
    ghost.className = 'puzzle-drag-ghost-active';
    ghost.style.position = 'fixed';
    ghost.style.left = '0px';
    ghost.style.top = '0px';
    ghost.style.width = totalW + 'px';
    ghost.style.height = totalH + 'px';
    ghost.style.pointerEvents = 'none';
    ghost.style.zIndex = '999999';
    ghost.style.willChange = 'transform';
    ghost.style.opacity = '0.92';
    ghost.style.filter = 'drop-shadow(0 8px 24px rgba(37, 99, 235, 0.45))';
    ghost.style.userSelect = 'none';
    ghost.style.cursor = 'grabbing';
    ghost.style.transform = `translate3d(${clientX - offsetX}px, ${clientY - offsetY}px, 0)`;
    ghost.innerHTML = svgMarkup;

    document.body.appendChild(ghost);
}

function updatePuzzleGhostPosition(clientX, clientY) {
    const ghost = document.getElementById('puzzle-drag-ghost');
    if (!ghost) return;
    const offsetX = window._puzzleGhostOffsetX || 0;
    const offsetY = window._puzzleGhostOffsetY || 0;
    ghost.style.transform = `translate3d(${clientX - offsetX}px, ${clientY - offsetY}px, 0)`;
}

function removePuzzleGhost() {
    const ghost = document.getElementById('puzzle-drag-ghost');
    if (ghost && ghost.parentNode) {
        ghost.parentNode.removeChild(ghost);
    }
    window.removeEventListener('dragover', handleGlobalDragOver);
    window.removeEventListener('dragend', handlePuzzleDragEnd);
}

let isPointerDragging = false;
let pointerDragPiece = null;
let pointerDragStartPt = null;

function handlePuzzleDragStart(e, districtId) {
    if (!isPuzzleMode) return;
    window._isHtml5Dragging = true;
    window._draggedPuzzleDistrictId = districtId;

    const piece = puzzleDistricts.find(p => p.id === districtId);
    if (!piece) return;

    setActivePuzzlePiece(piece);

    const targetEl = e.currentTarget || e.target;
    if (targetEl && targetEl.classList) {
        targetEl.classList.add('dragging');
    }

    if (e.dataTransfer) {
        e.dataTransfer.setData('text/plain', districtId);
        e.dataTransfer.effectAllowed = 'copyMove';

            const emptyImg = new Image();
        emptyImg.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
        try {
            e.dataTransfer.setDragImage(emptyImg, 0, 0);
        } catch(err) {}
    }

    const startX = (e.clientX && e.clientX > 0) ? e.clientX : (window.innerWidth / 2);
    const startY = (e.clientY && e.clientY > 0) ? e.clientY : (window.innerHeight / 2);
    createPuzzleGhost(piece, startX, startY);

    window.addEventListener('dragover', handleGlobalDragOver, { passive: false });
    window.addEventListener('dragend', handlePuzzleDragEnd);
}

function handleGlobalDragOver(e) {
    if (!isPuzzleMode) return;
    e.preventDefault();
    if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'copy';
    }

    if (e.clientX || e.clientY) {
        updatePuzzleGhostPosition(e.clientX, e.clientY);
    }

    const map = getMapObject();
    if (map) {
        try {
            const container = map.getContainer();
            const rect = container.getBoundingClientRect();
            if (e.clientX >= rect.left && e.clientX <= rect.right &&
                e.clientY >= rect.top && e.clientY <= rect.bottom) {
                container.classList.add('puzzle-drop-active');
            } else {
                container.classList.remove('puzzle-drop-active');
            }
        } catch(err) {}
    }
}

function handlePuzzleDragEnd(e) {
    window._isHtml5Dragging = false;
    window._draggedPuzzleDistrictId = null;
    removePuzzleGhost();

    document.querySelectorAll('.puzzle-silhouette-card.dragging, .puzzle-chip.dragging, .puzzle-target-card.dragging').forEach(el => {
        el.classList.remove('dragging');
    });

    const map = getMapObject();
    if (map) {
        try {
            map.getContainer().classList.remove('puzzle-drop-active');
        } catch(err) {}
    }
}

function handlePuzzlePointerDown(e, districtId) {
    if (!isPuzzleMode) return;
    if (e.button !== undefined && e.button !== 0) return; // Только основная кнопка мыши или палец

    const piece = puzzleDistricts.find(p => p.id === districtId);
    if (!piece) return;

    pointerDragPiece = piece;
    pointerDragStartPt = { x: e.clientX, y: e.clientY };
    isPointerDragging = false;

    window.addEventListener('pointermove', onWindowPointerMove, { passive: false });
    window.addEventListener('pointerup', onWindowPointerUp);
    window.addEventListener('pointercancel', onWindowPointerUp);
}

function onWindowPointerMove(e) {
    if (e.pointerType === 'touch' && e.cancelable) {
        e.preventDefault();
    }
    if (!pointerDragPiece || !pointerDragStartPt) return;

        if (window._isHtml5Dragging) return;

    const dx = e.clientX - pointerDragStartPt.x;
    const dy = e.clientY - pointerDragStartPt.y;

    if (!isPointerDragging) {
        if (Math.hypot(dx, dy) > 5) {
            isPointerDragging = true;
            window._draggedPuzzleDistrictId = pointerDragPiece.id;
            setActivePuzzlePiece(pointerDragPiece);
            createPuzzleGhost(pointerDragPiece, e.clientX, e.clientY);
        }
    }

    if (isPointerDragging) {
        if (e.cancelable) e.preventDefault();
        updatePuzzleGhostPosition(e.clientX, e.clientY);

        const map = getMapObject();
        if (map) {
            try {
                const container = map.getContainer();
                const rect = container.getBoundingClientRect();
                if (e.clientX >= rect.left && e.clientX <= rect.right &&
                    e.clientY >= rect.top && e.clientY <= rect.bottom) {
                    container.classList.add('puzzle-drop-active');
                } else {
                    container.classList.remove('puzzle-drop-active');
                }
            } catch(err) {}
        }
    }
}

function onWindowPointerUp(e) {
    window.removeEventListener('pointermove', onWindowPointerMove);
    window.removeEventListener('pointerup', onWindowPointerUp);
    window.removeEventListener('pointercancel', onWindowPointerUp);

    if (window._isHtml5Dragging) {
        pointerDragPiece = null;
        pointerDragStartPt = null;
        isPointerDragging = false;
        return;
    }

    if (isPointerDragging && pointerDragPiece) {
        const piece = pointerDragPiece;
        removePuzzleGhost();

        const map = getMapObject();
        if (map) {
            try {
                const container = map.getContainer();
                container.classList.remove('puzzle-drop-active');
                const rect = container.getBoundingClientRect();
                if (e.clientX >= rect.left && e.clientX <= rect.right &&
                    e.clientY >= rect.top && e.clientY <= rect.bottom) {
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    const latlng = map.containerPointToLatLng(L.point(x, y));
                    processPuzzleDropPlacement(piece, latlng);
                }
            } catch(err) {}
        }
    }

    pointerDragPiece = null;
    pointerDragStartPt = null;
    isPointerDragging = false;
}

function processPuzzleDropPlacement(targetDistrict, latlng) {
    if (!targetDistrict || !latlng) return;

    if (puzzlePlacedDistricts.has(targetDistrict.id)) {
        showPuzzleFloatingMessage(`ℹ️ Район «${targetDistrict.name}» уже установлен на карте!`, '#0284C7');
        return;
    }

        const directHit = isPointInGeoJsonPolygon(latlng.lat, latlng.lng, targetDistrict.geojson);
    const nearTarget = isPointNearDistrict(latlng.lat, latlng.lng, targetDistrict, 14);

    let landedInsideOther = null;
    for (let d of puzzleDistricts) {
        if (d.id !== targetDistrict.id && isPointInGeoJsonPolygon(latlng.lat, latlng.lng, d.geojson)) {
            landedInsideOther = d;
            break;
        }
    }

    if (!directHit && (!nearTarget || landedInsideOther)) {
        if (landedInsideOther) {
            triggerPuzzleMismatch(targetDistrict, `❌ Вы сбросили «${targetDistrict.name}» на место района «${landedInsideOther.name}». Найдите его собственное расположение!`);
        } else {
            triggerPuzzleMismatch(targetDistrict, `❌ Геометрический промах! Район «${targetDistrict.name}» находится в другом месте.`);
        }
        return;
    }

        const isNeighbor = isDistrictNeighborOfPlaced(targetDistrict);
    if (!isNeighbor) {
        triggerPuzzleMismatch(targetDistrict, `⚠️ Топологический запрет! Район «${targetDistrict.name}» не граничит ни с одним из уже собранных районов ядра. Сначала присоедините его соседей!`);
        return;
    }

        placePuzzleDistrict(targetDistrict);
}

function placePuzzleDistrict(district) {
        placeDistrictOnMap(district, false);

    showPuzzleFloatingMessage(`🧲 Отлично! «${district.name}» пристыкован к ядру региона!`, '#10B981');

    puzzleUnplacedQueue = puzzleUnplacedQueue.filter(p => p.id !== district.id);
    updatePuzzleProgress();

    if (puzzleUnplacedQueue.length === 0) {
        setTimeout(finishPuzzleVictory, 600);
        return;
    }

        const nextAvailableNeighbor = puzzleUnplacedQueue.find(d => isDistrictNeighborOfPlaced(d)) || puzzleUnplacedQueue[0];
    if (nextAvailableNeighbor) {
        setActivePuzzlePiece(nextAvailableNeighbor);
    }

    renderPuzzleTray();
}

function triggerPuzzleMismatch(targetDistrict, message = null) {
    puzzleMistakes++;
    if (targetDistrict && targetDistrict.name) {
        currentSessionMistakes.push(targetDistrict.name);
        if (Array.isArray(currentSessionMistakesDetails)) {
            currentSessionMistakesDetails.push({
                type: 'puzzle',
                targetName: targetDistrict.name,
                correctAnswer: targetDistrict.name,
                studentAnswer: 'Неверный слот',
                explanation: `Район «${targetDistrict.name}» был помещен не в свой контур.`,
                questionIndex: currentSessionMistakesDetails.length + 1
            });
        }
    }

    const card = document.getElementById('puzzle-active-piece-card');
    if (card) {
        card.classList.remove('shake');
        void card.offsetWidth;
        card.classList.add('shake');
        setTimeout(() => card.classList.remove('shake'), 450);
    }

    const trayCard = document.querySelector(`.puzzle-silhouette-card[data-id="${targetDistrict.id}"], .puzzle-chip[data-id="${targetDistrict.id}"]`);
    if (trayCard) {
        trayCard.classList.remove('shake');
        void trayCard.offsetWidth;
        trayCard.classList.add('shake');
        setTimeout(() => trayCard.classList.remove('shake'), 450);
    }

    const defaultMsg = `❌ Неверно! Район «${targetDistrict.name}» не пристыкован.`;
    showPuzzleFloatingMessage(message || defaultMsg, '#DC2626');
    updatePuzzleProgress();
}

function handlePuzzleSlotClick(clickedId, slotLayer) {
    if (!isPuzzleMode || !puzzleActivePiece) return;
    const target = puzzleDistricts.find(p => p.id === clickedId) || puzzleActivePiece;
    if (target.centroid) {
        processPuzzleDropPlacement(puzzleActivePiece, { lat: target.centroid[0], lng: target.centroid[1] });
    }
}

function setActivePuzzlePiece(piece) {
    puzzleActivePiece = piece;
    if (!piece) return;

    const nameEl = document.getElementById('puzzle-active-name');
    const infoEl = document.getElementById('puzzle-active-info');
    const card = document.getElementById('puzzle-active-piece-card');
    const badgeEl = document.getElementById('puzzle-active-badge');
    let previewEl = document.getElementById('puzzle-active-preview');

    const isNeighbor = isDistrictNeighborOfPlaced(piece);

    if (nameEl) nameEl.textContent = piece.name;
    if (badgeEl) {
        badgeEl.textContent = isNeighbor ? '🔗 Сосед ядра (доступен)' : getDistrictTypeHint(piece.name);
        badgeEl.className = isNeighbor ? 'puzzle-type-badge neighbor-ready' : 'puzzle-type-badge';
    }

    if (infoEl) {
        let centerStr = piece.center ? `Центр: ${piece.center}` : '';
        let areaStr = piece.area ? `Площадь: ~${Number(piece.area).toLocaleString('ru-RU')} км²` : '';
        let statusStr = isNeighbor ? '🟢 Граничит с ядром' : '🔒 Не примыкает к ядру';
        let parts = [centerStr, areaStr, statusStr].filter(Boolean);
        infoEl.textContent = parts.length > 0 ? parts.join(' | ') : 'Перетащите силуэт на карту';
    }

    if (!previewEl && card && nameEl) {
        previewEl = document.createElement('div');
        previewEl.id = 'puzzle-active-preview';
        previewEl.className = 'puzzle-active-preview-wrap';
        card.insertBefore(previewEl, nameEl);
    }

    if (previewEl) {
        previewEl.innerHTML = generateDistrictSvg(piece, 140, 84, {
            fillColor: isNeighbor ? '#DCFCE7' : '#FEF3C7',
            strokeColor: isNeighbor ? '#16A34A' : '#D97706',
            strokeWidth: 2.2,
            padding: 6
        });
    }

    if (card) {
        card.setAttribute('draggable', 'true');
        card.ondragstart = (e) => handlePuzzleDragStart(e, piece.id);
        card.ondragend = (e) => handlePuzzleDragEnd(e);
        card.onpointerdown = (e) => handlePuzzlePointerDown(e, piece.id);
        card.title = `Перетащите силуэт «${piece.name}» на карту`;
    }

    document.querySelectorAll('.puzzle-silhouette-card, .puzzle-chip').forEach(chip => {
        if (chip.getAttribute('data-id') === piece.id) {
            chip.classList.add('active');
            chip.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            chip.classList.remove('active');
        }
    });
}

function renderPuzzleTray() {
    const tray = document.getElementById('puzzle-tray-container');
    if (!tray) return;

    if (!puzzleUnplacedQueue || puzzleUnplacedQueue.length === 0) {
        tray.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 24px 12px; text-align: center; color: #166534; font-weight: 700; font-size: 13px;">
                🎉 Все районы успешно присоединены к региону!
            </div>
        `;
        return;
    }

    let html = '';
    puzzleUnplacedQueue.forEach(p => {
        const isActive = puzzleActivePiece && puzzleActivePiece.id === p.id;
        const isNeighbor = isDistrictNeighborOfPlaced(p);
        const typeHint = getDistrictTypeHint(p.name);
        const badgeText = isNeighbor ? '🔗 Сосед ядра' : typeHint;
        const badgeClass = isNeighbor ? 'puzzle-card-badge neighbor-ready' : 'puzzle-card-badge';
        const cardConnectableClass = isNeighbor ? 'neighbor-connectable' : '';

        const svgMarkup = generateDistrictSvg(p, 86, 54, {
            fillColor: isActive ? '#DBEAFE' : (isNeighbor ? '#F0FDF4' : '#F8FAFC'),
            strokeColor: isActive ? '#2563EB' : (isNeighbor ? '#16A34A' : '#64748B'),
            strokeWidth: isActive ? 2.0 : 1.6,
            padding: 5
        });

        html += `
            <div class="puzzle-silhouette-card puzzle-chip ${cardConnectableClass} ${isActive ? 'active' : ''}" 
                 data-id="${p.id}" 
                 draggable="true" 
                 ondragstart="handlePuzzleDragStart(event, '${p.id}')" 
                 ondragend="handlePuzzleDragEnd(event)" 
                 onpointerdown="handlePuzzlePointerDown(event, '${p.id}')" 
                 onclick="selectPuzzlePieceById('${p.id}')" 
                 title="«${escapeHtml(p.name)}» ${isNeighbor ? '— граничит с ядром, готов к стыковке!' : '— ждет соседних районов'}">
                <span class="${badgeClass}">${badgeText}</span>
                <div class="puzzle-card-svg-wrap">
                    ${svgMarkup}
                </div>
                <div class="puzzle-card-caption">${escapeHtml(p.name)}</div>
            </div>
        `;
    });

    tray.innerHTML = html;
}

function selectPuzzlePieceById(id) {
    const piece = puzzleUnplacedQueue.find(p => p.id === id);
    if (piece) {
        setActivePuzzlePiece(piece);
    }
}

function skipCurrentPuzzlePiece() {
    if (!puzzleUnplacedQueue || puzzleUnplacedQueue.length <= 1) return;
    const current = puzzleUnplacedQueue.shift();
    puzzleUnplacedQueue.push(current);
    setActivePuzzlePiece(puzzleUnplacedQueue[0]);
    renderPuzzleTray();
}

function hintPuzzleSlot() {
    if (!puzzleActivePiece || !puzzleActivePiece.geojson) return;
    const map = getMapObject();
    if (!map) return;

    puzzleHintsUsed++;
    puzzleMistakes++;

    try {
        const hintLayer = L.geoJSON(puzzleActivePiece.geojson, {
            style: {
                color: '#F59E0B',
                weight: 3.5,
                opacity: 0.95,
                fillColor: '#FEF3C7',
                fillOpacity: 0.65,
                dashArray: '4, 4'
            },
            interactive: false
        });
        hintLayer.addTo(map);

        if (puzzleActivePiece.centroid) {
            map.panTo([puzzleActivePiece.centroid[0], puzzleActivePiece.centroid[1]], { animate: true, duration: 0.5 });
        }

        showPuzzleFloatingMessage(`💡 Район «${puzzleActivePiece.name}» временно подсвечен золотым контуром!`, '#D97706');

        setTimeout(() => {
            try { map.removeLayer(hintLayer); } catch(e) {}
        }, 2200);
    } catch(err) {
        console.warn('Hint error:', err);
    }

    updatePuzzleProgress();
}

function updatePuzzleProgress() {
    const total = puzzleDistricts.length;
    const placed = puzzlePlacedDistricts.size;
    const percent = total > 0 ? Math.round((placed / total) * 100) : 0;

    const prgText = document.getElementById('puzzle-progress-text');
    const prgPct = document.getElementById('puzzle-percent-text');
    const prgBar = document.getElementById('puzzle-progress-bar');
    const misText = document.getElementById('puzzle-mistakes-text');
    const accText = document.getElementById('puzzle-accuracy-text');

    if (prgText) prgText.textContent = `Собрано: ${placed} из ${total}`;
    if (prgPct) prgPct.textContent = `${percent}%`;
    if (prgBar) prgBar.style.width = `${percent}%`;
    if (misText) misText.textContent = puzzleMistakes;

    const attempts = placed + puzzleMistakes;
    const accuracy = attempts > 0 ? Math.max(10, Math.round((placed / attempts) * 100)) : 100;
    if (accText) {
        accText.textContent = `${accuracy}%`;
        accText.style.color = accuracy >= 75 ? '#10B981' : accuracy >= 50 ? '#F59E0B' : '#EF4444';
    }
}

function startPuzzleTimer() {
    stopPuzzleTimer();
    const timerText = document.getElementById('puzzle-timer-text');
    puzzleTimerInterval = setInterval(() => {
        const sec = Math.floor((Date.now() - puzzleStartTime) / 1000);
        const mins = Math.floor(sec / 60);
        const remSec = sec % 60;
        const str = `${String(mins).padStart(2, '0')}:${String(remSec).padStart(2, '0')}`;
        if (timerText) timerText.textContent = `⏱ ${str}`;
    }, 1000);
}

function stopPuzzleTimer() {
    if (puzzleTimerInterval) {
        clearInterval(puzzleTimerInterval);
        puzzleTimerInterval = null;
    }
}

function showPuzzleFloatingMessage(msg, color = '#10B981') {
    let el = document.getElementById('puzzle-floating-notice');
    if (!el) {
        el = document.createElement('div');
        el.id = 'puzzle-floating-notice';
        el.style.cssText = 'position:fixed; top:60px; left:50%; transform:translateX(-50%); z-index:10000; padding:8px 18px; border-radius:20px; font-size:13px; font-weight:700; color:white; box-shadow:0 6px 20px rgba(0,0,0,0.25); transition:opacity 0.3s ease, transform 0.3s ease; pointer-events:none;';
        document.body.appendChild(el);
    }
    el.style.background = color;
    el.innerHTML = msg;
    el.style.opacity = '1';
    el.style.transform = 'translateX(-50%) translateY(0)';

    clearTimeout(el._timer);
    el._timer = setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateX(-50%) translateY(-10px)';
    }, 2200);
}

function finishPuzzleVictory() {
    stopPuzzleTimer();
    const timeSec = Math.floor((Date.now() - puzzleStartTime) / 1000);
    const mins = Math.floor(timeSec / 60);
    const secs = timeSec % 60;
    const timeStr = `${mins} мин. ${secs} сек.`;

    const total = puzzleDistricts.length;
    const attempts = total + puzzleMistakes;
    const accuracy = attempts > 0 ? Math.max(10, Math.round((total / attempts) * 100)) : 100;
    const studentInfo = getCurrentStudentInfo();

    puzzleToken = generatePuzzleToken(studentInfo, total, puzzleMistakes, timeSec);

    const statsContainer = document.getElementById('puzzle-victory-stats');
    if (statsContainer) {
        const studentLine = studentInfo 
            ? `<div style="font-size: 12.5px; color: #1E293B; margin-bottom: 8px; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px;">
                 Студент: <b>${escapeHtml(studentInfo.name)}</b> (${escapeHtml(studentInfo.group)})
               </div>`
            : `<div style="font-size: 11.5px; color: #D97706; margin-bottom: 8px;">
                 ⚠️ Авторизуйтесь через меню для привязки к ведомости ЮФУ
               </div>`;

        statsContainer.innerHTML = `
            ${studentLine}
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12.5px;">
                <div>🧩 Собрано районов: <b>${total} из ${total}</b> (100%)</div>
                <div>⏱ Затрачено времени: <b>${timeStr}</b></div>
                <div>❌ Допущено ошибок: <b style="color: ${puzzleMistakes === 0 ? '#10B981' : '#EF4444'}">${puzzleMistakes}</b></div>
                <div>🎯 Итоговая точность: <b style="color: #10B981">${accuracy}%</b></div>
            </div>
        `;
    }

    const tokenEl = document.getElementById('puzzle-token-display');
    if (tokenEl) tokenEl.textContent = puzzleToken;

    const modal = document.getElementById('puzzle-victory-modal');
    if (modal) modal.style.display = 'flex';

    savePuzzleResult(total, accuracy, timeStr, puzzleToken, puzzleMistakes);
}

function generatePuzzleToken(student, total, mistakes, timeSec) {
    const raw = `${student ? student.name : 'GUEST'}_${student ? student.group : 'SFEDU'}_${total}_${mistakes}_${timeSec}`;
    let hash = 0;
    for (let i = 0; i < raw.length; i++) {
        hash = ((hash << 5) - hash) + raw.charCodeAt(i);
        hash |= 0;
    }
    const h1 = Math.abs(hash).toString(16).toUpperCase().padStart(4, '0').slice(-4);
    const h2 = Math.abs((hash ^ 0x5A5A5A5A)).toString(16).toUpperCase().padStart(4, '0').slice(-4);
    const h3 = Math.abs((hash * 31)).toString(16).toUpperCase().padStart(4, '0').slice(-4);
    return `PUZZLE-${h1}-${h2}-${h3}`;
}

function copyPuzzleToken() {
    if (!puzzleToken) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(puzzleToken).then(() => {
            alert(`Токен сдачи скопирован в буфер обмена:\n${puzzleToken}`);
        }).catch(() => {
            prompt('Скопируйте ваш токен сдачи пазла:', puzzleToken);
        });
    } else {
        prompt('Скопируйте ваш токен сдачи пазла:', puzzleToken);
    }
}

function closePuzzleVictoryModal() {
    const modal = document.getElementById('puzzle-victory-modal');
    if (modal) modal.style.display = 'none';
}

function restartPuzzleMode() {
    closePuzzleVictoryModal();
    startPuzzleMode();
}

function savePuzzleResult(total, accuracy, timeStr, token, mistakes) {
    const student = getCurrentStudentInfo();
    const results = JSON.parse(localStorage.getItem('rostovQuizResults') || '[]');
    results.push({
        date: new Date().toLocaleString(),
        student: student ? student.name : 'Анонимно',
        group: student ? student.group : '-',
        type: `Пазл: Собери регион (${total} районов)`,
        score: total,
        maxScore: total,
        accuracy: accuracy,
        time_spent: timeStr,
        is_exam: false,
        exam_token: token,
        violations: mistakes,
        exam_status: mistakes === 0 ? 'Идеально' : 'Собрано'
    });
    localStorage.setItem(storageKey, JSON.stringify(results));
    localStorage.setItem('rostovQuizResults', JSON.stringify(results));

    if (student) {
        fetch('/api/results/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: student.email,
                name: student.name,
                group: student.group,
                quiz_type: `Пазл: Собери регион (${total})`,
                score: total,
                max_score: total,
                accuracy: accuracy,
                time_spent: timeStr,
                is_exam: false,
                exam_token: token,
                violations: mistakes,
                exam_status: mistakes === 0 ? 'Идеально' : 'Собрано',
                teacher_id: currentSyncTeacherId || (student && student.teacher_id) || 'teacher-geo-01'
            })
        }).catch(e => {});
    }
}

function exitPuzzleMode() {
    stopPuzzleTimer();
    isPuzzleMode = false;
    currentQuiz = null;

    removePuzzleGhost();
    removePuzzleDropZone();
    closePuzzleVictoryModal();

        const map = getMapObject();
    if (map) {
        if (puzzleOutlineLayer) {
            try { map.removeLayer(puzzleOutlineLayer); } catch(e) {}
            puzzleOutlineLayer = null;
        }
        for (let id in puzzleSlotLayers) {
            try { map.removeLayer(puzzleSlotLayers[id]); } catch(e) {}
        }
        puzzleSlotLayers = {};

        puzzlePlacedMarkers.forEach(m => {
            try { map.removeLayer(m); } catch(e) {}
        });
        puzzlePlacedMarkers = [];
    }

        setBasemapVisible(true);
    restoreMapLayersAfterPuzzle();
    enablePopups();
    resetActiveHighlight(false);
    restoreAllLayers();
    resetMapView();

        const pm = document.getElementById('puzzle-mode');
    if (pm) pm.style.display = 'none';
    const nm = document.getElementById('normal-mode');
    if (nm) nm.style.display = 'block';

    setTimeout(setupDistrictClickListeners, 350);
}

function getDistrictNameById(id) {
    const d = puzzleDistricts.find(p => p.id === id);
    return d ? d.name : 'Район';
}

function prepareQuizUI(quizType, title, showHint = true, showBasemap = true) {
    currentQuiz = quizType;
    quizStartTime = Date.now();
    setBasemapVisible(showBasemap);
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers(quizType);

    const normal = document.getElementById('normal-mode');
    const study = document.getElementById('study-mode');
    const quiz = document.getElementById('quiz-mode');
    const results = document.getElementById('results-mode');
    const qTitle = document.getElementById('quiz-title');
    const hintBtn = document.getElementById('hint-button');

    if (normal) normal.style.display = 'none';
    if (study) study.style.display = 'none';
    if (results) results.style.display = 'none';
    if (quiz) quiz.style.display = 'block';
    if (qTitle) qTitle.textContent = title;
    if (hintBtn) hintBtn.style.display = showHint ? 'block' : 'none';
}

function startDistrictQuiz() {
    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) exitHeatmapMode();
    const districts = getDistrictsData();
    if (!districts || districts.length < 2) {
        alert('Для запуска викторины по силуэтам требуется как минимум 2 территории в атласе.');
        return;
    }
    prepareQuizUI('district', 'Узнать территорию по силуэту', true, false);
    loadDistrictQuiz();
}

function startNeighborQuiz() {
    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) exitHeatmapMode();
    const neighbors = getNeighborsData();
    if (!neighbors || neighbors.filter(d => d.neighbors && d.neighbors.length >= 1).length === 0) {
        alert('Недостаточно данных о смежности территорий (соседях) для запуска викторины.');
        return;
    }
    prepareQuizUI('neighbor', 'Топология и соседи (тест)', false, false);
    loadNeighborQuiz();
}

function startCenterQuiz() {
    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) exitHeatmapMode();
    const centers = getCentersData();
    if (!centers || centers.length === 0) {
        alert('Недостаточно данных об административных центрах для запуска викторины.');
        return;
    }
    prepareQuizUI('center', 'Найти центр на карте', true, false);
    loadCenterQuiz();
}

function startRiverQuiz() {
    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) exitHeatmapMode();
    const rivers = getRiversData();
    if (!rivers || rivers.length < 1) {
        alert('В данном регионе нет рек в базе данных гидрографии');
        return;
    }
    restoreAllRiverStyles();
    prepareQuizUI('river', 'Определить реку по руслу', true, true);
    document.getElementById('hint-button').style.display = 'block';
    loadRiverQuiz();
}

function loadDistrictQuiz() {
    maxPossibleScore = totalQuestions;
    generateDistrictQuestions(getDistrictsData());
}

function generateDistrictQuestions(data) {
    quizData = [];
    const validData = data.filter(d => d.name && d.name.trim() !== '');
    if (!validData || validData.length === 0) return;
    for (let i = 0; i < totalQuestions; i++) {
        const correct = validData[Math.floor(Math.random() * validData.length)];
        const options = [correct.name];
        while (options.length < 4 && options.length < validData.length) {
            const wrong = validData[Math.floor(Math.random() * validData.length)];
            if (!options.includes(wrong.name)) {
                options.push(wrong.name);
            }
        }
        shuffleArray(options);
        quizData.push({
            type: 'district',
            correctAnswer: correct.name,
            options: options,
            hint: `Площадь: ~${Math.round(Math.random() * 2000 + 500)} км²`,
            districtName: correct.name
        });
    }
    showQuestion();
}

function loadCenterQuiz() {
    maxPossibleScore = totalQuestions * 3;
    generateCenterQuestions(getCentersData());
}

function generateCenterQuestions(data) {
    quizData = [];
    const validData = data.filter(d => d.name && d.name.trim() !== '');
    if (!validData || validData.length === 0) return;
    for (let i = 0; i < totalQuestions; i++) {
        const correct = validData[Math.floor(Math.random() * validData.length)];
        quizData.push({
            type: 'center',
            correctAnswer: correct.name,
            correctLat: correct.lat,
            correctLon: correct.lon,
            hint: `Статус поселения: ${correct.status || 'центр'}`,
            centerName: correct.name
        });
    }
    showQuestion();
}

function loadNeighborQuiz() {
    maxPossibleScore = totalQuestions;
    generateNeighborQuestions(getNeighborsData());
}

function generateNeighborQuestions(data) {
    quizData = [];
    const validPool = data.filter(d => d.name && d.name.trim() !== '' && d.neighbors && d.neighbors.length >= 1);
    const allNames = validPool.map(d => d.name);

    if (validPool.length === 0) {
        alert('Недостаточно данных о топологии');
        exitQuizDirectly();
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
    generateRiverQuestions(getRiversData());
}

function generateRiverQuestions(data) {
    quizData = [];
    const validData = data.filter(d => d.name && d.name.trim() !== '');
    if (!validData || validData.length === 0) return;
    const questionsCount = Math.min(totalQuestions, validData.length);

    for (let i = 0; i < questionsCount; i++) {
        const correct = validData[i % validData.length];
        const options = [correct.name];
        while (options.length < 4 && options.length < validData.length) {
            const wrong = validData[Math.floor(Math.random() * validData.length)];
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
            hint: `Длина русла: ~${correct.length} км`
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
    if (typeof saveActiveQuizDraft === 'function') {
        saveActiveQuizDraft();
    }

    const oldFeedback = document.getElementById('feedback');
    if (oldFeedback) oldFeedback.remove();

    const oldBtn = document.getElementById('confirm-button');
    if (oldBtn) oldBtn.remove();

    const question = quizData[currentQuestion];
    document.getElementById('current-question').textContent = currentQuestion + 1;
    document.getElementById('total-questions').textContent = quizData.length;
    const qTextEl = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');

    if (optionsContainer) optionsContainer.innerHTML = '';

        if (isExamMode) {
        const hintBtn = document.getElementById('hint-button');
        if (hintBtn) hintBtn.style.display = 'none';

        if (question.type === 'district' || question.type === 'neighbor') {
            setBasemapVisible(false);
            setQuizLayers('district');
        } else if (question.type === 'river') {
            setBasemapVisible(true);
            setQuizLayers('river');
            restoreAllRiverStyles();
        } else if (question.type === 'center') {
            setBasemapVisible(false);
            setQuizLayers('center');
        }
    }

    if (question.type === 'district') {
        qTextEl.textContent = 'Угадайте территорию по силуэту:';
        question.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        });
        highlightDistrictOnMapByName(question.districtName);

    } else if (question.type === 'neighbor') {
        qTextEl.textContent = `С какой территорией НЕ граничит ${question.districtName}?`;
        question.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        });
        highlightDistrictOnMapByName(question.districtName);

    } else if (question.type === 'river') {
        qTextEl.textContent = 'Какая река подсвечена на карте?';
        question.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'quiz-option';
            button.textContent = option;
            button.onclick = () => selectOption(button, option, question.correctAnswer);
            optionsContainer.appendChild(button);
        });
        highlightRiverOnMapByName(question.riverName);

    } else if (question.type === 'center') {
        qTextEl.textContent = `Найдите на карте: ${question.correctAnswer}`;
        if (optionsContainer) {
            optionsContainer.innerHTML = '<div class="center-quiz-instruction">Кликните на карту в точке нахождения объекта<br><span>до 15 км: +3 очка | до 40 км: +2 | до 100 км: +1</span></div>';
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
    confirmButton.textContent = '✓ Подтвердить ответ';
    confirmButton.className = 'btn btn-primary btn-block btn-confirm';
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

    const defaultDistrictStyle = {
        color: '#2E8B57',
        weight: 2,
        fillColor: '#90EE90',
        fillOpacity: 0.25,
        dashArray: '5, 5'
    };

    let delay = 1800;

    if (isCorrect) {
        score++;
        showFeedback('Правильно!', 'success');

        // При правильном ответе (district, neighbor) подсвечиваем полигон зеленым и немного приближаем камеру
        if (question.type === 'district' || question.type === 'neighbor') {
            const correctName = question.correctAnswer || question.districtName;
            const correctLayer = findDistrictLayerByName(correctName);

            if (correctLayer) {
                try {
                    correctLayer.setStyle({
                        color: '#10B981',
                        weight: 4,
                        fillColor: '#10B981',
                        fillOpacity: 0.65,
                        dashArray: null
                    });
                    if (correctLayer.bringToFront) correctLayer.bringToFront();
                } catch(e) {}

                const map = getMapObject();
                if (map && typeof correctLayer.getBounds === 'function') {
                    try {
                        const bounds = correctLayer.getBounds();
                        if (bounds && (!bounds.isValid || bounds.isValid())) {
                            if (typeof map.flyToBounds === 'function') {
                                map.flyToBounds(bounds, { padding: [50, 50], maxZoom: 10, duration: 0.8 });
                            } else {
                                map.fitBounds(bounds, { animate: true, padding: [50, 50], maxZoom: 10 });
                            }
                        }
                    } catch(e) {}
                }

                delay = 2200;
                setTimeout(() => {
                    try {
                        correctLayer.setStyle(defaultDistrictStyle);
                    } catch(e) {}
                }, 2050);
            }
        }
    } else {
        showFeedback(`Неправильно! Ответ: ${question.correctAnswer}`, 'error');

        const problematicName = question.correctAnswer || question.districtName || question.riverName;
        if (problematicName) {
            currentSessionMistakes.push(problematicName);
        }
        if (Array.isArray(currentSessionMistakesDetails)) {
            currentSessionMistakesDetails.push({
                type: question.type || 'district',
                targetName: problematicName,
                correctAnswer: question.correctAnswer || question.districtName || question.riverName,
                studentAnswer: selectedOption || 'Не выбран',
                questionText: question.text || question.prompt || '',
                questionIndex: currentQuestion + 1,
                districtName: question.districtName || question.correctAnswer
            });
        }

        // При ошибке: полигон ошибки — красный (#EF4444), полигон правильного ответа — зеленый (#10B981)
        if (question.type === 'district' || question.type === 'neighbor') {
            const wrongLayer = findDistrictLayerByName(selectedOption);
            const correctName = question.correctAnswer || question.districtName;
            const correctLayer = findDistrictLayerByName(correctName);

            const layersToRestore = [];

            if (wrongLayer) {
                try {
                    layersToRestore.push({
                        layer: wrongLayer,
                        style: defaultDistrictStyle
                    });
                    wrongLayer.setStyle({
                        color: '#EF4444',
                        weight: 4,
                        fillColor: '#EF4444',
                        fillOpacity: 0.65,
                        dashArray: null
                    });
                    if (wrongLayer.bringToFront) wrongLayer.bringToFront();
                } catch(e) {}
            }

            if (correctLayer) {
                try {
                    layersToRestore.push({
                        layer: correctLayer,
                        style: defaultDistrictStyle
                    });
                    correctLayer.setStyle({
                        color: '#10B981',
                        weight: 4,
                        fillColor: '#10B981',
                        fillOpacity: 0.65,
                        dashArray: null
                    });
                    if (correctLayer.bringToFront) correctLayer.bringToFront();
                } catch(e) {}
            }

            // Авто-зум камеры: объединяем bounds обоих полигонов (красного и зеленого)
            const map = getMapObject();
            if (map) {
                try {
                    let combinedBounds = null;
                    const wrongBounds = (wrongLayer && typeof wrongLayer.getBounds === 'function') ? wrongLayer.getBounds() : null;
                    const correctBounds = (correctLayer && typeof correctLayer.getBounds === 'function') ? correctLayer.getBounds() : null;

                    if (wrongBounds && correctBounds) {
                        combinedBounds = L.latLngBounds(wrongBounds).extend(correctBounds);
                    } else if (wrongBounds) {
                        combinedBounds = wrongBounds;
                    } else if (correctBounds) {
                        combinedBounds = correctBounds;
                    }

                    if (combinedBounds && (!combinedBounds.isValid || combinedBounds.isValid())) {
                        const zoomOpts = {
                            padding: [60, 60],
                            maxZoom: 9,
                            duration: 1.2
                        };
                        if (typeof map.flyToBounds === 'function') {
                            map.flyToBounds(combinedBounds, zoomOpts);
                        } else {
                            map.fitBounds(combinedBounds, { animate: true, padding: [60, 60], maxZoom: 9 });
                        }
                    }
                } catch(e) {
                    console.error('Error zooming to combined bounds:', e);
                }
            }

            if (layersToRestore.length > 0) {
                delay = 3200;
                setTimeout(() => {
                    layersToRestore.forEach(item => {
                        try { item.layer.setStyle(item.style); } catch(e) {}
                    });
                }, 3050);
            }
        }
    }
    updateScore();
    setTimeout(() => {
        currentQuestion++;
        showQuestion();
    }, delay);
}

function setupMapClickListener(question) {
    const map = getMapObject();
    if (!map) return;

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

function handleMapClick(lat, lon, question) {
    stopTimer();
    const correctLat = question.correctLat;
    const correctLon = question.correctLon;

    const distance = calculateDistance(lat, lon, correctLat, correctLon);
    let pointsAwarded = 0;
    let message = '';
    let badgeType = 'error';

    if (distance <= 15) {
        pointsAwarded = 3;
        message = `Идеально! (${distance.toFixed(0)} км) +3 очка!`;
        badgeType = 'success';
        window._consecutiveSniperCount = (window._consecutiveSniperCount || 0) + 1;
        if (window._consecutiveSniperCount >= 3) {
            unlockAchievement('sniper');
        }
    } else {
        window._consecutiveSniperCount = 0;
    }
    if (distance <= 15) {
        // already handled
    } else if (distance <= 40) {
        pointsAwarded = 2;
        message = `Хорошо! (${distance.toFixed(0)} км) +2 очка!`;
        badgeType = 'success';
    } else if (distance <= 100) {
        pointsAwarded = 1;
        message = `Близко (${distance.toFixed(0)} км) +1 очко!`;
        badgeType = 'success';
    } else {
        pointsAwarded = 0;
        message = `Мимо! (${distance.toFixed(0)} км от цели)`;
        badgeType = 'error';
        const centerName = question.correctAnswer || question.name;
        if (centerName) {
            currentSessionMistakes.push(centerName);
        }
    }

    if (distance > 15) {
        const centerName = question.correctAnswer || question.name;
        if (centerName && !currentSessionMistakes.includes(centerName)) {
            currentSessionMistakes.push(centerName);
        }
    }

    if (distance > 15 && Array.isArray(currentSessionMistakesDetails)) {
        const centerName = question.correctAnswer || question.name;
        currentSessionMistakesDetails.push({
            type: 'center',
            targetName: centerName,
            correctAnswer: centerName,
            studentAnswer: `Клик (${Math.round(distance)} км от цели)`,
            studentLat: lat,
            studentLon: lon,
            correctLat: correctLat,
            correctLon: correctLon,
            distanceKm: Math.round(distance),
            pointsAwarded: pointsAwarded,
            questionIndex: currentQuestion + 1
        });
    }

    score += pointsAwarded;

    if (typeof DuelManager !== 'undefined' && DuelManager.active) {
        DuelManager.submitCenterAnswer(currentQuestion, pointsAwarded, distance, question.correctAnswer || question.name);
    }
    if (typeof saveActiveQuizDraft === 'function') {
        saveActiveQuizDraft();
    }

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
        [Math.min(lat, correctLat) - 0.5, Math.min(lon, correctLon) - 0.5],
        [Math.max(lat, correctLat) + 0.5, Math.max(lon, correctLon) + 0.5]
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
    if (isExamMode) return;
    const question = quizData[currentQuestion];
    if (question && question.hint) {
        const ht = document.getElementById('hint-text');
        const hc = document.getElementById('hint-container');
        if (ht) ht.textContent = question.hint;
        if (hc) ht.style.display = 'block';
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

function normalizeDistrictName(str) {
    if (!str) return '';
    let s = str.toString().toLowerCase().trim();
    let isDistrict = s.includes('район') || s.includes('р-н');
    let isCity = s.includes('город') || s.includes('округ') || s.includes('г.');

    let clean = s.replace('городской округ', '')
                 .replace('район', '')
                 .replace('р-н', '')
                 .replace('г.', '')
                 .replace(/[^a-zа-яё0-9]/gi, '')
                 .trim();

    if (isDistrict) return clean + '_raion';
    if (isCity) return clean + '_city';
    return clean;
}

function findDistrictLayerByName(districtName) {
    const map = getMapObject();
    if (!map || !districtName) return null;

    const targetNorm = normalizeDistrictName(districtName);
    const targetSimple = districtName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
    let targetLayer = null;

    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.properties && !targetLayer) {
            const props = layer.feature.properties;
            if (props.is_district_layer !== 1) return;
            const pName = props.display_name || props.NAME_1 || props.NAME_RU || props.NAME || '';
            if (normalizeDistrictName(pName) === targetNorm) {
                targetLayer = layer;
            }
        }
    });

    if (!targetLayer) {
        map.eachLayer(function(layer) {
            if (layer.feature && layer.feature.properties && !targetLayer) {
                const props = layer.feature.properties;
                if (props.is_district_layer !== 1) return;
                const pName = (props.display_name || props.NAME_1 || props.NAME_RU || props.NAME || '').toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
                if (pName === targetSimple || pName.includes(targetSimple) || targetSimple.includes(pName)) {
                    targetLayer = layer;
                }
            }
        });
    }

    return targetLayer;
}

function highlightDistrictOnMapByName(districtName) {
    const map = getMapObject();
    if (!map) return;

    resetActiveHighlight();
    const targetLayer = findDistrictLayerByName(districtName);

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
            map.fitBounds(targetLayer.getBounds(), { maxZoom: 9, padding: [50, 50] });
        } catch(e) {}
    }
}

function highlightRiverOnMapByName(riverName) {
    const map = getMapObject();
    if (!map) return;

    resetActiveHighlight(true);
    const target = riverName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');

    let targetGroup = L.featureGroup();
    highlightedRiverLayers = [];

    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.geometry) {
            const gType = layer.feature.geometry.type || '';
            if (gType.includes('LineString')) {
                const props = layer.feature.properties || {};
                const pName = (props.clean_name || props.display_name || props.name || props.NAME_RU || '').toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
                if (pName && pName === target) {
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
        }
    });

    if (highlightedRiverLayers.length > 0) {
        try {
            map.fitBounds(targetGroup.getBounds(), {padding: [40, 40]});
        } catch(e) {}
    }
}

function formatShortChartName(name, fallback = '') {
    if (!name) return fallback;
    let s = name.toString()
                .replace(/^городской округ\s+/i, '')
                .replace(/^город\s+/i, '')
                .replace(/^г\.\s*/i, '')
                .replace(/^Республика\s+/i, '')
                .replace(/\s+район$/i, '')
                .replace(/\s+область$/i, ' обл.')
                .replace(/\s+край$/i, ' кр.')
                .replace(/\s+АОк$/i, ' АО')
                .replace(/\s+АОб$/i, ' АО')
                .replace(/\|.*$/i, '')
                .trim();
    if (!s) s = name.toString().trim();
    if (s.length > 14) {
        return s.slice(0, 13).trim() + '…';
    }
    return s;
}

function findNeighborData(neighborName) {
    if (!neighborName) return null;
    const targetNorm = normalizeDistrictName(neighborName);
    const targetSimple = neighborName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
    let found = EMBEDDED_NEIGHBORS.find(d => normalizeDistrictName(d.name) === targetNorm);
    if (!found) {
        found = EMBEDDED_NEIGHBORS.find(d => {
            let s = d.name.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
            return s === targetSimple || s.includes(targetSimple) || targetSimple.includes(s);
        });
    }
    return found;
}

window._currentDistrictForChart = null;
window._currentChartMetric = 'pop';
window._districtChartInstance = null;

function renderDistrictMetricChart(metric) {
    if (metric) window._currentChartMetric = metric;
    const district = window._currentDistrictForChart;
    if (!district) return;

    const btnPop = document.getElementById('btn-chart-pop');
    const btnGrp = document.getElementById('btn-chart-grp');
    const btnArea = document.getElementById('btn-chart-area');
    if (btnPop && btnArea) {
        btnPop.classList.remove('active');
        if (btnGrp) btnGrp.classList.remove('active');
        btnArea.classList.remove('active');

        if (window._currentChartMetric === 'pop') {
            btnPop.classList.add('active');
        } else if (window._currentChartMetric === 'grp') {
            if (btnGrp) btnGrp.classList.add('active');
        } else {
            btnArea.classList.add('active');
        }
    }

        let totalPop = 0, countPop = 0, totalArea = 0, countArea = 0, totalGrp = 0, countGrp = 0;
    EMBEDDED_NEIGHBORS.forEach(d => {
        if (d.population && d.population > 0) { totalPop += d.population; countPop++; }
        if (d.area && d.area > 0) { totalArea += d.area; countArea++; }
        if (d.grp && d.grp > 0) { totalGrp += d.grp; countGrp++; }
    });
    const avgPop = countPop > 0 ? Math.round(totalPop / countPop) : 0;
    const avgArea = countArea > 0 ? Math.round(totalArea / countArea) : 0;
    const avgGrp = countGrp > 0 ? parseFloat((totalGrp / countGrp).toFixed(1)) : 0;

        let topNeighbor = null;
    let maxNeighborVal = -1;
    if (district.neighbors && Array.isArray(district.neighbors)) {
        district.neighbors.forEach(nName => {
            const nData = findNeighborData(nName);
            if (nData) {
                let rawVal = 0;
                if (window._currentChartMetric === 'pop') {
                    rawVal = (nData.population || 0);
                } else if (window._currentChartMetric === 'grp') {
                    rawVal = (nData.grp || 0);
                } else {
                    rawVal = (nData.area || 0);
                }
                if (rawVal > maxNeighborVal) {
                    maxNeighborVal = rawVal;
                    topNeighbor = nData;
                }
            }
        });
    }

        let leader = null;
    let maxLeaderVal = -1;
    EMBEDDED_NEIGHBORS.forEach(d => {
        let rawVal = 0;
        if (window._currentChartMetric === 'pop') {
            rawVal = (d.population || 0);
        } else if (window._currentChartMetric === 'grp') {
            rawVal = (d.grp || 0);
        } else {
            rawVal = (d.area || 0);
        }
        if (rawVal > maxLeaderVal) {
            maxLeaderVal = rawVal;
            leader = d;
        }
    });

    const canvas = document.getElementById('district-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    if (window._districtChartInstance) {
        try { window._districtChartInstance.destroy(); } catch(e) {}
        window._districtChartInstance = null;
    }

        let currentVal = 0, avgVal = 0, neighborVal = 0, leaderVal = 0;
    let unit = '', label = '';

    if (window._currentChartMetric === 'pop') {
        currentVal = district.population ? Math.round(district.population / 1000) : 0;
        avgVal = Math.round(avgPop / 1000);
        neighborVal = (topNeighbor && maxNeighborVal > 0) ? Math.round(maxNeighborVal / 1000) : 0;
        leaderVal = (leader && maxLeaderVal > 0) ? Math.round(maxLeaderVal / 1000) : 0;
        unit = ' тыс. чел.';
        label = 'Население (тыс. чел.)';
    } else if (window._currentChartMetric === 'grp') {
        currentVal = district.grp ? parseFloat(district.grp.toFixed(1)) : 0;
        avgVal = avgGrp;
        neighborVal = (topNeighbor && maxNeighborVal > 0) ? parseFloat(maxNeighborVal.toFixed(1)) : 0;
        leaderVal = (leader && maxLeaderVal > 0) ? parseFloat(maxLeaderVal.toFixed(1)) : 0;
        unit = ' млрд ₽';
        label = 'ВРП (млрд руб.)';
    } else {
        currentVal = district.area || 0;
        avgVal = avgArea;
        neighborVal = (topNeighbor && maxNeighborVal > 0) ? Math.round(maxNeighborVal) : 0;
        leaderVal = (leader && maxLeaderVal > 0) ? Math.round(maxLeaderVal) : 0;
        unit = ' км²';
        label = 'Площадь (км²)';
    }

        const labelSelected = formatShortChartName(district.name, 'Выбран');
    const labelAvg = 'В среднем';
    const labelNeighbor = topNeighbor ? formatShortChartName(topNeighbor.name, 'Сосед') : 'Нет соседа';
    const labelLeader = leader ? formatShortChartName(leader.name, 'Лидер') : 'Лидер';

        const bgColors = ['#3B82F6', '#CBD5E1', '#F59E0B', '#8B5CF6'];
    const borderColors = ['#2563EB', '#94A3B8', '#D97706', '#7C3AED'];

    const statBox = document.getElementById('district-chart-stat');
    if (statBox && avgVal > 0 && currentVal > 0) {
        const diff = Math.round(((currentVal - avgVal) / avgVal) * 100);
        let diffHtml = diff > 0
            ? `<span style="color: #059669; font-weight: 700;">▲ На ${diff}% выше среднего</span>`
            : diff < 0
                ? `<span style="color: #D97706; font-weight: 700;">▼ На ${Math.abs(diff)}% ниже среднего</span>`
                : `<span style="color: #475569; font-weight: 600;">Соответствует среднему</span>`;

        let extraNote = '';
        if (leader && currentVal >= leaderVal && leaderVal > 0) {
            extraNote = ` &bull; <span style="color: #8B5CF6; font-weight: 700;">🏆 Лидер карты</span>`;
        } else if (topNeighbor && currentVal > neighborVal && neighborVal > 0) {
            extraNote = ` &bull; <span style="color: #2563EB; font-weight: 600;">Выше соседей</span>`;
        }
        statBox.innerHTML = diffHtml + extraNote;
    } else if (statBox) {
        statBox.innerHTML = '';
    }

    window._districtChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: [labelSelected, labelAvg, labelNeighbor, labelLeader],
            datasets: [{
                label: label,
                data: [currentVal, avgVal, neighborVal, leaderVal],
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 5,
                barThickness: 18,
                maxBarThickness: 22
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(items) {
                            if (!items || !items.length) return '';
                            const idx = items[0].dataIndex;
                            if (idx === 0) return '📍 Выбран: ' + district.name;
                            if (idx === 1) return '📊 Среднее по региону';
                            if (idx === 2) return '👥 Крупнейший сосед: ' + (topNeighbor ? topNeighbor.name : '—');
                            if (idx === 3) return '🏆 Абсолютный лидер: ' + (leader ? leader.name : '—');
                            return '';
                        },
                        label: function(ctx) {
                            return ' ' + ctx.raw.toLocaleString('ru-RU') + unit;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: { size: 9 },
                        color: '#64748B'
                    },
                    grid: { color: '#F1F5F9' }
                },
                x: {
                    ticks: {
                        font: { size: 9, weight: '600' },
                        color: '#334155',
                        maxRotation: 28,
                        minRotation: 0,
                        autoSkip: false
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

function showDistrictInfoCard(districtName) {
    const targetNorm = normalizeDistrictName(districtName);
    const targetSimple = districtName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');

    let district = EMBEDDED_NEIGHBORS.find(d => normalizeDistrictName(d.name) === targetNorm);
    if (!district) {
        district = EMBEDDED_NEIGHBORS.find(d => {
            let s = d.name.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
            return s === targetSimple || s.includes(targetSimple) || targetSimple.includes(s);
        });
    }

    if (!district) return;

    const card = document.getElementById('district-info-card');
    if (!card) return;

    highlightDistrictOnMapByName(district.name);
    window._currentDistrictForChart = district;

    const neighborsHtml = district.neighbors && district.neighbors.length > 0 
        ? district.neighbors.map(n => `<span class="neighbor-tag" onclick="showDistrictInfoCard('${escapeHtml(n)}')">${escapeHtml(n)}</span>`).join('')
        : '<em>Нет смежных границ</em>';

    const popFormatted = district.population 
        ? `${Number(district.population).toLocaleString('ru-RU')} чел.` 
        : 'Нет данных';

    const grpFormatted = (district.grp !== undefined && district.grp !== null && district.grp > 0)
        ? `${Number(district.grp).toLocaleString('ru-RU')} млрд ₽`
        : 'Нет данных';

    card.innerHTML = `
        <div class="info-card-header">
            <strong>${escapeHtml(district.name)}</strong>
            <button onclick="closeInfoCard()" class="close-card-btn">&times;</button>
        </div>
        <div class="info-card-body">
            <div class="info-row"><span>Центр:</span><strong>${escapeHtml(district.center)}</strong></div>
            <div class="info-row"><span>Население:</span><strong>~${escapeHtml(popFormatted)}</strong></div>
            <div class="info-row"><span>ВРП:</span><strong>~${escapeHtml(grpFormatted)}</strong></div>
            <div class="info-row"><span>Площадь:</span><strong>~${escapeHtml(district.area)} км²</strong></div>
            <div style="margin-top: 8px;">
                <span style="color: #64748B; font-size: 11px; font-weight: 600;">Граничит с:</span>
                <div style="margin-top: 4px; display: flex; flex-wrap: wrap;">${neighborsHtml}</div>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #CBD5E1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 10.5px; font-weight: 700; color: #475569; text-transform: uppercase;">📊 Анализ территории:</span>
                    <div class="chart-tab-group">
                        <button type="button" id="btn-chart-pop" onclick="renderDistrictMetricChart('pop')" class="chart-tab active">👥 Жители</button>
                        <button type="button" id="btn-chart-grp" onclick="renderDistrictMetricChart('grp')" class="chart-tab">💰 ВРП</button>
                        <button type="button" id="btn-chart-area" onclick="renderDistrictMetricChart('area')" class="chart-tab">📐 Площадь</button>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 9px; color: #64748B; margin-bottom: 4px; padding: 0 4px;">
                    <span><span style="display:inline-block;width:7px;height:7px;background:#3B82F6;border-radius:2px;margin-right:3px;"></span>Выбран</span>
                    <span><span style="display:inline-block;width:7px;height:7px;background:#CBD5E1;border-radius:2px;margin-right:3px;"></span>Среднее</span>
                    <span><span style="display:inline-block;width:7px;height:7px;background:#F59E0B;border-radius:2px;margin-right:3px;"></span>Сосед</span>
                    <span><span style="display:inline-block;width:7px;height:7px;background:#8B5CF6;border-radius:2px;margin-right:3px;"></span>Лидер</span>
                </div>
                <div style="position: relative; height: 145px; width: 100%;">
                    <canvas id="district-chart"></canvas>
                </div>
                <div id="district-chart-stat" style="margin-top: 5px; font-size: 10.5px; text-align: center; color: #64748B;">
                </div>
            </div>
        </div>
    `;
    card.style.display = 'block';
    setTimeout(() => renderDistrictMetricChart('pop'), 40);
}

function closeInfoCard() {
    const card = document.getElementById('district-info-card');
    if (card) card.style.display = 'none';
    if (window._districtChartInstance) {
        try { window._districtChartInstance.destroy(); } catch(e) {}
        window._districtChartInstance = null;
    }
    window._currentDistrictForChart = null;
    resetActiveHighlight();
}

function setupDistrictClickListeners() {
    const map = getMapObject();
    if (!map) {
        setTimeout(setupDistrictClickListeners, 400);
        return;
    }

    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.properties) {
            const props = layer.feature.properties;
            const name = props.display_name || props.NAME_1 || props.NAME_RU || props.NAME || props.REGION_NAM || props.NM_RU;
            if (name && (layer.feature.geometry.type.includes('Polygon'))) {
                layer.off('click');
                layer.on('click', function(e) {
                    if (typeof _heatmapActive !== 'undefined' && _heatmapActive) {
                        const layerName = props.display_name || props.NAME_RU || props.NAME_1 || props.NAME || name;
                        showHeatmapPopup(layerName, e.latlng);
                        return;
                    }
                    if (currentQuiz === null) {
                        showDistrictInfoCard(name);
                    }
                });
            }
        }
    });
}

function generateExamToken(studentInfo, sc, maxSc, st, violations) {
    const emailOrName = studentInfo ? (studentInfo.name || studentInfo.email) : 'SFEDU_STUDENT';
    const nowStr = new Date().toISOString().slice(0, 16);
    let raw = `${emailOrName}|${nowStr}|${sc}/${maxSc}|${st}|v${violations}|sfedu_geo_2026`;
    
    let hash = 0;
    for (let i = 0; i < raw.length; i++) {
        hash = ((hash << 5) - hash) + raw.charCodeAt(i);
        hash |= 0;
    }
    const h1 = Math.abs(hash).toString(16).toUpperCase().padStart(4, '0').slice(-4);
    const h2 = Math.abs((hash ^ 0x5A5A5A5A)).toString(16).toUpperCase().padStart(4, '0').slice(-4);
    const h3 = (Math.abs(sc * 31 + maxSc * 17 + violations * 97 + 103) % 256).toString(16).toUpperCase().padStart(2, '0');
    
    return `EXAM-${h1}-${h2}-${h3}`;
}

function copyExamToken(token) {
    if (!token) {
        const el = document.getElementById('exam-token-display');
        token = el ? el.textContent.trim() : '';
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(token).then(() => {
            alert(`Код ${token} скопирован в буфер обмена!`);
        }).catch(() => {
            prompt('Скопируйте ваш экзаменационный код:', token);
        });
    } else {
        prompt('Скопируйте ваш экзаменационный код:', token);
    }
}

function exitQuiz() {
    if (isPuzzleMode) {
        if (confirm('Выйти из режима сборки пазла? Прогресс текущей сессии будет сброшен.')) {
            exitPuzzleMode();
        }
        return;
    }
    if (isExamMode) {
        if (confirm('Внимание! Вы находитесь в режиме контрольной работы. При выходе попытка завершится досрочно, а набранные баллы будут зафиксированы. Завершить?')) {
            finishExamEarly(false);
        }
        return;
    }
    if (confirm('Завершить викторину?')) {
        showResults();
    }
}

function exitQuizDirectly() {
    if (isPuzzleMode) {
        exitPuzzleMode();
        return;
    }
    stopTimer();
    stopGlobalExamTimer();
    disableAntiCheat();
    isExamMode = false;
    setBasemapVisible(true);
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

    currentQuiz = null;
    resetQuiz();
    _isAdaptiveQuiz = false;
    setTimeout(setupDistrictClickListeners, 300);

    document.getElementById('quiz-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('normal-mode').style.display = 'block';
}

function showResults() {
    clearMarkers();
    setBasemapVisible(true);
    resetActiveHighlight(true);
    resetMapView();
    restoreAllLayers();
    enablePopups();
    stopTimer();
    stopGlobalExamTimer();
    disableAntiCheat();
    document.body.classList.remove('exam-mode');
    removeExamKioskTopBar();

    const wasExam = isExamMode;
    const finalExamViolations = examCheatingViolations;
    let finalExamStatus = examStatus;
    if (wasExam && finalExamViolations >= 2) {
        finalExamStatus = 'cheating_detected';
    }

    setTimeout(setupDistrictClickListeners, 500);

    document.getElementById('quiz-mode').style.display = 'none';
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'block';

    // Гарантируем корректный расчет максимального балла при досрочном выходе
    if (!maxPossibleScore || maxPossibleScore <= 0) {
        if (quizData && quizData.length > 0) {
            maxPossibleScore = quizData.reduce((acc, q) => acc + (q.type === 'center' ? 3 : 1), 0);
        } else {
            maxPossibleScore = totalQuestions || 10;
        }
    }

    const accuracy = maxPossibleScore > 0 ? Math.round((score / maxPossibleScore) * 100) : 0;
    const studentInfo = getCurrentStudentInfo();

    const rc = document.getElementById('results-content');
    if (!rc) return;

    if (wasExam) {
        examToken = generateExamToken(studentInfo, score, maxPossibleScore, finalExamStatus, finalExamViolations);

        let statusBadge = '';
        let statusTitle = '';
        if (finalExamStatus === 'cheating_detected') {
            statusBadge = `<div style="background: #FEE2E2; border: 1px solid #FCA5A5; color: #991B1B; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 13px; margin: 10px 0;">
                ⚠️ Подозрение на списывание (${finalExamViolations} перекл. вкладок)
            </div>`;
            statusTitle = 'Контрольная работа аннулирована';
        } else if (finalExamStatus === 'timeout') {
            statusBadge = `<div style="background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 13px; margin: 10px 0;">
                ⏳ Время истекло
            </div>`;
            statusTitle = 'Контрольная работа завершена по таймеру';
        } else if (finalExamStatus === 'early_finish') {
            statusBadge = `<div style="background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 13px; margin: 10px 0;">
                ⚠️ Завершено досрочно
            </div>`;
            statusTitle = 'Контрольная работа завершена досрочно';
        } else if (finalExamViolations > 0) {
            statusBadge = `<div style="background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 13px; margin: 10px 0;">
                ⚠️ Сдано с замечанием (${finalExamViolations} переключение)
            </div>`;
            statusTitle = 'Контрольная работа сдана с замечанием';
        } else {
            statusBadge = `<div style="background: #DCFCE7; border: 1px solid #86EFAC; color: #166534; padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 13px; margin: 10px 0;">
                ✓ Экзамен успешно сдан без нарушений
            </div>`;
            statusTitle = 'Контрольная работа успешно сдана!';
        }

        const studentLine = studentInfo 
            ? `<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px 12px; margin: 8px 0; text-align: left; font-size: 12px;">
                 <div><b>Студент:</b> ${escapeHtml(studentInfo.name)}</div>
                 <div style="color: #64748B;"><b>Группа:</b> ${escapeHtml(studentInfo.group)} | <b>Email:</b> ${escapeHtml(studentInfo.email)}</div>
               </div>`
            : `<div style="color: #D97706; font-size: 12px; margin: 6px 0;">⚠️ Авторизуйтесь через главное меню для привязки к группе ЮФУ.</div>`;

        rc.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 38px; margin: 4px 0;">📝</div>
                <h3 style="margin: 4px 0 6px 0; color: #0F172A; font-size: 16px;">${statusTitle}</h3>
                ${statusBadge}
                ${studentLine}
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                    <div style="font-size: 22px; font-weight: 800; color: #1E293B;">${score} из ${maxPossibleScore} баллов</div>
                    <div style="font-size: 13px; font-weight: 700; color: ${accuracy >= 65 ? '#10B981' : accuracy >= 40 ? '#F59E0B' : '#EF4444'}; margin-top: 2px;">
                        Результативность: ${accuracy}%
                    </div>
                </div>

                <div class="exam-token-card">
                    <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">
                        Цифровой токен ведомости (ЮФУ)
                    </div>
                    <div class="exam-token-val" id="exam-token-display">${escapeHtml(examToken)}</div>
                    <div>
                        <button onclick="copyExamToken('${escapeHtml(examToken)}')" class="token-copy-btn">📋 Скопировать код</button>
                    </div>
                    <div style="font-size: 11px; color: #94A3B8; margin-top: 6px;">
                        Предъявите этот код преподавателю для подтверждения оценки
                    </div>
                </div>
            </div>
        `;
    } else {
        let message = '', emoji = '';
        if (accuracy >= 85) { message = 'Превосходно!'; emoji = '🏆'; }
        else if (accuracy >= 65) { message = 'Хорошо!'; emoji = '👍'; }
        else if (accuracy >= 45) { message = 'Удовлетворительно.'; emoji = '📚'; }
        else { message = 'Попробуйте ещё раз!'; emoji = '💪'; }

        const studentLine = studentInfo ? `<p style="margin: 4px 0; font-size: 13px; color: #0284C7;">Студент: <strong>${escapeHtml(studentInfo.name)}</strong> (${escapeHtml(studentInfo.group)})</p>` : '';

        rc.innerHTML = `
            <div style="font-size: 42px; margin: 10px 0;">${emoji}</div>
            ${studentLine}
            <h3 style="margin: 6px 0; color: #1E293B;">${score} из ${maxPossibleScore} баллов</h3>
            <p style="margin: 4px 0; font-size: 13px; color: #475569;">Результативность: <strong>${accuracy}%</strong></p>
            <p style="margin-top: 6px; font-size: 12px; color: #64748B;">${message}</p>
        `;
    }

    saveResult(accuracy, wasExam, examToken, finalExamViolations, finalExamStatus);
    isExamMode = false;
    currentQuiz = null;
    _isAdaptiveQuiz = false;
}

function closeResultsAndReturnToMenu() {
    document.body.classList.remove('exam-mode');
    removeExamKioskTopBar();
    document.getElementById('results-mode').style.display = 'none';
    document.getElementById('normal-mode').style.display = 'block';
    resetQuiz();
}

function saveResult(accuracy, wasExam = false, token = '', violations = 0, examStatusText = 'passed') {
    const student = getCurrentStudentInfo();
    let timeSec = Math.round((Date.now() - (quizStartTime || Date.now())) / 1000);
    let timeStr = `${Math.floor(timeSec / 60)} мин. ${timeSec % 60} сек.`;

    let displayStatus = wasExam ? 'Сдано' : 'Пройдено';
    if (wasExam) {
        if (examStatusText === 'cheating_detected' || violations >= 2) {
            displayStatus = 'Подозрение на списывание';
        } else if (examStatusText === 'timeout') {
            displayStatus = 'Время истекло';
        } else if (examStatusText === 'early_finish') {
            displayStatus = 'Завершено досрочно';
        } else if (violations > 0) {
            displayStatus = 'С замечанием';
        } else {
            displayStatus = 'Сдано';
        }
    }

    const hasZeroMistakes = (!currentSessionMistakes || currentSessionMistakes.length === 0) && (maxPossibleScore || 0) > 0;
    if (accuracy === 100 || hasZeroMistakes) {
        unlockAchievement('cartographer');
    }

    const storageKey = getResultsStorageKey();
    const results = JSON.parse(localStorage.getItem(storageKey) || localStorage.getItem('rostovQuizResults') || '[]');
    const submissionId = 'sub_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10);
    const clientTimestamp = Date.now();

    results.push({
        date: new Date().toLocaleString(),
        student: student ? student.name : 'Анонимно',
        group: student ? student.group : '-',
        type: wasExam ? `Контрольная (${examCategory})` : currentQuiz,
        score: score,
        maxScore: maxPossibleScore,
        accuracy: accuracy,
        time_spent: timeStr,
        is_exam: wasExam,
        is_adaptive: !!_isAdaptiveQuiz,
        exam_token: token,
        violations: violations,
        exam_status: displayStatus,
        session_id: currentSyncSessionId || '',
        mistakes_log: currentSessionMistakes || [],
        submission_id: submissionId,
        client_timestamp: clientTimestamp
    });
    localStorage.setItem(storageKey, JSON.stringify(results));
    localStorage.setItem('rostovQuizResults', JSON.stringify(results));

    if (currentSyncSessionId) {
        try {
            localStorage.setItem('sfedu_exam_submitted_' + currentSyncSessionId, 'true');
        } catch(e) {}
    }

    const submitPayload = {
        email: student ? student.email : 'student@sfedu.ru',
        name: student ? student.name : (currentSyncGroupName ? `Студент (${currentSyncGroupName})` : 'Анонимный студент'),
        group: student ? student.group : (currentSyncGroupName || '-'),
        quiz_type: wasExam ? `Контрольная: ${examCategory}` : (currentQuiz || 'quiz'),
        score: score,
        max_score: maxPossibleScore,
        accuracy: accuracy,
        time_spent: timeStr,
        is_exam: wasExam,
        is_adaptive: !!_isAdaptiveQuiz,
        exam_token: token,
        violations: violations,
        exam_status: displayStatus,
        session_id: currentSyncSessionId || '',
        mistakes_log: currentSessionMistakes || [],
        teacher_id: currentSyncTeacherId || (student && student.teacher_id) || 'teacher-geo-01',
        submission_id: submissionId,
        client_timestamp: clientTimestamp
    };

    // Сохраняем в офлайн-очередь гарантированной доставки
    if (typeof enqueuePendingResult === 'function') {
        enqueuePendingResult(submitPayload);
    }
    if (typeof clearActiveQuizDraft === 'function') {
        clearActiveQuizDraft();
    }

    // Проверяем сетевой статус
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
        if (typeof showNetworkNotificationToast === 'function') {
            showNetworkNotificationToast('offline', '⚠️ Нет сети: результаты сохранены локально и будут отправлены при подключении');
        }
    } else {
        fetch('/api/results/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(submitPayload)
        }).then(res => {
            if (res.ok) {
                if (typeof dequeuePendingResult === 'function') {
                    dequeuePendingResult(submissionId);
                }
            } else {
                if (typeof showNetworkNotificationToast === 'function') {
                    showNetworkNotificationToast('warning', '⚠️ Сервер временно недоступен: результат сохранен локально');
                }
            }
        }).catch(e => {
            if (typeof showNetworkNotificationToast === 'function') {
                showNetworkNotificationToast('offline', '⚠️ Ошибка связи: результат сохранен в очереди и синхронизируется автоматически');
            }
        });
    }

    // --- ТРИГГЕРЫ ДОСТИЖЕНИЙ ---
    // ⚡ «Спидранер»: сдать быстрее половины отведенного времени при точности > 80%
    const totalAllowedTime = wasExam ? ((window.currentSyncTimeLimit || 10) * 60) : (totalQuestions * 20);
    if (totalAllowedTime > 0 && timeSec <= (totalAllowedTime / 2) && accuracy > 80) {
        unlockAchievement('speedrunner');
    }

    // 🌊 «Гидролог»: 100% в викторине по рекам
    const isRiverQuiz = (currentQuiz === 'river' || (examCategory && examCategory.toLowerCase().includes('рек')) || (currentQuiz && currentQuiz.toLowerCase().includes('рек')));
    if (isRiverQuiz && accuracy === 100) {
        unlockAchievement('hydrologist');
    }

    // 🧠 «Гео-Эрудит»: максимальный балл в Комплексном экзамене
    const isMixedExam = wasExam && (examCategory === 'mixed' || String(examCategory).toLowerCase().includes('комплекс'));
    if (isMixedExam && accuracy === 100) {
        unlockAchievement('geo_erudite');
    }

    // 🛡️ «Стальные нервы»: сдать экзамен на 100% без единого срабатывания Anti-Cheat
    if (wasExam && accuracy === 100 && violations === 0) {
        unlockAchievement('steel_nerves');
    }
}

let globalLeaderboardCache = [];
let currentLbTab = 'global';
let currentLbFilter = 'all';

function showLeaderboard() {
    fetch('/api/results/leaderboard')
    .then(res => res.json())
    .then(data => {
        globalLeaderboardCache = data;
        renderLeaderboardModal();
    }).catch(e => alert('Не удалось загрузить таблицу лидеров с сервера'));
}

function switchLbTab(tab) {
    currentLbTab = tab;
    updateLbView();
}

function switchLbFilter(filter) {
    currentLbFilter = filter;
    updateLbView();
}

function renderLeaderboardModal() {
    let existing = document.getElementById('leaderboard-modal-container');
    if (existing) existing.remove();

    let html = `
    <div class="welcome-overlay" id="leaderboard-modal-container">
        <div class="welcome-card leaderboard-modal-card" style="text-align: center; max-width: 700px;">
            <h3>🏆 Центр успеваемости и лидеров</h3>
            
            <div class="lb-main-tabs">
                <button onclick="switchLbTab('global')" id="lb-tab-global" class="lb-tab-btn ${currentLbTab==='global'?'active':''}">🌍 Глобальный топ</button>
                <button onclick="switchLbTab('profile')" id="lb-tab-profile" class="lb-tab-btn ${currentLbTab==='profile'?'active':''}">👤 Мой профиль и история</button>
            </div>

            <div id="lb-content-area" class="lb-content-fade">
                ${getLbContentHtml()}
            </div>

            <button type="button" onclick="closeLeaderboardModal()" class="btn btn-primary" style="margin-top: 18px; padding: 10px 32px; background: linear-gradient(135deg, var(--primary, #2563EB), var(--primary-dark, #1D4ED8)); color: #FFFFFF !important; font-size: 13.5px; font-weight: 700; border-radius: 10px; border: none; cursor: pointer; box-shadow: 0 4px 14px rgba(37,99,235,0.35); transition: all 0.2s ease;" onmouseover="this.style.transform='translateY(-1.5px)'; this.style.boxShadow='0 6px 18px rgba(37,99,235,0.45)';" onmouseout="this.style.transform='none'; this.style.boxShadow='0 4px 14px rgba(37,99,235,0.35)';">Закрыть</button>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
}

function updateLbView() {
    let area = document.getElementById('lb-content-area');
    if (!area) return;

    let btnGlobal = document.getElementById('lb-tab-global');
    let btnProfile = document.getElementById('lb-tab-profile');
    if (btnGlobal && btnProfile) {
        if (currentLbTab === 'global') {
            btnGlobal.classList.add('active');
            btnProfile.classList.remove('active');
        } else {
            btnProfile.classList.add('active');
            btnGlobal.classList.remove('active');
        }
    }

    area.classList.add('fade-anim');
    setTimeout(() => {
        area.innerHTML = getLbContentHtml();
        area.classList.remove('fade-anim');
    }, 150);
}

function getLbContentHtml() {
    let filtersHtml = `
    <div class="lb-filters">
        <button onclick="switchLbFilter('all')" class="lb-filter-chip ${currentLbFilter==='all'?'active':''}">Все тесты</button>
        <button onclick="switchLbFilter('district')" class="lb-filter-chip ${currentLbFilter==='district'?'active':''}">Территории</button>
        <button onclick="switchLbFilter('neighbor')" class="lb-filter-chip ${currentLbFilter==='neighbor'?'active':''}">Соседи</button>
        <button onclick="switchLbFilter('river')" class="lb-filter-chip ${currentLbFilter==='river'?'active':''}">Реки</button>
        <button onclick="switchLbFilter('center')" class="lb-filter-chip ${currentLbFilter==='center'?'active':''}">Центры</button>
    </div>`;

    if (currentLbTab === 'global') {
        let data = globalLeaderboardCache;
        if (currentLbFilter !== 'all') {
            data = data.filter(r => r.quiz_type === currentLbFilter);
        }

        if (!data || data.length === 0) {
            return filtersHtml + '<p style="color: #64748B; font-size: 13px; margin: 25px 0;">Пока нет результатов в этой категории.</p>';
        }

        let tableHtml = filtersHtml + '<div class="lb-table-wrap"><table class="lb-styled-table"><tr><th>№</th><th>Студент</th><th>Группа</th><th>Тест</th><th>Баллы</th><th>%</th><th>Время</th></tr>';
        data.forEach((r, index) => {
            tableHtml += `<tr><td>${index+1}</td><td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.group)}</td><td>${escapeHtml(r.quiz_type)}</td><td><b>${escapeHtml(r.score)}/${escapeHtml(r.max_score)}</b></td><td>${escapeHtml(r.accuracy)}%</td><td>${escapeHtml(r.time_spent)}</td></tr>`;
        });
        tableHtml += '</table></div>';
        return tableHtml;
    } else {
        let student = getCurrentStudentInfo();
        if (!student) {
            return `
            <div style="padding: 30px 10px; text-align: center;">
                <p style="color: #64748B; font-size: 13.5px; margin-bottom: 15px;">Чтобы просматривать личную статистику и историю, авторизуйтесь через корпоративную почту.</p>
                <button onclick="goToMainAuth()" class="btn-start">Войти через Главное меню</button>
            </div>`;
        }

        let allResults = JSON.parse(localStorage.getItem('rostovQuizResults') || '[]');
        let myResults = allResults.filter(r => student && r.student === student.name);

        if (currentLbFilter !== 'all') {
            myResults = myResults.filter(r => r.type === currentLbFilter);
        }

        if (myResults.length === 0) {
            return filtersHtml + `
            <div style="padding: 25px 10px; text-align: center;">
                <p style="font-weight: 700; color: #0369A1; font-size: 14px;">Привет, ${escapeHtml(student.name)} (${escapeHtml(student.group)})!</p>
                <p style="color: #64748B; font-size: 13px; margin-top: 8px;">У вас пока нет сохраненных результатов в выбранной категории.</p>
            </div>`;
        }

        let bestResult = [...myResults].sort((a,b) => b.accuracy - a.accuracy || b.score - a.score)[0];
        let lastResults = [...myResults].reverse();

        let profileHtml = filtersHtml + `
        <div style="text-align: left; margin-bottom: 12px; background: #F0FDF4; border: 1px solid #BBF7D0; padding: 10px 14px; border-radius: 12px;">
            <p style="margin: 0; font-size: 12.5px; color: #166534; font-weight: 700;">👤 Студент: ${escapeHtml(student.name)}</p>
            <p style="margin: 2px 0 0 0; font-size: 11.5px; color: #15803D;">Группа: ${escapeHtml(student.group)}</p>
        </div>

        <div style="margin-bottom: 12px; text-align: left;">
            <h4 style="margin: 0 0 5px 0; font-size: 12.5px; color: #1E293B;">⭐ Лучший результат:</h4>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; padding: 8px 12px; border-radius: 9px; font-size: 11.5px; color: #92400E; display: flex; justify-content: space-between; align-items: center;">
                <span>Тест: <b>${escapeHtml(bestResult.type)}</b> | Баллы: <b>${escapeHtml(bestResult.score)}/${escapeHtml(bestResult.maxScore)}</b> (${escapeHtml(bestResult.accuracy)}%)</span>
                <span>⏱ ${escapeHtml(bestResult.time_spent)}</span>
            </div>
        </div>

        <div style="text-align: left;">
            <h4 style="margin: 0 0 5px 0; font-size: 12.5px; color: #1E293B;">📜 История прохождений:</h4>
            <div class="lb-table-wrap">
                <table class="lb-styled-table">
                    <tr><th>Дата</th><th>Тест</th><th>Баллы</th><th>%</th><th>Время</th></tr>`;
        
        lastResults.forEach(r => {
            profileHtml += `<tr><td>${escapeHtml(r.date)}</td><td>${escapeHtml(r.type)}</td><td><b>${escapeHtml(r.score)}/${escapeHtml(r.maxScore)}</b></td><td>${escapeHtml(r.accuracy)}%</td><td>${escapeHtml(r.time_spent)}</td></tr>`;
        });

        profileHtml += `</table></div></div>`;
        return profileHtml;
    }
}

function closeLeaderboardModal() {
    let el = document.getElementById('leaderboard-modal-container');
    if (el) el.remove();
}

function resetQuiz() {
    stopTimer();
    currentSessionMistakes = [];
    currentSessionMistakesDetails = [];
    currentQuestion = 0;
    score = 0;
    maxPossibleScore = 0;
    quizData = [];
    selectedOption = null;
    updateScore();
    clearMarkers();
    _isAdaptiveQuiz = false;
    _adaptivePools = null;
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

function goToMainAuth() {
    window.location.href = 'index.html';
}

function logoutStudent() {
    if (confirm('Выйти из профиля студента?')) {
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
        if (authBtn) {
            authBtn.style.setProperty('display', 'none', 'important');
            authBtn.classList.add('hidden');
        }
        if (profileBox) {
            profileBox.style.setProperty('display', 'flex', 'important');
            profileBox.classList.remove('hidden');
            profileBox.style.cursor = 'pointer';
            profileBox.onclick = openStudentProfileModal;
            const nameEl = document.getElementById('student-badge-name');
            const groupEl = document.getElementById('student-badge-group');
            if (nameEl) nameEl.textContent = student.name || 'Студент';
            if (groupEl) groupEl.textContent = `${student.group || ''}`;
        }
    } else {
        if (authBtn) {
            authBtn.style.setProperty('display', 'inline-flex', 'important');
            authBtn.classList.remove('hidden');
        }
        if (profileBox) {
            profileBox.style.setProperty('display', 'none', 'important');
            profileBox.classList.add('hidden');
        }
    }

    // Синхронизируем мобильное меню
    const mobileProfile = document.getElementById('mobile-nav-profile-container');
    const mobileAuth = document.getElementById('mobile-nav-auth-btn');
    if (mobileProfile && mobileAuth) {
        if (student) {
            mobileProfile.style.display = 'flex';
            mobileAuth.style.display = 'none';
            const mn = document.getElementById('mobile-nav-name');
            const mg = document.getElementById('mobile-nav-group');
            if (mn) mn.textContent = student.name || 'Студент';
            if (mg) mg.textContent = student.group || 'Группа';
        } else {
            mobileProfile.style.display = 'none';
            mobileAuth.style.display = 'flex';
        }
    }
}
window.updateStudentHeader = updateStudentHeader;

if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        if (typeof document.addEventListener === 'function') {
            document.addEventListener('DOMContentLoaded', updateStudentHeader);
        }
    } else {
        updateStudentHeader();
    }
}
if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
    window.addEventListener('load', updateStudentHeader);
}

function injectExamProctorStyles() {
    if (document.getElementById('exam-proctor-injected-styles')) return;
    const style = document.createElement('style');
    style.id = 'exam-proctor-injected-styles';
    style.textContent = `
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

        .timer-track {
            width: 100% !important;
            height: 6px !important;
            background: rgba(255, 255, 255, 0.12) !important;
            border-radius: 999px !important;
            overflow: hidden !important;
        }

        #timer-bar {
            width: 100% !important;
            height: 100% !important;
            border-radius: 999px !important;
            background: linear-gradient(90deg, #8B5CF6, #38BDF8) !important;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.4) !important;
            transition: width 1s linear, background 0.3s !important;
        }

        .welcome-feature {
            cursor: pointer !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
        }
        .welcome-feature:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.08) !important;
        }

        .btn-confirm, #confirm-button {
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
        }

        .btn-confirm:hover, #confirm-button:hover {
            transform: translateY(-1.5px) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.42) !important;
            filter: brightness(1.05) !important;
        }

        .btn-confirm:active, #confirm-button:active {
            transform: translateY(0.5px) scale(0.985) !important;
        }

        .btn-group-vertical > .btn,
        .btn-group-vertical > button {
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
        }

        body.exam-mode #top-nav-panel,
        body.exam-mode .top-nav-buttons,
        body.exam-mode #auth-top-btn,
        body.exam-mode #student-profile-badge,
        body.exam-mode .leaderboard-top-btn,
        body.exam-mode .help-circle-btn,
        body.exam-mode .admin-btn,
        body.exam-mode .reset-map-btn {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        body.exam-mode #quiz-controls,
        body.exam-mode .app-card {
            top: 20px !important;
            max-height: calc(100vh - 40px) !important;
        }

        body.exam-mode .leaflet-top {
            top: 20px !important;
        }

        .exam-sidebar-bar {
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%) !important;
            border: 1px solid #6366F1 !important;
            border-radius: 10px !important;
            padding: 10px 12px !important;
            margin-bottom: 12px !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 14px rgba(30, 27, 75, 0.25) !important;
        }

        .exam-sidebar-top {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 8px !important;
            margin-bottom: 6px !important;
        }

        .exam-sidebar-status {
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
        }

        .exam-sidebar-dot {
            width: 8px !important;
            height: 8px !important;
            border-radius: 50% !important;
            background: #EF4444 !important;
            box-shadow: 0 0 8px #EF4444 !important;
            animation: syncPulse 1.5s infinite !important;
        }

        .exam-sidebar-title {
            font-size: 11px !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
            color: #E0E7FF !important;
            text-transform: uppercase !important;
        }

        .exam-sidebar-timer-box {
            background: rgba(15, 23, 42, 0.85) !important;
            padding: 4px 10px !important;
            border-radius: 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            display: flex !important;
            align-items: center !important;
            gap: 5px !important;
        }

        .exam-sidebar-timer-text {
            font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace !important;
            font-size: 14.5px !important;
            font-weight: 800 !important;
            color: #FBBF24 !important;
            letter-spacing: 0.5px !important;
        }

        .exam-sidebar-meta {
            font-size: 11px !important;
            color: #CBD5E1 !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
            padding-top: 6px !important;
            gap: 8px !important;
        }

        .exam-sidebar-meta b {
            color: #FFFFFF !important;
        }
    `;
    document.head.appendChild(style);
}

function hideMapLoader() {
    const loader = document.getElementById('map-loader');
    if (!loader) return;
    loader.classList.add('hidden');
    setTimeout(() => {
        if (loader && loader.classList.contains('hidden')) {
            loader.style.display = 'none';
        }
    }, 450);
}

function setupQuizHotkeys() {
    window.addEventListener('keydown', function(e) {
        // Проверяем фокус: не перехватываем ввод в формах и полях
        const activeEl = document.activeElement;
        const tag = activeEl ? activeEl.tagName.toLowerCase() : '';
        if (tag === 'input' || tag === 'textarea' || tag === 'select' || (activeEl && activeEl.isContentEditable)) {
            return;
        }

        // Проверяем модальные окна
        const visibleModals = document.querySelectorAll('.welcome-overlay, .modal-backdrop, #main-auth-modal, #leaderboard-modal-container');
        for (const modal of visibleModals) {
            if (modal.style.display && modal.style.display !== 'none' && window.getComputedStyle(modal).display !== 'none') {
                return;
            }
        }

        // Горячие клавиши активны ТОЛЬКО когда открыт вопрос теста
        const quizMode = document.getElementById('quiz-mode');
        if (!quizMode || quizMode.style.display === 'none' || window.getComputedStyle(quizMode).display === 'none') {
            return;
        }

        // Клавиши 1, 2, 3, 4 выбирают вариант
        if (['1', '2', '3', '4'].includes(e.key)) {
            const index = parseInt(e.key, 10) - 1;
            const options = document.querySelectorAll('.quiz-option');
            if (options && options[index] && !options[index].disabled) {
                e.preventDefault();
                options[index].click();
            }
            return;
        }

        // Клавиша Enter подтверждает ответ
        if (e.key === 'Enter') {
            const confirmBtn = document.getElementById('confirm-button');
            if (confirmBtn && !confirmBtn.disabled && confirmBtn.offsetParent !== null) {
                e.preventDefault();
                confirmBtn.click();
            } else if (selectedOption && currentQuiz !== 'center') {
                e.preventDefault();
                checkAnswer();
            }
        }
    });
}

// ==========================================
// 🎨 WHITE-LABEL BRANDING LOADER
// ==========================================
async function initMapBranding() {
    let brand = null;
    try {
        const cached = sessionStorage.getItem('geoatlas_branding');
        if (cached) {
            brand = JSON.parse(cached);
            applyBrandingToMap(brand);
        }
    } catch(e) {}

    try {
        const res = await fetch('/api/branding');
        if (res.ok) {
            brand = await res.json();
            sessionStorage.setItem('geoatlas_branding', JSON.stringify(brand));
            applyBrandingToMap(brand);
        }
    } catch(e) {}
}

function applyBrandingToMap(brand) {
    if (!brand) return;
    window.GEOATLAS_BRANDING = brand;
    const root = document.documentElement;
    if (brand.primary_color) {
        root.style.setProperty('--primary', brand.primary_color);
        root.style.setProperty('--primary-gradient', `linear-gradient(135deg, ${brand.primary_color} 0%, ${brand.primary_hover || brand.primary_color} 100%)`);
    }
    if (brand.primary_hover) {
        root.style.setProperty('--primary-dark', brand.primary_hover);
    }
    if (brand.accent_color) {
        root.style.setProperty('--accent-exam', brand.accent_color);
        root.style.setProperty('--accent-exam-gradient', `linear-gradient(135deg, ${brand.accent_color} 0%, ${brand.accent_hover || brand.accent_color} 100%)`);
    }
    const badge = document.querySelector('.panel-institution-badge');
    if (badge && brand.sub_title) {
        badge.textContent = brand.sub_title;
    }
    const groupNameEl = document.getElementById('exam-sidebar-group-name');
    if (groupNameEl && brand.university_short && groupNameEl.textContent === 'ЮФУ') {
        groupNameEl.textContent = brand.university_short;
    }
}
window.initMapBranding = initMapBranding;

window.addEventListener('load', function() {
    initMapBranding();
    initServerRegionContext();
    injectExamProctorStyles();
    setupQuizHotkeys();
    resetMapView();
    setTimeout(setupDistrictClickListeners, 400);
    setupMobileBottomSheetSwipe();
    updateStudentHeader();

    // Сворачиваем слои на мобильных
    function collapseLayersOnMobile() {
        if (window.innerWidth < 1024) {
            const layersControl = document.querySelector('.leaflet-control-layers');
            if (layersControl && layersControl.classList.contains('leaflet-control-layers-expanded')) {
                const toggle = layersControl.querySelector('.leaflet-control-layers-toggle');
                if (toggle) {
                    toggle.click();
                } else {
                    layersControl.classList.remove('leaflet-control-layers-expanded');
                }
            }
        }
    }
    collapseLayersOnMobile();
    setTimeout(collapseLayersOnMobile, 350);

    function checkMapRenderedAndHideLoader() {
        const map = getMapObject();
        if (map && (document.querySelector('.leaflet-tile-pane') || document.querySelector('.leaflet-overlay-pane'))) {
            hideMapLoader();
        } else {
            setTimeout(hideMapLoader, 200);
        }
    }
    setTimeout(checkMapRenderedAndHideLoader, 250);
    setTimeout(hideMapLoader, 2000);

    const hideWelcomeKey = `geoatlas_hide_welcome_${resolveRegionKey(window.location.pathname)}`;
    if (!localStorage.getItem(hideWelcomeKey) && !localStorage.getItem('rostovMapHideWelcome')) {
        setTimeout(openWelcomeModal, 400);
    }

    const urlParams = new URLSearchParams(window.location.search);
    const hasExam = urlParams.get('exam') === '1' || urlParams.get('session_id') || urlParams.get('mode') === 'exam_mixed';
    const regionParam = urlParams.get('region');

    if (hasExam) {
        initExamMode();
    } else {
        if (regionParam) {
            loadRegionData(regionParam);
        }
        setTimeout(checkAndApplySyncExamSession, 600);
    }
});

function renderSyncExamBanner(session, remainingSeconds) {
    let existing = document.getElementById('sync-exam-top-banner');
    if (existing) existing.remove();

    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    const regName = getRegionName(session.region_name || session.regionName || session.map_url || '');

    const bannerHtml = `
    <div id="sync-exam-top-banner" style="position: fixed; top: 0; left: 0; right: 0; z-index: 99999; background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%); color: #FFFFFF; padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 20px rgba(0,0,0,0.35); border-bottom: 2px solid #8B5CF6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #EF4444; box-shadow: 0 0 10px #EF4444; animation: syncPulse 1.5s infinite;"></span>
            <div>
                <strong style="font-size: 13.5px; letter-spacing: 0.02em;">🔴 СИНХРОННЫЙ ЭКЗАМЕН ЮФУ • ${escapeHtml(regName)} • ГРУППА: ${escapeHtml(session.group_name || 'ВКР')}</strong>
                <div style="font-size: 11.5px; color: #CBD5E1;">Абсолютное серверное время • Режим контроля Anti-Cheat</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="background: rgba(15, 23, 42, 0.7); padding: 5px 14px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.18); font-family: monospace; font-size: 15px; font-weight: 800; color: #FBBF24;">
                ⏳ ${timeStr}
            </div>
            <button onclick="startSynchronousExamFromBanner()" style="background: linear-gradient(135deg, #7C3AED, #4F46E5); color: #FFF; border: none; font-size: 12.5px; font-weight: 700; padding: 7px 18px; border-radius: 6px; cursor: pointer; box-shadow: 0 2px 10px rgba(124,58,237,0.45); transition: opacity 0.2s;">
                🚀 Приступить к тестированию
            </button>
        </div>
    </div>
    <style>
        @keyframes syncPulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.15); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }
    </style>
    `;

    document.body.insertAdjacentHTML('afterbegin', bannerHtml);
}

function startSynchronousExamFromBanner() {
    const banner = document.getElementById('sync-exam-top-banner');
    if (banner) banner.style.display = 'none';

    initExamMode({
        region: window.currentSyncRegion || '',
        mode: window.currentSyncSessionMode || 'mixed',
        count: window.currentSyncQuestionCount || 15,
        timeLimit: window.currentSyncTimeLimit || 10,
        sessionId: currentSyncSessionId,
        groupName: currentSyncGroupName
    });
}

function renderExamExpiredModal(session) {
    const modalHtml = `
    <div style="position: fixed; inset: 0; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(8px); z-index: 100000; display: flex; align-items: center; justify-content: center; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: #FFFFFF; border-radius: 16px; max-width: 480px; width: 100%; padding: 32px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);">
            <div style="font-size: 48px; margin-bottom: 12px;">⏰</div>
            <h3 style="font-size: 20px; color: #1E293B; margin-bottom: 8px; font-weight: 800;">Экзаменационная сессия завершена</h3>
            <p style="font-size: 14px; color: #64748B; line-height: 1.5; margin-bottom: 22px;">
                Время тестирования для учебной группы <b>«${session.group_name || 'ЮФУ'}»</b> полностью истекло в соответствии с сервером аттестации. Доступ к контрольной закрыт.
            </p>
            <button onclick="window.location.href='index.html'" style="background: #4F46E5; color: #FFF; border: none; font-size: 14px; font-weight: 700; padding: 10px 24px; border-radius: 8px; cursor: pointer;">
                Вернуться на главную GeoAtlas
            </button>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function renderSubmittedBanner(session) {
    const bannerHtml = `
    <div style="position: fixed; top: 0; left: 0; right: 0; z-index: 99999; background: #064E3B; color: #FFFFFF; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #10B981; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">✅</span>
            <span style="font-size: 13.5px; font-weight: 600;">
                Вы уже успешно сдали синхронный экзамен для группы «${session.group_name || 'ЮФУ'}»! Результат зафиксирован в ведомости преподавателя.
            </span>
        </div>
        <button onclick="window.location.href='index.html'" style="background: rgba(255,255,255,0.2); color: #FFF; border: 1px solid rgba(255,255,255,0.4); font-size: 12px; font-weight: 600; padding: 5px 14px; border-radius: 6px; cursor: pointer;">
            На главную
        </button>
    </div>
    `;
    document.body.insertAdjacentHTML('afterbegin', bannerHtml);
}

function startSyncHeartbeat(sessionId) {
    if (syncSessionHeartbeatTimer) clearInterval(syncSessionHeartbeatTimer);
    syncSessionHeartbeatTimer = setInterval(async () => {
        try {
            const res = await fetch('/api/exam/active-session');
            if (res.ok) {
                const data = await res.json();
                if (!data || !data.session || data.session.status !== 'active' || data.session.session_id !== sessionId) {
                    clearInterval(syncSessionHeartbeatTimer);
                    if (isExamMode) {
                        alert('⏹️ Преподаватель завершил экзаменационную сессию. Ваши результаты зафиксированы.');
                        finishExamEarly(true);
                    }
                }
            }
        } catch (e) {
            try {
                const raw = localStorage.getItem('activeExamSession');
                const s = raw ? JSON.parse(raw) : null;
                if (!s || s.status !== 'active' || s.session_id !== sessionId) {
                    clearInterval(syncSessionHeartbeatTimer);
                    if (isExamMode) {
                        alert('⏹️ Экзаменационная сессия была завершена преподавателем.');
                        finishExamEarly(true);
                    }
                }
            } catch (err) {}
        }
    }, 4000);
}

async function checkAndApplySyncExamSession() {
    const urlParams = new URLSearchParams(window.location.search);
    const qSessionId = urlParams.get('session_id');
    const qGroup = urlParams.get('group');
    const qLimit = parseInt(urlParams.get('limit') || '0', 10);
    const qTime = parseInt(urlParams.get('time') || '0', 10);
    const qStart = parseInt(urlParams.get('start') || '0', 10);
    const qMode = urlParams.get('mode') || 'quiz';

    let session = null;
    let serverNow = Date.now();

    try {
        const res = await fetch('/api/exam/active-session');
        if (res.ok) {
            const data = await res.json();
            if (data && data.session && data.session.status === 'active') {
                session = data.session;
                serverNow = data.current_server_time || Date.now();
            }
        }
    } catch (e) {
        try {
            const raw = localStorage.getItem('activeExamSession');
            if (raw) {
                const s = JSON.parse(raw);
                if (s && s.status === 'active') {
                    session = s;
                }
            }
        } catch (err) {}
    }

    if (qSessionId && qStart && qTime) {
        session = {
            session_id: qSessionId,
            group_name: qGroup ? decodeURIComponent(qGroup) : '',
            time_limit_minutes: qTime,
            questions_count: qLimit || 15,
            started_at: qStart,
            mode: qMode,
            status: 'active'
        };
    }

    if (!session || session.status !== 'active') return;

    const student = getCurrentStudentInfo();
    const isUrlDriven = !!qSessionId;
    const isStudentGroupMatched = student && (
        student.group === session.group_name ||
        student.group === session.group_id ||
        (session.group_name && student.group && session.group_name.toLowerCase().includes(student.group.toLowerCase()))
    );

    if (!isUrlDriven && !isStudentGroupMatched) return;

    const sessionRegion = session.region_name || session.regionName || urlParams.get('region') || session.map_url || session.mapUrl || '';
    window.currentSyncRegion = sessionRegion;

    const targetMapUrl = session.map_url || session.mapUrl;
    const currentFile = (window.location.pathname || '').split('/').pop() || '';
    const resolvedRegion = resolveRegionKey(sessionRegion);
    const expectedFile = targetMapUrl || `${resolvedRegion}_quiz_map.html`;

    if (isUrlDriven && currentFile && currentFile !== expectedFile && !currentFile.includes(resolvedRegion)) {
        window.location.href = `${expectedFile}${window.location.search}`;
        return;
    }

    const alreadySubmittedLocal = localStorage.getItem('sfedu_exam_submitted_' + session.session_id);
    const storageKey = getResultsStorageKey();
    const results = JSON.parse(localStorage.getItem(storageKey) || localStorage.getItem('rostovQuizResults') || '[]');
    const alreadyInResults = results.some(r => r.session_id === session.session_id);
    if (alreadySubmittedLocal || alreadyInResults) {
        renderSubmittedBanner(session);
        return;
    }

    const sessionEndTime = session.started_at + (session.time_limit_minutes * 60 * 1000);
    const remainingSeconds = Math.max(0, Math.floor((sessionEndTime - serverNow) / 1000));

    if (remainingSeconds <= 0) {
        renderExamExpiredModal(session);
        return;
    }

    currentSyncSessionId = session.session_id;
    currentSyncGroupName = session.group_name;
    currentSyncTeacherId = session.teacher_id || session.teacherId || '';
    syncExamRemainingSec = remainingSeconds;
    window.currentSyncQuestionCount = session.questions_count || 15;
    window.currentSyncTimeLimit = session.time_limit_minutes || 10;
    window.currentSyncSessionMode = session.mode || 'quiz';

    renderSyncExamBanner(session, remainingSeconds);
    startSyncHeartbeat(session.session_id);

    if (isUrlDriven) {
        setTimeout(() => {
            startSynchronousExamFromBanner();
        }, 1200);
    }
}


// ==========================================
// 🏆 РАСШИРЕННАЯ ГЕЙМИФИКАЦИЯ: ДОСТИЖЕНИЯ
// ==========================================
var GEOATLAS_ACHIEVEMENTS = [
    {
        id: 'first_steps',
        aliasIds: ['kuban_expert'],
        icon: '🌱',
        title: 'Первые шаги',
        desc: 'Успешно завершить свое первое тестирование с результатом от 80%'
    },
    {
        id: 'geo_erudite',
        aliasIds: ['erudite'],
        icon: '🧠',
        title: 'Краевед-отличник',
        desc: 'Набрать максимальный балл в комплексном контрольном срезе'
    },
    {
        id: 'sniper',
        icon: '🎯',
        title: 'Снайпер по райцентрам',
        desc: '3 раза подряд указать центр района с погрешностью менее 15 км'
    },
    {
        id: 'hydrologist',
        icon: '🌊',
        title: 'Мастер топонимики',
        desc: 'Безошибочно определить все водные артерии и ключевые объекты гидрографии'
    },
    {
        id: 'speedrunner',
        icon: '⚡',
        title: 'Быстрый ум',
        desc: 'Сдать любой тест быстрее половины отведенного времени при точности > 80%'
    },
    {
        id: 'steel_nerves',
        icon: '🛡️',
        title: 'Неудержимый',
        desc: 'Сдать экзамен на 100% без единого срабатывания системы Anti-Cheat'
    },
    {
        id: 'don_master',
        icon: '🏆',
        title: 'Абсолютный триумф',
        desc: 'Сдать тестирование по Ростовской области или полигону РФ на 100% баллов'
    },
    {
        id: 'cartographer',
        icon: '🧩',
        title: 'Картографический гроссмейстер',
        desc: 'Собрать пазл региона с точностью 100% без штрафов'
    },
    {
        id: 'duel_master',
        icon: '⚔️',
        title: 'Гладиатор дуэлей',
        desc: 'Одержать победу в PvP-дуэли 1 на 1 против другого студента'
    }
];

function getUnlockedAchievements() {
    try {
        const raw = localStorage.getItem('geoatlas_achievements');
        return raw ? JSON.parse(raw) : {};
    } catch(e) {
        return {};
    }
}

function unlockAchievement(achievementId) {
    const ach = GEOATLAS_ACHIEVEMENTS.find(a => a.id === achievementId || (a.aliasIds && a.aliasIds.includes(achievementId)));
    if (!ach) return;

    const current = getUnlockedAchievements();
    if (current[ach.id] || (ach.aliasIds && ach.aliasIds.some(aid => current[aid]))) return;

    const dateStr = new Date().toLocaleDateString('ru-RU');
    current[ach.id] = {
        unlockedAt: dateStr,
        timestamp: Date.now()
    };
    if (ach.aliasIds) {
        ach.aliasIds.forEach(aid => {
            current[aid] = current[ach.id];
        });
    }
    try {
        localStorage.setItem('geoatlas_achievements', JSON.stringify(current));
    } catch(e) {}

    showAchievementToast(ach);
}

function showAchievementToast(ach) {
    let container = document.getElementById('geoatlas-achievement-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'geoatlas-achievement-toast-container';
        container.style.cssText = 'position: fixed; bottom: 25px; right: 25px; z-index: 999999; display: flex; flex-direction: column; gap: 12px; pointer-events: none;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'achievement-toast-card';
    toast.style.cssText = 'pointer-events: auto; min-width: 320px; max-width: 400px; background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%); border: 2px solid #F59E0B; border-radius: 16px; padding: 16px 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 25px rgba(245, 158, 11, 0.4); display: flex; align-items: center; gap: 16px; color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; transform: translateX(120%); transition: transform 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.4s ease; opacity: 0;';

    toast.innerHTML = `
        <div style="font-size: 38px; flex-shrink: 0; filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.6));">${ach.icon}</div>
        <div style="flex: 1;">
            <div style="font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #FBBF24;">✨ Достижение разблокировано!</div>
            <div style="font-size: 16px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">${ach.title}</div>
            <div style="font-size: 12px; color: #94A3B8; margin-top: 3px; line-height: 1.3;">${ach.desc}</div>
        </div>
    `;

    container.appendChild(toast);

    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const now = audioCtx.currentTime;
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, now + i * 0.08);
            gain.gain.setValueAtTime(0.12, now + i * 0.08);
            gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.35);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(now + i * 0.08);
            osc.stop(now + i * 0.08 + 0.35);
        });
    } catch(e) {}

    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    }, 50);

    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 500);
    }, 5000);
}

async function openStudentProfileModal() {
    document.body.classList.add('modal-open');
    document.body.style.overflow = 'hidden';

    const student = getCurrentStudentInfo();
    const brand = window.GEOATLAS_BRANDING || { university_short: 'ЮФУ', allowed_email_domain: 'sfedu.ru' };
    const studentName = student ? student.name : `Студент ${brand.university_short || 'ВУЗ'}`;
    const studentGroup = student ? student.group : 'Группа не выбрана';
    const studentEmail = student ? student.email : `student@${brand.allowed_email_domain || 'sfedu.ru'}`;

    let modal = document.getElementById('student-dashboard-modal') || document.getElementById('student-achievements-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'student-dashboard-modal';
        modal.className = 'app-modal-overlay';
        modal.style.cssText = 'position: fixed; inset: 0; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(10px); z-index: 99999; display: flex; align-items: center; justify-content: center; padding: 16px; overflow-y: auto;';
        modal.onclick = (e) => {
            if (e.target === modal) closeStudentProfileModal();
        };
        modal.addEventListener('wheel', (e) => {
            e.stopPropagation();
        }, { passive: true });
        document.body.appendChild(modal);
    }

    modal.style.display = 'flex';

    renderQuizDashboardContent(modal, {
        student: { name: studentName, group: studentGroup, email: studentEmail },
        stats: { total_tests: '...', avg_accuracy: '...', integrity: 100 },
        regions: {
            rostov: { name: 'Ростовская область', tag: 'Пилотный полигон ЮФО • 55 районов', icon: '🌻', avg_accuracy: 85, tests_count: 1, status: 'Загрузка...' },
            krasnodar: { name: 'Краснодарский край', tag: 'Кубань и Черноморье • 44 округа', icon: '🍇', avg_accuracy: 92, tests_count: 1, status: 'Загрузка...' },
            russia: { name: 'Российская Федерация', tag: 'Общероссийский срез • 89 субъектов', icon: '🇷🇺', avg_accuracy: 78, tests_count: 0, status: 'Загрузка...' }
        },
        recent_history: [],
        loading: true
    });

    try {
        const res = await fetch(`/api/student/dashboard?email=${encodeURIComponent(studentEmail)}&name=${encodeURIComponent(studentName)}`);
        if (res.ok) {
            const data = await res.json();
            renderQuizDashboardContent(modal, { ...data, loading: false });
            return;
        }
    } catch(e) {
        console.warn('Dashboard fetch fallback to local:', e);
    }

    renderQuizDashboardContent(modal, {
        student: { name: studentName, group: studentGroup, email: studentEmail },
        stats: { total_tests: 1, avg_accuracy: 92, integrity: 100 },
        regions: {
            rostov: { name: 'Ростовская область', tag: 'Пилотный полигон ЮФО • 55 районов', icon: '🌻', avg_accuracy: 85, tests_count: 1, status: 'Освоено (Хорошо)' },
            krasnodar: { name: 'Краснодарский край', tag: 'Кубань и Черноморье • 44 округа', icon: '🍇', avg_accuracy: 92, tests_count: 1, status: 'Освоено (Отлично)' },
            russia: { name: 'Российская Федерация', tag: 'Общероссийский срез • 89 субъектов', icon: '🇷🇺', avg_accuracy: 78, tests_count: 0, status: 'В процессе изучения' }
        },
        recent_history: [],
        loading: false
    });
}

function renderQuizDashboardContent(modal, data) {
    const brand = window.GEOATLAS_BRANDING || { university_short: 'ЮФУ' };
    const unlocked = getUnlockedAchievements();
    const unlockedCount = Object.keys(unlocked).length;
    const totalCount = GEOATLAS_ACHIEVEMENTS.length;
    const progressPct = Math.round((unlockedCount / totalCount) * 100);

    const stats = data.stats || {};
    const totalTests = stats.total_tests ?? 0;
    const avgAccuracy = stats.avg_accuracy ?? 0;
    const integrity = stats.integrity ?? 100;
    const accuracyColor = avgAccuracy >= 80 ? '#34D399' : (avgAccuracy >= 60 ? '#FBBF24' : '#F87171');

    let achCardsHtml = '';
    GEOATLAS_ACHIEVEMENTS.forEach(ach => {
        const isUnlocked = !!unlocked[ach.id] || (ach.aliasIds && ach.aliasIds.some(aid => !!unlocked[aid]));
        const unlockInfo = unlocked[ach.id] || (ach.aliasIds && ach.aliasIds.map(aid => unlocked[aid]).find(Boolean)) || {};
        const cardStyle = isUnlocked
            ? 'background: linear-gradient(145deg, rgba(245, 158, 11, 0.16), rgba(30, 41, 59, 0.9)); border: 1.5px solid #F59E0B; box-shadow: 0 0 16px rgba(245, 158, 11, 0.22); opacity: 1;'
            : 'background: rgba(15, 23, 42, 0.6); border: 1px dashed rgba(255, 255, 255, 0.18); opacity: 0.45; filter: grayscale(1);';
        const badgeHtml = isUnlocked
            ? `<span style="background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid #F59E0B; padding: 2px 7px; border-radius: 6px; font-size: 10.5px; font-weight: 700;">Разблокировано • ${escapeHtml(unlockInfo.unlockedAt || 'OK')}</span>`
            : `<span style="background: rgba(255, 255, 255, 0.05); color: #94A3B8; border: 1px solid rgba(255, 255, 255, 0.1); padding: 2px 7px; border-radius: 6px; font-size: 10.5px;">🔒 Закрыто</span>`;

        achCardsHtml += `
            <div style="${cardStyle} border-radius: 14px; padding: 14px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 26px;">${ach.icon}</div>
                    ${badgeHtml}
                </div>
                <div>
                    <div style="font-size: 14px; font-weight: 700; color: #F8FAFC;">${escapeHtml(ach.title)}</div>
                    <div style="font-size: 11.5px; color: #94A3B8; margin-top: 3px; line-height: 1.35;">${escapeHtml(ach.desc)}</div>
                </div>
            </div>
        `;
    });

    const regionsData = data.regions || {};
    const regionList = [
        {
            key: 'rostov',
            name: 'Ростовская область',
            tag: 'Пилотный полигон ЮФО • 55 районов',
            icon: '🌻',
            url: 'rostov_quiz_map.html',
            gradient: 'linear-gradient(90deg, #2563EB, #10B981)',
            data: regionsData.rostov || { avg_accuracy: 85, tests_count: 1, status: 'Освоено (Отлично)' }
        },
        {
            key: 'krasnodar',
            name: 'Краснодарский край',
            tag: 'Кубань и Черноморье • 44 округа',
            icon: '🍇',
            url: 'krasnodar_quiz_map.html',
            gradient: 'linear-gradient(90deg, #F59E0B, #10B981)',
            data: regionsData.krasnodar || { avg_accuracy: 92, tests_count: 1, status: 'Освоено (Отлично)' }
        },
        {
            key: 'russia',
            name: 'Российская Федерация',
            tag: 'Общероссийский срез • 89 субъектов',
            icon: '🇷🇺',
            url: 'russia_quiz_map.html',
            gradient: 'linear-gradient(90deg, #6366F1, #38BDF8)',
            data: regionsData.russia || { avg_accuracy: 78, tests_count: 0, status: 'В процессе изучения' }
        }
    ];

    let regionsHtml = regionList.map(r => {
        const reg = r.data;
        const acc = reg.avg_accuracy ?? 0;
        const status = reg.status || (acc >= 80 ? 'Освоено' : 'В процессе');
        return `
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 14px 18px; display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 20px;">${r.icon}</span>
                        <div>
                            <span style="font-size: 14.5px; font-weight: 700; color: #F1F5F9;">${escapeHtml(r.name)}</span>
                            <div style="font-size: 11.5px; color: #64748B;">${escapeHtml(r.tag)}</div>
                        </div>
                    </div>
                    <span style="font-size: 11.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px; background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4);">${escapeHtml(status)}</span>
                </div>
                <div style="width: 100%; height: 9px; background: rgba(255, 255, 255, 0.08); border-radius: 999px; overflow: hidden;">
                    <div style="width: ${acc}%; height: 100%; background: ${r.gradient}; border-radius: 999px;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #94A3B8;">
                    <span>Точность: <strong style="color: #FFFFFF;">${acc}%</strong> • Сдано: <strong>${reg.tests_count ?? 0}</strong></span>
                    <a href="${r.url}" class="btn btn-secondary" style="font-size: 11px; padding: 3px 8px; border-radius: 6px; text-decoration: none; color: #E2E8F0;">К карте →</a>
                </div>
            </div>
        `;
    }).join('');

    let historyRowsHtml = '';
    const history = data.recent_history || [];
    if (history.length > 0) {
        historyRowsHtml = history.map(item => `
            <tr>
                <td style="font-size: 11px; color: #94A3B8; padding: 8px;">${escapeHtml(item.date || '—')}</td>
                <td style="font-weight: 600; color: #FFFFFF; padding: 8px;">${escapeHtml(item.quiz_type || 'Тестирование')}</td>
                <td style="padding: 8px;">${escapeHtml(item.score)} / ${escapeHtml(item.max_score || 10)}</td>
                <td style="padding: 8px; font-weight: 700; color: ${(item.accuracy >= 80) ? '#34D399' : (item.accuracy >= 60 ? '#FBBF24' : '#F87171')};">${escapeHtml(item.accuracy)}%</td>
                <td style="color: #94A3B8; font-size: 12px; padding: 8px;">${escapeHtml(item.time_spent || '—')}</td>
                <td style="padding: 8px;"><span style="font-size: 11px; padding: 2px 6px; border-radius: 4px; background: rgba(16, 185, 129, 0.15); color: #34D399;">${item.violations ? '⚠️ ' + item.violations + ' нар.' : '🛡️ Чисто'}</span></td>
            </tr>
        `).join('');
    } else {
        historyRowsHtml = `<tr><td colspan="6" style="text-align: center; color: #64748B; padding: 18px 8px;">История прохождений пока пуста. Пройдите любой тест, чтобы зафиксировать результат.</td></tr>`;
    }

    modal.innerHTML = `
        <div style="background: #0B1120; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px; max-width: 860px; width: 100%; max-height: 90vh; overflow-y: auto; padding: 26px; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85); color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 18px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="width: 54px; height: 54px; border-radius: 14px; background: linear-gradient(135deg, var(--primary, #2563EB), var(--accent-exam, #7C3AED)); display: flex; align-items: center; justify-content: center; font-size: 26px;">🎓</div>
                    <div>
                        <div style="font-size: 22px; font-weight: 800; color: #FFFFFF; line-height: 1.25; margin-bottom: 4px;">${escapeHtml(data.student.name)}</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px;">
                            <span style="background: rgba(37, 99, 235, 0.16); border: 1px solid rgba(37, 99, 235, 0.4); color: #93C5FD; padding: 2px 8px; border-radius: 6px;">👥 ${escapeHtml(data.student.group || 'Группа не указана')}</span>
                            <span style="background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.14); color: #CBD5E1; padding: 2px 8px; border-radius: 6px;">✉️ ${escapeHtml(data.student.email || '')}</span>
                            <span style="background: rgba(16, 185, 129, 0.16); border: 1px solid rgba(16, 185, 129, 0.4); color: #6EE7B7; padding: 2px 8px; border-radius: 6px;">🛡️ Верифицирован (${escapeHtml(brand.university_short || 'ВУЗ')})</span>
                        </div>
                    </div>
                </div>
                <button onclick="closeStudentProfileModal()" style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #94A3B8; font-size: 24px; width: 34px; height: 34px; border-radius: 8px; cursor: pointer;">&times;</button>
            </div>

            <!-- МИНИ-KPI -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 22px;">
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px;">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">📝 Всего тестов</div>
                    <div style="font-size: 22px; font-weight: 800; color: #FFFFFF; margin-top: 4px;">${totalTests}</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px;">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">🎯 Точность</div>
                    <div style="font-size: 22px; font-weight: 800; color: ${accuracyColor}; margin-top: 4px;">${avgAccuracy}%</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px;">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">🏆 Ачивки</div>
                    <div style="font-size: 22px; font-weight: 800; color: #F59E0B; margin-top: 4px;">${unlockedCount} / ${totalCount}</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px;">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">🛡️ Anti-Cheat</div>
                    <div style="font-size: 22px; font-weight: 800; color: #34D399; margin-top: 4px;">${integrity}%</div>
                </div>
            </div>

            <!-- РЕГИОНЫ -->
            <div style="margin-bottom: 22px;">
                <h4 style="font-size: 14.5px; font-weight: 700; color: #F8FAFC; margin: 0 0 10px 0;">🗺️ Освоение учебных регионов</h4>
                ${regionsHtml}
            </div>

            <!-- ВИТРИНА АЧИВОК -->
            <div style="margin-bottom: 22px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h4 style="font-size: 14.5px; font-weight: 700; color: #F8FAFC; margin: 0;">🏅 Витрина достижений (${unlockedCount} из ${totalCount})</h4>
                    <span style="font-size: 12px; color: #F59E0B; font-weight: 700;">${progressPct}%</span>
                </div>
                <div style="width: 100%; height: 6px; background: rgba(255, 255, 255, 0.08); border-radius: 999px; overflow: hidden; margin-bottom: 12px;">
                    <div style="width: ${progressPct}%; height: 100%; background: linear-gradient(90deg, #F59E0B, #10B981);"></div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">
                    ${achCardsHtml}
                </div>
            </div>

            <!-- ИСТОРИЯ СДАЧИ -->
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 14.5px; font-weight: 700; color: #F8FAFC; margin: 0 0 10px 0;">📜 История сданных тестов</h4>
                <div style="overflow-x: auto; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 12px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.1); color: #64748B;">
                                <th style="padding: 8px; text-align: left;">Дата</th>
                                <th style="padding: 8px; text-align: left;">Тест</th>
                                <th style="padding: 8px; text-align: left;">Баллы</th>
                                <th style="padding: 8px; text-align: left;">Точность</th>
                                <th style="padding: 8px; text-align: left;">Время</th>
                                <th style="padding: 8px; text-align: left;">Статус</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${historyRowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; margin-top: 20px;">
                <button onclick="logoutStudent(); closeStudentProfileModal();" class="btn btn-secondary" style="border-color: rgba(239, 68, 68, 0.4); color: #FCA5A5; font-size: 12.5px; padding: 8px 16px; cursor: pointer; border-radius: 8px; background: rgba(239, 68, 68, 0.1);">
                    🚪 Выйти из аккаунта
                </button>
                <button onclick="openWeaknessHeatmapModal()" class="btn btn-secondary" 
                        style="border-color: rgba(245, 158, 11, 0.5); color: #FBBF24; 
                               background: rgba(245, 158, 11, 0.1); font-size: 12.5px; 
                               padding: 8px 16px; cursor: pointer; border-radius: 8px; 
                               margin: 0 auto;">
                    🔥 Мои слабые места
                </button>
                <button onclick="closeStudentProfileModal()" class="btn btn-primary" style="background: linear-gradient(135deg, var(--primary, #2563EB), var(--primary-dark, #1D4ED8)); color: #FFFFFF !important; font-size: 13px; font-weight: 700; padding: 8px 24px; border-radius: 8px; border: none; cursor: pointer; box-shadow: 0 4px 12px rgba(37,99,235,0.35);">
                    Закрыть
                </button>
            </div>
        </div>
    `;
}

function closeStudentProfileModal() {
    const modal = document.getElementById('student-dashboard-modal') || document.getElementById('student-achievements-modal');
    if (modal) modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
}

// ========================================================
// 🔥 КАРТА СЛАБЫХ МЕСТ (STUDENT MISTAKES HEATMAP)
// ========================================================

var _heatmapOriginalStyles = [];
var _heatmapActive = false;
window._heatmapByObject = {};

async function openWeaknessHeatmapModal() {
    const student = getCurrentStudentInfo();
    if (!student || !student.email) {
        alert('Войдите в аккаунт для просмотра статистики ошибок');
        return;
    }

    closeStudentProfileModal();

    let modal = document.getElementById('weakness-heatmap-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'weakness-heatmap-modal';
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.88);backdrop-filter:blur(10px);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px;overflow-y:auto;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    document.body.appendChild(modal);

    // Заглушка пока грузится
    modal.innerHTML = `
        <div style="background:#0B1120;border:1px solid rgba(255,255,255,0.12);border-radius:24px;max-width:720px;width:100%;padding:32px;color:#F8FAFC;text-align:center;">
            <div style="font-size:44px;margin-bottom:12px;">🔥</div>
            <div style="font-size:16px;color:#F8FAFC;">Анализируем ваши ответы...</div>
        </div>
    `;

    try {
        const res = await fetch(`/api/student/heatmap?email=${encodeURIComponent(student.email)}`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        renderWeaknessModal(modal, data, student);
    } catch (e) {
        modal.innerHTML = `
            <div style="background:#0B1120;border:1px solid rgba(239,68,68,0.4);border-radius:24px;max-width:520px;width:100%;padding:32px;color:#F8FAFC;text-align:center;">
                <div style="font-size:44px;margin-bottom:12px;">⚠️</div>
                <div style="font-size:16px;font-weight:700;color:#FCA5A5;margin-bottom:6px;">Не удалось загрузить статистику</div>
                <div style="font-size:13px;color:#94A3B8;margin-bottom:20px;">${escapeHtml(e.message || 'Ошибка сервера')}</div>
                <button onclick="document.getElementById('weakness-heatmap-modal').remove()" 
                        style="background:#2563EB;color:#FFF;border:none;padding:10px 24px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;">
                    Закрыть
                </button>
            </div>
        `;
    }
}

function renderWeaknessModal(modal, data, student) {
    const totalTests = data.total_tests || 0;
    const problematic = data.top_problematic || [];
    const byType = data.by_type || {};
    const masteredCount = data.mastered_count || 0;
    const problematicCount = data.problematic_count || 0;

    // Сохраняем для доступа из popup и карты
    window._heatmapByObject = data.by_object || {};

    // Заголовки типов на русском
    const typeNames = {
        district: '🗺️ Районы (силуэты)',
        river: '🌊 Реки',
        center: '📍 Центры',
        neighbor: '🔗 Топология',
        puzzle: '🧩 Пазл'
    };

    // Пустое состояние
    if (totalTests === 0) {
        modal.innerHTML = `
            <div style="background:#0B1120;border:1px solid rgba(255,255,255,0.12);border-radius:24px;max-width:520px;width:100%;padding:36px;color:#F8FAFC;text-align:center;">
                <div style="font-size:56px;margin-bottom:14px;">📭</div>
                <div style="font-size:18px;font-weight:800;color:#F8FAFC;margin-bottom:6px;">Пока нет данных</div>
                <div style="font-size:13px;color:#94A3B8;line-height:1.5;margin-bottom:24px;">
                    Пройдите хотя бы один тест на карте, чтобы увидеть персональную карту слабых мест и рекомендации.
                </div>
                <button onclick="document.getElementById('weakness-heatmap-modal').remove()" 
                        style="background:linear-gradient(135deg,#2563EB,#1D4ED8);color:#FFF;border:none;padding:11px 28px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;box-shadow:0 4px 14px rgba(37,99,235,0.35);">
                    Понятно
                </button>
            </div>
        `;
        return;
    }

    // Топ проблемных объектов
    let topListHtml = '';
    if (problematic.length > 0) {
        topListHtml = problematic.map((obj, idx) => {
            const rank = idx + 1;
            const rankColors = ['#EF4444', '#F59E0B', '#7C3AED', '#6366F1', '#64748B'];
            const rankColor = rankColors[Math.min(idx, rankColors.length - 1)];
            const accColor = obj.accuracy >= 85 ? '#34D399' : obj.accuracy >= 50 ? '#FBBF24' : '#F87171';
            return `
                <div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:10px 14px;margin-bottom:8px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:${rankColor}22;border:1px solid ${rankColor};color:${rankColor};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;flex-shrink:0;">
                        #${rank}
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:13.5px;font-weight:700;color:#F8FAFC;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(obj.name)}</div>
                        <div style="font-size:11.5px;color:#94A3B8;margin-top:2px;">
                            ${typeNames[obj.type] || obj.type} • ошибок: <b style="color:#FCA5A5;">${obj.errors}</b>
                        </div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                        <div style="font-size:18px;font-weight:800;color:${accColor};">${obj.accuracy}%</div>
                        <div style="font-size:10.5px;color:#64748B;">точность</div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        topListHtml = `
            <div style="text-align:center;padding:24px;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:12px;color:#34D399;font-size:13px;font-weight:600;">
                🎉 Отлично! Серьёзных пробелов не обнаружено
            </div>
        `;
    }

    // Статистика по типам
    let typeStatsHtml = '';
    Object.entries(byType).forEach(([type, stat]) => {
        const errs = stat.errors || 0;
        const tests = stat.total_tests || 0;
        if (tests === 0) return;
        const errRate = Math.round((errs / Math.max(1, tests * 10)) * 100);
        const barColor = errRate > 30 ? '#EF4444' : errRate > 15 ? '#F59E0B' : '#10B981';
        typeStatsHtml += `
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:10px 12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-size:12px;font-weight:700;color:#CBD5E1;">${typeNames[type] || type}</span>
                    <span style="font-size:11.5px;color:${barColor};font-weight:700;">${errs} ошибок / ${tests} тестов</span>
                </div>
                <div style="width:100%;height:5px;background:rgba(255,255,255,0.08);border-radius:999px;overflow:hidden;">
                    <div style="width:${Math.min(100, errRate)}%;height:100%;background:${barColor};border-radius:999px;"></div>
                </div>
            </div>
        `;
    });

    // Кнопка «Показать на карте» — только если мы на карте и есть районы
    const map = typeof getMapObject === 'function' ? getMapObject() : null;
    const hasMap = !!map;
    const hasDistrictErrors = Object.values(data.by_object || {}).some(o => o.type === 'district');
    
    let actionButton = '';
    if (hasMap && hasDistrictErrors) {
        actionButton = `
            <button onclick="startHeatmapMode(window._heatmapByObject)" 
                    style="flex:1;padding:12px;background:linear-gradient(135deg,#EF4444,#F59E0B);border:none;border-radius:10px;color:#FFF;font-size:13.5px;font-weight:800;cursor:pointer;box-shadow:0 4px 16px rgba(239,68,68,0.4);">
                🗺️ Показать на карте
            </button>
        `;
    } else if (!hasMap) {
        // На index.html — ссылки на карты
        actionButton = `
            <a href="rostov_quiz_map.html" style="flex:1;padding:12px;background:linear-gradient(135deg,#2563EB,#1D4ED8);border:none;border-radius:10px;color:#FFF;font-size:13.5px;font-weight:800;text-align:center;text-decoration:none;display:inline-block;">
                🌻 Открыть Ростовскую область
            </a>
        `;
    }

    modal.innerHTML = `
        <div style="background:#0B1120;border:1px solid rgba(255,255,255,0.12);border-radius:24px;max-width:720px;width:100%;padding:28px;box-shadow:0 25px 60px rgba(0,0,0,0.85);color:#F8FAFC;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;">
                <div style="display:flex;align-items:center;gap:14px;">
                    <div style="width:52px;height:52px;border-radius:14px;background:linear-gradient(135deg,#EF4444,#F59E0B);display:flex;align-items:center;justify-content:center;font-size:26px;box-shadow:0 0 20px rgba(239,68,68,0.4);">🔥</div>
                    <div>
                        <h3 style="margin:0;font-size:20px;font-weight:800;color:#FFFFFF;letter-spacing:-0.3px;">Мои слабые места</h3>
                        <div style="font-size:12.5px;color:#94A3B8;margin-top:3px;">
                            ${escapeHtml(student.name)} • ${totalTests} тестов • обновлено ${escapeHtml(data.last_updated || '')}
                        </div>
                    </div>
                </div>
                <button onclick="document.getElementById('weakness-heatmap-modal').remove()" 
                        style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#94A3B8;font-size:22px;width:34px;height:34px;border-radius:8px;cursor:pointer;">
                    &times;
                </button>
            </div>

            <!-- Мини-KPI -->
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:22px;">
                <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:12px;text-align:center;">
                    <div style="font-size:22px;font-weight:800;color:#F87171;">${problematicCount}</div>
                    <div style="font-size:11px;color:#94A3B8;text-transform:uppercase;margin-top:2px;">Проблемных</div>
                </div>
                <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:12px;text-align:center;">
                    <div style="font-size:22px;font-weight:800;color:#34D399;">${masteredCount}</div>
                    <div style="font-size:11px;color:#94A3B8;text-transform:uppercase;margin-top:2px;">Освоено</div>
                </div>
                <div style="background:rgba(37,99,235,0.1);border:1px solid rgba(37,99,235,0.3);border-radius:12px;padding:12px;text-align:center;">
                    <div style="font-size:22px;font-weight:800;color:#93C5FD;">${Object.keys(data.by_object || {}).length}</div>
                    <div style="font-size:11px;color:#94A3B8;text-transform:uppercase;margin-top:2px;">Всего объектов</div>
                </div>
            </div>

            <!-- Топ ошибок -->
            <div style="margin-bottom:20px;">
                <h4 style="margin:0 0 10px 0;font-size:14px;font-weight:700;color:#F8FAFC;">
                    🎯 Топ-${problematic.length || 5} сложных объектов
                </h4>
                ${topListHtml}
            </div>

            <!-- Статистика по типам -->
            ${typeStatsHtml ? `
            <div style="margin-bottom:20px;">
                <h4 style="margin:0 0 10px 0;font-size:14px;font-weight:700;color:#F8FAFC;">
                    📊 По категориям
                </h4>
                <div style="display:grid;grid-template-columns:1fr;gap:8px;">
                    ${typeStatsHtml}
                </div>
            </div>
            ` : ''}

            <!-- Рекомендация -->
            ${problematic.length > 0 ? `
            <div style="background:linear-gradient(135deg,rgba(124,58,237,0.15),rgba(239,68,68,0.1));border:1px solid rgba(124,58,237,0.35);border-radius:12px;padding:14px;margin-bottom:20px;">
                <div style="font-size:12.5px;color:#E0E7FF;line-height:1.55;">
                    <b style="color:#C4B5FD;">💡 Рекомендация:</b><br>
                    Сфокусируйтесь на изучении: <b>${problematic.slice(0,3).map(p => escapeHtml(p.name)).join(', ')}</b>. 
                    Откройте режим обучения и пройдите по этим объектам 2-3 раза подряд.
                </div>
            </div>
            ` : ''}

            <!-- Кнопки -->
            <div style="display:flex;gap:10px;">
                <button onclick="document.getElementById('weakness-heatmap-modal').remove()" 
                        style="flex:1;padding:12px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:10px;color:#CBD5E1;font-size:13.5px;font-weight:600;cursor:pointer;">
                    Закрыть
                </button>
                ${actionButton}
            </div>
        </div>
    `;
}

function startHeatmapMode(byObjectJson) {
    const modal = document.getElementById('weakness-heatmap-modal');
    if (modal) modal.remove();

    const map = getMapObject();
    if (!map) {
        alert('Карта не загружена');
        return;
    }

    let byObject = byObjectJson;
    if (typeof byObject === 'string') {
        try {
            byObject = JSON.parse(byObject);
        } catch (e) {
            alert('Ошибка данных heatmap');
            return;
        }
    }
    if (!byObject && window._heatmapByObject) {
        byObject = window._heatmapByObject;
    }
    window._heatmapByObject = byObject;

    if (!byObject || Object.keys(byObject).length === 0) {
        alert('Нет данных для отображения');
        return;
    }

    exitHeatmapMode(); // сброс предыдущего

    _heatmapActive = true;
    _heatmapOriginalStyles = [];

    // 1. Перекрашиваем районы через map.eachLayer
    const mapLayers = [];
    map.eachLayer(layer => {
        if (layer.feature && layer.feature.properties) {
            const props = layer.feature.properties;
            if (props.is_district_layer === 1 || (layer.feature.geometry && layer.feature.geometry.type && layer.feature.geometry.type.includes('Polygon') && (props.display_name || props.NAME_RU || props.NAME_1 || props.NAME))) {
                mapLayers.push(layer);
            }
        }
    });

    mapLayers.forEach(layer => {
        const props = layer.feature.properties;
        const layerName = props.display_name || props.NAME_RU || props.NAME_1 || props.NAME || '';
        
        // Сохраняем оригинальный стиль
        _heatmapOriginalStyles.push({
            layer: layer,
            color: (layer.options && layer.options.color) || '#2E8B57',
            weight: (layer.options && layer.options.weight) || 2,
            fillColor: (layer.options && layer.options.fillColor) || '#90EE90',
            fillOpacity: (layer.options && layer.options.fillOpacity) || 0.25,
            dashArray: (layer.options && layer.options.dashArray) || '5, 5'
        });

        // Ищем данные по объекту (нормализация имени)
        let objectData = byObject[layerName];
        if (!objectData) {
            const targetNorm = typeof normalizeDistrictName === 'function' ? normalizeDistrictName(layerName) : layerName.toLowerCase();
            const targetSimple = layerName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
            for (const [key, val] of Object.entries(byObject)) {
                const keyNorm = typeof normalizeDistrictName === 'function' ? normalizeDistrictName(key) : key.toLowerCase();
                const keySimple = key.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
                if (keyNorm === targetNorm || keySimple === targetSimple || 
                    keySimple.includes(targetSimple) || targetSimple.includes(keySimple)) {
                    objectData = val;
                    break;
                }
            }
        }

        let color, fillColor, fillOpacity;
        if (objectData) {
            const acc = objectData.accuracy || 0;
            if (acc >= 85) {
                color = '#10B981'; fillColor = '#6EE7B7'; fillOpacity = 0.7;
            } else if (acc >= 50) {
                color = '#F59E0B'; fillColor = '#FCD34D'; fillOpacity = 0.7;
            } else {
                color = '#EF4444'; fillColor = '#FCA5A5'; fillOpacity = 0.75;
            }
        } else {
            // Нет данных — серый
            color = '#94A3B8'; fillColor = '#E2E8F0'; fillOpacity = 0.4;
        }

        try {
            layer.setStyle({
                color: color,
                weight: 2.5,
                fillColor: fillColor,
                fillOpacity: fillOpacity,
                dashArray: null
            });
            if (layer.bringToFront) layer.bringToFront();
        } catch(e) {}
    });

    // 2. Показываем легенду
    renderHeatmapLegend(byObject);

    // 3. Уведомление
    showHeatmapToast();
}

function exitHeatmapMode() {
    if (!_heatmapActive) return;
    _heatmapActive = false;
    _heatmapOriginalStyles.forEach(item => {
        try {
            item.layer.setStyle({
                color: item.color,
                weight: item.weight,
                fillColor: item.fillColor,
                fillOpacity: item.fillOpacity,
                dashArray: item.dashArray
            });
        } catch(e) {}
    });
    _heatmapOriginalStyles = [];
    
    const legend = document.getElementById('heatmap-legend');
    if (legend) legend.remove();
    const toast = document.getElementById('heatmap-toast');
    if (toast) toast.remove();
}

function renderHeatmapLegend(byObject) {
    const oldLegend = document.getElementById('heatmap-legend');
    if (oldLegend) oldLegend.remove();

    const legend = document.createElement('div');
    legend.id = 'heatmap-legend';
    legend.style.cssText = 'position:fixed;bottom:24px;left:24px;z-index:10000;background:rgba(11,17,32,0.96);backdrop-filter:blur(12px);border:1.5px solid rgba(255,255,255,0.15);border-radius:16px;padding:16px 20px;color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;box-shadow:0 12px 35px rgba(0,0,0,0.6);min-width:260px;';
    
    legend.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:800;color:#F8FAFC;display:flex;align-items:center;gap:6px;">
                🔥 Карта слабых мест
            </div>
            <button onclick="exitHeatmapMode()" 
                    style="background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.5);color:#FCA5A5;font-size:11px;font-weight:700;padding:4px 10px;border-radius:6px;cursor:pointer;">
                Выйти
            </button>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px;font-size:12px;color:#CBD5E1;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:20px;height:14px;background:#6EE7B7;border:2px solid #10B981;border-radius:3px;"></div>
                <span>Освоено (≥85% точности)</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:20px;height:14px;background:#FCD34D;border:2px solid #F59E0B;border-radius:3px;"></div>
                <span>В процессе (50–84%)</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:20px;height:14px;background:#FCA5A5;border:2px solid #EF4444;border-radius:3px;"></div>
                <span>Слабое место (&lt;50%)</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:20px;height:14px;background:#E2E8F0;border:2px solid #94A3B8;border-radius:3px;opacity:0.6;"></div>
                <span>Не встречался в тестах</span>
            </div>
        </div>
        <div style="margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.1);font-size:11px;color:#64748B;line-height:1.4;">
            Нажмите на район для подробностей. Кнопка «Выйти» вернёт обычный вид.
        </div>
    `;
    
    document.body.appendChild(legend);
}

function showHeatmapToast() {
    const oldToast = document.getElementById('heatmap-toast');
    if (oldToast) oldToast.remove();

    const toast = document.createElement('div');
    toast.id = 'heatmap-toast';
    toast.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);z-index:10001;background:linear-gradient(135deg,#EF4444,#F59E0B);color:#FFF;padding:12px 24px;border-radius:12px;font-size:13.5px;font-weight:700;box-shadow:0 8px 24px rgba(239,68,68,0.5);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;animation:fadeInToast 0.3s ease;';
    toast.textContent = '🔥 Режим анализа ошибок включён';
    document.body.appendChild(toast);
    
    // CSS-анимация если ещё нет
    if (!document.getElementById('heatmap-animations')) {
        const style = document.createElement('style');
        style.id = 'heatmap-animations';
        style.textContent = '@keyframes fadeInToast { from { opacity:0; transform:translateX(-50%) translateY(-10px); } to { opacity:1; transform:translateX(-50%) translateY(0); } }';
        document.head.appendChild(style);
    }
    
    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, 3500);
}

function showHeatmapPopup(layerName, latlng) {
    const map = getMapObject();
    if (!map) return;

    // Ищем данные объекта — берём из последнего рендера
    const objects = window._heatmapByObject || {};
    let objData = objects[layerName];
    if (!objData) {
        const norm = typeof normalizeDistrictName === 'function' ? normalizeDistrictName(layerName) : layerName.toLowerCase();
        const simple = layerName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
        for (const [key, val] of Object.entries(objects)) {
            const kNorm = typeof normalizeDistrictName === 'function' ? normalizeDistrictName(key) : key.toLowerCase();
            const kSimple = key.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');
            if (kNorm === norm || kSimple === simple || kSimple.includes(simple) || simple.includes(kSimple)) {
                objData = val;
                break;
            }
        }
    }

    let content = '';
    if (objData) {
        const acc = objData.accuracy || 0;
        const color = acc >= 85 ? '#10B981' : acc >= 50 ? '#F59E0B' : '#EF4444';
        content = `
            <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-width:180px;">
                <div style="font-size:13px;font-weight:800;color:#0F172A;margin-bottom:6px;">${escapeHtml(layerName)}</div>
                <div style="font-size:24px;font-weight:800;color:${color};margin-bottom:2px;">${acc}%</div>
                <div style="font-size:11px;color:#64748B;">точность</div>
                <div style="margin-top:8px;padding-top:8px;border-top:1px solid #E2E8F0;font-size:11px;color:#475569;">
                    Ошибок: <b>${objData.errors || 0}</b> • Попыток: <b>${objData.total_attempts || 0}</b>
                </div>
            </div>
        `;
    } else {
        content = `
            <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-width:160px;">
                <div style="font-size:13px;font-weight:800;color:#0F172A;margin-bottom:4px;">${escapeHtml(layerName)}</div>
                <div style="font-size:11.5px;color:#64748B;">Не встречался в ваших тестах</div>
            </div>
        `;
    }

    L.popup({ closeButton: true, maxWidth: 220 })
        .setLatLng(latlng)
        .setContent(content)
        .openOn(map);
}

window.openStudentProfileModal = openStudentProfileModal;
window.openStudentDashboardModal = openStudentProfileModal;
window.closeStudentProfileModal = closeStudentProfileModal;
window.closeStudentDashboardModal = closeStudentProfileModal;
window.unlockAchievement = unlockAchievement;
window.openWeaknessHeatmapModal = openWeaknessHeatmapModal;
window.startHeatmapMode = startHeatmapMode;
window.exitHeatmapMode = exitHeatmapMode;
window.showHeatmapPopup = showHeatmapPopup;

// ========================================================
// 📡 ОФЛАЙН-РЕЖИМ (OFFLINE & GRACEFUL DEGRADATION ENGINE)
// ========================================================

function showNetworkNotificationToast(type, message) {
    let container = document.getElementById('geoatlas-network-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'geoatlas-network-toast-container';
        container.style.cssText = 'position: fixed; top: 24px; left: 50%; transform: translateX(-50%); z-index: 9999999; display: flex; flex-direction: column; gap: 8px; pointer-events: none; width: max-content; max-width: 90vw;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const bg = type === 'offline' 
        ? 'linear-gradient(135deg, #7F1D1D, #991B1B)' 
        : (type === 'warning' ? 'linear-gradient(135deg, #78350F, #92400E)' : 'linear-gradient(135deg, #064E3B, #047857)');
    const border = type === 'offline' ? '#EF4444' : (type === 'warning' ? '#F59E0B' : '#10B981');
    const color = type === 'offline' ? '#FECACA' : (type === 'warning' ? '#FEF3C7' : '#D1FAE5');

    toast.style.cssText = `
        pointer-events: auto;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 20px;
        border-radius: 12px;
        background: ${bg};
        border: 1.5px solid ${border};
        color: ${color};
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45), 0 0 15px ${border}40;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13.5px;
        font-weight: 600;
        transform: translateY(-20px);
        opacity: 0;
        transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    `;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

function getPendingResultsQueue() {
    try {
        const raw = localStorage.getItem('geoatlas_pending_results_queue');
        return raw ? JSON.parse(raw) : [];
    } catch(e) {
        return [];
    }
}

function enqueuePendingResult(payload) {
    try {
        const q = getPendingResultsQueue();
        if (!q.some(item => item.submission_id === payload.submission_id)) {
            q.push(payload);
            localStorage.setItem('geoatlas_pending_results_queue', JSON.stringify(q));
        }
    } catch(e) {}
}

function dequeuePendingResult(submissionId) {
    try {
        let q = getPendingResultsQueue();
        q = q.filter(item => item.submission_id !== submissionId);
        localStorage.setItem('geoatlas_pending_results_queue', JSON.stringify(q));
    } catch(e) {}
}

async function syncPendingResultsQueue() {
    if (typeof navigator !== 'undefined' && !navigator.onLine) return;
    const q = getPendingResultsQueue();
    if (!q || q.length === 0) return;

    try {
        const res = await fetch('/api/results/sync-batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: q })
        });
        if (res.ok) {
            localStorage.setItem('geoatlas_pending_results_queue', JSON.stringify([]));
            showNetworkNotificationToast('online', `✅ Синхронизировано результатов из офлайна: ${q.length}`);
        }
    } catch(e) {}
}

function saveActiveQuizDraft() {
    try {
        if (!currentQuiz || currentQuiz === 'study' || typeof isExamMode === 'undefined') return;
        const draft = {
            quizType: currentQuiz,
            isExam: isExamMode,
            examCategory: typeof examCategory !== 'undefined' ? examCategory : '',
            score: score,
            mistakes: mistakes,
            total: typeof total !== 'undefined' ? total : 0,
            currentQuestion: typeof currentQuestion !== 'undefined' ? currentQuestion : 0,
            quizDataLength: (quizData && Array.isArray(quizData)) ? quizData.length : 0,
            mistakes_log: currentSessionMistakes || [],
            sessionId: typeof currentSyncSessionId !== 'undefined' ? currentSyncSessionId : '',
            timestamp: Date.now()
        };
        localStorage.setItem('geoatlas_active_quiz_draft', JSON.stringify(draft));
    } catch(e) {}
}

function clearActiveQuizDraft() {
    try {
        localStorage.removeItem('geoatlas_active_quiz_draft');
        const promptEl = document.getElementById('geoatlas-restore-draft-prompt');
        if (promptEl) promptEl.remove();
    } catch(e) {}
}

function checkActiveQuizDraft() {
    try {
        const raw = localStorage.getItem('geoatlas_active_quiz_draft');
        if (!raw) return;
        const draft = JSON.parse(raw);
        // Draft valid for 2 hours and was in progress
        if (Date.now() - draft.timestamp < 7200000 && draft.currentQuestion > 0 && draft.currentQuestion < draft.quizDataLength) {
            showDraftRestorePrompt(draft);
        } else {
            clearActiveQuizDraft();
        }
    } catch(e) {}
}

function showDraftRestorePrompt(draft) {
    if (document.getElementById('geoatlas-restore-draft-prompt')) return;
    const prompt = document.createElement('div');
    prompt.id = 'geoatlas-restore-draft-prompt';
    prompt.style.cssText = `
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index: 999999;
        background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
        border: 2px solid #3B82F6;
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6), 0 0 20px rgba(59, 130, 246, 0.4);
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        max-width: 380px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    `;
    prompt.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 26px;">💾</div>
            <div>
                <div style="font-size: 14.5px; font-weight: 700; color: #93C5FD;">Найден сохраненный прогресс!</div>
                <div style="font-size: 12px; color: #94A3B8; margin-top: 2px;">
                    Тест: <b>${escapeHtml(draft.quizType)}</b> (вопрос ${draft.currentQuestion + 1} из ${draft.quizDataLength}, набрано: ${draft.score} б.)
                </div>
            </div>
        </div>
        <div style="display: flex; gap: 8px; justify-content: flex-end;">
            <button id="discard-draft-btn" style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #94A3B8; padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer;">Сбросить</button>
            <button id="restore-draft-btn" style="background: #2563EB; border: none; color: #FFFFFF; padding: 6px 16px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer;">Восстановить</button>
        </div>
    `;
    document.body.appendChild(prompt);

    document.getElementById('discard-draft-btn').onclick = () => {
        clearActiveQuizDraft();
    };

    document.getElementById('restore-draft-btn').onclick = () => {
        prompt.remove();
        score = draft.score || 0;
        mistakes = draft.mistakes || 0;
        currentQuestion = draft.currentQuestion || 0;
        currentSessionMistakes = draft.mistakes_log || [];
        showQuestion();
        showNetworkNotificationToast('online', '🔄 Прогресс успешно восстановлен!');
    };
}

// Сетевые слушатели и Service Worker
if (typeof window !== 'undefined') {
    window.addEventListener('online', () => {
        showNetworkNotificationToast('online', '🌐 Связь с сервером восстановлена! Синхронизируем данные...');
        syncPendingResultsQueue();
    });
    window.addEventListener('offline', () => {
        showNetworkNotificationToast('offline', '📡 Автономный режим: соединение с сетью потеряно. Все ответы сохраняются локально.');
    });

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js').catch(() => {});
        });
    }

    // Периодическая фоновая синхронизация
    setInterval(syncPendingResultsQueue, 30000);
    // Проверка черновика при загрузке
    setTimeout(checkActiveQuizDraft, 1200);
}

// ========================================================
// ⚔️ DUEL MULTIPLAYER (1 ON 1 PvP SYSTEM)
// ========================================================

var DuelManager = {
    active: false,
    ws: null,
    pollTimer: null,
    roomId: null,
    playerId: null,
    role: null, // 'host' or 'join'
    mode: 'center', // 'center' or 'puzzle'
    region: 'rostov',
    roomState: null,
    myScore: 0,
    oppScore: 0,
    myProgress: 0,
    oppProgress: 0,
    total: 7,
    isWsConnected: false,
    hasFinished: false,

    initFromUrl() {
        if (typeof window === 'undefined') return;
        const params = new URLSearchParams(window.location.search);
        const duelCode = params.get('duel');
        const pId = params.get('player');
        const rRole = params.get('role');
        if (duelCode) {
            if (pId && rRole) {
                this.startDuelSession(duelCode, pId, rRole);
            } else {
                this.openModal(duelCode);
            }
        }
    },

    openModal(prefillCode = '') {
        this.injectStyles();
        let modal = document.getElementById('geoatlas-duel-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'geoatlas-duel-modal';
            modal.style.cssText = 'position: fixed; inset: 0; background: rgba(3, 7, 18, 0.88); backdrop-filter: blur(10px); z-index: 999999; display: flex; align-items: center; justify-content: center; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
            document.body.appendChild(modal);
        }
        modal.style.display = 'flex';
        this.renderModalLobby(modal, prefillCode);
    },

    closeModal() {
        const modal = document.getElementById('geoatlas-duel-modal');
        if (modal) modal.style.display = 'none';
    },

    renderModalLobby(modal, prefillCode = '') {
        const student = getCurrentStudentInfo() || { name: 'Студент', group: 'Группа' };
        modal.innerHTML = `
            <div style="background: #0B1120; border: 1.5px solid rgba(255, 255, 255, 0.14); border-radius: 24px; max-width: 580px; width: 100%; padding: 28px; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85); color: #F8FAFC;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <div style="width: 52px; height: 52px; border-radius: 14px; background: linear-gradient(135deg, #EF4444, #F59E0B); display: flex; align-items: center; justify-content: center; font-size: 28px; box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);">⚔️</div>
                        <div>
                            <h3 style="margin: 0; font-size: 21px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.3px;">PvP-Дуэль 1 на 1</h3>
                            <div style="font-size: 12.5px; color: #94A3B8; margin-top: 3px;">Битва географов в реальном времени</div>
                        </div>
                    </div>
                    <button onclick="DuelManager.closeModal()" style="background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.1); color: #94A3B8; font-size: 22px; width: 34px; height: 34px; border-radius: 8px; cursor: pointer;">&times;</button>
                </div>

                <div style="display: flex; gap: 8px; margin-bottom: 22px; background: rgba(255, 255, 255, 0.04); padding: 4px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08);">
                    <button id="duel-tab-create" style="flex: 1; padding: 10px; border-radius: 9px; font-size: 13.5px; font-weight: 700; cursor: pointer; border: none; background: #2563EB; color: #FFFFFF; transition: all 0.2s;">👑 Создать дуэль</button>
                    <button id="duel-tab-join" style="flex: 1; padding: 10px; border-radius: 9px; font-size: 13.5px; font-weight: 600; cursor: pointer; border: none; background: transparent; color: #94A3B8; transition: all 0.2s;">🔗 Войти по коду</button>
                </div>

                <!-- БЛОК СОЗДАНИЯ -->
                <div id="duel-content-create">
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; font-size: 12.5px; font-weight: 700; color: #CBD5E1; margin-bottom: 8px;">Дисциплина дуэли:</label>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <label style="display: flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.03); border: 1.5px solid #2563EB; border-radius: 12px; padding: 12px; cursor: pointer;">
                                <input type="radio" name="duel-mode" value="center" checked style="accent-color: #2563EB;">
                                <div>
                                    <div style="font-size: 13px; font-weight: 700; color: #FFFFFF;">🎯 Райцентры</div>
                                    <div style="font-size: 11px; color: #94A3B8;">Скорость и точность клика (7 раундов)</div>
                                </div>
                            </label>
                            <label style="display: flex; align-items: center; gap: 10px; background: rgba(255, 255, 255, 0.03); border: 1.5px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 12px; cursor: pointer;">
                                <input type="radio" name="duel-mode" value="puzzle" style="accent-color: #2563EB;">
                                <div>
                                    <div style="font-size: 13px; font-weight: 700; color: #FFFFFF;">🧩 Сборка пазла</div>
                                    <div style="font-size: 11px; color: #94A3B8;">Кто быстрее соберет контур региона</div>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-size: 12.5px; font-weight: 700; color: #CBD5E1; margin-bottom: 8px;">Регион карты:</label>
                        <select id="duel-region-select" style="width: 100%; background: #0F172A; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 10px; padding: 11px 14px; color: #FFFFFF; font-size: 13.5px; outline: none;">
                            <option value="rostov" selected>🌾 Ростовская область</option>
                            <option value="krasnodar">🌻 Краснодарский край (Кубань)</option>
                            <option value="russia">🇷🇺 Российская Федерация (Субъекты)</option>
                        </select>
                    </div>

                    <div id="duel-create-action-area">
                        <button id="btn-create-duel-room" style="width: 100%; padding: 13px; background: linear-gradient(135deg, #2563EB, #1D4ED8); border: none; border-radius: 12px; color: #FFFFFF; font-size: 14.5px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);">
                            🚀 Создать комнату дуэли
                        </button>
                    </div>
                </div>

                <!-- БЛОК ВХОДА ПО КОДУ -->
                <div id="duel-content-join" style="display: none;">
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-size: 12.5px; font-weight: 700; color: #CBD5E1; margin-bottom: 8px;">Код комнаты (от соперника):</label>
                        <input type="text" id="duel-join-code-input" value="${escapeHtml(prefillCode)}" placeholder="Например: DUEL-4821" style="width: 100%; background: #0F172A; border: 1.5px solid rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 13px 16px; color: #FFFFFF; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; outline: none; box-sizing: border-box;">
                    </div>
                    <button id="btn-join-duel-room" style="width: 100%; padding: 13px; background: linear-gradient(135deg, #10B981, #059669); border: none; border-radius: 12px; color: #FFFFFF; font-size: 14.5px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35);">
                        ⚔️ Присоединиться к битве
                    </button>
                </div>
            </div>
        `;

        const tabCreate = document.getElementById('duel-tab-create');
        const tabJoin = document.getElementById('duel-tab-join');
        const contentCreate = document.getElementById('duel-content-create');
        const contentJoin = document.getElementById('duel-content-join');

        tabCreate.onclick = () => {
            tabCreate.style.background = '#2563EB'; tabCreate.style.color = '#FFFFFF';
            tabJoin.style.background = 'transparent'; tabJoin.style.color = '#94A3B8';
            contentCreate.style.display = 'block'; contentJoin.style.display = 'none';
        };

        tabJoin.onclick = () => {
            tabJoin.style.background = '#2563EB'; tabJoin.style.color = '#FFFFFF';
            tabCreate.style.background = 'transparent'; tabCreate.style.color = '#94A3B8';
            contentCreate.style.display = 'none'; contentJoin.style.display = 'block';
        };

        if (prefillCode) {
            tabJoin.click();
        }

        document.getElementById('btn-create-duel-room').onclick = async () => {
            const btn = document.getElementById('btn-create-duel-room');
            btn.disabled = true;
            btn.textContent = '⏳ Создаем комнату...';
            try {
                const mode = document.querySelector('input[name="duel-mode"]:checked').value;
                const region = document.getElementById('duel-region-select').value;
                const res = await this.createRoom(mode, region);
                this.renderRoomWaitingScreen(modal, res, 'host');
            } catch(e) {
                alert(e.message || 'Ошибка создания комнаты');
                btn.disabled = false;
                btn.textContent = '🚀 Создать комнату дуэли';
            }
        };

        document.getElementById('btn-join-duel-room').onclick = async () => {
            const codeInput = document.getElementById('duel-join-code-input');
            const code = codeInput.value.trim().toUpperCase();
            if (!code) {
                alert('Пожалуйста, введите код комнаты (например DUEL-1234)');
                return;
            }
            const btn = document.getElementById('btn-join-duel-room');
            btn.disabled = true;
            btn.textContent = '⏳ Подключаемся...';
            try {
                const res = await this.joinRoom(code);
                this.renderRoomWaitingScreen(modal, res, 'join');
            } catch(e) {
                alert(e.message || 'Ошибка входа в комнату');
                btn.disabled = false;
                btn.textContent = '⚔️ Присоединиться к битве';
            }
        };
    },

    async createRoom(mode, region) {
        const student = getCurrentStudentInfo() || {};
        const res = await fetch('/api/duel/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: mode || 'center',
                region: region || 'rostov',
                host_name: student.name || 'Студент',
                host_group: student.group || '-',
                host_email: student.email || 'student@sfedu.ru'
            })
        });
        if (!res.ok) throw new Error('Ошибка создания комнаты');
        return await res.json();
    },

    async joinRoom(roomCode) {
        const student = getCurrentStudentInfo() || {};
        const res = await fetch('/api/duel/join', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                room_id: roomCode.trim().toUpperCase(),
                player_name: student.name || 'Студент',
                player_group: student.group || '-',
                player_email: student.email || 'student@sfedu.ru'
            })
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'Комната не найдена или заполнена');
        }
        return await res.json();
    },

    renderRoomWaitingScreen(modal, data, role) {
        const room = data.room || {};
        const inviteUrl = `${window.location.origin}/map/${data.region}?duel=${data.room_id}`;
        modal.innerHTML = `
            <div style="background: #0B1120; border: 1.5px solid rgba(255, 255, 255, 0.14); border-radius: 24px; max-width: 580px; width: 100%; padding: 28px; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85); color: #F8FAFC;">
                <div style="text-align: center; margin-bottom: 22px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #F59E0B; font-weight: 800;">КОМНАТА ДУЭЛИ СОЗДАНА</div>
                    <div style="font-size: 36px; font-weight: 900; color: #FFFFFF; letter-spacing: 3px; margin: 6px 0;">${escapeHtml(data.room_id)}</div>
                    <div style="font-size: 13px; color: #94A3B8;">Дисциплина: <b>${data.mode === 'center' ? '🎯 Райцентры на скорость' : '🧩 Пазл региона'}</b> • 🌍 ${escapeHtml(data.region)}</div>
                </div>

                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 16px; margin-bottom: 20px;">
                    <div style="font-size: 12px; color: #CBD5E1; font-weight: 600; margin-bottom: 8px;">Ссылка-приглашение для второго студента:</div>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" readonly value="${escapeHtml(inviteUrl)}" style="flex: 1; background: #0F172A; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 8px 12px; color: #93C5FD; font-size: 12px; outline: none;">
                        <button id="copy-duel-link-btn" style="background: #2563EB; border: none; border-radius: 8px; color: #FFFFFF; padding: 8px 14px; font-size: 12px; font-weight: 700; cursor: pointer;">Копировать</button>
                    </div>
                </div>

                <!-- СПИСОК УЧАСТНИКОВ -->
                <div style="margin-bottom: 24px;">
                    <div style="font-size: 12.5px; font-weight: 700; color: #CBD5E1; margin-bottom: 10px;">Участники дуэли:</div>
                    <div id="duel-lobby-players-list" style="display: flex; flex-direction: column; gap: 8px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 10px 14px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>👑</span>
                                <span style="font-size: 13.5px; font-weight: 700; color: #FFFFFF;">${escapeHtml(room.players?.[0]?.name || 'Игрок 1')}</span>
                            </div>
                            <span style="font-size: 11px; color: #34D399; font-weight: 700;">ГОТОВ ✅</span>
                        </div>
                        <div id="duel-opp-slot" style="display: flex; align-items: center; justify-content: space-between; background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 10px; padding: 10px 14px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>⏳</span>
                                <span style="font-size: 13px; color: #94A3B8;">Ожидание второго игрока...</span>
                            </div>
                            <span style="font-size: 11px; color: #F59E0B; font-weight: 600;">ЖДЕМ ПОДКЛЮЧЕНИЯ</span>
                        </div>
                    </div>
                </div>

                <div style="display: flex; gap: 10px;">
                    <button onclick="DuelManager.closeModal()" style="flex: 1; padding: 12px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; color: #CBD5E1; font-size: 13.5px; font-weight: 600; cursor: pointer;">Выйти</button>
                    <button id="btn-start-duel-now" style="flex: 2; padding: 12px; background: linear-gradient(135deg, #EF4444, #F59E0B); border: none; border-radius: 12px; color: #FFFFFF; font-size: 14.5px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);">
                        ⚔️ Начать дуэль!
                    </button>
                </div>
            </div>
        `;

        document.getElementById('copy-duel-link-btn').onclick = () => {
            navigator.clipboard.writeText(inviteUrl);
            document.getElementById('copy-duel-link-btn').textContent = 'Скопировано! ✓';
            setTimeout(() => {
                const el = document.getElementById('copy-duel-link-btn');
                if (el) el.textContent = 'Копировать';
            }, 2000);
        };

        const startBtn = document.getElementById('btn-start-duel-now');
        startBtn.onclick = () => {
            this.launchDuelOnMap(data);
        };

        // Начинаем опрашивать состояние комнаты
        const lobbyPollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/duel/state/${data.room_id}`);
                if (!res.ok) return;
                const state = await res.json();
                const currentRoom = state.room || {};
                const players = currentRoom.players || [];
                if (players.length >= 2) {
                    const opp = players[1];
                    const oppSlot = document.getElementById('duel-opp-slot');
                    if (oppSlot) {
                        oppSlot.style.background = 'rgba(16, 185, 129, 0.08)';
                        oppSlot.style.border = '1px solid rgba(16, 185, 129, 0.3)';
                        oppSlot.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span>⚔️</span>
                                <span style="font-size: 13.5px; font-weight: 700; color: #FFFFFF;">${escapeHtml(opp.name)} (${escapeHtml(opp.group || '')})</span>
                            </div>
                            <span style="font-size: 11px; color: #34D399; font-weight: 700;">ПОДКЛЮЧЕН! 🚀</span>
                        `;
                    }
                    startBtn.textContent = '⚔️ В бой! Начать дуэль';
                    startBtn.style.animation = 'pulse 1s infinite alternate';
                }
                if (currentRoom.status === 'playing') {
                    clearInterval(lobbyPollInterval);
                    this.launchDuelOnMap(data);
                }
            } catch(e) {}
        }, 1200);

        // Сохраняем ссылку на интервал
        this._lobbyPollInterval = lobbyPollInterval;
    },

    launchDuelOnMap(data) {
        if (this._lobbyPollInterval) clearInterval(this._lobbyPollInterval);
        this.closeModal();

        const currentMapUrl = window.location.pathname;
        const targetRegion = data.region || 'rostov';

        // Если мы уже находимся на карте этого региона
        if (currentMapUrl.includes(targetRegion) || (typeof window.currentRegionKey !== 'undefined' && window.currentRegionKey === targetRegion)) {
            this.startDuelSession(data.room_id, data.player_id, data.role);
        } else {
            // Переходим на страницу карты
            window.location.href = data.map_url || `/map/${targetRegion}?duel=${data.room_id}&player=${data.player_id}&role=${data.role}`;
        }
    },

    startDuelSession(roomId, playerId, role) {
        this.active = true;
        this.roomId = roomId.toUpperCase();
        this.playerId = playerId;
        this.role = role;
        this.myScore = 0;
        this.oppScore = 0;
        this.myProgress = 0;
        this.oppProgress = 0;
        this.hasFinished = false;
        this._gameplayStarted = false;

        this.injectStyles();
        this.renderLiveHUD();
        this.connectWebSocket();
    },

    fetchRoomState: async function() {
        try {
            const res = await fetch(`/api/duel/state/${this.roomId}?player_id=${this.playerId}`);
            if (res.ok) {
                const data = await res.json();
                if (data && data.room) {
                    this.updateFromRoomState(data.room);
                    return data.room;
                }
            }
        } catch (e) {}
        return null;
    },

    showWaitingOverlay: function() {
        let el = document.getElementById('duel-waiting-overlay');
        if (!el) {
            el = document.createElement('div');
            el.id = 'duel-waiting-overlay';
            el.style.cssText = 'position:fixed;inset:0;background:rgba(3,7,18,0.85);backdrop-filter:blur(8px);z-index:9999998;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;';
            document.body.appendChild(el);
        }
        el.style.display = 'flex';
        el.innerHTML = `
            <div style="background:#0B1120;border:2px solid #F59E0B;border-radius:20px;padding:32px;text-align:center;max-width:440px;color:#F8FAFC;box-shadow:0 25px 60px rgba(0,0,0,0.85);">
                <div style="font-size:44px;margin-bottom:10px;">⏳</div>
                <h2 style="color:#FFFFFF;margin:0 0 6px 0;font-size:20px;">Ожидание соперника</h2>
                <p style="color:#94A3B8;font-size:13px;margin:0 0 6px 0;">Комната: <strong style="color:#FBBF24;font-family:monospace;">${escapeHtml(this.roomId)}</strong></p>
                <p style="color:#64748B;font-size:12px;margin:0 0 20px 0;">Соперник ещё не присоединился. Как только он подключится — игра начнётся автоматически.</p>
                <button onclick="DuelManager.surrenderDuel()" style="background:#EF4444;color:#FFFFFF;border:none;border-radius:10px;padding:10px 24px;font-size:13.5px;font-weight:700;cursor:pointer;">🏳️ Отказаться от дуэли</button>
            </div>
        `;
    },

    hideWaitingOverlay: function() {
        const el = document.getElementById('duel-waiting-overlay');
        if (el) el.style.display = 'none';
    },

    surrenderDuel: function() {
        if (!this.active && !this.roomId) {
            this.hideWaitingOverlay();
            return;
        }
        const doSurrender = () => {
            const wasWaiting = !this._gameplayStarted;
            this.hideWaitingOverlay();
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'surrender' }));
            } else {
                fetch(`/api/duel/action/${this.roomId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_id: this.playerId, action: 'surrender', payload: {} })
                }).then(r => r.json()).then(data => {
                    if (data && data.room) this.updateFromRoomState(data.room);
                }).catch(() => {});
            }
            if (wasWaiting) {
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 400);
            }
        };
        if (confirm('Сдаться и получить техническое поражение?')) {
            doSurrender();
        }
    },

    connectWebSocket() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${proto}//${location.host}/ws/duel/${this.roomId}/${this.playerId}`;
        try {
            this.ws = new WebSocket(url);
            this.ws.onopen = async () => {
                this.isWsConnected = true;
                if (this.pollTimer) clearInterval(this.pollTimer);
                const state = await this.fetchRoomState();
                if (state && state.status === 'playing') {
                    this.hideWaitingOverlay();
                    if (!this._gameplayStarted) this.startGamePlay(state);
                } else if (state && state.status === 'finished') {
                    this.hideWaitingOverlay();
                    this.onGameOver(state);
                } else {
                    this.showWaitingOverlay();
                    this.sendAction({ type: 'ready', ready: true });
                }
            };
            this.ws.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    this.handleSocketMessage(msg);
                } catch(err) {}
            };
            this.ws.onerror = () => { this.fallbackToPolling(); };
            this.ws.onclose = () => {
                this.isWsConnected = false;
                if (this.active && !this.hasFinished) this.fallbackToPolling();
            };
        } catch(e) {
            this.fallbackToPolling();
        }
        this._wsTimeout = setTimeout(() => {
            if (!this.isWsConnected && this.active && !this.hasFinished) {
                this.fallbackToPolling();
            }
        }, 2200);
    },

    fallbackToPolling() {
        if (this.pollTimer) return;
        this.pollTimer = setInterval(async () => {
            if (!this.active || this.hasFinished) return;
            try {
                const res = await fetch(`/api/duel/state/${this.roomId}?player_id=${this.playerId}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.room) {
                        this.updateFromRoomState(data.room);
                    }
                }
            } catch(e) {}
        }, 1000);
    },

    sendAction(actionData) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(actionData));
        } else {
            fetch(`/api/duel/action/${this.roomId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: this.playerId,
                    action: actionData.type || 'action',
                    payload: actionData
                })
            }).then(r => r.json()).then(data => {
                if (data && data.room) this.updateFromRoomState(data.room);
            }).catch(() => {});
        }
    },

    handleSocketMessage(msg) {
        if (!msg) return;
        if (msg.room) this.updateFromRoomState(msg.room);
        if (msg.type === 'countdown') {
            this.hideWaitingOverlay();
            this.showCountdownOverlay(msg.seconds);
        } else if (msg.type === 'game_start') {
            this.hideWaitingOverlay();
            this.startGamePlay(msg.room);
        } else if (msg.type === 'opponent_action') {
            this.onOpponentAction(msg);
        } else if (msg.type === 'game_over') {
            this.hideWaitingOverlay();
            this.onGameOver(msg.room);
        }
    },

    updateFromRoomState(room) {
        this.roomState = room;
        this.mode = room.mode;
        this.region = room.region;

        const players = room.players || [];
        const myP = players.find(p => p.player_id === this.playerId);
        const oppP = players.find(p => p.player_id !== this.playerId);

        if (myP) {
            this.myScore = myP.score;
            this.myProgress = myP.progress;
            this.total = myP.total || 7;
        }
        if (oppP) {
            this.oppScore = oppP.score;
            this.oppProgress = oppP.progress;
        }

        this.updateHUDValues(myP, oppP);

        if (room.status === 'playing' && !this._gameplayStarted) {
            this.hideWaitingOverlay();
            this.startGamePlay(room);
        }

        if (room.status === 'finished' && !this.hasFinished) {
            this.hideWaitingOverlay();
            this.onGameOver(room);
        }
    },

    startGamePlay(room) {
        this._gameplayStarted = true;
        this.removeCountdownOverlay();

        if (this.mode === 'center') {
            if (room.questions && room.questions.length > 0) {
                // Инициализируем идентичные вопросы для обоих студентов
                quizData = room.questions.map(q => ({
                    type: 'center',
                    correctAnswer: q.name,
                    correctLat: q.lat,
                    correctLon: q.lon,
                    hint: `Статус: ${q.status || 'райцентр'}`,
                    centerName: q.name
                }));
                totalQuestions = quizData.length;
                currentQuestion = 0;
                score = 0;
                mistakes = 0;
                prepareQuizUI('center', '🎯 Дуэль: Найти райцентр', true, false);
                showQuestion();
            } else {
                startCenterQuiz();
            }
        } else if (this.mode === 'puzzle') {
            startPuzzleMode();
        }
    },

    showCountdownOverlay(seconds) {
        let el = document.getElementById('duel-countdown-overlay');
        if (!el) {
            el = document.createElement('div');
            el.id = 'duel-countdown-overlay';
            el.style.cssText = 'position: fixed; inset: 0; background: rgba(3, 7, 18, 0.85); backdrop-filter: blur(8px); z-index: 9999999; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; pointer-events: none;';
            document.body.appendChild(el);
        }
        el.innerHTML = `
            <div style="font-size: 16px; font-weight: 800; color: #F59E0B; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px;">⚔️ Битва начинается через:</div>
            <div style="font-size: 110px; font-weight: 900; color: #FFFFFF; text-shadow: 0 0 35px rgba(245, 158, 11, 0.8);">${seconds}</div>
        `;
    },

    removeCountdownOverlay() {
        const el = document.getElementById('duel-countdown-overlay');
        if (el) el.remove();
    },

    renderLiveHUD() {
        let hud = document.getElementById('geoatlas-duel-live-hud');
        if (!hud) {
            hud = document.createElement('div');
            hud.id = 'geoatlas-duel-live-hud';
            document.body.appendChild(hud);
        }
        const student = getCurrentStudentInfo() || { name: 'Вы' };
        hud.innerHTML = `
            <div class="duel-hud-container">
                <!-- ВЫ -->
                <div class="duel-player-box my-box">
                    <div class="duel-box-header">
                        <span class="duel-crown">👑</span>
                        <span class="duel-name">${escapeHtml(student.name || 'Вы')}</span>
                        <span class="duel-score" id="hud-my-score">0 б.</span>
                    </div>
                    <div class="duel-bar-track">
                        <div class="duel-bar-fill my-fill" id="hud-my-bar" style="width: 0%"></div>
                    </div>
                    <div class="duel-sub-info" id="hud-my-sub">Прогресс: 0 / 7</div>
                </div>

                <!-- ЦЕНТР VS -->
                <div class="duel-vs-box">
                    <div class="duel-vs-title">⚔️ ДУЭЛЬ 1V1</div>
                    <div class="duel-vs-badge" id="hud-round-badge">РАУНД 1 / 7</div>
                    <button onclick="DuelManager.surrenderDuel()" class="duel-surrender-btn" title="Сдаться (техническое поражение)">🏳️ Сдаться</button>
                </div>

                <!-- СОПЕРНИК -->
                <div class="duel-player-box opp-box">
                    <div class="duel-box-header">
                        <span class="duel-score opp-score" id="hud-opp-score">0 б.</span>
                        <span class="duel-name" id="hud-opp-name">Соперник</span>
                        <span class="duel-crown">⚔️</span>
                    </div>
                    <div class="duel-bar-track">
                        <div class="duel-bar-fill opp-fill" id="hud-opp-bar" style="width: 0%"></div>
                    </div>
                    <div class="duel-sub-info" id="hud-opp-sub">Ожидание хода...</div>
                </div>
            </div>
            <div id="duel-live-event-banner" class="duel-event-banner"></div>
        `;
    },

    updateHUDValues(myP, oppP) {
        const myScoreEl = document.getElementById('hud-my-score');
        const myBarEl = document.getElementById('hud-my-bar');
        const mySubEl = document.getElementById('hud-my-sub');

        const oppScoreEl = document.getElementById('hud-opp-score');
        const oppNameEl = document.getElementById('hud-opp-name');
        const oppBarEl = document.getElementById('hud-opp-bar');
        const oppSubEl = document.getElementById('hud-opp-sub');
        const roundBadgeEl = document.getElementById('hud-round-badge');

        const totalItems = this.total || 7;

        if (myP && myScoreEl && myBarEl && mySubEl) {
            myScoreEl.textContent = `${myP.score} б.`;
            const pct = Math.min(100, Math.round((myP.progress / totalItems) * 100));
            myBarEl.style.width = `${pct}%`;
            mySubEl.textContent = `Прогресс: ${myP.progress} / ${totalItems}`;
        }

        if (oppP && oppScoreEl && oppBarEl && oppSubEl && oppNameEl) {
            oppNameEl.textContent = oppP.name || 'Соперник';
            oppScoreEl.textContent = `${oppP.score} б.`;
            const pct = Math.min(100, Math.round((oppP.progress / totalItems) * 100));
            oppBarEl.style.width = `${pct}%`;
            oppSubEl.textContent = `Прогресс: ${oppP.progress} / ${totalItems}`;
        }

        if (roundBadgeEl) {
            if (this.mode === 'center') {
                const currentRound = Math.min(totalItems, (myP?.progress || 0) + 1);
                roundBadgeEl.textContent = `РАУНД ${currentRound} / ${totalItems}`;
            } else {
                roundBadgeEl.textContent = `ГОНКА ПАЗЛА`;
            }
        }
    },

    submitCenterAnswer(questionIndex, points, distance, targetName) {
        if (!this.active) return;
        this.sendAction({
            type: 'answer_center',
            question_index: questionIndex,
            points: points,
            distance: distance,
            target_name: targetName
        });
    },

    submitPuzzlePiece(placedCount, mistakes, districtName) {
        if (!this.active) return;
        this.sendAction({
            type: 'place_piece',
            placed_count: placedCount,
            mistakes: mistakes,
            district_name: districtName
        });
    },

    onOpponentAction(msg) {
        const banner = document.getElementById('duel-live-event-banner');
        if (!banner) return;

        let text = '';
        if (msg.action === 'answer_center') {
            text = `⚡ Соперник: ${msg.target_name} (+${msg.points} б., ${Math.round(msg.distance)} км)`;
        } else if (msg.action === 'place_piece') {
            text = `🧩 Соперник собрал район «${msg.district_name}» (${msg.placed_count} всего)`;
        }

        banner.textContent = text;
        banner.style.opacity = '1';
        banner.style.transform = 'translateY(0)';
        setTimeout(() => {
            banner.style.opacity = '0';
            banner.style.transform = 'translateY(-10px)';
        }, 2500);
    },

    onGameOver(room) {
        if (this._wsTimeout) clearTimeout(this._wsTimeout);
        this.hideWaitingOverlay();
        if (this.hasFinished) return;
        this.hasFinished = true;
        this.active = false;
        if (this.pollTimer) clearInterval(this.pollTimer);

        const players = room.players || [];
        const myP = players.find(p => p.player_id === this.playerId) || { score: 0 };
        const oppP = players.find(p => p.player_id !== this.playerId) || { score: 0, name: 'Соперник' };

        const isWinner = room.winner === this.playerId;
        const isDraw = room.winner === 'draw';

        if (isWinner) {
            unlockAchievement('duel_master');
            // Бонус к очкам за победу
            try {
                const curBonus = parseInt(localStorage.getItem('geoatlas_duel_bonus_xp') || '0');
                localStorage.setItem('geoatlas_duel_bonus_xp', String(curBonus + 50));
            } catch(e) {}
        }

        const modal = document.createElement('div');
        modal.style.cssText = 'position: fixed; inset: 0; background: rgba(3, 7, 18, 0.92); backdrop-filter: blur(12px); z-index: 99999999; display: flex; align-items: center; justify-content: center; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
        
        const headerTitle = isWinner ? '🏆 ПОБЕДА В ДУЭЛИ!' : (isDraw ? '🤝 БОЕВАЯ НИЧЬЯ!' : '⚔️ ПОБЕДА СОПЕРНИКА');
        const headerColor = isWinner ? '#F59E0B' : (isDraw ? '#38BDF8' : '#F87171');
        const headerGlow = isWinner ? '0 0 30px rgba(245, 158, 11, 0.6)' : 'none';

        modal.innerHTML = `
            <div style="background: #0B1120; border: 2px solid ${headerColor}; border-radius: 24px; max-width: 540px; width: 100%; padding: 32px; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9), ${headerGlow}; color: #F8FAFC; text-align: center;">
                <div style="font-size: 56px; margin-bottom: 8px;">${isWinner ? '👑' : (isDraw ? '🤝' : '⚔️')}</div>
                <h2 style="font-size: 28px; font-weight: 900; color: ${headerColor}; margin: 0 0 8px 0; letter-spacing: -0.5px;">${headerTitle}</h2>
                <div style="font-size: 13.5px; color: #94A3B8; margin-bottom: 24px;">${escapeHtml(room.winner_reason || '')}</div>

                ${isWinner ? `
                    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(30, 41, 59, 0.8)); border: 1.5px solid #F59E0B; border-radius: 14px; padding: 14px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px; text-align: left;">
                        <div style="font-size: 32px;">⚔️</div>
                        <div>
                            <div style="font-size: 11px; text-transform: uppercase; color: #FBBF24; font-weight: 800;">Ачивка разблокирована</div>
                            <div style="font-size: 15px; font-weight: 700; color: #FFFFFF;">Гроза дуэлей (+50 XP)</div>
                        </div>
                    </div>
                ` : ''}

                <!-- СРАВНЕНИЕ РЕЗУЛЬТАТОВ -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 26px;">
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px;">
                        <div style="font-size: 12px; color: #94A3B8;">Вы (${escapeHtml(myP.name || 'Вы')})</div>
                        <div style="font-size: 32px; font-weight: 900; color: #34D399; margin: 4px 0;">${myP.score}</div>
                        <div style="font-size: 11.5px; color: #64748B;">прогресс: ${myP.progress}/${this.total}</div>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px;">
                        <div style="font-size: 12px; color: #94A3B8;">Соперник (${escapeHtml(oppP.name || 'Соперник')})</div>
                        <div style="font-size: 32px; font-weight: 900; color: #F87171; margin: 4px 0;">${oppP.score}</div>
                        <div style="font-size: 11.5px; color: #64748B;">прогресс: ${oppP.progress}/${this.total}</div>
                    </div>
                </div>

                <div style="display: flex; gap: 10px;">
                    <button id="duel-rematch-btn" style="flex: 1; padding: 12px; background: #2563EB; border: none; border-radius: 12px; color: #FFFFFF; font-size: 14px; font-weight: 700; cursor: pointer;">⚔️ Новая дуэль</button>
                    <button id="duel-exit-btn" style="flex: 1; padding: 12px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; color: #CBD5E1; font-size: 14px; font-weight: 600; cursor: pointer;">В меню атласа</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('duel-rematch-btn').onclick = () => {
            modal.remove();
            const hud = document.getElementById('geoatlas-duel-live-hud');
            if (hud) hud.remove();
            this.openModal();
        };

        document.getElementById('duel-exit-btn').onclick = () => {
            modal.remove();
            const hud = document.getElementById('geoatlas-duel-live-hud');
            if (hud) hud.remove();
            if (typeof resetQuiz === 'function') resetQuiz();
            window.location.href = '/index.html';
        };
    },

    injectStyles() {
        if (document.getElementById('geoatlas-duel-styles')) return;
        const style = document.createElement('style');
        style.id = 'geoatlas-duel-styles';
        style.textContent = `
            #geoatlas-duel-live-hud {
                position: fixed;
                top: 15px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 99999;
                width: 90%;
                max-width: 920px;
                pointer-events: none;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            .duel-hud-container {
                display: flex;
                align-items: center;
                gap: 16px;
                background: rgba(11, 17, 32, 0.92);
                border: 1.5px solid rgba(255, 255, 255, 0.14);
                backdrop-filter: blur(12px);
                border-radius: 18px;
                padding: 10px 18px;
                box-shadow: 0 12px 35px rgba(0, 0, 0, 0.65);
                pointer-events: auto;
            }
            .duel-player-box {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .duel-box-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 13.5px;
                font-weight: 700;
                color: #FFFFFF;
            }
            .duel-score {
                background: rgba(37, 99, 235, 0.2);
                border: 1px solid #2563EB;
                color: #93C5FD;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 11.5px;
            }
            .opp-score {
                background: rgba(239, 68, 68, 0.2);
                border-color: #EF4444;
                color: #FCA5A5;
            }
            .duel-bar-track {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 999px;
                overflow: hidden;
            }
            .duel-bar-fill {
                height: 100%;
                transition: width 0.4s ease;
            }
            .my-fill {
                background: linear-gradient(90deg, #2563EB, #10B981);
            }
            .opp-fill {
                background: linear-gradient(90deg, #EF4444, #F59E0B);
            }
            .duel-sub-info {
                font-size: 11px;
                color: #94A3B8;
            }
            .duel-vs-box {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 3px;
                flex-shrink: 0;
            }
            .duel-vs-title {
                font-size: 10.5px;
                font-weight: 900;
                letter-spacing: 1px;
                color: #F59E0B;
            }
            .duel-vs-badge {
                background: rgba(245, 158, 11, 0.15);
                border: 1px solid #F59E0B;
                color: #FBBF24;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 10.5px;
                font-weight: 800;
            }
            .duel-surrender-btn {
                margin-top: 4px;
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.5);
                color: #FCA5A5;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .duel-surrender-btn:hover {
                background: #EF4444;
                color: #FFFFFF;
                border-color: #EF4444;
            }
            .duel-event-banner {
                margin: 8px auto 0 auto;
                width: max-content;
                max-width: 420px;
                padding: 6px 14px;
                background: rgba(15, 23, 42, 0.94);
                border: 1px solid #38BDF8;
                border-radius: 999px;
                color: #E0F2FE;
                font-size: 12px;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
                text-align: center;
                opacity: 0;
                transform: translateY(-10px);
                transition: all 0.3s ease;
                pointer-events: none;
            }
        `;
        document.head.appendChild(style);
    }
};

window.DuelManager = DuelManager;
window.openDuelModal = (code) => DuelManager.openModal(code);
window.closeDuelModal = () => DuelManager.closeModal();
window.syncPendingResultsQueue = syncPendingResultsQueue;
window.checkActiveQuizDraft = checkActiveQuizDraft;
window.saveActiveQuizDraft = saveActiveQuizDraft;
window.clearActiveQuizDraft = clearActiveQuizDraft;

// Автопроверка параметров URL для дуэли
if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
        DuelManager.initFromUrl();
    });
}
