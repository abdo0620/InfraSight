// Hash format: #<mode>-<page>, e.g. #citizen-requests
export function parseRoute(modes, defaultMode) {
  const [m, p] = location.hash.slice(1).split('-');
  const mode = modes[m] ? m : defaultMode;
  const pages = modes[mode].pages;
  const page = pages.find((x) => x.id === p) || pages[0];
  return { mode, page };
}

export const navigate = (mode, pageId) => { location.hash = `${mode}-${pageId}`; };
export const onRouteChange = (fn) => addEventListener('hashchange', fn);
