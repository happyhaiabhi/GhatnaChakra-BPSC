/* Shared portal-wide colour mode. Pages now always open in normal mode
   (light). Night mode still works when the user clicks the toggle, but the
   choice is not persisted across reloads. */
(() => {
  function readTheme() {
    return 'light';
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

  function applyTheme(theme) {
    const safeTheme = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', safeTheme);
    document.documentElement.style.colorScheme = safeTheme;
    updateControls(safeTheme);
    document.dispatchEvent(new CustomEvent('examportalthemechange', { detail: { theme: safeTheme } }));
    return safeTheme;
  }

  function toggleTheme() {
    return applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  }

  // Runs synchronously in <head> so every page starts in normal mode.
  applyTheme(readTheme());

  document.addEventListener('DOMContentLoaded', () => updateControls(document.documentElement.getAttribute('data-theme') || 'light'));
  document.addEventListener('click', (event) => {
    const toggle = event.target.closest?.('[data-theme-toggle]');
    if (toggle) toggleTheme();
  });

  window.ExamPortalTheme = { apply: applyTheme, toggle: toggleTheme, current: () => document.documentElement.getAttribute('data-theme') || 'light' };
})();
