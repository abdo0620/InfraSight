import { prepareImage, segmentDamage, assessDamage, repairImage, overlayMask, thumbnail } from '../../../services/ai/index.js';
import { addCase, listCases } from '../../../services/storage/caseStore.js';
import { STEPS, LABEL, renderPage, reportHtml } from './view.js';

let S = fresh();
let flash = '';
function fresh() { return { work: null, point: { x: 0.5, y: 0.5 }, seg: null, report: null, after: null, views: null, busy: false, coords: null, verifiedLocation: null }; }

function markup() {
  const f = flash; flash = '';
  return renderPage({ flash: f, cases: listCases() });
}

function mount(root) {
  const $ = (id) => root.querySelector('#' + id);
  const setStep = (i, state) => {
    const li = root.querySelector(`.steps li[data-i="${i}"]`);
    if (!li) return;
    li.dataset.state = state;
    li.querySelector('.st').textContent = LABEL[state];
  };
  const movePin = () => { 
    const pin = $('pin');
    if (pin) {
      pin.style.left = S.point.x * 100 + '%'; 
      pin.style.top = S.point.y * 100 + '%'; 
    }
  };
  const resetResult = () => { 
    if ($('out')) $('out').hidden = true; 
    if ($('err')) $('err').hidden = true; 
    STEPS.forEach((_, i) => setStep(i, 'idle')); 
  };
  const show = (v) => {
    if ($('view')) $('view').src = S.views[v];
    root.querySelectorAll('#seg button').forEach((b) => b.classList.toggle('on', b.dataset.v === v));
  };

  const fileInput = $('file');
  if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      S = fresh();
      S.work = await prepareImage(file);
      if ($('photo')) $('photo').src = S.work.toDataURL('image/jpeg', 0.85);
      if ($('stage')) $('stage').hidden = false;
      if ($('hint')) $('hint').hidden = false;
      if ($('drop-text')) $('drop-text').textContent = 'Change photo';
      if ($('run')) $('run').disabled = false;
      movePin();
      resetResult();
    });
  }

  const photo = $('photo');
  if (photo) {
    photo.addEventListener('click', (e) => {
      const r = e.target.getBoundingClientRect();
      S.point = { x: (e.clientX - r.left) / r.width, y: (e.clientY - r.top) / r.height };
      movePin();
    });
  }

  const runBtn = $('run');
  if (runBtn) {
    runBtn.addEventListener('click', async () => {
      if (!S.work || S.busy) return;
      S.busy = true;
      runBtn.disabled = true;
      resetResult();
      let i = 0;
      try {
        setStep(0, 'run'); S.seg = await segmentDamage(S.work, S.point); setStep(0, 'done');
        i = 1; setStep(1, 'run'); S.report = await assessDamage(S.work, S.seg); setStep(1, 'done');
        i = 2; setStep(2, 'run'); S.after = await repairImage(S.work, S.seg); setStep(2, 'done');
        S.views = {
          before: S.work.toDataURL('image/jpeg', 0.85),
          mask: overlayMask(S.work, S.seg).toDataURL('image/jpeg', 0.85),
          after: S.after.toDataURL('image/jpeg', 0.85),
        };
        if ($('report')) $('report').innerHTML = reportHtml(S.report);
        show('after');
        if ($('out')) $('out').hidden = false;
      } catch (err) {
        setStep(i, 'fail');
        if ($('err')) {
          $('err').textContent = err.message;
          $('err').hidden = false;
        }
      }
      S.busy = false;
      runBtn.disabled = false;
    });
  }

  const seg = $('seg');
  if (seg) {
    seg.addEventListener('click', (e) => { if (e.target.dataset.v) show(e.target.dataset.v); });
  }

  // Gestion de l'input d'adresse et suggestions
  const locInput = $('loc');
  if (locInput) {
    if (!root.querySelector('#loc-suggestions')) {
      const wrapper = document.createElement('div');
      wrapper.style.position = 'relative';
      locInput.parentNode.insertBefore(wrapper, locInput);
      wrapper.appendChild(locInput);

      const suggestionsBox = document.createElement('div');
      suggestionsBox.id = 'loc-suggestions';
      suggestionsBox.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--surface, #1e1e1e);
        border: 1px solid var(--line, #333);
        border-radius: 4px;
        max-height: 220px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
        font-size: 13px;
      `;
      wrapper.appendChild(suggestionsBox);
    }

    const suggestionsBox = $('loc-suggestions');
    let searchTimeout = null;

    locInput.addEventListener('input', () => {
      S.verifiedLocation = null;
      S.coords = null;
      const query = locInput.value.trim();

      clearTimeout(searchTimeout);
      if (query.length < 1) {
        if (suggestionsBox) {
          suggestionsBox.innerHTML = '';
          suggestionsBox.style.display = 'none';
        }
        return;
      }

      searchTimeout = setTimeout(async () => {
        try {
          const searchQuery = query.toLowerCase().includes('brest') ? query : `${query}, Brest, France`;
          const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=fr&limit=15`);
          const data = await response.json();

          const brestResults = data.filter(item => item.display_name.toLowerCase().includes('brest'));

          if (brestResults && brestResults.length > 0) {
            suggestionsBox.innerHTML = brestResults.map((item, idx) => {
              const parts = item.display_name.split(',').map(p => p.trim());
              const shortName = parts.slice(0, 3).join(', ');
              return `<div class="loc-suggestion-item" data-idx="${idx}" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid var(--line, #333); color: var(--text, #f2f2f2);">${shortName}</div>`;
            }).join('');
            suggestionsBox.style.display = 'block';

            suggestionsBox.querySelectorAll('.loc-suggestion-item').forEach((el, idx) => {
              el.addEventListener('click', () => {
                const selected = brestResults[idx];
                const parts = selected.display_name.split(',').map(p => p.trim());
                const shortName = parts.slice(0, 3).join(', ');

                locInput.value = shortName;
                S.verifiedLocation = shortName;
                S.coords = { lat: parseFloat(selected.lat), lon: parseFloat(selected.lon) };
                suggestionsBox.style.display = 'none';
              });
            });
          } else {
            suggestionsBox.innerHTML = `<div style="padding: 8px 12px; color: var(--muted, #888);">Aucune adresse correspondante à Brest.</div>`;
            suggestionsBox.style.display = 'block';
          }
        } catch (err) {
          console.error(err);
        }
      }, 200);
    });
  }

  const submitBtn = $('submit');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      const locInputVal = locInput ? locInput.value.trim() : '';

      if (!locInputVal) {
        alert('Veuillez entrer une adresse.');
        return;
      }

      if (!S.coords || !S.verifiedLocation) {
        alert('Veuillez sélectionner une adresse officielle dans la liste des suggestions.');
        return;
      }

      addCase({
        location: S.verifiedLocation,
        coords: S.coords,
        note: $('note') ? $('note').value.trim() : '',
        type: S.report ? S.report.damage_type : 'Unknown',
        severity: S.report ? S.report.severity : 5,
        priority: S.report ? S.report.priority : 'Normal',
        thumb: S.work ? thumbnail(S.work) : '',
        before: S.work ? thumbnail(S.work, 520) : '',
        after: S.after ? thumbnail(S.after, 520) : '',
        report: S.report,
      });

      S = fresh();
      flash = 'Request submitted successfully with a verified address. The city will review it.';
      root.innerHTML = markup();
      mount(root);
    });
  }
}

export default {
  id: 'requests',
  title: 'Requests',
  render: () => { S = fresh(); return markup(); },
  mount,
};