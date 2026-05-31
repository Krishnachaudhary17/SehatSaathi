const CACHE_NAME = 'sehat-saathi-v3';
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './logo.png',
    './manifest.json'
];

// Install Event — only cache bare essentials, NOT style.css or JS
self.addEventListener('install', (event) => {
    self.skipWaiting(); // Take control immediately
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// Activate Event — delete ALL old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    // Delete every cache that isn't current version
                    if (cache !== CACHE_NAME) {
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim()) // Take control of all open pages
    );
});

// Fetch Event — Network FIRST for everything (CSS, JS always fresh)
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;

    // API calls: always network, never cache
    if (event.request.url.includes('/api/')) return;

    // CSS and JS: always go to network (never serve stale)
    const url = new URL(event.request.url);
    if (url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
        event.respondWith(fetch(event.request));
        return;
    }

    // Everything else: network first, cache fallback
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
