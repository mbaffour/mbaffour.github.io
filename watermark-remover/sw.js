/* sw.js — offline support.
   A tool that promises nothing leaves your device should also work when your
   device is not on a network. Cache-first for the handful of files that make
   up the app; the cache name carries a version so a deploy replaces it. */

const CACHE = 'watermark-remover-v1';
const ASSETS = [
    './',
    'index.html',
    'tests.html',
    'manifest.webmanifest',
    'assets/app.css',
    'assets/js/bytes.js',
    'assets/js/unicode.js',
    'assets/js/images.js',
    'assets/js/pdf.js',
    'assets/js/containers.js',
    'assets/js/app.js',
    'assets/js/tests.js',
    '../assets/fonts/fonts.css',
    '../assets/fonts/fraunces-var-latin.woff2',
    '../assets/fonts/inter-var-latin.woff2',
    '../assets/fonts/jetbrains-mono-var-latin.woff2'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE)
            // addAll is all-or-nothing; a single 404 would leave the app
            // uncached forever, so each asset is allowed to fail on its own.
            .then(cache => Promise.all(ASSETS.map(url => cache.add(url).catch(() => null))))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const req = event.request;
    if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;

    event.respondWith(
        caches.match(req).then(hit => hit || fetch(req).then(res => {
            if (res && res.ok && res.type === 'basic') {
                const copy = res.clone();
                caches.open(CACHE).then(c => c.put(req, copy));
            }
            return res;
        }).catch(() => caches.match('index.html')))
    );
});
