/**
 * RecentDetections — live feed of the most recent ANPR detections.
 *
 * Props:
 *   detections  Array<{ id, plate, camera_name, location, timestamp,
 *                        plate_confidence, vehicle_confidence }>
 */

const pct = (v) => (v == null ? null : `${Math.round(Number(v) * 100)}%`);

function formatTime(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDate(ts) {
  if (!ts) return '';
  return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

export default function RecentDetections({ detections }) {
  if (!detections || detections.length === 0) {
    return <p className="empty-state">No recent detections recorded.</p>;
  }

  return (
    <div className="detection-feed" role="list" aria-label="Recent detections">
      {detections.map((d) => {
        const plateConf  = pct(d.plate_confidence);
        const vehicleConf = pct(d.vehicle_confidence);
        return (
          <div className="detection-row" key={d.id} role="listitem">
            <div className="detection-plate" aria-label={`Plate ${d.plate}`}>{d.plate}</div>
            <div className="detection-meta">
              <div className="detection-camera">{d.camera_name}</div>
              <div className="detection-loc">{d.location}</div>
              {(plateConf || vehicleConf) && (
                <div className="confidence-pills">
                  {plateConf   && <span className="conf-pill" title="Plate confidence">Plate {plateConf}</span>}
                  {vehicleConf && <span className="conf-pill" title="Vehicle confidence">Vehicle {vehicleConf}</span>}
                </div>
              )}
            </div>
            <div className="detection-time">
              <div>{formatTime(d.timestamp)}</div>
              <div>{formatDate(d.timestamp)}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
