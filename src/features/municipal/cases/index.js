import { listCases, addReport, reportsFor } from '../../../services/storage/caseStore.js';
import { renderPage } from './view.js';

let flash = '';

function markup() {
  const f = flash; flash = '';
  const rows = listCases()
    .map((c) => ({ ...c, reportCount: reportsFor(c.id).length }))
    .sort((a, b) => b.severity - a.severity || b.createdAt.localeCompare(a.createdAt));
  return renderPage({ flash: f, rows });
}

export default {
  id: 'cases',
  title: 'Cases',
  render: markup,
  mount(root) {
    root.onclick = (e) => {
      const b = e.target.closest('[data-case]');
      if (!b) return;
      const r = addReport(b.dataset.case);
      flash = `Report ${r.id} generated. <a href="#municipal-reports">Open Reports</a>`;
      root.innerHTML = markup();
    };
  },
};
