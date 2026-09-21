/**
 * AlertsPanel — shows deterministic demo alerts generated from real data.
 *
 * Props:
 *   alerts  Array<{ id, severity, type, title, detail, source, is_demo }>
 */

const ICONS = {
  CAMERA_OFFLINE: '📵',
  HIGH_TRAFFIC:   '🚦',
  SYSTEM_OK:      '✅',
  DEFAULT:        '⚠️',
};

export default function AlertsPanel({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return <p className="empty-state">No alerts.</p>;
  }

  return (
    <div className="alerts-list" role="list" aria-label="Active alerts">
      {alerts.map((alert) => {
        const icon = ICONS[alert.type] ?? ICONS.DEFAULT;
        const severityCls = `alert-item severity-${alert.severity.toLowerCase()}`;
        return (
          <div className={severityCls} key={alert.id} role="listitem" id={`alert-${alert.id}`}>
            <span className="alert-icon" aria-hidden="true">{icon}</span>
            <div className="alert-body">
              <div className="alert-title">{alert.title}</div>
              <div className="alert-detail">{alert.detail}</div>
              <div className="alert-footer">
                <span className="alert-source">Source: {alert.source}</span>
                {alert.is_demo && (
                  <span className="badge badge-demo" style={{ fontSize: 9, padding: '1px 6px' }}>
                    Simulated
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
