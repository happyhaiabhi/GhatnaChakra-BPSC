/* Registers the offline service worker.
 *
 * Loaded with `defer` from every page. It is entirely optional: no
 * service-worker support, an insecure origin, or a file:// open all skip it
 * silently and the site behaves exactly as before.
 */
(() => {
  try {
    // file:// has no service workers, and Chrome only allows them on https or
    // localhost. Registering there would just log an error.
    if (!('serviceWorker' in navigator)) return;
    if (location.protocol !== 'https:' && location.hostname !== 'localhost'
        && location.hostname !== '127.0.0.1') return;

    window.addEventListener('load', () => {
      // `../sw.js` from bpsc/index.html and `sw.js` from the root both resolve
      // to the same root-scoped worker, so the whole portal shares one cache.
      const url = location.pathname.indexOf('/bpsc/') !== -1 ? '../sw.js' : 'sw.js';
      navigator.serviceWorker.register(url, { scope: undefined })
        .catch((err) => console.warn('[sw] registration failed:', err && err.message));
    });
  } catch (_) {
    /* Storage can be unavailable in strict private modes; the site still works. */
  }
})();
