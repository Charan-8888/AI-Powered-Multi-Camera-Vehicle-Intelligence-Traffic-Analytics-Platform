const formatTime = (value) => value ? new Date(value).toLocaleString() : '—';
export default function VehicleSummary({ vehicle, trajectory }) {
  return <section className="card"><h2>Vehicle</h2><strong>{vehicle.plate}</strong><dl><dt>Type</dt><dd>{vehicle.vehicle_type || 'Unknown'}</dd><dt>First seen</dt><dd>{formatTime(trajectory?.first_seen)}</dd><dt>Last seen</dt><dd>{formatTime(trajectory?.last_seen)}</dd><dt>Detections</dt><dd>{trajectory?.total_detections ?? 0}</dd></dl></section>;
}
