import test from 'node:test';
import assert from 'node:assert/strict';
import { addCase, addReport, getCase, listCases, reportsFor } from '../src/services/storage/caseStore.js';

const sample = { location: 'Rue X', type: 'Road surface damage', severity: 6, priority: 'Standard' };

test('addCase assigns an id and the Submitted status', () => {
  const c = addCase(sample);
  assert.match(c.id, /^CASE-\d{4}$/);
  assert.equal(c.status, 'Submitted');
  assert.equal(listCases()[0].id, c.id);
});

test('addReport links to the case and moves it to In review', () => {
  const c = addCase(sample);
  const r = addReport(c.id);
  assert.match(r.id, /^RPT-\d{4}$/);
  assert.equal(getCase(c.id).status, 'In review');
  assert.equal(reportsFor(c.id).length, 1);
});

test('addReport throws for an unknown case', () => {
  assert.throws(() => addReport('CASE-9999'), /not found/);
});
