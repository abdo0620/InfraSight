export function renderSidebar(el, mode, pages, activeId) {
  el.innerHTML = pages
    .map((p) => `<a class="nav-link${p.id === activeId ? ' is-active' : ''}" href="#${mode}-${p.id}">${p.title}</a>`)
    .join('');
}
