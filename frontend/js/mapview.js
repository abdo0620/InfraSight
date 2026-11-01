// Your Leaflet map (from index.js), adapted: CityMap.init({role, tickets, zones, onPin, onZone})
(function(){
const MAP_CSS="\n        /* Map view. Colours come from the page (styles.css --bg), so the map fades into the page with no visible edge. */\n        .municipal-theme {\n          --surface: rgba(22, 22, 26, 0.22);\n          --surface-line: rgba(255, 255, 255, 0.035);\n          --text: #f4f4f5;\n          --muted: #a1a1aa;\n          --danger: #d97706;\n          color-scheme: dark;\n        }\n\n        .dashboard-container {\n          position: relative;\n          width: 100%;\n          height: calc(100vh - 150px);\n          min-height: 480px;\n          margin: 0;\n          box-sizing: border-box;\n          overflow: hidden;\n          background-color: var(--bg);\n          color: var(--text);\n          font-family: Inter, -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif;\n        }\n\n        /* 1. Map, faded into the page on all four sides */\n        .map-wrapper {\n          position: absolute;\n          inset: 0;\n          z-index: 1;\n          background: var(--bg);\n        }\n\n        .leaflet-tile-pane {\n          filter: invert(100%) hue-rotate(180deg) grayscale(100%) brightness(1.3) contrast(1.7);\n        }\n\n        .map-vignette {\n          position: absolute;\n          inset: 0;\n          pointer-events: none;\n          z-index: 450;\n          background:\n            linear-gradient(to right, var(--bg) 0, transparent 110px, transparent calc(100% - 110px), var(--bg) 100%),\n            linear-gradient(to bottom, var(--bg) 0, transparent 90px, transparent calc(100% - 90px), var(--bg) 100%);\n        }\n\n        #municipal-map {\n          width: 100%;\n          height: 100%;\n          background: var(--bg);\n          font-family: inherit;\n        }\n\n        /* Shared card look for everything that floats on the map */\n        .map-card,\n        .legend-group,\n        .floating-side-panel,\n        .map-legend {\n          background: var(--surface);\n          border: 1px solid var(--surface-line);\n          border-radius: 10px;\n          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);\n          backdrop-filter: blur(5px) saturate(150%);\n          -webkit-backdrop-filter: blur(5px) saturate(150%);\n        }\n\n        /* 2. Top bar: two cards, stats on the left, tools on the right */\n        .floating-overlay-top {\n          position: absolute;\n          top: 1rem;\n          left: 1rem;\n          right: 1rem;\n          z-index: 1000;\n          display: flex;\n          flex-wrap: wrap;\n          align-items: flex-start;\n          justify-content: space-between;\n          gap: 0.75rem;\n          pointer-events: none;\n        }\n\n        .legend-group {\n          display: flex;\n          align-items: center;\n          gap: 0.7rem;\n          flex-wrap: wrap;\n          padding: 0.35rem 0.55rem;\n          pointer-events: auto;\n        }\n\n        .legend-stat-item {\n          display: flex;\n          flex-direction: column;\n          padding-right: 0.7rem;\n          border-right: 1px solid var(--surface-line);\n        }\n\n        .legend-stat-val {\n          font-size: 1.1rem;\n          font-weight: 600;\n          line-height: 1.1;\n          color: var(--text);\n        }\n\n        .legend-stat-label,\n        .histo-title {\n          font-size: 0.56rem;\n          font-weight: 500;\n          color: var(--muted);\n          text-transform: uppercase;\n          letter-spacing: 0.08em;\n        }\n\n        .severity-histogram {\n          display: flex;\n          align-items: flex-end;\n          gap: 2px;\n          height: 20px;\n          margin-top: 4px;\n          padding-bottom: 2px;\n          border-bottom: 1px solid rgba(255, 255, 255, 0.12);\n        }\n\n        .histo-bar {\n          width: 7px;\n          min-height: 3px;\n          border-radius: 2px 2px 0 0;\n          cursor: pointer;\n          opacity: 0.9;\n          transition: opacity 0.15s, transform 0.15s;\n          transform-origin: bottom;\n        }\n\n        .histo-bar:hover {\n          opacity: 1;\n          transform: scaleY(1.08);\n        }\n\n        .histo-bar.active-filter {\n          opacity: 1;\n          box-shadow: 0 0 0 1.5px var(--text);\n        }\n\n        .toolbar-group {\n          display: flex;\n          align-items: center;\n          gap: 2px;\n          padding: 2px;\n          background: rgba(255, 255, 255, 0.04);\n          border-radius: 7px;\n        }\n\n        .tool-btn {\n          padding: 0.28rem 0.5rem;\n          background: transparent;\n          border: none;\n          color: var(--muted);\n          border-radius: 5px;\n          font: inherit;\n          font-size: 0.68rem;\n          font-weight: 500;\n          cursor: pointer;\n          transition: background 0.15s, color 0.15s;\n          display: flex;\n          align-items: center;\n          gap: 5px;\n        }\n\n        .tool-btn:hover {\n          background: rgba(255, 255, 255, 0.07);\n          color: var(--text);\n        }\n\n        .tool-btn.active {\n          background: rgba(255, 255, 255, 0.13);\n          color: var(--text);\n        }\n\n        .tool-btn.danger {\n          color: #f87171;\n        }\n\n        .tool-btn.danger:hover {\n          background: rgba(239, 68, 68, 0.15);\n        }\n\n        .severity-picker {\n          display: flex;\n          align-items: center;\n          gap: 0.5rem;\n          font-size: 0.68rem;\n          color: var(--muted);\n        }\n\n        .severity-picker input[type=\"range\"] {\n          accent-color: #d97706;\n          cursor: pointer;\n          width: 64px;\n          padding: 0;\n          background: none;\n          border: 0;\n        }\n\n        /* 3. Incident list, can be collapsed to its header */\n        .floating-side-panel {\n          position: absolute;\n          right: 1rem;\n          top: 4rem;\n          max-height: calc(100% - 10.5rem);\n          width: 240px;\n          z-index: 1000;\n          padding: 0.5rem;\n          display: flex;\n          flex-direction: column;\n          gap: 0.3rem;\n          pointer-events: auto;\n        }\n\n        .floating-side-panel.collapsed {\n          bottom: auto;\n          width: auto;\n          min-width: 150px;\n          gap: 0;\n        }\n\n        .floating-side-panel.collapsed .incident-list {\n          display: none;\n        }\n\n\n        .panel-header {\n          display: flex;\n          justify-content: space-between;\n          align-items: center;\n          gap: 0.75rem;\n          font-size: 0.6rem;\n          font-weight: 600;\n          text-transform: uppercase;\n          letter-spacing: 0.08em;\n          color: var(--text);\n          padding: 0 0.15rem;\n        }\n\n        .panel-header > div {\n          display: flex;\n          align-items: center;\n          gap: 0.25rem;\n        }\n\n        .panel-link {\n          background: none;\n          border: none;\n          color: var(--muted);\n          font: inherit;\n          font-size: 0.62rem;\n          font-weight: 500;\n          text-transform: none;\n          letter-spacing: 0;\n          cursor: pointer;\n          padding: 0.2rem 0.4rem;\n          border-radius: 4px;\n        }\n\n        .panel-link:hover {\n          color: var(--text);\n          background: rgba(255, 255, 255, 0.07);\n        }\n\n        .incident-list {\n          overflow-y: auto;\n          display: flex;\n          flex-direction: column;\n          gap: 2px;\n          flex: 1;\n          margin: 0 -0.25rem;\n          padding: 0 0.25rem;\n          scrollbar-width: thin;\n          scrollbar-color: rgba(255, 255, 255, 0.15) transparent;\n        }\n\n        .incident-card {\n          background: transparent;\n          border-radius: 6px;\n          padding: 0.4rem 0.45rem;\n          cursor: pointer;\n          transition: background 0.15s;\n          display: flex;\n          flex-direction: column;\n          gap: 2px;\n        }\n\n        .incident-card:hover {\n          background: rgba(255, 255, 255, 0.06);\n        }\n\n        .incident-card-header {\n          display: flex;\n          justify-content: space-between;\n          align-items: flex-start;\n          gap: 0.5rem;\n          font-size: 0.68rem;\n          font-weight: 600;\n          color: var(--text);\n        }\n\n        .incident-card-desc {\n          font-size: 0.62rem;\n          color: var(--muted);\n          white-space: nowrap;\n          overflow: hidden;\n          text-overflow: ellipsis;\n          padding-left: 12px;\n        }\n\n        /* 4. Legend (bottom left) */\n        .leaflet-bottom.leaflet-left .map-legend {\n          margin: 0 0 1rem 1rem;\n        }\n\n        .map-legend {\n          width: 150px;\n          padding: 0.45rem 0.55rem 0.4rem;\n          color: var(--text);\n          font-size: 0.68rem;\n          line-height: 1.3;\n        }\n\n        .ml-title {\n          font-size: 0.55rem;\n          font-weight: 500;\n          color: var(--muted);\n          text-transform: uppercase;\n          letter-spacing: 0.08em;\n          margin-bottom: 4px;\n        }\n\n        .ml-title ~ .ml-title {\n          margin-top: 7px;\n          padding-top: 6px;\n          border-top: 1px solid var(--surface-line);\n        }\n\n        .ml-ramp {\n          height: 6px;\n          border-radius: 4px;\n          background: linear-gradient(90deg, rgb(250, 204, 21) 0%, rgb(249, 115, 22) 50%, rgb(220, 38, 38) 80%, rgb(127, 29, 29) 100%);\n        }\n\n        .ml-dots {\n          display: flex;\n          justify-content: space-between;\n          align-items: center;\n          padding: 0 1px;\n        }\n\n        .ml-dots i {\n          width: 8px;\n          height: 8px;\n          border-radius: 50%;\n          box-shadow: 0 0 0 1.5px #121214;\n        }\n\n        .ml-scale {\n          display: flex;\n          justify-content: space-between;\n          margin-top: 3px;\n          color: var(--muted);\n          font-size: 0.55rem;\n        }\n\n        /* 5. Leaflet controls in the same dark style */\n        .leaflet-bottom.leaflet-right .leaflet-control-zoom {\n          margin: 0 1rem 0.5rem 0;\n        }\n\n        .leaflet-bar,\n        .leaflet-touch .leaflet-bar {\n          border: 1px solid var(--surface-line);\n          border-radius: 8px;\n          overflow: hidden;\n          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);\n        }\n\n        .leaflet-bar a,\n        .leaflet-touch .leaflet-bar a {\n          background: var(--surface);\n          color: var(--text);\n          border-bottom: 1px solid var(--surface-line);\n          width: 26px;\n          height: 26px;\n          line-height: 26px;\n          font-size: 14px;\n        }\n\n        .leaflet-bar a:hover {\n          background: #222226;\n          color: var(--text);\n        }\n\n        .leaflet-bar a:last-child {\n          border-bottom: none;\n        }\n\n        .leaflet-control-attribution.leaflet-control {\n          background: transparent;\n          color: #52525b;\n          font-size: 10px;\n          margin: 0 1rem 0.25rem 0;\n        }\n\n        .leaflet-control-attribution a {\n          color: #71717a;\n        }\n\n        .leaflet-popup-content-wrapper {\n          background: rgba(20, 20, 24, 0.95);\n          color: #d4d4d8;\n          border: 1px solid var(--surface-line);\n          border-radius: 10px;\n          box-shadow: 0 12px 30px rgba(0, 0, 0, 0.8);\n        }\n\n        .leaflet-popup-tip {\n          background: rgba(20, 20, 24, 0.95);\n        }\n\n\n        /* legend toggle: only used on phones */\n        .ml-toggle {\n          display: none;\n        }\n\n        /* 6. Phones: compact bars, list as a bottom sheet, legend behind a button */\n        @media (max-width: 760px) {\n          .dashboard-container {\n            height: 72vh;\n            min-height: 440px;\n          }\n\n          .floating-overlay-top {\n            top: 0.5rem;\n            left: 0.5rem;\n            right: 0.5rem;\n            gap: 0.4rem;\n          }\n\n          .legend-group {\n            padding: 0.3rem 0.45rem;\n            gap: 0.4rem;\n            max-width: 100%;\n          }\n\n          .severity-picker label {\n            display: none;\n          }\n\n          .floating-side-panel {\n            top: auto;\n            left: 0.5rem;\n            right: 0.5rem;\n            bottom: 0.5rem;\n            width: auto;\n            max-height: 45%;\n          }\n\n          .floating-side-panel.collapsed {\n            left: auto;\n            bottom: 0.5rem;\n            min-width: 0;\n          }\n\n          .leaflet-control-zoom {\n            display: none;\n          }\n\n          .leaflet-bottom.leaflet-left {\n            bottom: 2.6rem;\n          }\n\n          .leaflet-bottom.leaflet-left .map-legend {\n            margin: 0 0 0 0.5rem;\n          }\n\n          .map-legend {\n            width: auto;\n            padding: 0;\n          }\n\n          .ml-toggle {\n            display: block;\n            background: none;\n            border: none;\n            color: var(--text);\n            font: inherit;\n            font-size: 0.6rem;\n            font-weight: 600;\n            text-transform: uppercase;\n            letter-spacing: 0.08em;\n            padding: 0.45rem 0.6rem;\n            cursor: pointer;\n          }\n\n          .ml-body {\n            display: none;\n            width: 150px;\n            padding: 0 0.55rem 0.45rem;\n          }\n\n          .map-legend.open .ml-body {\n            display: block;\n          }\n\n          .leaflet-control-attribution.leaflet-control {\n            display: none;\n          }\n        }\n.pin-sheet{position:absolute;left:1rem;bottom:1rem;width:min(380px,calc(100% - 2rem));max-height:72%;overflow:auto;z-index:1100;background:#0c0c0e;color:#fff;border-radius:14px;padding:14px;box-shadow:0 20px 50px rgba(0,0,0,.7)}\n.pin-sheet label.f{color:#a1a1aa;font-size:12px;margin:10px 0 4px;display:block}\n";
const MAP_HTML="<div class=\"dashboard-container municipal-theme\" data-mode=\"municipal\">\n        <div class=\"map-wrapper\">\n          <div id=\"municipal-map\"><\/div>\n          <div class=\"map-vignette\"><\/div>\n        <\/div>\n\n        <div class=\"floating-overlay-top\">\n          <div class=\"legend-group\">\n            <div class=\"legend-stat-item\">\n              <span class=\"legend-stat-val\" id=\"dot-count\">0<\/span>\n              <span class=\"legend-stat-label\">Incidents<\/span>\n            <\/div>\n\n            <div style=\"display: flex; flex-direction: column; gap: 2px;\">\n              <div class=\"histo-title\">Severity filter<\/div>\n              <div class=\"severity-histogram\" id=\"severity-histogram\"><\/div>\n            <\/div>\n          <\/div>\n\n          <div class=\"legend-group\">\n            <div class=\"toolbar-group\">\n              <button class=\"tool-btn active\" id=\"mode-dot\">Dot<\/button>\n              <button class=\"tool-btn\" id=\"mode-zone\">Zone<\/button>\n            <\/div>\n\n            <div class=\"severity-picker\">\n              <label for=\"severity-slider\">Severity:<\/label>\n              <input type=\"range\" id=\"severity-slider\" min=\"0\" max=\"10\" step=\"1\" value=\"5\">\n              <span id=\"severity-val\" style=\"font-weight: 600; color: var(--text); min-width: 14px;\">5<\/span>\n            <\/div>\n\n            <button class=\"tool-btn danger\" id=\"clear-all\">Clear<\/button>\n          <\/div>\n        <\/div>\n\n        <div id=\"pin-panel\"><\/div>\n        <div class=\"floating-side-panel\">\n          <div class=\"panel-header\">\n            <span id=\"list-title\">All Incidents<\/span>\n            <div><button class=\"panel-link\" id=\"reset-filter-btn\" style=\"display: none;\">Reset<\/button><button class=\"panel-link\" id=\"toggle-list\" aria-expanded=\"true\">Hide<\/button><\/div>\n          <\/div>\n          <div class=\"incident-list\" id=\"sidebar-incident-list\"><\/div>\n        <\/div>\n      <\/div>";
function getSeverityColor(score) {
  const s = Math.max(0, Math.min(10, score));
  let r, g, b;

  if (s <= 5) {
    const t = s / 5;
    r = Math.round(90 + (214 - 90) * t);
    g = Math.round(105 + (158 - 105) * t);
    b = Math.round(120 + (46 - 120) * t);
  } else {
    const t = (s - 5) / 5;
    r = Math.round(214 + (217 - 214) * t);
    g = Math.round(158 + (119 - 158) * t);
    b = Math.round(46 + (6 - 46) * t);
  }
  return `rgb(${r}, ${g}, ${b})`;
}

function initMunicipalMap(opts) {
  const brestCoords = [48.3904, -4.4861];
  
  const map = L.map('municipal-map', {
    center: brestCoords,
    zoom: 14,
    minZoom: 10,
    maxZoom: 19,
    zoomControl: false,
    updateWhenZooming: false,
    keepBuffer: 6
  });

  map.createPane('redDotsPane');
  map.getPane('redDotsPane').style.zIndex = 9999;

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 10,
    subdomains: ['a', 'b', 'c'],
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  const markersCluster = L.markerClusterGroup({
    iconCreateFunction: function(cluster) {
      const childMarkers = cluster.getAllChildMarkers();
      let totalScore = 0;
      childMarkers.forEach(m => {
        totalScore += (m.options.severityScore ?? 5);
      });
      const avgScore = totalScore / childMarkers.length;
      const clusterColor = getSeverityColor(avgScore);
      const size = childMarkers.length < 10 ? 34 : childMarkers.length < 50 ? 42 : 50;

      return L.divIcon({
        html: `<div style="background-color: ${clusterColor}; color: #ffffff; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: 700; font-size: 0.75rem; box-shadow: 0 4px 15px rgba(0,0,0,0.6); border: 2px solid rgba(255,255,255,0.3);">${cluster.getChildCount()}</div>`,
        className: 'custom-cluster-icon',
        iconSize: [size, size]
      });
    }
  });
  map.addLayer(markersCluster);

  let currentMode = 'dot';
  let dotRadius = 10;
  let currentSeverity = 5;
  let activeIncidents = [];
  let activePolygons = [];
  let zonePoints = [];
  let tempPolyline = null;
  let activeScoreFilter = null;

  const dotBtn = document.getElementById('mode-dot');
  const zoneBtn = document.getElementById('mode-zone');
  const severitySlider = document.getElementById('severity-slider');
  const severityValEl = document.getElementById('severity-val');
  const clearBtn = document.getElementById('clear-all');
  const dotCountEl = document.getElementById('dot-count');
  const sidebarListEl = document.getElementById('sidebar-incident-list');
  const listTitleEl = document.getElementById('list-title');
  const resetFilterBtn = document.getElementById('reset-filter-btn');
  const histogramEl = document.getElementById('severity-histogram');
  const sidePanel = document.querySelector('.floating-side-panel');
  const toggleListBtn = document.getElementById('toggle-list');
  const LIST_KEY = 'infrasight.listHidden';
  function setListHidden(hide, remember = true) {
    sidePanel.classList.toggle('collapsed', hide);
    toggleListBtn.textContent = hide ? 'Show' : 'Hide';
    toggleListBtn.setAttribute('aria-expanded', String(!hide));
    if (remember) try { localStorage.setItem(LIST_KEY, hide ? '1' : '0'); } catch (e) {}
  }
  let listHidden = window.matchMedia('(max-width: 760px)').matches;
  try { const v = localStorage.getItem(LIST_KEY); if (v === '1' || v === '0') listHidden = v === '1'; } catch (e) {}
  setListHidden(listHidden, false);
  toggleListBtn.addEventListener('click', () => setListHidden(!sidePanel.classList.contains('collapsed')));
  const staff = opts.role !== 'citizen';
  if (!staff) {
    document.querySelector('.toolbar-group').innerHTML = '<span style="font-size:.75rem;color:var(--text);padding:.4rem .6rem">Click anywhere on the map to report a problem</span>';
    document.querySelector('.severity-picker').remove();
    clearBtn.remove();
  } else {
    document.querySelector('.toolbar-group').insertAdjacentHTML('beforeend', '<button class="tool-btn active" id="ai-zones">AI zones</button><button class="tool-btn" id="finish-zone">Finish zone</button>');
  }

  dotBtn.addEventListener('click', () => {
    currentMode = 'dot';
    dotBtn.classList.add('active');
    zoneBtn.classList.remove('active');
  });

  zoneBtn.addEventListener('click', () => {
    currentMode = 'zone';
    zoneBtn.classList.add('active');
    dotBtn.classList.remove('active');
  });

  severitySlider.addEventListener('input', (e) => {
    currentSeverity = parseInt(e.target.value, 10);
    severityValEl.textContent = currentSeverity;
  });

  function addIncidentMarker(lat, lng, label = 'Incident', severityScore = 5, imageUrl = null, description = 'No additional description provided.', isCitizen = false, ref = null) {
    const colorHex = getSeverityColor(severityScore);

    const circle = L.circleMarker([lat, lng], {
      pane: 'redDotsPane',
      color: '#121214',
      fillColor: colorHex,
      fillOpacity: 0.95,
      radius: dotRadius,
      weight: 1.5
    });

    circle.options.severityScore = severityScore;

    const defaultImg = imageUrl || null;
    
    circle.bindPopup(`
      <div style="width: 220px; font-family: inherit;">
        <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 4px; color: #fff;">${label}</div>
        <div style="font-size: 0.7rem; color: #aaa; margin-bottom: 6px;">Severity Score: <b style="color: ${colorHex};">${severityScore} / 10</b></div>
        ${defaultImg ? `<img src="${defaultImg}" alt="Incident photo" style="width: 100%; height: 120px; object-fit: cover; border-radius: 6px; margin-bottom: 6px;" />` : ''}
        <p style="font-size: 0.7rem; color: #ccc; margin: 0 0 6px 0; line-height: 1.3;">${description}</p>
        <div style="font-size: 0.6rem; color: #777;">GPS: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
        ${ref ? `<a href="#ticket-${ref}" style="display:inline-block;margin-top:6px;font-size:0.7rem;color:#d97757;">Open ticket</a>` : ''}
      </div>
    `);

    const id = 'dot_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
    const incidentObj = { id, layer: circle, lat, lng, type: 'dot', label, severityScore, description, isCitizen, ref };
    
    activeIncidents.push(incidentObj);

    if (activeScoreFilter === null || Math.round(severityScore) === activeScoreFilter) {
      markersCluster.addLayer(circle);
    }

    updateUI();
    return circle;
  }

  function loadCitizenCases() {
    (opts.tickets || []).forEach(t => addIncidentMarker(t.lat, t.lng, t.label, t.score, t.img, t.desc, true, t.canOpen ? t.id : null));
    updateUI();
  }

  loadCitizenCases();

  const ZC = ['#000', '#6b7a8a', '#9a8f5c', '#c9952c', '#d97706', '#ef4444'];
  const aiLayer = L.layerGroup();
  let pinMarker = null;
  function placePin(lat, lng) {
    if (pinMarker) map.removeLayer(pinMarker);
    pinMarker = L.circleMarker([lat, lng], { pane: 'redDotsPane', color: '#fff', fillColor: '#d97757', fillOpacity: 1, radius: 11, weight: 2 }).addTo(map);
    if (opts.onPin) opts.onPin(lat, lng);
  }
  function addZonePolygon(points, level, id) {
    // organic outline and yellow-to-red layers, like the AI zones (js/map.js)
    const p = window.drawOrganicPolygon(points, Math.min(5, Math.max(1, level || 3)), id).addTo(map);
    activePolygons.push({ id, layer: p, type: 'zone' });
  }
  if (staff) {
    const legend = L.control({ position: 'bottomleft' });
    legend.onAdd = () => {
      const d = L.DomUtil.create('div', 'map-legend');
      const dots = [0, 2, 4, 6, 8, 10].map(v => `<i style="background:${getSeverityColor(v)}"></i>`).join('');
      d.innerHTML = '<button type="button" class="ml-toggle" aria-expanded="false">Legend</button><div class="ml-body">'
        + '<div class="ml-title">Danger zones</div><div class="ml-ramp"></div>'
        + '<div class="ml-scale"><span>Moderate</span><span>High</span><span>Severe</span></div>'
        + `<div class="ml-title">Reports by severity</div><div class="ml-dots">${dots}</div>`
        + '<div class="ml-scale"><span>0</span><span>5</span><span>10</span></div></div>';
      const tg = d.querySelector('.ml-toggle');
      tg.onclick = () => tg.setAttribute('aria-expanded', String(d.classList.toggle('open')));
      L.DomEvent.disableClickPropagation(d);
      return d;
    };
    legend.addTo(map);
  }
  if (staff) {
    (opts.tickets || []).forEach(t => {
      if (!t.zone) return;
      window.drawZone(t.zone, t.lat, t.lng).bindTooltip(t.tip, { sticky: true }).addTo(aiLayer);
      if (t.detour) L.polyline(t.detour, window.DETOUR_STYLE).bindTooltip(t.detourTip, { sticky: true }).addTo(aiLayer);
    });
    // streets with repeated problems (Hotspots page): purple dashed rings, bigger with more reports
    (opts.hotspots || []).forEach(h => {
      if (h.lat == null) return;
      L.polygon(window.organicRing(h.lat, h.lng, 60 + h.count * 25, h.street), { color: '#a855f7', fillColor: '#a855f7', fillOpacity: 0.1, weight: 2, dashArray: '2 6' })
        .bindTooltip(h.tip, { sticky: true }).addTo(aiLayer);
    });
    aiLayer.addTo(map);
    (opts.zones || []).forEach(z => addZonePolygon(z.points, z.level, z.id));
    document.getElementById('ai-zones').onclick = e => {
      const on = map.hasLayer(aiLayer);
      if (on) map.removeLayer(aiLayer); else map.addLayer(aiLayer);
      e.currentTarget.classList.toggle('active', !on);
    };
    document.getElementById('finish-zone').onclick = () => {
      if (zonePoints.length < 3) return;
      const level = Math.max(1, Math.min(5, Math.ceil(currentSeverity / 2)));
      const id = 'zone_' + Date.now();
      addZonePolygon(zonePoints.slice(), level, id);
      if (opts.onZone) opts.onZone({ id, points: zonePoints.slice(), level });
      zonePoints = [];
      if (tempPolyline) map.removeLayer(tempPolyline);
    };
  }

  let resizeTimer = null;
  map.whenReady(() => {
    map.invalidateSize(true);
    resizeTimer = setTimeout(() => map.invalidateSize(true), 150);
  });


  map.on('click', (e) => {
    const { lat, lng } = e.latlng;
    if (opts.role === 'citizen') { placePin(lat, lng); return; }
    if (currentMode === 'dot') {
      addIncidentMarker(lat, lng, 'Manual Inspection', currentSeverity, null, 'Manually placed observation.', false);
    } else if (currentMode === 'zone') {
      zonePoints.push([lat, lng]);
      
      if (tempPolyline) map.removeLayer(tempPolyline);
      tempPolyline = L.polyline(zonePoints, { color: '#ef4444', dashArray: '4, 4' }).addTo(map);

      if (false) {
        const polygon = L.polygon(zonePoints, {
          pane: 'redDotsPane',
          color: '#ef4444',
          fillColor: '#ef4444',
          fillOpacity: 0.25,
          weight: 2
        }).addTo(map);

        const id = 'zone_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
        activePolygons.push({ id, layer: polygon, type: 'zone' });
        zonePoints = [];
        if (tempPolyline) map.removeLayer(tempPolyline);
        updateUI();
      }
    }
  });

  function updateUI() {
    dotCountEl.textContent = activeIncidents.length;

    let histoHtml = '';
    const counts = Array(11).fill(0);
    activeIncidents.forEach(item => {
      const s = Math.round(item.severityScore);
      if (s >= 0 && s <= 10) counts[s]++;
    });
    const maxCount = Math.max(...counts, 1);

    for (let score = 0; score <= 10; score++) {
      const cnt = counts[score];
      const heightPx = Math.max(4, Math.round((cnt / maxCount) * 24));
      const barColor = getSeverityColor(score);
      const isActive = activeScoreFilter === score ? 'active-filter' : '';

      histoHtml += `
        <div class="histo-bar ${isActive}" 
             style="height: ${heightPx}px; background-color: ${barColor};" 
             title="Score ${score}: ${cnt} incidents (Click to filter)"
             onclick="filterByScore(${score})">
        </div>
      `;
    }
    histogramEl.innerHTML = histoHtml;

    const displayedIncidents = activeScoreFilter === null 
      ? activeIncidents 
      : activeIncidents.filter(i => Math.round(i.severityScore) === activeScoreFilter);

    if (activeScoreFilter !== null) {
      listTitleEl.textContent = `Score ${activeScoreFilter} (${displayedIncidents.length})`;
      resetFilterBtn.style.display = 'block';
    } else {
      listTitleEl.textContent = `All Incidents (${displayedIncidents.length})`;
      resetFilterBtn.style.display = 'none';
    }

    if (displayedIncidents.length === 0) {
      sidebarListEl.innerHTML = `<div style="font-size: 0.7rem; color: var(--muted); text-align: center; padding: 1.5rem 0;">No incidents found.</div>`;
    } else {
      sidebarListEl.innerHTML = displayedIncidents.map(item => {
        const col = getSeverityColor(item.severityScore);
        return `
          <div class="incident-card" onclick="zoomToIncident('${item.id}')">
            <div class="incident-card-header">
              <span style="display: flex; align-items: baseline; gap: 6px;">
                <span style="flex: none; width: 6px; height: 6px; border-radius: 50%; background: ${col}; transform: translateY(-1px);"></span>
                ${item.label}
              </span>
              <span style="flex: none; font-size: 0.65rem; color: ${col}; font-weight: 600; font-variant-numeric: tabular-nums;">${item.severityScore}/10</span>
            </div>
            <div class="incident-card-desc">${item.description}</div>
          </div>
        `;
      }).join('');
    }
  }

  window.filterByScore = function(score) {
    if (activeScoreFilter === score) {
      activeScoreFilter = null;
    } else {
      activeScoreFilter = score;
    }

    markersCluster.clearLayers();
    activeIncidents.forEach(item => {
      if (activeScoreFilter === null || Math.round(item.severityScore) === activeScoreFilter) {
        markersCluster.addLayer(item.layer);
      }
    });

    updateUI();
  };

  resetFilterBtn.addEventListener('click', () => {
    activeScoreFilter = null;
    markersCluster.clearLayers();
    activeIncidents.forEach(item => markersCluster.addLayer(item.layer));
    updateUI();
  });

  window.zoomToIncident = function(id) {
    const found = activeIncidents.find(i => i.id === id);
    if (found && found.layer) {
      map.setView([found.lat, found.lng], 16, { animate: true });
      found.layer.openPopup();
    }
  };

  clearBtn.addEventListener('click', () => {
    markersCluster.clearLayers();
    activePolygons.forEach(item => map.removeLayer(item.layer));
    activeIncidents = [];
    activePolygons = [];
    zonePoints = [];
    activeScoreFilter = null;
    if (tempPolyline) map.removeLayer(tempPolyline);
    updateUI();
  });
  // Cancel the pending resize: running it on a removed map throws "_leaflet_pos" errors.
  return { map, destroy() { clearTimeout(resizeTimer); map.stop(); map.remove(); } };
}

window.CityMap={css:MAP_CSS,html:MAP_HTML,init:initMunicipalMap};
})();
