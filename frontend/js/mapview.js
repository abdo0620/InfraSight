// Your Leaflet map (from index.js), adapted: CityMap.init({role, tickets, zones, onPin, onZone})
(function(){
const MAP_CSS="\n        :root[data-mode=\"municipal\"], .municipal-theme {\n          --bg: #121214;\n          --surface: rgba(0, 0, 0, 0.1);\n          --text: #ffffff;\n          --muted: #a1a1aa;\n          --line: transparent;\n          --accent: #3f3f46;\n          --danger: #d97706;\n          color-scheme: dark;\n        }\n\n        .dashboard-container {\n          position: relative;\n          width: 100%;\n          height: calc(100vh - 150px);\n          min-height: 480px;\n          border-radius: 16px;\n          margin: 0;\n          padding: 1rem;\n          box-sizing: border-box;\n          overflow: hidden;\n          background-color: var(--bg);\n          color: var(--text);\n          font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif;\n        }\n\n        /* 1. Fullscreen Map Background */\n        .map-wrapper {\n          position: absolute;\n          inset: 0;\n          width: 100%;\n          height: 100%;\n          z-index: 1;\n          background: #121214;\n        }\n\n        .leaflet-tile-pane {\n          filter: \n            invert(100%) \n            hue-rotate(180deg) \n            grayscale(100%) \n            brightness(1.3) \n            contrast(1.7);\n        }\n\n        .map-vignette {\n          position: absolute;\n          inset: 0;\n          pointer-events: none;\n          z-index: 400;\n          box-shadow: \n            inset 0 0 80px 40px #121214,\n            inset 0 0 150px 90px #121214;\n        }\n\n        #municipal-map {\n          width: 100%;\n          height: 100%;\n          background: #121214;\n        }\n\n        /* 2. Top Legend & Filter Bar: 0.1 opacity, no borders, no blur */\n        .floating-overlay-top {\n          position: absolute;\n          top: 1rem;\n          left: 1rem;\n          right: 1rem;\n          z-index: 1000;\n          background: rgba(0, 0, 0, 0.1) !important;\n          backdrop-filter: none !important;\n          -webkit-backdrop-filter: none !important;\n          border: none !important;\n          border-radius: 12px;\n          box-shadow: none !important;\n          padding: 0.65rem 1.25rem;\n          display: flex;\n          flex-wrap: wrap;\n          align-items: center;\n          justify-content: space-between;\n          gap: 1rem;\n        }\n\n        .legend-group {\n          display: flex;\n          align-items: center;\n          gap: 1.25rem;\n          flex-wrap: wrap;\n        }\n\n        .legend-stat-item {\n          display: flex;\n          flex-direction: column;\n          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);\n        }\n\n        .legend-stat-val {\n          font-size: 1.15rem;\n          font-weight: 700;\n          color: #ffffff;\n        }\n\n        .legend-stat-label {\n          font-size: 0.65rem;\n          color: var(--muted);\n          text-transform: uppercase;\n          letter-spacing: 0.08em;\n        }\n\n        .severity-histogram {\n          display: flex;\n          align-items: flex-end;\n          gap: 3px;\n          height: 32px;\n          padding: 3px 6px;\n          background: rgba(0, 0, 0, 0.15) !important;\n          border-radius: 6px;\n          border: none !important;\n        }\n\n        .histo-bar {\n          width: 12px;\n          min-height: 4px;\n          border-radius: 2px 2px 0 0;\n          cursor: pointer;\n          transition: transform 0.15s, opacity 0.15s;\n        }\n\n        .histo-bar:hover {\n          transform: scaleY(1.1);\n          opacity: 0.85;\n        }\n\n        .histo-bar.active-filter {\n          outline: 2px solid #ffffff;\n        }\n\n        .toolbar-group {\n          display: flex;\n          align-items: center;\n          gap: 0.5rem;\n        }\n\n        .tool-btn {\n          padding: 0.45rem 0.75rem;\n          background: rgba(0, 0, 0, 0.2) !important;\n          border: none !important;\n          color: #ffffff;\n          border-radius: 6px;\n          font-size: 0.75rem;\n          cursor: pointer;\n          transition: all 0.2s ease;\n          font-weight: 500;\n          display: flex;\n          align-items: center;\n          gap: 5px;\n          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);\n        }\n\n        .tool-btn:hover {\n          background: rgba(255, 255, 255, 0.1) !important;\n        }\n\n        .tool-btn.active {\n          background: rgba(255, 255, 255, 0.2) !important;\n        }\n\n        .tool-btn.danger {\n          color: #ef4444;\n        }\n\n        .tool-btn.danger:hover {\n          background: rgba(239, 68, 68, 0.2) !important;\n        }\n\n        .severity-picker {\n          display: flex;\n          align-items: center;\n          gap: 0.5rem;\n          font-size: 0.75rem;\n          color: var(--muted);\n          background: rgba(0, 0, 0, 0.2) !important;\n          padding: 0.25rem 0.6rem;\n          border-radius: 6px;\n          border: none !important;\n          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);\n        }\n\n        .severity-picker input[type=\"range\"] {\n          accent-color: #d97706;\n          cursor: pointer;\n          width: 70px;\n        }\n\n        /* 3. Floating Incident List: 0.1 opacity, no borders, text-shadow */\n        .floating-side-panel {\n          position: absolute;\n          right: 1rem;\n          top: 4.5rem;\n          bottom: 1rem;\n          width: 320px;\n          z-index: 1000;\n          background: rgba(0, 0, 0, 0.1) !important;\n          backdrop-filter: none !important;\n          -webkit-backdrop-filter: none !important;\n          border: none !important;\n          border-radius: 14px;\n          box-shadow: none !important;\n          padding: 1rem;\n          display: flex;\n          flex-direction: column;\n          gap: 0.75rem;\n          pointer-events: auto;\n        }\n\n        @media (max-width: 768px) {\n          .floating-side-panel {\n            display: none;\n          }\n        }\n\n        .panel-header {\n          display: flex;\n          justify-content: space-between;\n          align-items: center;\n          font-size: 0.75rem;\n          font-weight: 600;\n          text-transform: uppercase;\n          letter-spacing: 0.05em;\n          color: #ffffff;\n          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);\n          border: none !important;\n          padding-bottom: 0.5rem;\n        }\n\n        .incident-list {\n          overflow-y: auto;\n          display: flex;\n          flex-direction: column;\n          gap: 0.5rem;\n          flex: 1;\n        }\n\n        .incident-card {\n          background: rgba(0, 0, 0, 0.1) !important;\n          border: none !important;\n          border-radius: 8px;\n          padding: 0.65rem;\n          cursor: pointer;\n          transition: all 0.2s;\n          display: flex;\n          flex-direction: column;\n          gap: 3px;\n          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);\n        }\n\n        .incident-card:hover {\n          background: rgba(255, 255, 255, 0.08) !important;\n        }\n\n        .incident-card-header {\n          display: flex;\n          justify-content: space-between;\n          align-items: center;\n          font-size: 0.75rem;\n          font-weight: 600;\n          color: #ffffff;\n        }\n\n        .incident-card-desc {\n          font-size: 0.65rem;\n          color: #d4d4d8;\n          white-space: nowrap;\n          overflow: hidden;\n          text-overflow: ellipsis;\n        }\n\n        .leaflet-popup-content-wrapper {\n          background: rgba(20, 20, 24, 0.92) !important;\n          color: #d4d4d8 !important;\n          border: none !important;\n          border-radius: 10px;\n          box-shadow: 0 12px 30px rgba(0, 0, 0, 0.8);\n        }\n        .leaflet-popup-tip {\n          background: rgba(20, 20, 24, 0.92) !important;\n        }\n      \n.pin-sheet{position:absolute;left:1rem;bottom:1rem;width:min(380px,calc(100% - 2rem));max-height:72%;overflow:auto;z-index:1100;background:#0c0c0e;color:#fff;border-radius:14px;padding:14px;box-shadow:0 20px 50px rgba(0,0,0,.7)}\n.pin-sheet label.f{color:#a1a1aa;font-size:12px;margin:10px 0 4px;display:block}\n";
const MAP_HTML="<div class=\"dashboard-container municipal-theme\" data-mode=\"municipal\">\n        <div class=\"map-wrapper\">\n          <div id=\"municipal-map\"><\/div>\n          <div class=\"map-vignette\"><\/div>\n        <\/div>\n\n        <div class=\"floating-overlay-top\">\n          <div class=\"legend-group\">\n            <div class=\"legend-stat-item\">\n              <span class=\"legend-stat-val\" id=\"dot-count\">0<\/span>\n              <span class=\"legend-stat-label\">Incidents<\/span>\n            <\/div>\n\n            <div style=\"display: flex; flex-direction: column; gap: 2px;\">\n              <div style=\"font-size: 0.6rem; color: #a1a1aa; text-transform: uppercase; text-shadow: 0 1px 2px #000;\">Severity Filter<\/div>\n              <div class=\"severity-histogram\" id=\"severity-histogram\"><\/div>\n            <\/div>\n          <\/div>\n\n          <div class=\"legend-group\">\n            <div class=\"toolbar-group\">\n              <button class=\"tool-btn active\" id=\"mode-dot\">Dot<\/button>\n              <button class=\"tool-btn\" id=\"mode-zone\">Zone<\/button>\n            <\/div>\n\n            <div class=\"severity-picker\">\n              <label for=\"severity-slider\">Severity:<\/label>\n              <input type=\"range\" id=\"severity-slider\" min=\"0\" max=\"10\" step=\"1\" value=\"5\">\n              <span id=\"severity-val\" style=\"font-weight: 600; color: #fff; min-width: 14px;\">5<\/span>\n            <\/div>\n\n            <button class=\"tool-btn danger\" id=\"clear-all\">Clear<\/button>\n          <\/div>\n        <\/div>\n\n        <div id=\"pin-panel\"><\/div>\n        <div class=\"floating-side-panel\">\n          <div class=\"panel-header\">\n            <span id=\"list-title\">All Incidents<\/span>\n            <button id=\"reset-filter-btn\" style=\"background: none; border: none; color: #a1a1aa; font-size: 0.6rem; cursor: pointer; display: none;\">Reset<\/button>\n          <\/div>\n          <div class=\"incident-list\" id=\"sidebar-incident-list\"><\/div>\n        <\/div>\n      <\/div>";
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
  const staff = opts.role !== 'citizen';
  if (!staff) {
    document.querySelector('.toolbar-group').innerHTML = '<span style="font-size:.8rem;color:#fff;text-shadow:0 1px 3px #000">Click anywhere on the map to report a problem</span>';
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
      const d = L.DomUtil.create('div');
      d.style.cssText = 'background:rgba(10,10,12,.85);color:#e9e9ec;padding:6px 10px;border-radius:8px;font:11px Inter,system-ui,sans-serif';
      d.innerHTML = 'Danger<div style="width:150px;height:8px;margin:4px 0 2px;border-radius:4px;background:linear-gradient(90deg,#facc15,#f97316 50%,#dc2626 80%,#7f1d1d)"></div>'
        + '<div style="display:flex;justify-content:space-between;color:#a1a1aa"><span>moderate</span><span>severe</span></div>';
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
      sidebarListEl.innerHTML = `<div style="font-size: 0.7rem; color: #a1a1aa; text-align: center; padding: 1.5rem 0; text-shadow: 0 1px 2px #000;">No incidents found.</div>`;
    } else {
      sidebarListEl.innerHTML = displayedIncidents.map(item => {
        const col = getSeverityColor(item.severityScore);
        return `
          <div class="incident-card" onclick="zoomToIncident('${item.id}')">
            <div class="incident-card-header">
              <span style="display: flex; align-items: center; gap: 5px;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: ${col};"></span>
                ${item.label}
              </span>
              <span style="font-size: 0.65rem; color: ${col}; font-weight: 700;">${item.severityScore}/10</span>
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
