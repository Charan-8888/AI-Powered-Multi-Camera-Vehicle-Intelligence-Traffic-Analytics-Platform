import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet';

/**
 * CityMap — Leaflet map showing all registered cameras as markers.
 *
 * Props:
 *   cameras  Array<{ id, name, location, latitude, longitude,
 *                    status, traffic_level, detection_count }>
 *
 * Uses real lat/lng from the DB when available.
 * Falls back to deterministic demo coordinates for Hyderabad if null.
 */

// Hyderabad-area fallback demo coordinates per camera index
const DEMO_COORDS = [
  [17.3850, 78.4867],
  [17.4399, 78.4983],
  [17.3617, 78.4747],
  [17.4124, 78.5015],
  [17.4500, 78.3800],
  [17.3700, 78.5500],
  [17.4900, 78.4400],
  [17.3200, 78.5000],
];

function markerColor(status, level) {
  if (status === 'OFFLINE') return '#f87171';      // red
  if (level === 'HIGH')     return '#fbbf24';      // amber
  if (level === 'MODERATE') return '#38bdf8';      // sky
  return '#34d399';                                // green
}

export default function CityMap({ cameras }) {
  if (!cameras || cameras.length === 0) {
    return (
      <div className="city-map-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-surface-2)', color: 'var(--text-muted)' }}>
        No cameras to display.
      </div>
    );
  }

  // Attach coordinates — real if available, else deterministic demo fallback
  const withCoords = cameras.map((cam, idx) => ({
    ...cam,
    lat: cam.latitude  != null ? Number(cam.latitude)  : DEMO_COORDS[idx % DEMO_COORDS.length][0],
    lng: cam.longitude != null ? Number(cam.longitude) : DEMO_COORDS[idx % DEMO_COORDS.length][1],
    coordSource: cam.latitude != null ? 'real' : 'demo',
  }));

  const center = withCoords.reduce(
    ([lat, lng], c) => [lat + c.lat / withCoords.length, lng + c.lng / withCoords.length],
    [0, 0],
  );

  return (
    <>
      <div className="city-map-container">
        <MapContainer
          center={center}
          zoom={12}
          scrollWheelZoom={false}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution="© <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {withCoords.map((cam) => (
            <CircleMarker
              key={cam.id}
              center={[cam.lat, cam.lng]}
              radius={10}
              pathOptions={{
                color: '#07101e',
                fillColor: markerColor(cam.status, cam.traffic_level),
                fillOpacity: 0.9,
                weight: 2,
              }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                <strong>{cam.name}</strong>
              </Tooltip>
              <Popup>
                <strong>{cam.name}</strong><br />
                {cam.location}<br />
                Status: <strong>{cam.status}</strong><br />
                Traffic: <strong>{cam.traffic_level}</strong><br />
                Detections: <strong>{cam.detection_count}</strong>
                {cam.coordSource === 'demo' && (
                  <><br /><em style={{ color: '#888', fontSize: 11 }}>⚠ Demo coordinates</em></>
                )}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div className="map-legend" aria-label="Map legend">
        <div className="map-legend-item">
          <span className="legend-dot" style={{ background: '#34d399' }} />
          Low traffic / Online
        </div>
        <div className="map-legend-item">
          <span className="legend-dot" style={{ background: '#38bdf8' }} />
          Moderate traffic
        </div>
        <div className="map-legend-item">
          <span className="legend-dot" style={{ background: '#fbbf24' }} />
          High traffic
        </div>
        <div className="map-legend-item">
          <span className="legend-dot" style={{ background: '#f87171' }} />
          Camera offline
        </div>
      </div>
    </>
  );
}
