import { esc } from '../../../shared/dom.js';
import { fmtDate } from '../../../shared/format.js';
import { pageHeader } from '../../../shared/ui/pageHeader.js';

// rows: reports, each with its `case`
export function renderPage({ rows }) {
  const table = rows.length
    ? `<table class="tbl"><thead><tr><th>Report</th><th>Case</th><th>Location</th><th>Damage</th><th>Severity</th><th>Generated</th><th></th></tr></thead><tbody>${rows
        .map((r) => `<tr><td>${r.id}</td><td>${r.case.id}</td><td>${esc(r.case.location)}</td><td>${esc(r.case.type)}</td><td>${r.case.severity}/10</td><td>${fmtDate(r.createdAt)}</td><td class="acts"><button class="btn sm ghost" data-view="${r.id}">View</button> <button class="btn sm" data-dl="${r.id}">Download PDF</button></td></tr>`)
        .join('')}</tbody></table>`
    : '<p class="empty">No reports yet. Generate one from Cases.</p>';
  return `${pageHeader('Reports', 'PDF reports generated from cases.')}<p class="err" id="msg" hidden></p><section class="section">${table}</section><section class="section" id="preview" hidden><h2>Preview</h2><iframe id="frame" class="pdf-frame" title="PDF preview"></iframe></section>`;
}
