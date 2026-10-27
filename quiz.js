let currentQuiz = null;
let currentQuestion = 0;
let score = 0;
let maxPossibleScore = 0;
let totalQuestions = 10;
let quizData = [];
let selectedOption = null;
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

// ==================== РЕЖИМ КОНТРОЛЬНОЙ (ЭКЗАМЕНА) ====================
let isExamMode = false;
let examCategory = 'mixed';
let examQuestionCount = 15;
let examTimeLimitMinutes = 10;
let examTimeRemaining = 600; // секунды обратного отсчета
let examGlobalTimer = null;
let examCheatingViolations = 0;
let examStatus = 'passed'; // 'passed', 'warning', 'cheating_detected'
let examToken = '';
let antiCheatActive = false;
let blurCooldown = false;

// ==================== СИНХРОННЫЙ ЭКЗАМЕНАЦИОННЫЙ ДИСПЕТЧЕР (LMS) ====================
let currentSyncSessionId = null;
let currentSyncGroupName = null;
let syncExamRemainingSec = null;
let syncSessionHeartbeatTimer = null;

let studyCategory = 'districts';
let studyQueue = [];
let studyIndex = 0;
let studyCenterMarker = null;

// ==================== РЕЖИМ ПАЗЛА (СОБЕРИ РЕГИОН) ====================
let isPuzzleMode = false;
let puzzleDistricts = [];
let puzzleUnplacedQueue = [];
let puzzleActivePiece = null;
let puzzleAnchorDistrict = null;
let puzzlePlacedDistricts = new Set();
let puzzleSlotLayers = {};
let puzzlePlacedMarkers = [];
let puzzleOutlineLayer = null;
let puzzleTimerInterval = null;
let puzzleStartTime = 0;
let puzzleMistakes = 0;
let puzzleHintsUsed = 0;
let puzzleToken = '';
let puzzleSavedLayerStyles = [];

const PUZZLE_PALETTE = [
    '#38BDF8', '#34D399', '#F472B6', '#A78BFA',
    '#FBBF24', '#60A5FA', '#4ADE80', '#FB7185',
    '#818CF8', '#F59E0B', '#2DD4BF', '#C084FC',
    '#E879F9', '#22C55E', '#38BDF8', '#FB923C'
];

function getPuzzlePieceColor(index) {
    return PUZZLE_PALETTE[index % PUZZLE_PALETTE.length];
}

// ==================== ДИНАМИЧЕСКИЙ ДОСТУП К ДАННЫМ РЕГИОНА ====================
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

function resolveRegionKey(raw) {
    if (!raw) return 'rostov';
    const s = String(raw).toLowerCase().trim()
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
    return s;
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
    return names[k] || (k.charAt(0).toUpperCase() + k.slice(1));
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

    // Если мы уже на целевой карте этого региона, данные уже встроены
    if (currentFile === targetMapFile && typeof EMBEDDED_DISTRICTS !== 'undefined') {
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

    // Если мы на другой странице и API недоступен, перенаправляем на файл региона
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
    if (map && window._dynamicBounds) {
        try {
            map.fitBounds(window._dynamicBounds, { padding: [20, 20] });
        } catch (e) {}
    }
}

// ==================== СТАТУС-ПАНЕЛЬ ЭКЗАМЕНА И KIOSK MODE ====================
function ensureExamKioskTopBar(opts = {}) {
    let bar = document.getElementById('exam-kiosk-top-bar');
    const student = getCurrentStudentInfo();
    const groupName = opts.groupName || currentSyncGroupName || (student ? student.group : '') || 'ВКР ЮФУ';
    const studentName = (student && student.name) ? student.name : 'Студент';
    const regionName = getRegionName(window.currentRegionKey || opts.region || '');

    // Скрываем старый баннер ожидания сессии если есть
    const oldBanner = document.getElementById('sync-exam-top-banner');
    if (oldBanner) oldBanner.style.display = 'none';

    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'exam-kiosk-top-bar';
        bar.className = 'exam-kiosk-bar';
        document.body.prepend(bar);
    }

    const safeSec = Math.max(0, examTimeRemaining);
    const mins = Math.floor(safeSec / 60);
    const secs = safeSec % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    bar.innerHTML = `
        <div class="kiosk-left">
            <span class="kiosk-dot"></span>
            <div>
                <div class="kiosk-title">🛡️ ЭКЗАМЕНАЦИОННЫЙ РЕЖИМ (KIOSK) • ${escapeHtml(regionName)} • ГРУППА: <span id="kiosk-group-badge">${escapeHtml(groupName)}</span></div>
                <div class="kiosk-meta">Студент: <b style="color:#FFF;">${escapeHtml(studentName)}</b> • Режим контроля Anti-Cheat ЮФУ</div>
            </div>
        </div>
        <div class="kiosk-right">
            <div class="kiosk-timer-box">
                <span style="font-size: 14px;">⏳</span>
                <span id="kiosk-timer-display" class="kiosk-timer-text">${timeStr}</span>
            </div>
        </div>
    `;
    bar.style.display = 'flex';
}

function removeExamKioskTopBar() {
    const bar = document.getElementById('exam-kiosk-top-bar');
    if (bar) bar.remove();
    const oldBanner = document.getElementById('sync-exam-top-banner');
    if (oldBanner) oldBanner.style.display = 'none';
}

// ==================== ИНИЦИАЛИЗАЦИЯ ЭКЗАМЕНА (БЕЗ ХАРДКОДА РЕГИОНА) ====================
async function initExamMode(options = {}) {
    const urlParams = new URLSearchParams(window.location.search);

    const regionParam = options.region || options.regionKey || options.regionName || options.region_name || 
                        urlParams.get('region') || urlParams.get('map') || 
                        (options.session && (options.session.regionName || options.session.region_name || options.session.mapUrl || options.session.map_url)) ||
                        '';

    const targetRegion = resolveRegionKey(regionParam);
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
        groupName: groupName
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
    if (panel) {
        const isCollapsed = panel.classList.toggle('collapsed');
        document.body.classList.toggle('ui-collapsed', isCollapsed);
        if (btn) {
            btn.setAttribute('aria-expanded', (!isCollapsed).toString());
            btn.title = isCollapsed ? 'Развернуть панель атласа' : 'Свернуть панель к карте';
        }
    }
}

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
        try { map.fitBounds(getRegionBoundsData() || (typeof REGION_BOUNDS !== 'undefined' ? REGION_BOUNDS : null), {padding: [15, 15]}); } catch(e) {}
    }
}

function setQuizLayers(quizMode) {
    try {
        const layers = document.querySelectorAll('.leaflet-control-layers-overlays label');
        layers.forEach(label => {
            const text = label.textContent.trim();
            const input = label.querySelector('input[type="checkbox"]');
            if (!input) return;

            // Аналитические слои (Население, ВРП) отключаем на время викторин
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
    if (isExamMode) {
        // В режиме контрольной работает глобальный таймер на весь тест
        return;
    }
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

/* ==================== ПРЕМИАЛЬНЫЙ ВИДЖЕТ ТАЙМЕРА И ПРОКТОРИНГА ==================== */
function ensureExamProctorWidgetDOM() {
    let tb = document.getElementById('timer-bar-container');
    if (!tb) return;
    
    tb.classList.add('exam-proctor-panel');
    
    if (!tb.querySelector('.exam-panel-top')) {
        tb.innerHTML = `
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
        `;
    }
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

/* ==================== ГЛОБАЛЬНЫЙ ЭКЗАМЕНАЦИОННЫЙ ТАЙМЕР ==================== */
function startGlobalExamTimer() {
    stopTimer();
    stopGlobalExamTimer();

    ensureExamProctorWidgetDOM();

    const tb = document.getElementById('timer-bar-container');
    if (tb) tb.style.display = 'block';

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

function stopGlobalExamTimer() {
    if (examGlobalTimer) {
        clearInterval(examGlobalTimer);
        examGlobalTimer = null;
    }
}

function updateGlobalExamTimerDisplay() {
    const timerText = document.getElementById('timer-text');
    const timerBar = document.getElementById('timer-bar');
    const statusText = document.getElementById('exam-proctor-status-text');

    const safeSec = Math.max(0, examTimeRemaining);
    const mins = Math.floor(safeSec / 60);
    const secs = safeSec % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    if (timerText) {
        timerText.textContent = timeStr;
        timerText.classList.add('exam-timer-display');
        if (safeSec < 60) {
            timerText.style.color = '#EF4444';
        } else if (safeSec < 180) {
            timerText.style.color = '#F59E0B';
        } else {
            timerText.style.color = '#38BDF8';
        }
    }

    const kioskTimer = document.getElementById('kiosk-timer-display');
    if (kioskTimer) {
        kioskTimer.textContent = timeStr;
        if (safeSec < 60) {
            kioskTimer.style.color = '#EF4444';
        } else if (safeSec < 180) {
            kioskTimer.style.color = '#F59E0B';
        } else {
            kioskTimer.style.color = '#FBBF24';
        }
    }

    if (statusText) {
        if (safeSec <= 0) {
            statusText.textContent = 'Время истекло';
            statusText.style.color = '#EF4444';
        } else if (safeSec < 60) {
            statusText.textContent = 'Финал: Менее 1 мин!';
            statusText.style.color = '#FCA5A5';
        } else if (currentSyncGroupName) {
            statusText.textContent = `Экзамен • ${currentSyncGroupName}`;
            statusText.style.color = '#CBD5E1';
        } else {
            const catTitles = {
                'mixed': 'Комплексный экзамен',
                'districts': 'Номенклатура районов',
                'rivers': 'Гидрография (Реки)',
                'centers': 'Административные центры',
                'neighbors': 'Топология смежности',
                'puzzle': 'Сборка-пазл'
            };
            statusText.textContent = catTitles[examCategory] || 'Экзамен (Anti-Cheat)';
            statusText.style.color = '#CBD5E1';
        }
    }

    if (timerBar) {
        const totalSec = Math.max(1, examTimeLimitMinutes * 60);
        const percent = Math.min(100, Math.max(0, (safeSec / totalSec) * 100));
        timerBar.style.width = `${percent}%`;
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

function handleExamTimeout() {
    stopGlobalExamTimer();
    stopTimer();

    // 1. Автоматически завершаем попытку и немедленно отправляем результат на сервер
    finishExamEarly(true);

    // 2. Отображаем неблокирующий баннер об окончании времени
    showExamTimeoutBanner();
}

/* ==================== ЗАЩИТА ОТ СПИСЫВАНИЯ (ANTI-CHEAT) ==================== */
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

/* ==================== ОБУЧАЮЩИЙ РЕЖИМ ==================== */
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
            ? item.neighbors.map(n => `<span class="neighbor-tag" onclick="jumpToStudyItem('${n}')">${n}</span>`).join('')
            : '<span style="color: #94A3B8; font-size: 11px;">Нет смежных границ</span>';

        const popFormatted = item.population ? `${Number(item.population).toLocaleString('ru-RU')} чел.` : 'Уточняется';

        contentEl.innerHTML = `
            <h3 class="study-title">${item.name}</h3>
            <div class="info-row"><span>Центр:</span><strong>${item.center || '—'}</strong></div>
            <div class="info-row"><span>Население:</span><strong>~${popFormatted}</strong></div>
            <div class="info-row"><span>Площадь:</span><strong>~${item.area} км²</strong></div>
            <div style="margin-top: 8px;">
                <span style="color: #64748B; font-size: 11px; font-weight: 600;">Граничит:</span>
                <div style="margin-top: 4px; display: flex; flex-wrap: wrap;">${neighborsHtml}</div>
            </div>
        `;
        highlightDistrictOnMapByName(item.name);

    } else if (studyCategory === 'rivers') {
        contentEl.innerHTML = `
            <h3 class="study-title">Река ${item.name}</h3>
            <div class="info-row"><span>Тип:</span><strong>Водный объект / Водоток</strong></div>
            <div class="info-row"><span>Протяженность:</span><strong>~${item.length} км</strong></div>
            <div class="hint-small" style="margin-top: 8px;">Русло выделено красной линией на карте</div>
        `;
        highlightRiverOnMapByName(item.name);

    } else if (studyCategory === 'centers') {
        contentEl.innerHTML = `
            <h3 class="study-title">${item.name}</h3>
            <div class="info-row"><span>Статус:</span><strong>${item.status || 'центр'}</strong></div>
            <div class="info-row"><span>Координаты:</span><strong>${item.lat.toFixed(3)}°, ${item.lon.toFixed(3)}°</strong></div>
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

/* ==================== РЕЖИМ КОНТРОЛЬНОЙ (ЭКЗАМЕНА) ==================== */
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
    examCheatingViolations = 0;
    examStatus = 'passed';
    examToken = '';
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

/* ==================== ИНТЕРАКТИВНЫЙ ПАЗЛ: СОБЕРИ РЕГИОН ==================== */
function startPuzzleMode() {
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

    // Сброс прочих режимов и таймеров
    removePuzzleGhost();
    stopTimer();
    stopGlobalExamTimer();
    disableAntiCheat();
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight(false);
    disablePopups();

    // Скрываем другие экраны интерфейса, показываем панель пазла
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'none';
    const pm = document.getElementById('puzzle-mode');
    if (pm) pm.style.display = 'block';

    // Скрываем базовые тайлы карты, оставляем чистый контурный холст
    setBasemapVisible(false);

    // Скрываем все штатные слои карты, сохраняя их параметры
    hideAllMapLayersForPuzzle();

    // Инициализация структуры данных пазла
    puzzleDistricts = JSON.parse(JSON.stringify(EMBEDDED_PUZZLE_DATA));
    puzzlePlacedDistricts = new Set();
    puzzleSlotLayers = {};
    puzzlePlacedMarkers = [];
    puzzleMistakes = 0;
    puzzleHintsUsed = 0;
    puzzleStartTime = Date.now();

    // 1. Отрисовка чистого внешнего контура региона (БЕЗ внутренних сеток и пунктиров)
    renderPuzzleRegionOutline();

    // 2. Выбор случайного стартового опорного района
    const randomIndex = Math.floor(Math.random() * puzzleDistricts.length);
    puzzleAnchorDistrict = puzzleDistricts[randomIndex];

    // 3. Фиксируем стартовый опорный район на карте с самого начала
    placeDistrictOnMap(puzzleAnchorDistrict, true);

    // 4. Все остальные районы отправляем в пул боковой панели
    puzzleUnplacedQueue = puzzleDistricts.filter(d => d.id !== puzzleAnchorDistrict.id);
    shuffleArray(puzzleUnplacedQueue);

    // 5. Выбираем первую деталь (предпочтительно соседа опорного района)
    const initialNeighbor = puzzleUnplacedQueue.find(d => isDistrictNeighborOfPlaced(d)) || puzzleUnplacedQueue[0];
    if (initialNeighbor) {
        setActivePuzzlePiece(initialNeighbor);
    }

    // 6. Отрисовка списка районов в трее (с реальными силуэтами и топологической индикацией)
    renderPuzzleTray();

    // 7. Обновление шкалы и счетчиков
    updatePuzzleProgress();

    // Центрирование карты по границам региона
    resetMapView();

    // Запуск таймера
    startPuzzleTimer();

    // Настройка зоны сброса Drag-and-Drop на контейнере карты
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
    // Чистое поле: предварительные внутренние линии, сетки и пунктирные слоты полностью убраны!
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

    // 1. Проверка по IDs соседей
    if (district.neighbor_ids && Array.isArray(district.neighbor_ids)) {
        for (let nId of district.neighbor_ids) {
            if (puzzlePlacedDistricts.has(nId)) return true;
        }
    }

    // 2. Проверка по именам соседей
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

    // 3. Пространственный fallback по пересечению bounding-box с допуском 0.015° (~1.5 км)
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

/* ==================== ГЕО-ПРОВЕРКА И DRAG-AND-DROP ПАЗЛА ==================== */
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

/* ==================== SVG СИЛУЭТЫ ДЕТАЛЕЙ ПАЗЛА ==================== */

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

function generateTrueScaleDragSilhouette(piece, map) {
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

/* ==================== ПЛАВАЮЩИЙ SVG-ПРИЗРАК ДЕТАЛИ (DRAG GHOST) ==================== */

function createPuzzleGhost(piece, clientX, clientY) {
    if (!piece) return;

    // Сначала удаляем предыдущий временный элемент, если он существует
    removePuzzleGhost();

    const map = getMapObject();
    const trueScale = generateTrueScaleDragSilhouette(piece, map);

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

/* ==================== ОБРАБОТЧИКИ ПЕРЕТАСКИВАНИЯ (HTML5 + POINTER) ==================== */

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

        // Прозрачный 1x1 пиксель скрывает браузерный серый прямоугольник по умолчанию
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
    if (!pointerDragPiece || !pointerDragStartPt) return;

    // Если нативный HTML5 drag уже запустился, не дублируем
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

    // 1. Проверка геометрического совпадения с целевым районом (a)
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

    // 2. Проверка топологического правила сборки («Конструктор по соседям») (б)
    const isNeighbor = isDistrictNeighborOfPlaced(targetDistrict);
    if (!isNeighbor) {
        triggerPuzzleMismatch(targetDistrict, `⚠️ Топологический запрет! Район «${targetDistrict.name}» не граничит ни с одним из уже собранных районов ядра. Сначала присоедините его соседей!`);
        return;
    }

    // Оба условия выполнены -> фиксация детали в растущее ядро региона
    completePuzzleDistrictPlacement(targetDistrict);
}

function completePuzzleDistrictPlacement(district) {
    // Впаиваем район на карту с заливкой
    placeDistrictOnMap(district, false);

    showPuzzleFloatingMessage(`🧲 Отлично! «${district.name}» пристыкован к ядру региона!`, '#10B981');

    puzzleUnplacedQueue = puzzleUnplacedQueue.filter(p => p.id !== district.id);
    updatePuzzleProgress();

    if (puzzleUnplacedQueue.length === 0) {
        setTimeout(finishPuzzleVictory, 600);
        return;
    }

    // Выбираем следующий активный район — предпочтительно тот, который УЖЕ доступен для стыковки!
    const nextAvailableNeighbor = puzzleUnplacedQueue.find(d => isDistrictNeighborOfPlaced(d)) || puzzleUnplacedQueue[0];
    if (nextAvailableNeighbor) {
        setActivePuzzlePiece(nextAvailableNeighbor);
    }

    renderPuzzleTray();
}

function triggerPuzzleMismatch(targetDistrict, message = null) {
    puzzleMistakes++;

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
                 title="«${p.name}» ${isNeighbor ? '— граничит с ядром, готов к стыковке!' : '— ждет соседних районов'}">
                <span class="${badgeClass}">${badgeText}</span>
                <div class="puzzle-card-svg-wrap">
                    ${svgMarkup}
                </div>
                <div class="puzzle-card-caption">${p.name}</div>
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
                 Студент: <b>${studentInfo.name}</b> (${studentInfo.group})
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
                exam_status: mistakes === 0 ? 'Идеально' : 'Собрано'
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

    // Удаляем контуры и слоты пазла с карты
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

    // Восстанавливаем видимость базовой подложки и слоев
    setBasemapVisible(true);
    restoreMapLayersAfterPuzzle();
    enablePopups();
    resetActiveHighlight(false);
    restoreAllLayers();
    resetMapView();

    // Возвращаем главное меню
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

/* ==================== ВИКТОРИНЫ ==================== */
function startDistrictQuiz() {
    const districts = getDistrictsData();
    if (!districts || districts.length < 2) {
        alert('Для запуска викторины по силуэтам требуется как минимум 2 территории в атласе.');
        return;
    }
    currentQuiz = 'district';
    quizStartTime = Date.now();
    setBasemapVisible(false);
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers('district');

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';

    document.getElementById('quiz-title').textContent = 'Узнать территорию по силуэту';
    document.getElementById('hint-button').style.display = 'block';
    loadDistrictQuiz();
}

function startNeighborQuiz() {
    const neighbors = getNeighborsData();
    if (!neighbors || neighbors.filter(d => d.neighbors && d.neighbors.length >= 1).length === 0) {
        alert('Недостаточно данных о смежности территорий (соседях) для запуска викторины.');
        return;
    }
    currentQuiz = 'neighbor';
    quizStartTime = Date.now();
    setBasemapVisible(false);
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers('neighbor');

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';

    document.getElementById('quiz-title').textContent = 'Топология и соседи (тест)';
    document.getElementById('hint-button').style.display = 'none';
    loadNeighborQuiz();
}

function startCenterQuiz() {
    const centers = getCentersData();
    if (!centers || centers.length === 0) {
        alert('Недостаточно данных об административных центрах для запуска викторины.');
        return;
    }
    currentQuiz = 'center';
    quizStartTime = Date.now();
    setBasemapVisible(true);
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    disablePopups();
    setQuizLayers('center');

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';

    document.getElementById('quiz-title').textContent = 'Найти центр на карте';
    document.getElementById('hint-button').style.display = 'block';
    loadCenterQuiz();
}

function startRiverQuiz() {
    const rivers = getRiversData();
    if (!rivers || rivers.length < 1) {
        alert('В данном регионе нет рек в базе данных гидрографии');
        return;
    }
    currentQuiz = 'river';
    quizStartTime = Date.now();
    setBasemapVisible(true);
    closeInfoCard();
    clearMarkers();
    resetActiveHighlight();
    restoreAllRiverStyles();
    disablePopups();
    setQuizLayers('river');

    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('quiz-mode').style.display = 'block';
    document.getElementById('results-mode').style.display = 'none';

    document.getElementById('quiz-title').textContent = 'Определить реку по руслу';
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

    // В режиме экзамена динамически переключаем видимость подложки в зависимости от типа текущего вопроса
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
            setBasemapVisible(true);
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

function highlightDistrictOnMapByName(districtName) {
    const map = getMapObject();
    if (!map) return;

    resetActiveHighlight();
    const targetNorm = normalizeDistrictName(districtName);
    const targetSimple = districtName.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '');

    let targetLayer = null;

    map.eachLayer(function(layer) {
        if (layer.feature && layer.feature.properties && !targetLayer) {
            const props = layer.feature.properties;
            
            // СТРОГИЙ ФИЛЬТР: Если это не территория (нет нашей метки), пропускаем!
            if (props.is_district_layer !== 1) return;

            const pName = props.display_name || props.NAME_1 || props.NAME_RU || props.NAME || '';
            if (normalizeDistrictName(pName) === targetNorm) {
                targetLayer = layer;
            }
        }
    });

    // Запасной поиск по частичному совпадению
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

    // 1. Расчет среднего значения по карте
    let totalPop = 0, countPop = 0, totalArea = 0, countArea = 0, totalGrp = 0, countGrp = 0;
    EMBEDDED_NEIGHBORS.forEach(d => {
        if (d.population && d.population > 0) { totalPop += d.population; countPop++; }
        if (d.area && d.area > 0) { totalArea += d.area; countArea++; }
        if (d.grp && d.grp > 0) { totalGrp += d.grp; countGrp++; }
    });
    const avgPop = countPop > 0 ? Math.round(totalPop / countPop) : 0;
    const avgArea = countArea > 0 ? Math.round(totalArea / countArea) : 0;
    const avgGrp = countGrp > 0 ? parseFloat((totalGrp / countGrp).toFixed(1)) : 0;

    // 2. Поиск крупнейшего соседа для текущего выбранного региона
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

    // 3. Поиск абсолютного лидера среди всех объектов на карте
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

    // Значения и единицы измерения для 4 колонок
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

    // Динамические подписи для 4 колонок (сокращенные до 12-14 символов с троеточием)
    const labelSelected = formatShortChartName(district.name, 'Выбран');
    const labelAvg = 'В среднем';
    const labelNeighbor = topNeighbor ? formatShortChartName(topNeighbor.name, 'Сосед') : 'Нет соседа';
    const labelLeader = leader ? formatShortChartName(leader.name, 'Лидер') : 'Лидер';

    // Цветовая дифференциация 4 колонок:
    // 1. Выбранный: #3B82F6 (синий)
    // 2. Среднее:   #CBD5E1 (серый)
    // 3. Сосед:     #F59E0B (оранжевый)
    // 4. Лидер:     #8B5CF6 (фиолетовый)
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
        ? district.neighbors.map(n => `<span class="neighbor-tag" onclick="showDistrictInfoCard('${n}')">${n}</span>`).join('')
        : '<em>Нет смежных границ</em>';

    const popFormatted = district.population 
        ? `${Number(district.population).toLocaleString('ru-RU')} чел.` 
        : 'Нет данных';

    const grpFormatted = (district.grp !== undefined && district.grp !== null && district.grp > 0)
        ? `${Number(district.grp).toLocaleString('ru-RU')} млрд ₽`
        : 'Нет данных';

    card.innerHTML = `
        <div class="info-card-header">
            <strong>${district.name}</strong>
            <button onclick="closeInfoCard()" class="close-card-btn">&times;</button>
        </div>
        <div class="info-card-body">
            <div class="info-row"><span>Центр:</span><strong>${district.center}</strong></div>
            <div class="info-row"><span>Население:</span><strong>~${popFormatted}</strong></div>
            <div class="info-row"><span>ВРП:</span><strong>~${grpFormatted}</strong></div>
            <div class="info-row"><span>Площадь:</span><strong>~${district.area} км²</strong></div>
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
        exitQuizDirectly();
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

    currentQuiz = null;
    setTimeout(setupDistrictClickListeners, 500);

    document.getElementById('quiz-mode').style.display = 'none';
    document.getElementById('normal-mode').style.display = 'none';
    document.getElementById('study-mode').style.display = 'none';
    document.getElementById('results-mode').style.display = 'block';

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
                 <div><b>Студент:</b> ${studentInfo.name}</div>
                 <div style="color: #64748B;"><b>Группа:</b> ${studentInfo.group} | <b>Email:</b> ${studentInfo.email}</div>
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
                    <div class="exam-token-val" id="exam-token-display">${examToken}</div>
                    <div>
                        <button onclick="copyExamToken('${examToken}')" class="token-copy-btn">📋 Скопировать код</button>
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

        const studentLine = studentInfo ? `<p style="margin: 4px 0; font-size: 13px; color: #0284C7;">Студент: <strong>${studentInfo.name}</strong> (${studentInfo.group})</p>` : '';

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

    const storageKey = getResultsStorageKey();
    const results = JSON.parse(localStorage.getItem(storageKey) || localStorage.getItem('rostovQuizResults') || '[]');
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
        exam_token: token,
        violations: violations,
        exam_status: displayStatus,
        session_id: currentSyncSessionId || ''
    });
    localStorage.setItem(storageKey, JSON.stringify(results));
    localStorage.setItem('rostovQuizResults', JSON.stringify(results));

    if (currentSyncSessionId) {
        try {
            localStorage.setItem('sfedu_exam_submitted_' + currentSyncSessionId, 'true');
        } catch(e) {}
    }

    // Всегда отправляем результаты на сервер (даже если студент не авторизовался заранее)
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
        exam_token: token,
        violations: violations,
        exam_status: displayStatus,
        session_id: currentSyncSessionId || ''
    };

    fetch('/api/results/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitPayload)
    }).catch(e => {});
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

            <button onclick="closeLeaderboardModal()" class="btn-start" style="margin-top: 16px;">Закрыть</button>
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
            tableHtml += `<tr><td>${index+1}</td><td>${r.name}</td><td>${r.group}</td><td>${r.quiz_type}</td><td><b>${r.score}/${r.max_score}</b></td><td>${r.accuracy}%</td><td>${r.time_spent}</td></tr>`;
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
                <p style="font-weight: 700; color: #0369A1; font-size: 14px;">Привет, ${student.name} (${student.group})!</p>
                <p style="color: #64748B; font-size: 13px; margin-top: 8px;">У вас пока нет сохраненных результатов в выбранной категории.</p>
            </div>`;
        }

        let bestResult = [...myResults].sort((a,b) => b.accuracy - a.accuracy || b.score - a.score)[0];
        let lastResults = [...myResults].reverse();

        let profileHtml = filtersHtml + `
        <div style="text-align: left; margin-bottom: 12px; background: #F0FDF4; border: 1px solid #BBF7D0; padding: 10px 14px; border-radius: 12px;">
            <p style="margin: 0; font-size: 12.5px; color: #166534; font-weight: 700;">👤 Студент: ${student.name}</p>
            <p style="margin: 2px 0 0 0; font-size: 11.5px; color: #15803D;">Группа: ${student.group}</p>
        </div>

        <div style="margin-bottom: 12px; text-align: left;">
            <h4 style="margin: 0 0 5px 0; font-size: 12.5px; color: #1E293B;">⭐ Лучший результат:</h4>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; padding: 8px 12px; border-radius: 9px; font-size: 11.5px; color: #92400E; display: flex; justify-content: space-between; align-items: center;">
                <span>Тест: <b>${bestResult.type}</b> | Баллы: <b>${bestResult.score}/${bestResult.maxScore}</b> (${bestResult.accuracy}%)</span>
                <span>⏱ ${bestResult.time_spent}</span>
            </div>
        </div>

        <div style="text-align: left;">
            <h4 style="margin: 0 0 5px 0; font-size: 12.5px; color: #1E293B;">📜 История прохождений:</h4>
            <div class="lb-table-wrap">
                <table class="lb-styled-table">
                    <tr><th>Дата</th><th>Тест</th><th>Баллы</th><th>%</th><th>Время</th></tr>`;
        
        lastResults.forEach(r => {
            profileHtml += `<tr><td>${r.date}</td><td>${r.type}</td><td><b>${r.score}/${r.maxScore}</b></td><td>${r.accuracy}%</td><td>${r.time_spent}</td></tr>`;
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
        if (authBtn) authBtn.style.display = 'none';
        if (profileBox) {
            profileBox.style.display = 'flex';
            document.getElementById('student-badge-name').textContent = student.name;
            document.getElementById('student-badge-group').textContent = `${student.group}`;
        }
    } else {
        if (authBtn) authBtn.style.display = 'flex';
        if (profileBox) profileBox.style.display = 'none';
    }
}

function injectExamProctorStyles() {
    if (document.getElementById('exam-proctor-injected-styles')) return;
    const style = document.createElement('style');
    style.id = 'exam-proctor-injected-styles';
    style.textContent = `
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

        #timer-bar-container.exam-proctor-panel {
            background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #1E293B 100%) !important;
            border: 1px solid rgba(139, 92, 246, 0.4) !important;
            border-radius: 12px !important;
            padding: 10px 14px !important;
            margin-bottom: 12px !important;
            box-shadow: 0 4px 18px rgba(15, 23, 42, 0.28), 0 1px 3px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            box-sizing: border-box !important;
            transition: all 0.3s ease !important;
        }

        .exam-panel-top {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            margin-bottom: 8px !important;
        }

        .exam-status-badge {
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            color: #CBD5E1 !important;
            letter-spacing: 0.3px !important;
            text-transform: uppercase !important;
        }

        .exam-status-dot {
            width: 8px !important;
            height: 8px !important;
            border-radius: 50% !important;
            background: #10B981 !important;
            box-shadow: 0 0 8px #10B981 !important;
            animation: proctorDotPulse 1.8s infinite !important;
        }

        @keyframes proctorDotPulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.25); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        .exam-timer-wrapper {
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            background: rgba(15, 23, 42, 0.7) !important;
            padding: 4px 10px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
        }

        .exam-timer-icon {
            font-size: 13px !important;
        }

        .exam-timer-display, #timer-text {
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 15px !important;
            font-weight: 800 !important;
            color: #38BDF8 !important;
            letter-spacing: 0.5px !important;
        }

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

        /* 1. Кнопка «Подтвердить ответ» (единый стиль с «Подсказка» и «Завершить викторину») */
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

        /* 2. Скрытие стандартной навигации в режиме экзамена (Kiosk Mode) */
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
            top: 66px !important;
            max-height: calc(100vh - 80px) !important;
        }

        body.exam-mode .leaflet-top {
            top: 62px !important;
        }

        /* 3. Фиолетовая статус-панель экзамена (Kiosk Bar) */
        .exam-kiosk-bar {
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
        }

        .exam-kiosk-bar .kiosk-left {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }

        .exam-kiosk-bar .kiosk-dot {
            width: 10px !important;
            height: 10px !important;
            border-radius: 50% !important;
            background: #EF4444 !important;
            box-shadow: 0 0 10px #EF4444 !important;
            animation: syncPulse 1.5s infinite !important;
        }

        .exam-kiosk-bar .kiosk-title {
            font-size: 13.5px !important;
            font-weight: 700 !important;
            letter-spacing: 0.02em !important;
        }

        .exam-kiosk-bar .kiosk-meta {
            font-size: 11.5px !important;
            color: #CBD5E1 !important;
        }

        .exam-kiosk-bar .kiosk-right {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }

        .exam-kiosk-bar .kiosk-timer-box {
            background: rgba(15, 23, 42, 0.75) !important;
            padding: 6px 14px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
        }

        .exam-kiosk-bar .kiosk-timer-text {
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 16px !important;
            font-weight: 800 !important;
            color: #FBBF24 !important;
            letter-spacing: 0.5px !important;
        }
    `;
    document.head.appendChild(style);
}

/* ИНИЦИАЛИЗАЦИЯ И ПРОВЕРКА ТЕМЫ */
window.addEventListener('load', function() {
    injectExamProctorStyles();
    ensureExamProctorWidgetDOM();
    resetMapView();
    setTimeout(setupDistrictClickListeners, 400);
    updateStudentHeader();

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

// ==================== СИНХРОННЫЙ ЭКЗАМЕНАЦИОННЫЙ ДИСПЕТЧЕР ЮФУ (LMS) ====================

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

function renderExamAlreadySubmittedBanner(session) {
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

    // Проверяем, сдавал ли студент уже этот экзамен
    const alreadySubmittedLocal = localStorage.getItem('sfedu_exam_submitted_' + session.session_id);
    const storageKey = getResultsStorageKey();
    const results = JSON.parse(localStorage.getItem(storageKey) || localStorage.getItem('rostovQuizResults') || '[]');
    const alreadyInResults = results.some(r => r.session_id === session.session_id);
    if (alreadySubmittedLocal || alreadyInResults) {
        renderExamAlreadySubmittedBanner(session);
        return;
    }

    // Абсолютный расчет времени:
    // Оставшееся_время = (sessionStartedAt + timeLimitMinutes * 60 * 1000) - currentServerTime
    const sessionEndTime = session.started_at + (session.time_limit_minutes * 60 * 1000);
    const remainingSeconds = Math.max(0, Math.floor((sessionEndTime - serverNow) / 1000));

    if (remainingSeconds <= 0) {
        renderExamExpiredModal(session);
        return;
    }

    currentSyncSessionId = session.session_id;
    currentSyncGroupName = session.group_name;
    syncExamRemainingSec = remainingSeconds;
    window.currentSyncQuestionCount = session.questions_count || 15;
    window.currentSyncTimeLimit = session.time_limit_minutes || 10;
    window.currentSyncSessionMode = session.mode || 'quiz';

    renderSyncExamBanner(session, remainingSeconds);
    startSyncHeartbeat(session.session_id);

    // Если студент перешел по прямой ссылке на экзамен, сразу активируем контрольную
    if (isUrlDriven) {
        setTimeout(() => {
            startSynchronousExamFromBanner();
        }, 1200);
    }
}
