import test from 'node:test';
import assert from 'node:assert/strict';
import { MODES } from '../src/app/modes.js';

test('every page has id, title and render, and ids are unique per mode', () => {
  for (const [mode, { pages }] of Object.entries(MODES)) {
    const ids = pages.map((p) => p.id);
    assert.equal(new Set(ids).size, ids.length, `duplicate page id in ${mode}`);
    for (const p of pages) {
      assert.ok(p.id && /^[a-z0-9]+$/.test(p.id), `bad id in ${mode}`);
      assert.ok(p.title, `missing title: ${mode}/${p.id}`);
      assert.equal(typeof p.render, 'function', `missing render: ${mode}/${p.id}`);
    }
  }
});

test('both modes exist', () => {
  assert.deepEqual(Object.keys(MODES).sort(), ['citizen', 'municipal']);
});
