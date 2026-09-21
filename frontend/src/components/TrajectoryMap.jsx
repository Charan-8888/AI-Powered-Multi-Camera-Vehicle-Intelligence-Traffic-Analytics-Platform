import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet';

function routePoints(detections) {
  const seen = new Set();
  return detections.filter(({ camera }) => {
    const hasCoordinates = camera?.latitude != null && camera?.longitude != null;
    if (!hasCoordinates || seen.has(camera.id)) return false;
    seen.add(camera.id);
    return true;
  });
}

export default function TrajectoryMap({ trajectory, detections }) {
  const points = routePoints(detections);
  if (!trajectory || !points.length) return <section className="card"><h2>Trajectory map</h2><p>No trajectory available.</p></section>;
  const positions = points.map(({ camera }) => [Number(camera.latitude), Number(camera.longitude)]);
  const center = positions.reduce(([lat, lng], [pointLat, pointLng]) => [lat + pointLat / positions.length, lng + pointLng / positions.length], [0, 0]);
  return <section className="card map-card"><div><h2>Trajectory map</h2><p className="map-note">Simulated camera locations for MVP demonstration.</p></div><MapContainer center={center} zoom={14} scrollWheelZoom={false} className="map"><TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />{positions.length > 1 && <Polyline positions={positions} pathOptions={{ color: '#55d6be', weight: 4 }} />}{points.map(({ camera, timestamp }, index) => <CircleMarker key={camera.id} center={[Number(camera.latitude), Number(camera.longitude)]} radius={9} pathOptions={{ color: '#08241f', fillColor: '#55d6be', fillOpacity: 1 }}><Popup><b>{index + 1}. {camera.name}</b><br />{camera.location_name || 'Demo location'}<br />{new Date(timestamp).toLocaleString()}</Popup></CircleMarker>)}</MapContainer></section>;
}
