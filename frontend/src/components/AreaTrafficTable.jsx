/**
 * AreaTrafficTable — displays per-area traffic aggregates.
 *
 * Props:
 *   areas   Array<{ area, camera_count, detection_count, unique_vehicles,
 *                   traffic_level, peak_period }>
 */
function LevelBadge({ level }) {
  const cls = level === 'HIGH' ? 'badge badge-high'
    : level === 'MODERATE'    ? 'badge badge-moderate'
    : 'badge badge-low';
  return (
    <span className={cls}>
      <span className="badge-dot" aria-hidden="true" />
      {level}
    </span>
  );
}

export default function AreaTrafficTable({ areas }) {
  if (!areas || areas.length === 0) {
    return <p className="empty-state">No area data available yet.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table" aria-label="Area traffic statistics">
        <thead>
          <tr>
            <th>Area / Zone</th>
            <th>Cameras</th>
            <th>Detections</th>
            <th>Unique Vehicles</th>
            <th>Traffic Level</th>
            <th>Peak Period <span className="badge badge-demo" style={{ fontSize: 9, padding: '1px 6px' }}>Demo</span></th>
          </tr>
        </thead>
        <tbody>
          {areas.map((row) => (
            <tr key={row.area}>
              <td className="area-name">{row.area}</td>
              <td className="num">{row.camera_count}</td>
              <td className="num">{row.detection_count.toLocaleString()}</td>
              <td className="num">{row.unique_vehicles.toLocaleString()}</td>
              <td><LevelBadge level={row.traffic_level} /></td>
              <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>{row.peak_period}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
