/**
 * CameraStatusGrid — card grid for all cameras.
 *
 * Props:
 *   cameras  Array<{ id, name, location, status, is_active,
 *                    detection_count, last_detection, traffic_level }>
 */
function StatusBadge({ status }) {
  return (
    <span className={`badge ${status === 'ONLINE' ? 'badge-online' : 'badge-offline'}`}>
      <span className="badge-dot" aria-hidden="true" />
      {status}
    </span>
  );
}

function LevelBadge({ level }) {
  const cls = level === 'HIGH'     ? 'badge badge-high'
    : level === 'MODERATE'         ? 'badge badge-moderate'
    : 'badge badge-low';
  return <span className={cls}>{level}</span>;
}

function formatRelative(ts) {
  if (!ts) return 'Never';
  const diff = Date.now() - new Date(ts).getTime();
  const mins  = Math.floor(diff / 60000);
  if (mins < 1)   return 'Just now';
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs  < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function CameraStatusGrid({ cameras }) {
  if (!cameras || cameras.length === 0) {
    return <p className="empty-state">No cameras registered yet.</p>;
  }

  return (
    <div className="camera-grid">
      {cameras.map((cam) => (
        <article className="camera-card" key={cam.id} id={`camera-card-${cam.id}`}>
          <div className="camera-card-header">
            <div>
              <div className="camera-name">{cam.name}</div>
              <div className="camera-location">{cam.location}</div>
            </div>
            <StatusBadge status={cam.status} />
          </div>

          <div className="camera-stats">
            <div className="camera-stat">
              <span className="camera-stat-value">{cam.detection_count.toLocaleString()}</span>
              <span className="camera-stat-label">Detections</span>
            </div>
            <div className="camera-stat">
              <LevelBadge level={cam.traffic_level} />
              <span className="camera-stat-label" style={{ marginTop: 4 }}>Traffic</span>
            </div>
          </div>

          <div className="camera-last">
            Last detection: <strong>{formatRelative(cam.last_detection)}</strong>
          </div>
        </article>
      ))}
    </div>
  );
}
