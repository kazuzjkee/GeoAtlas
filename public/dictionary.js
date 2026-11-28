(function () {
    'use strict';

    const FAV_KEY = 'geoatlas_dict_favorites';
    const RECENT_KEY = 'geoatlas_dict_recent';
    const THEME_KEY = 'geoatlas_theme';

    let dictData = { metadata: {}, categories: [], terms: [] };
    let termsBySlug = new Map();
    let activeCategory = 'all';
    let activeLetter = '';
    let onlyFavorites = false;

    function escapeHtml(str) {
        return String(str ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function normalizeText(str) {
        return String(str ?? '')
            .toLowerCase()
            .replace(/ё/g, 'е')
            .replace(/[^a-zа-я0-9\s-]/gi, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function stemRuToken(tok) {
        if (tok.length <= 4) return tok;
        return tok.replace(/(ами|ями|ого|его|ому|ему|ыми|ими|ах|ях|ов|ев|ей|ом|ем|ою|ею|ия|ие|ию|ии|ой|ый|ий|ая|яя|ое|ее|ые|ие|ы|и|а|я|у|ю|е|о)$/i, '');
    }

    function getFavorites() {
        try {
            const arr = JSON.parse(localStorage.getItem(FAV_KEY) || '[]');
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    }

    function saveFavorites(arr) {
        try { localStorage.setItem(FAV_KEY, JSON.stringify(arr)); } catch (e) {}
    }

    function getRecent() {
        try {
            const arr = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    }

    function pushRecent(slug) {
        const list = getRecent().filter(s => s !== slug);
        list.unshift(slug);
        try { localStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, 8))); } catch (e) {}
    }

    function applyTheme(theme) {
        const isDark = theme === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        const btn = document.getElementById('dict-theme-btn');
        if (btn) btn.textContent = isDark ? '☀️' : '🌙';
        try { localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light'); } catch (e) {}
    }

    window.toggleDictTheme = function () {
        const cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        applyTheme(cur === 'dark' ? 'light' : 'dark');
    };

    function scoreTerm(term, rawQuery) {
        const q = normalizeText(rawQuery);
        if (!q) return 1;

        const titleN = normalizeText(term.title);
        const synN = (term.synonyms || []).map(normalizeText);
        const kwN = (term.keywords || []).map(normalizeText);
        const defsN = normalizeText(`${term.short_def} ${term.academic_def} ${term.simple_explanation} ${term.example}`);

        if (titleN === q) return 1000;
        if (titleN.startsWith(q)) return 600;
        if (titleN.includes(q)) return 400;
        if (synN.some(s => s === q || s.includes(q))) return 280;
        if (kwN.some(k => k === q || k.includes(q))) return 200;
        if (defsN.includes(q)) return 100;

        // Multi-word / stem matching for Russian word forms
        const qTokens = q.split(' ').filter(Boolean).map(stemRuToken);
        if (qTokens.length > 0) {
            const titleStems = titleN.split(' ').map(stemRuToken).join(' ');
            const allText = `${titleN} ${synN.join(' ')} ${kwN.join(' ')} ${defsN}`;
            const allStems = allText.split(' ').map(stemRuToken).join(' ');
            if (qTokens.every(t => titleStems.includes(t))) return 320;
            if (qTokens.every(t => allStems.includes(t))) return 70;
        }
        return 0;
    }

    function renderCategories() {
        const box = document.getElementById('dict-categories');
        if (!box) return;
        const cats = dictData.categories || [];
        box.innerHTML = cats.map(c => `
            <button type="button" class="cat-card ${activeCategory === c.id ? 'active' : ''}" onclick="selectDictCategory('${escapeHtml(c.id)}')">
                <div class="cat-head">
                    <span style="font-weight:800;font-size:15px;">${escapeHtml(c.icon)} ${escapeHtml(c.name)}</span>
                    <span class="cat-count">${c.count}</span>
                </div>
                <div style="font-size:12.5px;color:var(--text-muted);">${escapeHtml(c.description)}</div>
            </button>
        `).join('');
    }

    function renderAlphaBar() {
        const bar = document.getElementById('dict-alpha-bar');
        if (!bar) return;
        const letters = Array.from(new Set(
            (dictData.terms || []).map(t => (t.title || '').trim().charAt(0).toUpperCase().replace('Ё', 'Е')).filter(Boolean)
        )).sort((a, b) => a.localeCompare(b, 'ru'));
        bar.innerHTML = `<button type="button" class="alpha-btn ${activeLetter === '' ? 'active' : ''}" onclick="selectDictLetter('')">Все</button>` +
            letters.map(l => `<button type="button" class="alpha-btn ${activeLetter === l ? 'active' : ''}" onclick="selectDictLetter('${escapeHtml(l)}')">${escapeHtml(l)}</button>`).join('');
    }

    function renderPersonalBars() {
        const wrap = document.getElementById('dict-personal-bars');
        const favWrap = document.getElementById('dict-favorites-wrap');
        const favList = document.getElementById('dict-favorites-list');
        const recWrap = document.getElementById('dict-recent-wrap');
        const recList = document.getElementById('dict-recent-list');
        if (!wrap) return;

        const favs = getFavorites().map(s => termsBySlug.get(s)).filter(Boolean);
        const recs = getRecent().map(s => termsBySlug.get(s)).filter(Boolean);

        if (favs.length === 0 && recs.length === 0) {
            wrap.style.display = 'none';
            return;
        }
        wrap.style.display = 'block';
        if (favWrap && favList) {
            favWrap.style.display = favs.length ? 'block' : 'none';
            favList.innerHTML = favs.map(t => `<button type="button" class="chip" onclick="openDictArticle('${escapeHtml(t.slug)}')">⭐ ${escapeHtml(t.title)}</button>`).join('');
        }
        if (recWrap && recList) {
            recWrap.style.display = recs.length ? 'block' : 'none';
            recList.innerHTML = recs.map(t => `<button type="button" class="chip" onclick="openDictArticle('${escapeHtml(t.slug)}')">${escapeHtml(t.title)}</button>`).join('');
        }
    }

    function renderDictTerms() {
        const searchEl = document.getElementById('dict-search');
        const grid = document.getElementById('dict-terms-grid');
        const empty = document.getElementById('dict-empty-state');
        const countEl = document.getElementById('dict-count-label');
        const clearBtn = document.getElementById('dict-clear-btn');
        const sortSel = document.getElementById('dict-sort-select');
        if (!grid) return;

        const q = searchEl ? searchEl.value.trim() : '';
        if (clearBtn) clearBtn.style.display = (q || activeCategory !== 'all' || activeLetter || onlyFavorites) ? 'inline-flex' : 'none';

        const favSet = new Set(getFavorites());
        let results = [];
        for (const t of (dictData.terms || [])) {
            if (activeCategory !== 'all' && t.category !== activeCategory) continue;
            if (onlyFavorites && !favSet.has(t.slug)) continue;
            if (activeLetter) {
                const first = (t.title || '').trim().charAt(0).toUpperCase().replace('Ё', 'Е');
                if (first !== activeLetter) continue;
            }
            const sc = scoreTerm(t, q);
            if (q && sc <= 0) continue;
            results.push({ term: t, score: sc });
        }

        const sortMode = sortSel ? sortSel.value : 'relevance';
        if (q && sortMode === 'relevance') {
            results.sort((a, b) => b.score - a.score || a.term.title.localeCompare(b.term.title, 'ru'));
        } else {
            results.sort((a, b) => a.term.title.localeCompare(b.term.title, 'ru'));
        }

        if (countEl) countEl.textContent = `Найдено терминов: ${results.length}`;

        if (results.length === 0) {
            grid.innerHTML = '';
            if (empty) empty.style.display = 'block';
            return;
        }
        if (empty) empty.style.display = 'none';

        grid.innerHTML = results.map(({ term: t }) => `
            <article class="term-card" onclick="openDictArticle('${escapeHtml(t.slug)}')">
                <div>
                    <div class="term-card-cat">${escapeHtml(t.category_name)}</div>
                    <h2 class="term-card-title">${escapeHtml(t.title)}</h2>
                    <p class="term-card-def">${escapeHtml(t.short_def)}</p>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--text-light);">
                    <span>${favSet.has(t.slug) ? '⭐ В избранном' : 'Открыть статью →'}</span>
                    ${t.formula ? '<span>📐 Формула</span>' : ''}
                </div>
            </article>
        `).join('');
    }
    window.renderDictTerms = renderDictTerms;

    function updateAutocomplete() {
        const searchEl = document.getElementById('dict-search');
        const listEl = document.getElementById('dict-autocomplete');
        if (!searchEl || !listEl) return;
        const q = searchEl.value.trim();
        if (!q || q.length < 2) {
            listEl.style.display = 'none';
            listEl.innerHTML = '';
            return;
        }
        const matches = (dictData.terms || [])
            .map(t => ({ t, s: scoreTerm(t, q) }))
            .filter(x => x.s > 0)
            .sort((a, b) => b.s - a.s)
            .slice(0, 7);

        if (matches.length === 0) {
            listEl.style.display = 'none';
            return;
        }
        listEl.innerHTML = matches.map(({ t }) => `
            <div class="autocomplete-item" role="option" onclick="openDictArticle('${escapeHtml(t.slug)}')">
                <div>
                    <strong>${escapeHtml(t.title)}</strong>
                    <div style="font-size:12px;color:var(--text-light);">${escapeHtml(t.category_name)}</div>
                </div>
                <span style="font-size:12px;color:var(--primary);">Открыть →</span>
            </div>
        `).join('');
        listEl.style.display = 'block';
    }

    window.selectDictCategory = function (catId) {
        activeCategory = (activeCategory === catId) ? 'all' : catId;
        renderCategories();
        renderDictTerms();
    };

    window.selectDictLetter = function (letter) {
        activeLetter = letter;
        renderAlphaBar();
        renderDictTerms();
    };

    window.toggleFavFilter = function () {
        onlyFavorites = !onlyFavorites;
        const btn = document.getElementById('dict-fav-filter-btn');
        if (btn) btn.classList.toggle('btn-primary', onlyFavorites);
        renderDictTerms();
    };

    window.resetDictFilters = function () {
        const searchEl = document.getElementById('dict-search');
        if (searchEl) searchEl.value = '';
        activeCategory = 'all';
        activeLetter = '';
        onlyFavorites = false;
        const btn = document.getElementById('dict-fav-filter-btn');
        if (btn) btn.classList.remove('btn-primary');
        renderCategories();
        renderAlphaBar();
        renderDictTerms();
        updateAutocomplete();
    };

    function getSimilarTerms(term) {
        const relSet = new Set(term.related || []);
        const kwSet = new Set((term.keywords || []).map(k => k.toLowerCase()));
        return (dictData.terms || [])
            .filter(other => other.slug !== term.slug && !relSet.has(other.slug))
            .map(other => {
                let score = other.category === term.category ? 2 : 0;
                for (const k of (other.keywords || [])) {
                    if (kwSet.has(k.toLowerCase())) score += 3;
                }
                return { other, score };
            })
            .filter(x => x.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 6)
            .map(x => x.other);
    }

    function renderArticle(slug) {
        const catView = document.getElementById('dict-catalog-view');
        const artView = document.getElementById('dict-article-view');
        if (!catView || !artView) return;

        const term = termsBySlug.get(slug);
        catView.style.display = 'none';
        artView.style.display = 'block';

        if (!term) {
            artView.innerHTML = `
                <div class="empty-state">
                    <h2>Термин «${escapeHtml(slug)}» не найден</h2>
                    <p>Возможно, адрес изменён или введён неверный идентификатор.</p>
                    <button type="button" class="btn btn-primary" onclick="backToDictionary()">← Вернуться к словарю</button>
                </div>
            `;
            return;
        }

        pushRecent(term.slug);
        renderPersonalBars();

        const isFav = getFavorites().includes(term.slug);
        const relTerms = (term.related || []).map(s => termsBySlug.get(s)).filter(Boolean);
        const simTerms = getSimilarTerms(term);

        artView.innerHTML = `
            <div class="breadcrumbs" aria-label="Хлебные крошки">
                <a href="/">Главная</a> <span>/</span>
                <a href="/dictionary" onclick="event.preventDefault(); backToDictionary();">Словарь</a> <span>/</span>
                <a href="/dictionary" onclick="event.preventDefault(); backToDictionary('${escapeHtml(term.category)}');">${escapeHtml(term.category_name)}</a> <span>/</span>
                <strong>${escapeHtml(term.title)}</strong>
            </div>

            <article class="article-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                    <div>
                        <span class="eyebrow">${escapeHtml(term.category_name)}</span>
                        <h1 class="page-title" style="margin-bottom:4px;">${escapeHtml(term.title)}</h1>
                        ${term.synonyms && term.synonyms.length ? `<div style="font-size:13px;color:var(--text-light);">Синонимы: ${term.synonyms.map(escapeHtml).join(', ')}</div>` : ''}
                    </div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <button type="button" class="btn ${isFav ? 'btn-primary' : ''}" id="article-fav-btn" onclick="toggleArticleFav('${escapeHtml(term.slug)}')">
                            ${isFav ? '⭐ В избранном' : '☆ В избранное'}
                        </button>
                        <button type="button" class="btn" id="article-copy-btn" onclick="copyArticleLink('${escapeHtml(term.slug)}')">🔗 Скопировать ссылку</button>
                        <button type="button" class="btn" onclick="backToDictionary()">← Вернуться к словарю</button>
                    </div>
                </div>

                <div class="article-section">
                    <h3>Кратко</h3>
                    <p style="margin:0 0 8px;font-weight:600;">${escapeHtml(term.short_def)}</p>
                    <p style="margin:0;color:var(--text-muted);"><strong>Простыми словами:</strong> ${escapeHtml(term.simple_explanation)}</p>
                </div>

                <div class="article-section">
                    <h3>Подробно (академическое определение)</h3>
                    <p style="margin:0;">${escapeHtml(term.academic_def)}</p>
                </div>

                <div class="article-section">
                    <h3>На практике</h3>
                    <p style="margin:0 0 8px;"><strong>Применение:</strong> ${escapeHtml(term.practical_use)}</p>
                    <p style="margin:0 0 8px;"><strong>Пример в географии:</strong> ${escapeHtml(term.example)}</p>
                    ${term.formula ? `<div><strong>Формула:</strong> <span class="formula-box">${escapeHtml(term.formula)}</span></div>` : ''}
                    ${term.units ? `<div style="margin-top:6px;"><strong>Единицы измерения:</strong> <code>${escapeHtml(term.units)}</code></div>` : ''}
                </div>

                ${relTerms.length ? `
                <div class="article-section">
                    <h3>Связанные понятия</h3>
                    <div class="chip-row">
                        ${relTerms.map(r => `<a href="/dictionary/${escapeHtml(r.slug)}" class="chip" onclick="event.preventDefault(); openDictArticle('${escapeHtml(r.slug)}');">${escapeHtml(r.title)}</a>`).join('')}
                    </div>
                </div>` : ''}

                ${simTerms.length ? `
                <div class="article-section">
                    <h3>Похожие термины</h3>
                    <div class="chip-row">
                        ${simTerms.map(s => `<a href="/dictionary/${escapeHtml(s.slug)}" class="chip" onclick="event.preventDefault(); openDictArticle('${escapeHtml(s.slug)}');">${escapeHtml(s.title)}</a>`).join('')}
                    </div>
                </div>` : ''}

                <div class="article-section">
                    <h3>Источники и литература</h3>
                    <ul style="margin:0;padding-left:18px;font-size:13.5px;color:var(--text-muted);">
                        ${(term.sources || []).map(src => `<li>${escapeHtml(src)}</li>`).join('')}
                    </ul>
                </div>
            </article>
        `;
        document.title = `${term.title} — Географический словарь GeoAtlas`;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    window.openDictArticle = function (slug, pushHist = true) {
        const listEl = document.getElementById('dict-autocomplete');
        if (listEl) listEl.style.display = 'none';
        if (pushHist) {
            history.pushState({ slug }, '', `/dictionary/${encodeURIComponent(slug)}`);
        }
        renderArticle(slug);
    };

    window.backToDictionary = function (catId) {
        const catView = document.getElementById('dict-catalog-view');
        const artView = document.getElementById('dict-article-view');
        if (catView) catView.style.display = 'block';
        if (artView) artView.style.display = 'none';
        if (catId) {
            activeCategory = catId;
            renderCategories();
            renderDictTerms();
        }
        document.title = 'Географический словарь — GeoAtlas ЮФУ';
        history.pushState({}, '', '/dictionary');
    };

    window.toggleArticleFav = function (slug) {
        const favs = getFavorites();
        const idx = favs.indexOf(slug);
        if (idx >= 0) favs.splice(idx, 1);
        else favs.unshift(slug);
        saveFavorites(favs);
        renderArticle(slug);
        renderDictTerms();
    };

    window.copyArticleLink = async function (slug) {
        const url = `${window.location.origin}/dictionary/${encodeURIComponent(slug)}`;
        const btn = document.getElementById('article-copy-btn');
        try {
            await navigator.clipboard.writeText(url);
            if (btn) btn.textContent = '✓ Ссылка скопирована';
        } catch (e) {
            if (btn) btn.textContent = url;
        }
        setTimeout(() => { if (btn) btn.textContent = '🔗 Скопировать ссылку'; }, 2200);
    };

    function handleInitialRoute() {
        const path = window.location.pathname.replace(/\/+$/, '');
        const match = path.match(/^\/dictionary\/([^/]+)$/);
        if (match && match[1]) {
            renderArticle(decodeURIComponent(match[1]));
            return;
        }
        const params = new URLSearchParams(window.location.search);
        const q = params.get('q');
        const searchEl = document.getElementById('dict-search');
        if (q && searchEl) searchEl.value = q;
        renderDictTerms();
    }

    async function initDictionary() {
        try {
            const savedTheme = localStorage.getItem(THEME_KEY);
            if (savedTheme === 'dark' || savedTheme === 'light') applyTheme(savedTheme);
        } catch (e) {}

        try {
            const res = await fetch('/public/dictionary.json');
            dictData = await res.json();
            termsBySlug = new Map((dictData.terms || []).map(t => [t.slug, t]));
        } catch (e) {
            const countEl = document.getElementById('dict-count-label');
            if (countEl) countEl.textContent = 'Не удалось загрузить базу словаря.';
            return;
        }

        renderCategories();
        renderAlphaBar();
        renderPersonalBars();

        const searchEl = document.getElementById('dict-search');
        if (searchEl) {
            searchEl.addEventListener('input', () => {
                updateAutocomplete();
                renderDictTerms();
            });
            document.addEventListener('click', (e) => {
                const listEl = document.getElementById('dict-autocomplete');
                if (listEl && !e.target.closest('.search-wrap')) listEl.style.display = 'none';
            });
        }

        window.addEventListener('popstate', () => {
            const path = window.location.pathname.replace(/\/+$/, '');
            const match = path.match(/^\/dictionary\/([^/]+)$/);
            if (match && match[1]) {
                renderArticle(decodeURIComponent(match[1]));
            } else {
                const catView = document.getElementById('dict-catalog-view');
                const artView = document.getElementById('dict-article-view');
                if (catView) catView.style.display = 'block';
                if (artView) artView.style.display = 'none';
                renderDictTerms();
            }
        });

        handleInitialRoute();
    }

    document.addEventListener('DOMContentLoaded', initDictionary);
})();
