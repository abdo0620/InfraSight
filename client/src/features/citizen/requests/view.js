import { AI } from '../../../config.js';
import { esc } from '../../../shared/dom.js';
import { fmtDate } from '../../../shared/format.js';
import { pageHeader } from '../../../shared/ui/pageHeader.js';

export const STEPS = [['Isolate the damage', 'SAM 3.1'], ['Assess the structure', 'Muse Spark'], ['Preview the repair', 'Muse Image']];
export const LABEL = { idle: 'Waiting', run: 'Running…', done: 'Done', fail: 'Failed' };

function myRequests(cases) {
  if (!cases.length) return '<p>No requests yet.</p>';
  return `<table class="tbl"><thead><tr><th></th><th>ID</th><th>Location</th><th>Damage</th><th>Severity</th><th>Status</th><th>Date</th></tr></thead><tbody>${cases
    .map((r) => `<tr><td><img src="${r.thumb}" alt=""></td><td>${r.id}</td><td>${esc(r.location)}</td><td>${esc(r.type)}</td><td>${r.severity}/10</td><td>${r.status}</td><td>${fmtDate(r.createdAt)}</td></tr>`)
    .join('')}</tbody></table>`;
}

export function reportHtml(r) {
  return `<div class="score"><span>${r.severity}</span>/10 <small>${esc(r.priority)}</small></div>
  <dl class="kv">
    <dt>Damage</dt><dd>${esc(r.damage_type)}</dd>
    <dt>Tripping hazard</dt><dd>${esc(r.tripping_hazard)}</dd>
    <dt>Exposed materials</dt><dd>${esc((r.exposed_materials || []).join(', '))}</dd>
    <dt>Accessibility</dt><dd>${esc(r.accessibility_impact)}</dd>
    <dt>Recommended action</dt><dd>${esc(r.recommended_action)}</dd>
  </dl>
  <details><summary>Structured JSON</summary><pre>${esc(JSON.stringify(r, null, 2))}</pre></details>`;
}

export function renderPage({ flash, cases }) {
  return `
  ${pageHeader('Requests', 'Report damaged infrastructure. Upload a photo and get a repair assessment.')}
  ${flash ? `<p class="flash">${flash}</p>` : ''}
  <section class="req-grid">
    <div class="panel">
      <h2>New request</h2>
      <label class="drop"><input type="file" accept="image/*" id="file" hidden><span id="drop-text">Choose a photo</span></label>
      <div class="stage" id="stage" hidden><img id="photo" alt="Uploaded damage"><span class="pin" id="pin"></span></div>
      <p class="hint" id="hint" hidden>Tap the damage to mark it.</p>
      <input id="loc" placeholder="Location (street, landmark)">
      <textarea id="note" rows="2" placeholder="Note (optional)"></textarea>
      <button class="btn" id="run" disabled>Analyze</button>
    </div>
    <div class="panel">
      <h2>Analysis</h2>
      <ol class="steps">${STEPS.map((s, i) => `<li data-i="${i}"><div><b>${s[0]}</b><small>${s[1]}</small></div><span class="st">Waiting</span></li>`).join('')}</ol>
      <p class="err" id="err" hidden></p>
      <div id="out" hidden>
        <div class="seg" id="seg"><button data-v="before">Before</button><button data-v="mask">Damage</button><button data-v="after" class="on">After</button></div>
        <img id="view" class="view" alt="Result">
        <div id="report"></div>
        <button class="btn" id="submit">Submit request</button>
      </div>
      ${AI.useMock ? '<p class="note">Demo mode: results are simulated in the browser.</p>' : ''}
    </div>
  </section>
  <section class="section"><h2>My requests</h2>${myRequests(cases)}</section>`;
}
