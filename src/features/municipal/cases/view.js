import { esc } from '../../../shared/dom.js';
import { fmtDate } from '../../../shared/format.js';
import { pageHeader } from '../../../shared/ui/pageHeader.js';

// rows: cases already sorted, each with a `reportCount`
export function renderPage({ flash, rows }) {
  const table = rows.length
    ? `<table class="tbl"><thead><tr><th></th><th>Case</th><th>Location</th><th>Damage</th><th>Severity</th><th>Priority</th><th>Status</th><th>Submitted</th><th>Reports</th><th></th></tr></thead><tbody>${rows
        .map((c) => `<tr><td><img src="${c.thumb}" alt=""></td><td>${c.id}</td><td>${esc(c.location)}</td><td>${esc(c.type)}</td><td>${c.severity}/10</td><td><span class="badge">${esc(c.priority)}</span></td><td>${c.status}</td><td>${fmtDate(c.createdAt)}</td><td>${c.reportCount}</td><td><button class="btn sm" data-case="${c.id}">Generate report</button></td></tr>`)
        .join('')}</tbody></table>`
    : '<p class="empty">No cases yet. Requests submitted by citizens appear here.</p>';
  return `${pageHeader('Cases', 'Citizen requests, most severe first.')}${flash ? `<p class="flash">${flash}</p>` : ''}<section class="section">${table}</section>`;
}
