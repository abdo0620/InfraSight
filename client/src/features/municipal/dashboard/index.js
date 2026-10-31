import { listCases, addCase } from '../../../services/storage/caseStore.js';

export default {
  id: 'dashboard',
  title: 'Dashboard',
  render: () => {
    const dashboardHtml = `
      <style>
        :root[data-mode="municipal"], .municipal-theme {
          --bg: #121214;
          --surface: rgba(0, 0, 0, 0.1);
          --text: #ffffff;
          --muted: #a1a1aa;
          --line: transparent;
          --accent: #3f3f46;
          --danger: #d97706;
          color-scheme: dark;
        }

        .dashboard-container {
          position: relative;
          width: 100%;
          height: calc(100vh - 80px);
          margin: 0;
          padding: 1rem;
          box-sizing: border-box;
          overflow: hidden;
          background-color: var(--bg);
          color: var(--text);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        /* 1. Fullscreen Map Background */
        .map-wrapper {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          z-index: 1;
          background: #121214;
        }

        .leaflet-tile-pane {
          filter: 
            invert(100%) 
            hue-rotate(180deg) 
            grayscale(100%) 
            brightness(1.3) 
            contrast(1.7);
        }

        .map-vignette {
          position: absolute;
          inset: 0;
          pointer-events: none;
          z-index: 400;
          box-shadow: 
            inset 0 0 80px 40px #121214,
            inset 0 0 150px 90px #121214;
        }

        #municipal-map {
          width: 100%;
          height: 100%;
          background: #121214;
        }

        /* 2. Top Legend & Filter Bar: 0.1 opacity, no borders, no blur */
        .floating-overlay-top {
          position: absolute;
          top: 1rem;
          left: 1rem;
          right: 1rem;
          z-index: 1000;
          background: rgba(0, 0, 0, 0.1) !important;
          backdrop-filter: none !important;
          -webkit-backdrop-filter: none !important;
          border: none !important;
          border-radius: 12px;
          box-shadow: none !important;
          padding: 0.65rem 1.25rem;
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
        }

        .legend-group {
          display: flex;
          align-items: center;
          gap: 1.25rem;
          flex-wrap: wrap;
        }

        .legend-stat-item {
          display: flex;
          flex-direction: column;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);
        }

        .legend-stat-val {
          font-size: 1.15rem;
          font-weight: 700;
          color: #ffffff;
        }

        .legend-stat-label {
          font-size: 0.65rem;
          color: var(--muted);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .severity-histogram {
          display: flex;
          align-items: flex-end;
          gap: 3px;
          height: 32px;
          padding: 3px 6px;
          background: rgba(0, 0, 0, 0.15) !important;
          border-radius: 6px;
          border: none !important;
        }

        .histo-bar {
          width: 12px;
          min-height: 4px;
          border-radius: 2px 2px 0 0;
          cursor: pointer;
          transition: transform 0.15s, opacity 0.15s;
        }

        .histo-bar:hover {
          transform: scaleY(1.1);
          opacity: 0.85;
        }

        .histo-bar.active-filter {
          outline: 2px solid #ffffff;
        }

        .toolbar-group {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .tool-btn {
          padding: 0.45rem 0.75rem;
          background: rgba(0, 0, 0, 0.2) !important;
          border: none !important;
          color: #ffffff;
          border-radius: 6px;
          font-size: 0.75rem;
          cursor: pointer;
          transition: all 0.2s ease;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 5px;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);
        }

        .tool-btn:hover {
          background: rgba(255, 255, 255, 0.1) !important;
        }

        .tool-btn.active {
          background: rgba(255, 255, 255, 0.2) !important;
        }

        .tool-btn.danger {
          color: #ef4444;
        }

        .tool-btn.danger:hover {
          background: rgba(239, 68, 68, 0.2) !important;
        }

        .severity-picker {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.75rem;
          color: var(--muted);
          background: rgba(0, 0, 0, 0.2) !important;
          padding: 0.25rem 0.6rem;
          border-radius: 6px;
          border: none !important;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);
        }

        .severity-picker input[type="range"] {
          accent-color: #d97706;
          cursor: pointer;
          width: 70px;
        }

        /* 3. Floating Incident List: 0.1 opacity, no borders, text-shadow */
        .floating-side-panel {
          position: absolute;
          right: 1rem;
          top: 4.5rem;
          bottom: 1rem;
          width: 320px;
          z-index: 1000;
          background: rgba(0, 0, 0, 0.1) !important;
          backdrop-filter: none !important;
          -webkit-backdrop-filter: none !important;
          border: none !important;
          border-radius: 14px;
          box-shadow: none !important;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          pointer-events: auto;
        }

        @media (max-width: 768px) {
          .floating-side-panel {
            display: none;
          }
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #ffffff;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);
          border: none !important;
          padding-bottom: 0.5rem;
        }

        .incident-list {
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          flex: 1;
        }

        .incident-card {
          background: rgba(0, 0, 0, 0.1) !important;
          border: none !important;
          border-radius: 8px;
          padding: 0.65rem;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          flex-direction: column;
          gap: 3px;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.95);
        }

        .incident-card:hover {
          background: rgba(255, 255, 255, 0.08) !important;
        }

        .incident-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.75rem;
          font-weight: 600;
          color: #ffffff;
        }

        .incident-card-desc {
          font-size: 0.65rem;
          color: #d4d4d8;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .leaflet-popup-content-wrapper {
          background: rgba(20, 20, 24, 0.92) !important;
          color: #d4d4d8 !important;
          border: none !important;
          border-radius: 10px;
          box-shadow: 0 12px 30px rgba(0, 0, 0, 0.8);
        }
        .leaflet-popup-tip {
          background: rgba(20, 20, 24, 0.92) !important;
        }
      </style>

      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
      <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />

      <div class="dashboard-container municipal-theme" data-mode="municipal">
        <div class="map-wrapper">
          <div id="municipal-map"></div>
          <div class="map-vignette"></div>
        </div>

        <div class="floating-overlay-top">
          <div class="legend-group">
            <div class="legend-stat-item">
              <span class="legend-stat-val" id="dot-count">0</span>
              <span class="legend-stat-label">Incidents</span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 2px;">
              <div style="font-size: 0.6rem; color: #a1a1aa; text-transform: uppercase; text-shadow: 0 1px 2px #000;">Severity Filter</div>
              <div class="severity-histogram" id="severity-histogram"></div>
            </div>
          </div>

          <div class="legend-group">
            <div class="toolbar-group">
              <button class="tool-btn active" id="mode-dot">📍 Dot</button>
              <button class="tool-btn" id="mode-zone">🛑 Zone</button>
            </div>

            <div class="severity-picker">
              <label for="severity-slider">Severity:</label>
              <input type="range" id="severity-slider" min="0" max="10" step="1" value="5">
              <span id="severity-val" style="font-weight: 600; color: #fff; min-width: 14px;">5</span>
            </div>

            <button class="tool-btn danger" id="clear-all">Clear</button>
          </div>
        </div>

        <div class="floating-side-panel">
          <div class="panel-header">
            <span id="list-title">All Incidents</span>
            <button id="reset-filter-btn" style="background: none; border: none; color: #a1a1aa; font-size: 0.6rem; cursor: pointer; display: none;">Reset</button>
          </div>
          <div class="incident-list" id="sidebar-incident-list"></div>
        </div>
      </div>
    `;

    setTimeout(() => {
      if (typeof L === 'undefined' || typeof L.markerClusterGroup === 'undefined') {
        const loadScript = (src, cb) => {
          const s = document.createElement('script');
          s.src = src;
          s.onload = cb;
          document.head.appendChild(s);
        };

        if (typeof L === 'undefined') {
          loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', () => {
            loadScript('https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js', () => initMunicipalMap());
          });
        } else {
          loadScript('https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js', () => initMunicipalMap());
        }
      } else {
        initMunicipalMap();
      }
    }, 50);

    return dashboardHtml;
  }
};

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

function initMunicipalMap() {
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

  function addIncidentMarker(lat, lng, label = 'Incident', severityScore = 5, imageUrl = null, description = 'No additional description provided.', isCitizen = false) {
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

    const defaultImg = imageUrl || 'https://images.unsplash.com/photo-1515260268569-9271009adfdb?auto=format&fit=crop&w=400&q=80';
    
    circle.bindPopup(`
      <div style="width: 220px; font-family: inherit;">
        <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 4px; color: #fff;">${label}</div>
        <div style="font-size: 0.7rem; color: #aaa; margin-bottom: 6px;">Severity Score: <b style="color: ${colorHex};">${severityScore} / 10</b></div>
        <img src="${defaultImg}" alt="Incident Photo" style="width: 100%; height: 100px; object-fit: cover; border-radius: 6px; margin-bottom: 6px;" />
        <p style="font-size: 0.7rem; color: #ccc; margin: 0 0 6px 0; line-height: 1.3;">${description}</p>
        <div style="font-size: 0.6rem; color: #777;">GPS: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
      </div>
    `);

    const id = 'dot_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
    const incidentObj = { id, layer: circle, lat, lng, type: 'dot', label, severityScore, description, isCitizen };
    
    activeIncidents.push(incidentObj);

    if (activeScoreFilter === null || Math.round(severityScore) === activeScoreFilter) {
      markersCluster.addLayer(circle);
    }

    updateUI();
    return circle;
  }

  function loadCitizenCases() {
    activeIncidents.filter(i => i.isCitizen).forEach(item => {
      markersCluster.removeLayer(item.layer);
    });
    activeIncidents = activeIncidents.filter(i => !i.isCitizen);

    let cases = listCases() || [];
    
    if (cases.length === 0) {
      const sampleCases = [
        { location: 'Rue de Siam, Brest', coords: { lat: 48.3883, lon: -4.4859 }, severityScore: 9, description: 'Deep pavement crack causing pedestrian tripping hazards.' },
        { location: 'Place de la Liberté, Brest', coords: { lat: 48.3904, lon: -4.4861 }, severityScore: 5, description: 'Faulty streetlight flickering intermittently.' },
        { location: 'Port de Commerce, Brest', coords: { lat: 48.3845, lon: -4.4821 }, severityScore: 2, description: 'Minor roadside graffiti near the commercial dock.' },
        { location: 'Jean Jaurès Avenue, Brest', coords: { lat: 48.3912, lon: -4.4830 }, severityScore: 8, description: 'Damaged and sunken manhole cover.' }
      ];
      sampleCases.forEach(sc => addCase(sc));
      cases = listCases() || [];
    }

    cases.forEach(c => {
      const lat = parseFloat(c.coords?.lat);
      const lng = parseFloat(c.coords?.lon);
      const score = typeof c.severityScore === 'number' ? c.severityScore : 5;
      const desc = c.description || 'Citizen reported degradation requiring inspection.';
      const img = c.imageUrl || null;
      
      if (!isNaN(lat) && !isNaN(lng)) {
        addIncidentMarker(lat, lng, `Citizen: ${c.location || 'Report'}`, score, img, desc, true);
      }
    });

    updateUI();
  }

  loadCitizenCases();

  map.whenReady(() => {
    map.invalidateSize(true);
    setTimeout(() => map.invalidateSize(true), 150);
  });

  window.addEventListener('storage', () => {
    loadCitizenCases();
    map.invalidateSize(true);
  });

  map.on('click', (e) => {
    const { lat, lng } = e.latlng;

    if (currentMode === 'dot') {
      addIncidentMarker(lat, lng, 'Manual Inspection', currentSeverity, null, 'Manually placed observation.', false);
    } else if (currentMode === 'zone') {
      zonePoints.push([lat, lng]);
      
      if (tempPolyline) map.removeLayer(tempPolyline);
      tempPolyline = L.polyline(zonePoints, { color: '#ef4444', dashArray: '4, 4' }).addTo(map);

      if (zonePoints.length >= 3 && confirm('Create alert zone with these points?')) {
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
}