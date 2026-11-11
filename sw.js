// ========================================================
// GeoAtlas Service Worker (Offline Support & PWA Cache)
// ========================================================
const CACHE_NAME = 'geoatlas-offline-v1';

const STATIC_PRECACHE_URLS = [
    '/',
    '/index.html',
    '/quiz.js',
    '/branding.json',
    '/public/theme.js',
    '/public/map.css',
    '/public/admin.css',
    '/public/admin.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async (cache) => {
            for (const url of STATIC_PRECACHE_URLS) {
                try {
                    await cache.add(url);
                } catch (e) {
                    // Gracefully skip single asset precache failure (e.g. if offline during install)
                }
            }
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const req = event.request;
    const url = new URL(req.url);

    // Skip non-GET requests (POST, PUT, DELETE) and WebSocket upgrades
    if (req.method !== 'GET') return;
    if (url.protocol === 'ws:' || url.protocol === 'wss:') return;

    // For API calls: Network-only, return graceful offline JSON if no network
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(req).catch(() => {
                return new Response(
                    JSON.stringify({ offline: true, error: 'Автономный режим: нет подключения к серверу' }),
                    {
                        status: 503,
                        headers: { 'Content-Type': 'application/json; charset=utf-8' }
                    }
                );
            })
        );
        return;
    }

    // For static files, HTML and assets: Network-first with Cache fallback
    event.respondWith(
        fetch(req)
            .then((networkResponse) => {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(req, responseClone);
                    });
                }
                return networkResponse;
            })
            .catch(() => {
                return caches.match(req).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // If navigation request and not in cache, fallback to index.html
                    if (req.mode === 'navigate' || req.destination === 'document') {
                        return caches.match('/index.html');
                    }
                    return new Response('Офлайн-режим: ресурс недоступен без интернета', {
                        status: 503,
                        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
                    });
                });
            })
    );
});
