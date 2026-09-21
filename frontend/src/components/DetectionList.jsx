const pct = (value) => value == null ? '—' : `${Math.round(Number(value) * 100)}%`;
export default function DetectionList({ detections }) {
  return <section className="card"><h2>Detection details</h2>{detections.map((item, index) => <article className="detection" key={index}><b>{item.camera.name}</b><span>{item.camera.location_name} · {new Date(item.timestamp).toLocaleString()}</span><small>Plate confidence: {pct(item.plate_confidence)} · Vehicle confidence: {pct(item.vehicle_confidence)}</small></article>)}</section>;
}
