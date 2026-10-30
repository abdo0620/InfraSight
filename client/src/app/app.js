import { DEFAULT_MODE } from '../config.js';
import { MODES } from './modes.js';
import { parseRoute, navigate, onRouteChange } from './router.js';
import { renderSidebar } from './layout/sidebar.js';
import { initModeSwitch, updateModeSwitch } from './layout/modeSwitch.js';
import { hideSplash, withSplash } from './layout/splash.js';   // new import

export function startApp() {
  const sidebar = document.getElementById('sidebar');
  const content = document.getElementById('content');
  let current = DEFAULT_MODE;

  function render() {
    const { mode, page } = parseRoute(MODES, DEFAULT_MODE);
    current = mode;
    updateModeSwitch(mode);
    renderSidebar(sidebar, mode, MODES[mode].pages, page.id);
    content.onclick = null; // pages may set their own handler in mount()
    content.innerHTML = page.render();
    page.mount?.(content);
    document.title = `${page.title} · Portal`;
  }

  let switching = false;
  initModeSwitch(async () => {
    if (switching) return;                 // ignore clicks during the transition
    switching = true;
    const next = current === 'citizen' ? 'municipal' : 'citizen';
    await withSplash(next, () => navigate(next, MODES[next].pages[0].id));
    switching = false;
  });
  onRouteChange(render);
  render();
  document.fonts.ready.then(() => setTimeout(hideSplash, 600));
}
