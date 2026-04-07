const CACHE_NAME = 'jefe-turno-v1';
const URLS = [
  '/',
  '/manifest.webmanifest',
  '/static/styles.css'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(URLS)));
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
