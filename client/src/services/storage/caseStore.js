// Shared data for both modes. Persists to localStorage when available.
// To use a real backend, keep these function names and change their bodies.
const KEY = 'portal.cases.v1';
let state = { cases: [], reports: [] };
try {
  const raw = localStorage.getItem(KEY);
  if (raw) { const s = JSON.parse(raw); state = { cases: s.cases || [], reports: s.reports || [] }; }
} catch (e) { /* storage unavailable: stay in memory */ }

function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ } }
const pad = (n) => String(n).padStart(4, '0');

export const listCases = () => [...state.cases];
export const getCase = (id) => state.cases.find((c) => c.id === id);

export function addCase(data) {
  const c = { id: 'CASE-' + pad(state.cases.length + 1), status: 'Submitted', createdAt: new Date().toISOString(), ...data };
  state.cases.unshift(c);
  save();
  return c;
}

export const listReports = () => [...state.reports];
export const reportsFor = (caseId) => state.reports.filter((r) => r.caseId === caseId);

export function addReport(caseId) {
  const c = getCase(caseId);
  if (!c) throw new Error('Case not found');
  const r = { id: 'RPT-' + pad(state.reports.length + 1), caseId, createdAt: new Date().toISOString() };
  state.reports.unshift(r);
  if (c.status === 'Submitted') c.status = 'In review';
  save();
  return r;
}
