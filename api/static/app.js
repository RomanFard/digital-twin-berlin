const API_BASE = window.location.origin;

// ============================================
// Kreuzberg Study Area
// ============================================
const KREUZBERG_CENTER = [52.4955, 13.4100];
const KREUZBERG_ZOOM = 13;
const KREUZBERG_BBOX = {
    min_lon: 13.38,
    max_lon: 13.47,
    min_lat: 52.48,
    max_lat: 52.52
};

let map = null;
let layers = {};
let allFeatures = [];
let featureTypes = [];
let currentMarker = null;
let kreuzbergLayer = null;

// Zones
let zones = [];
let activeZoneId = null;
let drawnItems = null;
let isDrawingMode = false;
let currentPolygon = null;
let drawingHintElement = null;
let drawStart = null;
let drawTemp = null;

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    checkHealth();
    loadLayers();
    loadStats();
    bindUI();
});

function initMap() {
    map = L.map('map').setView(KREUZBERG_CENTER, KREUZBERG_ZOOM);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'OpenStreetMap',
        maxZoom: 19
    }).addTo(map);

    addKreuzbergBoundary();
}

// ============================================
// Kreuzberg Boundary
// ============================================
async function addKreuzbergBoundary() {
    try {
        const response = await fetch('/static/berlin_bezirke.geojson');
        const data = await response.json();

        const kreuzbergFeature = data.features.find(f => {
            const name = f.properties.name || '';
            return name.includes('Kreuzberg');
        });

        if (!kreuzbergFeature) {
            console.warn('Kreuzberg boundary not found');
            return;
        }

        kreuzbergLayer = L.geoJSON(kreuzbergFeature, {
            style: {
                color: '#ff7800',
                weight: 3,
                opacity: 0.9,
                fillColor: '#ff7800',
                fillOpacity: 0.05,
                dashArray: '8, 4'
            }
        }).addTo(map);

        kreuzbergLayer.bindPopup(
            '<div style="font-family:sans-serif;min-width:180px">' +
            '<strong style="color:#ff7800;font-size:14px">Friedrichshain-Kreuzberg</strong><br>' +
            '<small>Berlin, Bezirk</small>' +
            '</div>'
        );

        map.fitBounds(kreuzbergLayer.getBounds(), { padding: [30, 30] });

        loadFeaturesInStudyArea();
    } catch (e) {
        console.error('Failed to load Kreuzberg boundary:', e);
    }
}

// ============================================
// API Calls
// ============================================
async function checkHealth() {
    try {
        const res = await fetch(API_BASE + '/health');
        const data = await res.json();
        updateStatus(true, data.trees_count);
    } catch (e) {
        updateStatus(false);
    }
}

async function loadLayers() {
    try {
        const res = await fetch(API_BASE + '/api/layers');
        featureTypes = await res.json();
        renderLayers();
    } catch (e) {
        console.error('Failed to load layers', e);
    }
}

async function loadStats() {
    try {
        const res = await fetch(API_BASE + '/api/stats');
        const stats = await res.json();
        renderStats(stats);
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

async function loadBezirke() {
    try {
        const res = await fetch(API_BASE + '/api/stats/bezirk');
        const data = await res.json();
        const select = document.getElementById('filter-bezirk');
        data.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.bezirk;
            opt.textContent = item.bezirk + ' (' + item.count + ')';
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Failed to load bezirke', e);
    }
}

async function loadFeaturesInStudyArea() {
    // چک کن Zone فعال داری
    try {
        const res = await fetch(API_BASE + '/api/zones/active/scene');
        const data = await res.json();

        if (data.zone && data.features && data.features.length > 0) {
            console.log(`✅ Loading from active zone: ${data.zone.name} (${data.total_count} trees)`);
            allFeatures = data.features;
            renderFeatures(data.features);
            renderMap(data.features);
            return;
        }

        console.log('ℹ️ No active zone, loading Kreuzberg polygon');
    } catch (e) {
        console.error('Failed to check active zone:', e);
    }

    // Zone فعال نداریم → همه درختان داخل پلیگون Kreuzberg
    try {
        if (!kreuzbergLayer) {
            console.warn('Kreuzberg layer not loaded');
            return;
        }

        let kreuzbergGeometry = null;
        kreuzbergLayer.eachLayer(layer => {
            if (layer.feature && layer.feature.geometry) {
                kreuzbergGeometry = layer.feature.geometry;
            }
        });

        if (!kreuzbergGeometry) {
            console.warn('Kreuzberg geometry not found');
            return;
        }

        const res = await fetch(API_BASE + '/api/features/in-polygon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                polygon: kreuzbergGeometry,
                limit: 5000,
                offset: 0
            })
        });

        if (!res.ok) throw new Error('API error: ' + res.status);

        const features = await res.json();
        console.log(`✅ Loaded ${features.length} Kreuzberg features`);
        allFeatures = features;
        renderFeatures(features);
        renderMap(features);
    } catch (e) {
        console.error('Failed to load study area features', e);
    }
}

async function loadFeatures(filters) {
    filters = filters || {};
    const params = new URLSearchParams();
    params.set('limit', Math.min(filters.limit || 500, 1000));
    if (filters.types) params.set('types', filters.types);
    if (filters.strname) params.set('strname', filters.strname);
    if (filters.bbox) {
        params.set('min_lon', filters.bbox[0]);
        params.set('min_lat', filters.bbox[1]);
        params.set('max_lon', filters.bbox[2]);
        params.set('max_lat', filters.bbox[3]);
    }

    try {
        const res = await fetch(API_BASE + '/api/features?' + params);
        const features = await res.json();
        allFeatures = features;
        renderFeatures(features);
        renderMap(features);
    } catch (e) {
        console.error('Failed to load features', e);
    }
}

async function loadFeaturesInPolygonWithLimit(polygonGeometry, limit) {
    try {
        const response = await fetch(API_BASE + '/api/features/in-polygon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                polygon: polygonGeometry,
                limit: limit,
                offset: 0
            })
        });

        if (!response.ok) throw new Error('API error: ' + response.status);

        const features = await response.json();
        allFeatures = features;
        renderFeatures(features);
        renderMap(features);

        console.log('Loaded ' + features.length + ' features in polygon');
    } catch (e) {
        console.error('Failed to load features in polygon:', e);
    }
}

// ============================================
// Status
// ============================================
function updateStatus(online, count) {
    const el = document.getElementById('api-status');
    if (online) {
        el.textContent = '🟢 Online' + (count ? ' • ' + count.toLocaleString() + ' trees' : '');
        el.className = 'status-badge online';
    } else {
        el.textContent = '🔴 Offline';
        el.className = 'status-badge offline';
    }
}

// ============================================
// Rendering
// ============================================
function renderLayers() {
    const container = document.getElementById('layers-list');
    container.innerHTML = '';

    featureTypes.forEach(type => {
        const item = document.createElement('div');
        item.className = 'layer-item';
        item.innerHTML =
            '<input type="checkbox" id="layer-' + type.code + '" checked />' +
            '<div class="layer-icon" style="background:' + type.color + '"></div>' +
            '<div class="layer-name">' + type.name_en + '</div>' +
            '<div class="layer-count" id="count-' + type.code + '">0</div>';
        container.appendChild(item);

        const checkbox = item.querySelector('input');
        checkbox.addEventListener('change', (e) => {
            toggleLayer(type.code, e.target.checked);
        });
    });
}

function renderStats(stats) {
    const container = document.getElementById('stats-list');
    container.innerHTML = '';

    stats.forEach(s => {
        const item = document.createElement('div');
        item.className = 'stat-item';
        item.innerHTML =
            '<span>' + s.type_code + '</span>' +
            '<span class="stat-count">' + s.active.toLocaleString() + '</span>';
        container.appendChild(item);
    });
}

function renderFeatures(features) {
    const tbody = document.getElementById('features-tbody');
    tbody.innerHTML = '';

    if (features.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No features found</td></tr>';
        document.getElementById('table-count').textContent = '0 rows';
        return;
    }

    features.forEach(f => {
        const attrs = f.attributes || {};
        const tr = document.createElement('tr');
        tr.innerHTML =
            '<td>' + f.feature_id + '</td>' +
            '<td><span style="color:' + f.color + '">●</span> ' + f.type_code + '</td>' +
            '<td>' + f.lon.toFixed(6) + '</td>' +
            '<td>' + f.lat.toFixed(6) + '</td>' +
            '<td>' + (attrs.bezirk || '-') + '</td>' +
            '<td>' + (attrs.art_dtsch || '-') + '</td>' +
            '<td>' + (attrs.stammumfg || '-') + '</td>' +
            '<td>' + (attrs.pflanzjahr || '-') + '</td>';
        tr.addEventListener('click', () => {
            map.setView([f.lat, f.lon], 18);
            openDetailPanel(f);
        });
        tbody.appendChild(tr);
    });

    document.getElementById('table-count').textContent = features.length + ' rows';
}

function renderMap(features) {
    Object.values(layers).forEach(layer => map.removeLayer(layer));
    layers = {};

    const grouped = {};
    features.forEach(f => {
        if (!grouped[f.type_code]) grouped[f.type_code] = [];
        grouped[f.type_code].push(f);
    });

    Object.keys(grouped).forEach(typeCode => {
        const type = featureTypes.find(t => t.code === typeCode);
        const items = grouped[typeCode];

        const layer = L.layerGroup();
        items.forEach(f => {
            const marker = L.circleMarker([f.lat, f.lon], {
                radius: 5,
                fillColor: type ? type.color : '#888',
                color: '#fff',
                weight: 1.5,
                fillOpacity: 0.9
            });

            marker.on('click', () => {
                openDetailPanel(f);
                if (currentMarker) {
                    currentMarker.setStyle({ weight: 1.5, color: '#fff' });
                }
                marker.setStyle({ weight: 3, color: '#ffcc00' });
                currentMarker = marker;
            });

            const attrs = f.attributes || {};
            marker.bindTooltip(attrs.art_dtsch || f.feature_id, {
                direction: 'top',
                offset: [0, -5]
            });

            layer.addLayer(marker);
        });

        layer.addTo(map);
        layers[typeCode] = layer;

        const countEl = document.getElementById('count-' + typeCode);
        if (countEl) countEl.textContent = items.length.toLocaleString();
    });

    document.getElementById('visible-count').textContent = features.length + ' features visible';
}

function toggleLayer(typeCode, visible) {
    if (!layers[typeCode]) return;
    if (visible) {
        layers[typeCode].addTo(map);
    } else {
        map.removeLayer(layers[typeCode]);
    }
}

// ============================================
// Detail Panel
// ============================================
function openDetailPanel(feature) {
    const panel = document.getElementById('detail-panel');
    const title = document.getElementById('detail-title');
    const body = document.getElementById('detail-body');
    const type = featureTypes.find(t => t.code === feature.type_code);

    title.textContent = type ? type.name_en + ' Details' : 'Feature Details';

    const attrs = feature.attributes || {};
    const typeColor = type ? type.color : '#888';

    const mainTitle = attrs.art_dtsch || attrs.name || feature.feature_id;
    const subTitle = attrs.art_bot || '';

    let age = '-';
    if (attrs.pflanzjahr) {
        const year = parseInt(attrs.pflanzjahr);
        if (!isNaN(year)) age = (2026 - year) + ' years';
    }

    let diameter = '-';
    if (attrs.stammumfg) {
        diameter = (attrs.stammumfg / Math.PI).toFixed(1) + ' cm';
    }

    let html = '';

    html += '<div class="detail-title-main">';
    html += '<span class="detail-icon-badge" style="background:' + typeColor + '">';
    html += (type ? type.code.charAt(0).toUpperCase() : '?');
    html += '</span>';
    html += '<span>' + mainTitle + '</span>';
    html += '</div>';

    if (subTitle) {
        html += '<div class="detail-title-sub">' + subTitle + '</div>';
    }

    html += '<div class="detail-section">';
    html += '<div class="detail-section-title">📍 Location</div>';
    html += '<div class="detail-row"><span class="detail-label">Longitude</span><span class="detail-value">' + feature.lon.toFixed(6) + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">Latitude</span><span class="detail-value">' + feature.lat.toFixed(6) + '</span></div>';
    if (attrs.bezirk) {
        html += '<div class="detail-row"><span class="detail-label">Bezirk</span><span class="detail-value">' + attrs.bezirk + '</span></div>';
    }
    html += '</div>';

    html += '<div class="detail-section">';
    html += '<div class="detail-section-title">🌳 Tree Info</div>';
    if (attrs.art_dtsch) {
        html += '<div class="detail-row"><span class="detail-label">German Name</span><span class="detail-value">' + attrs.art_dtsch + '</span></div>';
    }
    if (attrs.art_bot) {
        html += '<div class="detail-row"><span class="detail-label">Scientific Name</span><span class="detail-value">' + attrs.art_bot + '</span></div>';
    }
    if (attrs.gattung) {
        html += '<div class="detail-row"><span class="detail-label">Genus</span><span class="detail-value">' + attrs.gattung + '</span></div>';
    }
    if (attrs.art_gruppe) {
        html += '<div class="detail-row"><span class="detail-label">Group</span><span class="detail-value">' + attrs.art_gruppe + '</span></div>';
    }
    html += '</div>';

    html += '<div class="detail-section">';
    html += '<div class="detail-section-title">📏 Dimensions</div>';
    if (attrs.stammumfg) {
        html += '<div class="detail-row"><span class="detail-label">Trunk Circumference</span><span class="detail-value">' + attrs.stammumfg + ' cm</span></div>';
        html += '<div class="detail-row"><span class="detail-label">Trunk Diameter</span><span class="detail-value">' + diameter + '</span></div>';
    }
    if (attrs.baumhoehe) {
        html += '<div class="detail-row"><span class="detail-label">Height</span><span class="detail-value">' + attrs.baumhoehe + ' m</span></div>';
    }
    if (attrs.kronedurch) {
        html += '<div class="detail-row"><span class="detail-label">Crown Diameter</span><span class="detail-value">' + attrs.kronedurch + ' m</span></div>';
    }
    if (attrs.standalter) {
        html += '<div class="detail-row"><span class="detail-label">Estimated Age</span><span class="detail-value">' + attrs.standalter + ' years</span></div>';
    }
    html += '</div>';

    html += '<div class="detail-section">';
    html += '<div class="detail-section-title">📅 Dates</div>';
    if (attrs.pflanzjahr) {
        html += '<div class="detail-row"><span class="detail-label">Planting Year</span><span class="detail-value">' + attrs.pflanzjahr + '</span></div>';
        html += '<div class="detail-row"><span class="detail-label">Calculated Age</span><span class="detail-value">' + age + '</span></div>';
    }
    if (feature.last_updated) {
        html += '<div class="detail-row"><span class="detail-label">Last Updated</span><span class="detail-value">' + new Date(feature.last_updated).toLocaleDateString('en-US') + '</span></div>';
    }
    html += '</div>';

    if (attrs.eigentuemer) {
        html += '<div class="detail-section">';
        html += '<div class="detail-section-title">👤 Ownership</div>';
        html += '<div class="detail-row"><span class="detail-label">Owner</span><span class="detail-value">' + attrs.eigentuemer + '</span></div>';
        html += '</div>';
    }

    html += '<div class="detail-section">';
    html += '<div class="detail-section-title">🆔 Identifier</div>';
    html += '<span class="feature-id-badge">' + feature.feature_id + '</span>';
    html += '</div>';

    body.innerHTML = html;
    panel.classList.add('open');
}

function closeDetailPanel() {
    const panel = document.getElementById('detail-panel');
    panel.classList.remove('open');
    if (currentMarker) {
        currentMarker.setStyle({ weight: 1.5, color: '#fff' });
        currentMarker = null;
    }
}

// ============================================
// UI Events
// ============================================
function bindUI() {
    document.getElementById('btn-refresh').addEventListener('click', () => {
        checkHealth();
        loadStats();
        loadFeaturesInStudyArea();
    });

    document.getElementById('btn-dark').addEventListener('click', () => {
        document.body.classList.toggle('dark');
    });

    document.getElementById('btn-apply-filters').addEventListener('click', () => {
        const limit = Math.min(parseInt(document.getElementById('filter-limit').value) || 500, 50000);
        const strname = document.getElementById('filter-strname').value;

        if (kreuzbergLayer && kreuzbergLayer.getLayers().length > 0) {
            const feature = kreuzbergLayer.getLayers()[0].feature;
            if (strname) {
                loadFeatures({
                    limit: limit,
                    strname: strname,
                    bbox: [
                        KREUZBERG_BBOX.min_lon,
                        KREUZBERG_BBOX.min_lat,
                        KREUZBERG_BBOX.max_lon,
                        KREUZBERG_BBOX.max_lat
                    ]
                });
            } else {
                loadFeaturesInPolygonWithLimit(feature.geometry, limit);
            }
        } else {
            loadFeatures({
                limit: limit,
                strname: strname,
                bbox: [
                    KREUZBERG_BBOX.min_lon,
                    KREUZBERG_BBOX.min_lat,
                    KREUZBERG_BBOX.max_lon,
                    KREUZBERG_BBOX.max_lat
                ]
            });
        }
    });

    document.getElementById('btn-reset-filters').addEventListener('click', () => {
        document.getElementById('filter-bezirk').value = '';
        document.getElementById('filter-art').value = '';
        document.getElementById('filter-limit').value = 500;
        loadFeaturesInStudyArea();
    });

    document.getElementById('detail-close').addEventListener('click', closeDetailPanel);
}

// ============================================
// Zones Management
// ============================================
function initZonesLayer() {
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
}

async function loadZones() {
    try {
        const res = await fetch(API_BASE + '/api/zones');
        zones = await res.json();
        renderZones();
        drawZonesOnMap();
    } catch (e) {
        console.error('Failed to load zones', e);
    }
}

function renderZones() {
    const container = document.getElementById('zones-list');
    container.innerHTML = '';

    if (zones.length === 0) {
        container.innerHTML = '<div class="loading">No zones yet</div>';
        return;
    }

    zones.forEach(zone => {
        const isActive = zone.is_active;
        if (isActive) activeZoneId = zone.zone_id;

        const item = document.createElement('div');
        item.className = 'zone-item' + (isActive ? ' active' : '');
        item.innerHTML = `
            <div class="zone-item-header">
                <span class="zone-name">${zone.name}</span>
                ${isActive ? '<span class="zone-badge">ACTIVE</span>' : ''}
            </div>
            <div class="zone-meta">
                <span>${zone.description || ''}</span>
            </div>
            <div class="zone-actions">
                <button class="btn-zone-activate" 
                        onclick="activateZone('${zone.zone_id}')"
                        ${isActive ? 'disabled' : ''}>
                    ${isActive ? '✓ Active' : 'Set Active'}
                </button>
                <button class="btn-zone-delete" onclick="deleteZone('${zone.zone_id}')">
                    Delete
                </button>
            </div>
        `;
        container.appendChild(item);
    });
}

function drawZonesOnMap() {
    if (!drawnItems) return;
    drawnItems.clearLayers();

    zones.forEach(zone => {
        if (!zone.polygon) return;

        const isActive = zone.is_active;
        const layer = L.geoJSON(zone.polygon, {
            style: {
                color: isActive ? '#2ecc71' : '#3498db',
                weight: isActive ? 3 : 2,
                opacity: 0.8,
                fillColor: isActive ? '#2ecc71' : '#3498db',
                fillOpacity: isActive ? 0.15 : 0.05,
                dashArray: isActive ? null : '5, 5'
            }
        });

        layer.bindPopup(`<strong>${zone.name}</strong>`);
        layer.on('click', () => {
            if (!isActive) {
                activateZone(zone.zone_id);
            }
        });

        drawnItems.addLayer(layer);
    });
}

async function activateZone(zoneId) {
    try {
        const res = await fetch(`${API_BASE}/api/zones/${zoneId}/activate`, {
            method: 'PUT'
        });

        if (!res.ok) throw new Error('Failed to activate');

        await loadZones();
        await loadFeaturesInStudyArea();

        console.log('Zone activated:', zoneId);
    } catch (e) {
        console.error('Failed to activate zone', e);
        alert('Failed to activate zone');
    }
}

async function deleteZone(zoneId) {
    if (!confirm('Delete this zone?')) return;

    try {
        const res = await fetch(`${API_BASE}/api/zones/${zoneId}`, {
            method: 'DELETE'
        });

        if (!res.ok) throw new Error('Failed to delete');

        await loadZones();
        await loadFeaturesInStudyArea();
    } catch (e) {
        console.error('Failed to delete zone', e);
        alert('Failed to delete zone');
    }
}

function startDrawingMode() {
    isDrawingMode = true;
    document.body.classList.add('drawing-mode');
    document.getElementById('btn-draw-zone').style.display = 'none';
    document.getElementById('btn-cancel-draw').style.display = 'block';

    drawingHintElement = document.createElement('div');
    drawingHintElement.className = 'drawing-hint';
    drawingHintElement.textContent = '🖱️ کلیک کن و بکش تا محدوده رو رسم کنی';
    map.dragging.disable();
    document.querySelector('.map-container').appendChild(drawingHintElement);

    map.on('mousedown', onMouseDown);
    map.on('mousemove', onMouseMove);
    map.on('mouseup', onMouseUp);
}

function cancelDrawingMode() {
    isDrawingMode = false;
    document.body.classList.remove('drawing-mode');
    map.dragging.enable();
    document.getElementById('btn-draw-zone').style.display = 'block';
    document.getElementById('btn-cancel-draw').style.display = 'none';

    if (drawingHintElement) {
        drawingHintElement.remove();
        drawingHintElement = null;
    }

    if (currentPolygon) {
        currentPolygon.remove();
        currentPolygon = null;
    }

    map.off('mousedown', onMouseDown);
    map.off('mousemove', onMouseMove);
    map.off('mouseup', onMouseUp);
}

function onMouseDown(e) {
    if (!isDrawingMode) return;
    drawStart = e.latlng;
}

function onMouseMove(e) {
    if (!isDrawingMode || !drawStart) return;

    if (drawTemp) map.removeLayer(drawTemp);

    const bounds = L.latLngBounds(drawStart, e.latlng);
    drawTemp = L.rectangle(bounds, {
        color: '#3498db',
        weight: 2,
        fillOpacity: 0.2
    }).addTo(map);
}

function onMouseUp(e) {
    if (!isDrawingMode || !drawStart) return;

    const bounds = L.latLngBounds(drawStart, e.latlng);
    if (drawTemp) map.removeLayer(drawTemp);
    drawTemp = null;

    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    let drawnPolygon = {
        type: "Feature",
        properties: {},
        geometry: {
            type: "Polygon",
            coordinates: [[
                [sw.lng, sw.lat],
                [ne.lng, sw.lat],
                [ne.lng, ne.lat],
                [sw.lng, ne.lat],
                [sw.lng, sw.lat]
            ]]
        }
    };

    drawStart = null;

    // برش با Kreuzberg
    let finalPolygon = drawnPolygon.geometry;

    if (kreuzbergLayer) {
        try {
            let kreuzbergGeometry = null;
            kreuzbergLayer.eachLayer(layer => {
                if (layer.feature && layer.feature.geometry) {
                    kreuzbergGeometry = layer.feature.geometry;
                }
            });

            if (kreuzbergGeometry) {
                let kreuzbergFC;
                if (kreuzbergGeometry.type === 'MultiPolygon') {
                    kreuzbergFC = turf.featureCollection(
                        kreuzbergGeometry.coordinates.map(coords => turf.polygon(coords))
                    );
                } else {
                    kreuzbergFC = turf.featureCollection([turf.polygon(kreuzbergGeometry.coordinates)]);
                }

                const drawnFeature = turf.feature(drawnPolygon.geometry);

                let clipped = null;
                kreuzbergFC.features.forEach(poly => {
                    if (clipped) return;
                    const result = turf.intersect(turf.featureCollection([poly, drawnFeature]));
                    if (result && result.geometry) {
                        clipped = result;
                    }
                });

                if (clipped && clipped.geometry) {
                    console.log('✅ Polygon clipped to Kreuzberg');
                    finalPolygon = clipped.geometry;
                } else {
                    alert('⚠️ کادرت کاملاً بیرون Kreuzberg بود. لطفاً یه کادر داخل خط‌چین نارنجی بکش.');
                    cancelDrawingMode();
                    return;
                }
            }
        } catch (err) {
            console.warn('Clip failed, using original polygon:', err);
        }
    }

    if (currentPolygon) currentPolygon.remove();
    currentPolygon = L.geoJSON(finalPolygon, {
        color: '#3498db',
        weight: 3,
        fillOpacity: 0.1,
        dashArray: '5, 5'
    }).addTo(map);

    setTimeout(() => {
        const name = prompt('نام Zone:');
        if (!name) {
            cancelDrawingMode();
            return;
        }

        const description = prompt('توضیحات (اختیاری):') || '';

        saveZone(name, description, finalPolygon);
    }, 100);
}

async function saveZone(name, description, polygon) {
    try {
        const res = await fetch(API_BASE + '/api/zones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                description: description,
                polygon: polygon,
                filters: {},
                rules: {}
            })
        });

        if (!res.ok) throw new Error('Failed to save');

        alert('✅ Zone saved!');
        cancelDrawingMode();
        await loadZones();
    } catch (e) {
        console.error('Failed to save zone', e);
        alert('Failed to save zone');
    }
}

function initZonesUI() {
    document.getElementById('btn-draw-zone').addEventListener('click', startDrawingMode);
    document.getElementById('btn-cancel-draw').addEventListener('click', cancelDrawingMode);
}

// ============================================
// Run
// ============================================
setTimeout(loadBezirke, 2000);
setTimeout(() => {
    console.log('🚀 Initializing Zones...');
    initZonesLayer();
    initZonesUI();
    loadZones();
}, 3000);