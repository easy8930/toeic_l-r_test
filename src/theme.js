const themeKey = 'listening-room-theme';
export function applyTheme(theme, remember = false) {
  const selected = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = selected;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', selected === 'dark' ? '#14221b' : '#245b4b');
  const control = document.querySelector('#theme-select');
  if (control) control.value = selected;
  if (remember) {
    try { localStorage.setItem(themeKey, selected); } catch { /* Still apply for this session. */ }
  }
}
export function initThemeControl() {
  applyTheme(document.documentElement.dataset.theme);
  document.querySelector('#theme-select').addEventListener('change', event => applyTheme(event.target.value, true));
}
window.addEventListener('storage', event => {
  if (event.key === themeKey) applyTheme(event.newValue || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
});
