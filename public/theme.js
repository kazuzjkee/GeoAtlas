(function() {
    const STORAGE_KEY = 'geoatlas_theme';
    const html = document.documentElement;

    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getSavedTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch(e) {
            return null;
        }
    }

    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        const icon = document.getElementById('theme-toggle-icon');
        if (icon) {
            icon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) {
            meta.setAttribute('content', theme === 'dark' ? '#0B1120' : '#2563EB');
        }
        // Уведомляем карту (Leaflet) о смене темы
        window.dispatchEvent(new CustomEvent('geoatlas:theme-change', { detail: { theme } }));
    }

    function toggleTheme() {
        const current = html.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        try {
            localStorage.setItem(STORAGE_KEY, next);
        } catch(e) {}
        applyTheme(next);
    }

    // Инициализация: сохранённая тема > системная
    const saved = getSavedTheme();
    applyTheme(saved || getSystemTheme());

    // Следим за системной темой, если пользователь не переопределял
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!getSavedTheme()) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });

    window.toggleTheme = toggleTheme;
    window.applyGeoAtlasTheme = applyTheme;
    window.getGeoAtlasTheme = () => html.getAttribute('data-theme') || 'light';
})();
