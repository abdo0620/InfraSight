import { pageHeader } from '../../../shared/ui/pageHeader.js';
import { listCases, addCase } from '../../../services/storage/caseStore.js';

export default {
  id: 'dashboard',
  title: 'Dashboard',
  render: () => {
    // 1. Page Header
    const headerHtml = pageHeader('Dashboard', 'Municipal mode');

    // 2. Municipal Dashboard Layout
    const dashboardHtml = `
      ${headerHtml}
      
      <style>
        :root[data-mode="municipal"], .municipal-theme {
          --bg: #0f0f0f;
          --surface: #181818;
          --text: #f2f2f2;
          --muted: #888;
          --line: #2a2a2a;
          --accent: #f2f2f2;
          color-scheme: dark;
        }

        .dashboard-container {
          background-color: var(--bg, #0f0f0f);
          color: var(--text, #f2f2f2);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          padding: 1.5rem;
          min-height: calc(100vh - 80px);
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        /* Map Container Block */
        .map-wrapper {
          position: relative;
          background: #0f0f0f;
          border-radius: 16px;
          overflow: hidden;
          width: 100%;
          height: 580px;
          display: block;
          border: none;
        }

        /* OPTIMIZED FILTER: Makes all small residential streets and minor lanes brightly visible */
        .leaflet-tile-pane {
          filter: 
            invert(100%) 
            hue-rotate(180deg) 
            grayscale(100%) 
            brightness(1.4) 
            contrast(1.8);
        }

        /* Seamless Edge Blending to erase rectangular borders into #0f0f0f */
        .map-vignette {
          position: absolute;
          inset: 0;
          pointer-events: none;
          z-index: 400;
          box-shadow: 
            inset 0 0 60px 30px #0f0f0f,
            inset 0 0 110px 70px #0f0f0f;
        }

        #municipal-map {
          width: 100%;
          height: 100%;
          background: #0f0f0f;
        }

        /* Controls Section Below Map */
        .controls-section {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
        }

        .panel-card {
          background: var(--surface, #181818);
          border: 1px solid var(--line, #2a2a2a);
          border-radius: 12px;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .panel-title {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--muted, #888);
          margin: 0;
          font-weight: 600;
        }

        .stat-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.75rem;
        }

        .stat-box {
          background: #121212;
          border: 1px solid var(--line, #2a2a2a);
          border-radius: 8px;
          padding: 0.75rem;
        }

        .stat-val {
          font-size: 1.5rem;
          font-weight: 700;
          color: #ff4d4d;
        }

        .stat-label {
          font-size: 0.75rem;
          color: var(--muted, #888);
        }

        .btn-group {
          display: flex;
          gap: 0.5rem;
        }

        .btn-muni {
          flex: 1;
          padding: 0.6rem;
          background: #222;
          border: 1px solid var(--line, #2a2a2a);
          color: var(--text, #f2f2f2);
          border-radius: 6px;
          font-size: 0.8rem;
          cursor: pointer;
          transition: all 0.2s ease;
          font-weight: 500;
        }

        .btn-muni:hover, .btn-muni.active {
          background: var(--accent, #f2f2f2);
          color: #000;
        }

        .btn-muni.danger {
          border-color: #ff4d4d;
          color: #ff4d4d;
        }

        .btn-muni.danger:hover {
          background: #ff4d4d;
          color: #fff;
        }

        .marker-list {
          max-height: 160px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .marker-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0.75rem;
          background: #121212;
          border-radius: 6px;
          font-size: 0.8rem;
          border: 1px solid var(--line, #2a2a2a);
          cursor: pointer;
          transition: background 0.2s;
        }

        .marker-item:hover {
          background: #222;
        }

        .marker-item span {
          flex: 1;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .marker-item button {
          background: transparent;
          border: none;
          color: #ff4d4d;
          cursor: pointer;
          font-size: 1rem;
          font-weight: bold;
          padding: 0 0 0 10px;
        }
      </style>

      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

      <div class="dashboard-container municipal-theme" data-mode="municipal">
        <!-- 1. Map Block -->
        <div class="map-wrapper">
          <div id="municipal-map"></div>
          <div class="map-vignette"></div>
        </div>

        <!-- 2. Controls Section -->
        <div class="controls-section">
          <div class="panel-card">
            <h3 class="panel-title">Municipal Overview</h3>
            <div class="stat-grid">
              <div class="stat-box">
                <div class="stat-val" id="dot-count">0</div>
                <div class="stat-label">Red Incidents</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" id="zone-count">0</div>
                <div class="stat-label">Red Alert Zones</div>
              </div>
            </div>

            <h3 class="panel-title">Placement Mode</h3>
            <div class="btn-group">
              <button class="btn-muni active" id="mode-dot">🔴 Red Dot</button>
              <button class="btn-muni" id="mode-zone">🛑 Red Zone</button>
            </div>
            
            <div>
              <label style="font-size: 0.75rem; color: var(--muted, #888);">Dot Radius (px)</label>
              <input type="range" id="dot-size" min="6" max="24" value="10" style="width: 100%; margin-top: 0.3rem;">
            </div>

            <div class="btn-group">
              <button class="btn-muni danger" id="clear-all">Clear All Layers</button>
            </div>
          </div>

          <div class="panel-card">
            <h3 class="panel-title">Active Markers & Zones (Click to Zoom)</h3>
            <div class="marker-list" id="active-list">
              <div style="font-size: 0.8rem; color: var(--muted, #888);">No markers placed yet. Click on the map above to add dots.</div>
            </div>
          </div>
        </div>
      </div>
    `;

    // 3. Initialize Leaflet Map
    setTimeout(() => {
      if (typeof L === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => initMunicipalMap();
        document.head.appendChild(script);
      } else {
        initMunicipalMap();
      }
    }, 50);

    return dashboardHtml;
  }
};

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

  // Pane au premier plan absolu (z-index 9999)
  map.createPane('redDotsPane');
  map.getPane('redDotsPane').style.zIndex = 9999;

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 10,
    subdomains: ['a', 'b', 'c'],
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  let currentMode = 'dot';
  let dotRadius = 10;
  let activeIncidents = [];
  let zonePoints = [];
  let activePolygons = [];
  let tempPolyline = null;

  const dotBtn = document.getElementById('mode-dot');
  const zoneBtn = document.getElementById('mode-zone');
  const dotSizeInput = document.getElementById('dot-size');
  const clearBtn = document.getElementById('clear-all');
  const dotCountEl = document.getElementById('dot-count');
  const zoneCountEl = document.getElementById('zone-count');
  const activeListEl = document.getElementById('active-list');

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

  dotSizeInput.addEventListener('input', (e) => {
    dotRadius = parseInt(e.target.value, 10);
  });

  function addRedDot(lat, lng, label = 'Red Incident Dot', isCitizen = false) {
    const circle = L.circleMarker([lat, lng], {
      pane: 'redDotsPane',
      color: '#ff4d4d',
      fillColor: '#ff0000',
      fillOpacity: 0.95,
      radius: dotRadius,
      weight: 2
    }).addTo(map);

    const id = 'dot_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
    activeIncidents.push({ id, layer: circle, lat, lng, type: 'dot', label, isCitizen });
    
    circle.bindPopup(`<b style="color:#000;">${label}</b><br>Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`);
    updateUI();
    return circle;
  }

  function loadCitizenCases() {
    activeIncidents.filter(i => i.isCitizen).forEach(item => {
      if (item.layer) map.removeLayer(item.layer);
    });
    activeIncidents = activeIncidents.filter(i => !i.isCitizen);

    let cases = listCases() || [];
    
    if (cases.length === 0) {
      const sampleCases = [
        { location: 'Rue de Siam, Brest', coords: { lat: 48.3883, lon: -4.4859 } },
        { location: 'Place de la Liberté, Brest', coords: { lat: 48.3904, lon: -4.4861 } },
        { location: 'Port de Commerce, Brest', coords: { lat: 48.3845, lon: -4.4821 } }
      ];
      sampleCases.forEach(sc => addCase(sc));
      cases = listCases() || [];
    }

    cases.forEach(c => {
      const lat = parseFloat(c.coords?.lat);
      const lng = parseFloat(c.coords?.lon);
      
      if (!isNaN(lat) && !isNaN(lng)) {
        addRedDot(lat, lng, `Citoyen: ${c.location || 'Signalement'}`, true);
      }
    });

    updateUI();
  }

  loadCitizenCases();

  map.whenReady(() => {
    map.invalidateSize(true);
    setTimeout(() => map.invalidateSize(true), 150);
    setTimeout(() => map.invalidateSize(true), 400);
  });

  window.addEventListener('storage', () => {
    loadCitizenCases();
    map.invalidateSize(true);
  });

  map.on('click', (e) => {
    const { lat, lng } = e.latlng;

    if (currentMode === 'dot') {
      addRedDot(lat, lng, 'Manual Incident Dot', false);
    } else if (currentMode === 'zone') {
      zonePoints.push([lat, lng]);
      
      if (tempPolyline) map.removeLayer(tempPolyline);
      tempPolyline = L.polyline(zonePoints, { color: '#ff4d4d', dashArray: '4, 4' }).addTo(map);

      if (zonePoints.length >= 3 && confirm('Create Red Alert Zone with these points?')) {
        const polygon = L.polygon(zonePoints, {
          pane: 'redDotsPane',
          color: '#ff4d4d',
          fillColor: '#ff0000',
          fillOpacity: 0.35,
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
    zoneCountEl.textContent = activePolygons.length;

    const allItems = [...activeIncidents, ...activePolygons];

    if (allItems.length === 0) {
      activeListEl.innerHTML = `<div style="font-size: 0.8rem; color: var(--muted, #888);">No markers placed yet. Click on the map above to add dots.</div>`;
      return;
    }

    activeListEl.innerHTML = allItems.map((item, index) => `
      <div class="marker-item" onclick="zoomToMarker('${item.id}', '${item.type}')">
        <span>${item.type === 'dot' ? `🔴 ${item.label || 'Red Incident'}` : '🛑 Red Alert Zone'} #${index + 1}</span>
        <button onclick="event.stopPropagation(); removeMarker('${item.id}', '${item.type}')" title="Supprimer">&times;</button>
      </div>
    `).join('');
  }

  // Fonction pour zoomer sur un point depuis la légende
  window.zoomToMarker = function(id, type) {
    if (type === 'dot') {
      const found = activeIncidents.find(i => i.id === id);
      if (found && found.layer) {
        map.setView([found.lat, found.lng], 16, { animate: true });
        found.layer.openPopup();
      }
    } else {
      const found = activePolygons.find(i => i.id === id);
      if (found && found.layer) {
        map.fitBounds(found.layer.getBounds(), { animate: true });
      }
    }
  };

  window.removeMarker = function(id, type) {
    if (type === 'dot') {
      const idx = activeIncidents.findIndex(item => item.id === id);
      if (idx !== -1) {
        map.removeLayer(activeIncidents[idx].layer);
        activeIncidents.splice(idx, 1);
      }
    } else {
      const idx = activePolygons.findIndex(item => item.id === id);
      if (idx !== -1) {
        map.removeLayer(activePolygons[idx].layer);
        activePolygons.splice(idx, 1);
      }
    }
    updateUI();
  };

  clearBtn.addEventListener('click', () => {
    activeIncidents.forEach(item => map.removeLayer(item.layer));
    activePolygons.forEach(item => map.removeLayer(item.layer));
    activeIncidents = [];
    activePolygons = [];
    zonePoints = [];
    if (tempPolyline) map.removeLayer(tempPolyline);
    updateUI();
  });
}