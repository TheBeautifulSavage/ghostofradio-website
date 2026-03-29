const CACHE_NAME = 'ghost-of-radio-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/shows.html',
  '/about.html',
  '/privacy-policy.html',
  '/css/style.css',
  '/js/main.js',
  '/images/logo.png',
  '/images/hero.jpg',
  '/images/about.jpg',
  '/images/sam-spade.jpg',
  '/images/the-shadow.jpg',
  '/images/sherlock.jpg',
  '/images/johnny-dollar.jpg',
  '/images/whistler.jpg',
  '/manifest.json'
];

// Install: cache all core assets
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames
          .filter(function (name) { return name !== CACHE_NAME; })
          .map(function (name) { return caches.delete(name); })
      );
    })
  );
  self.clients.claim();
});

// Fetch: cache-first for HTML/CSS/JS/images, network-first for everything else
self.addEventListener('fetch', function (event) {
  var request = event.request;

  // Only handle GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests (YouTube embeds, Google Fonts, etc.)
  if (!request.url.startsWith(self.location.origin)) return;

  event.respondWith(
    caches.match(request).then(function (cached) {
      if (cached) {
        // Return cached version, but also update cache in background
        var fetchPromise = fetch(request).then(function (response) {
          if (response && response.status === 200) {
            var responseClone = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(request, responseClone);
            });
          }
          return response;
        }).catch(function () {});
        return cached;
      }

      // Not in cache — fetch from network and cache it
      return fetch(request).then(function (response) {
        if (response && response.status === 200) {
          var responseClone = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(request, responseClone);
          });
        }
        return response;
      });
    })
  );
});
