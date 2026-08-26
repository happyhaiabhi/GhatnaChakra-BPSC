/* Shared portal-wide colour mode. One setting controls portal, UPSC and BPSC. */
(() => {
  const STORAGE_KEY = 'exam_portal_theme';
  const LEGACY_BPSC_KEY = 'gc_theme';

  function readTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved === 'light' || saved === 'dark' ? saved : 'dark';
    } catch (_) {
      return 'dark';
    }
  }

  function updateControls(theme) {
    document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
      const dark = theme === 'dark';
      button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('title', dark ? 'Turn night mode off' : 'Turn night mode on');
      button.classList.toggle('is-active', dark);
      const state = button.querySelector('[data-theme-state]');
      if (state) state.textContent = dark ? 'On' : 'Off';
    });
  }

  function applyTheme(theme, persist = true) {
    const safeTheme = theme === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', safeTheme);
    document.documentElement.style.colorScheme = safeTheme;
    if (persist) {
      try {
        localStorage.setItem(STORAGE_KEY, safeTheme);
        // The imported BPSC application reads this legacy key on startup.
        localStorage.setItem(LEGACY_BPSC_KEY, safeTheme);
      } catch (_) { /* storage can be unavailable in strict file previews */ }
    }
    updateControls(safeTheme);
    document.dispatchEvent(new CustomEvent('examportalthemechange', { detail: { theme: safeTheme } }));
    return safeTheme;
  }

  function toggleTheme() {
    return applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  }

  // Runs synchronously in <head> to prevent a bright flash before CSS loads.
  applyTheme(readTheme());

  document.addEventListener('DOMContentLoaded', () => updateControls(document.documentElement.getAttribute('data-theme') || 'dark'));
  document.addEventListener('click', (event) => {
    const toggle = event.target.closest?.('[data-theme-toggle]');
    if (toggle) toggleTheme();
  });
  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY && (event.newValue === 'light' || event.newValue === 'dark')) {
      applyTheme(event.newValue, false);
    }
  });

  window.ExamPortalTheme = { apply: applyTheme, toggle: toggleTheme, current: () => document.documentElement.getAttribute('data-theme') || 'dark' };
})();
