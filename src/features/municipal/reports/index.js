import { listReports, getCase } from '../../../services/storage/caseStore.js';
import { buildReportPdf } from '../../../services/pdf/reportPdf.js';
import { renderPage } from './view.js';

export default {
  id: 'reports',
  title: 'Reports',
  render: () => renderPage({ rows: listReports().map((r) => ({ ...r, case: getCase(r.caseId) })).filter((r) => r.case) }),
  mount(root) {
    const msg = root.querySelector('#msg');
    root.onclick = (e) => {
      const v = e.target.closest('[data-view]'), d = e.target.closest('[data-dl]');
      const id = v?.dataset.view || d?.dataset.dl;
      if (!id) return;
      msg.hidden = true;
      try {
        const rep = listReports().find((r) => r.id === id);
        const doc = buildReportPdf(rep, getCase(rep.caseId));
        if (d) { doc.save(`${rep.id}.pdf`); return; }
        root.querySelector('#frame').src = URL.createObjectURL(doc.output('blob'));
        root.querySelector('#preview').hidden = false;
        root.querySelector('#preview').scrollIntoView({ behavior: 'smooth' });
      } catch (err) { msg.textContent = err.message; msg.hidden = false; }
    };
  },
};
