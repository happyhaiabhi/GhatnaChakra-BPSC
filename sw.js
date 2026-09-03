/* ═══════════════════════════════════════════════════════════════════════
   Exam Question Bank — service worker

   Makes the portal work offline and load instantly on repeat visits, which
   matters for anyone revising on a phone with patchy signal.

   Strategy (deliberately conservative — see the note at the bottom):

     HTML pages      network-first  → you never get a stale app shell; if the
                                      network is down, the cached page is used.
     css / js / svg  cache-first,     static assets are cheap and safe to serve
                     revalidated      from cache; a fresh copy is fetched in the
                     in background    background for the next visit.
     JSON datasets   network-first  → question data must never go stale; the
                     (cache fallback) cache is only a fallback for offline use.
     everything else network only     (Firebase, Google Fonts, PDFs, …)

   Registration is guarded so a browser without service workers — or an
   insecure origin — simply gets the normal site. Nothing here is required
   for the portal to work.

   ═══════════════════════════════════════════════════════════════════════ */

/* Bump this whenever a cached shell file changes, so old caches are dropped.
   It is the only thing you need to touch when you deploy a CSS/JS change. */
const CACHE_VERSION = 'v1';
const SHELL_CACHE = `exam-portal-shell-${CACHE_VERSION}`;
const DATA_CACHE = `exam-portal-data-${CACHE_VERSION}`;

/* Relative to the service worker's scope, so the same file works at
   http://localhost:8000/ and https://<user>.github.io/GhatnaChakra-BPSC/. */
const SHELL_ASSETS = [
  './',
  './index.html',
  './upsc.html',
  './404.html',
  './favicon.svg',
  './site.webmanifest',
  './portal.css',
  './styles.css',
  './bpsc-theme.css',
  './theme.js',
  './app.js',
  './data.js',
  './register-sw.js',
  './bpsc/index.html',
  './bpsc/css/base.css',
  './bpsc/css/floral-pattern.svg',
  './bpsc/css/portal-notes.css',
  './bpsc/css/screens.css',
  './bpsc/js/00-data.js',
  './bpsc/js/01-store.js',
  './bpsc/js/02-chapters.js',
  './bpsc/js/03-dashboard.js',
  './bpsc/js/04-history.js',
  './bpsc/js/05-search.js',
  './bpsc/js/06-focus.js',
  './bpsc/js/07-question.js',
  './bpsc/js/08-quiz.js',
  './bpsc/js/09-nav.js',
  './bpsc/js/10-sync.js',
  './bpsc/js/11-export.js',
  './bpsc/js/12-books.js',
  './bpsc/js/13-global-search.js',
  './bpsc/js/14-boot.js',
  './bpsc/js/date-banner.js',
  './bpsc/pyq-lab.css',
  './bpsc/pyq-lab.js',
];

const scopeUrl = (path) => new URL(path, self.registration.scope);

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL_CACHE);
    // addAll() rejects the whole batch if one file 404s; precache one by one so
    // a single missing file cannot abort the install.
    await Promise.all(SHELL_ASSETS.map(async (path) => {
      try {
        await cache.add(new Request(scopeUrl(path), { cache: 'reload' }));
      } catch (err) {
        console.warn('[sw] could not precache', path, err && err.message);
      }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keep = new Set([SHELL_CACHE, DATA_CACHE]);
    const names = await caches.keys();
    await Promise.all(names.filter((n) => !keep.has(n)).map((n) => caches.delete(n)));
    await self.clients.claim();
  })());
});

const isJson = (url) => url.pathname.endsWith('.json');
const isShellAsset = (url) =>
  /\.(css|js|svg|webmanifest)$/.test(url.pathname) || url.pathname.endsWith('/favicon.svg');

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request, { ignoreSearch: false });
    if (cached) return cached;
    // Last resort for navigations: hand back the cached portal.
    if (request.mode === 'navigate') {
      const shell = await cache.match(scopeUrl('./index.html'));
      if (shell) return shell;
    }
    throw err;
  }
}

async function cacheFirstWithRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then((response) => {
      if (response && response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => null);
  return cached || (await network) || fetch(request);
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  // Never touch cross-origin traffic (Firebase, Google Fonts, remote images)
  // or the browser's own devtools probes.
  if (url.origin !== self.location.origin) return;
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  // Large study PDFs are downloaded on purpose; leave them to the network.
  if (url.pathname.endsWith('.pdf')) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, SHELL_CACHE));
    return;
  }
  if (isJson(url)) {
    event.respondWith(networkFirst(request, DATA_CACHE));
    return;
  }
  if (isShellAsset(url)) {
    event.respondWith(cacheFirstWithRevalidate(request, SHELL_CACHE));
    return;
  }
  // Anything else on our origin: straight to the network.
});

/* ── Manual controls ─────────────────────────────────────────────────────
   From any page:  navigator.serviceWorker.controller.postMessage('clear-cache')
   to wipe everything (handy while developing). */
self.addEventListener('message', (event) => {
  if (event.data === 'clear-cache') {
    event.waitUntil((async () => {
      const names = await caches.keys();
      await Promise.all(names.map((n) => caches.delete(n)));
      const cache = await caches.open(SHELL_CACHE);
      await Promise.all(SHELL_ASSETS.map(async (path) => {
        try { await cache.add(new Request(scopeUrl(path), { cache: 'reload' })); }
        catch (_) { /* ignore */ }
      }));
    })());
  }
});

/* NOTE ON FRESHNESS
   -----------------
   HTML and JSON are network-first, so an online visitor always gets current
   content; the cache is only used when the network fails. That is the safe
   default for a question bank.

   If you would rather have instant repeat loads and can tolerate serving one
   visit of slightly stale questions, switch the JSON branch above to
   `cacheFirstWithRevalidate(request, DATA_CACHE)`. One line. */
