/**
 * KpiCard — headline metric card.
 *
 * Props:
 *   icon    string   emoji or text icon
 *   value   string | number
 *   label   string
 *   accent  CSS colour token name (optional, defaults to --accent)
 *   isDemo  bool     if true shows DEMO badge, else REAL
 *   id      string   unique HTML id for testing
 */
export default function KpiCard({ icon, value, label, accent, isDemo = false, id }) {
  const style = accent ? { '--kpi-accent': accent } : {};
  return (
    <article className="kpi-card" style={style} id={id}>
      <div className="kpi-icon" aria-hidden="true">{icon}</div>
      <div className="kpi-value">{value ?? '—'}</div>
      <div className="kpi-label">{label}</div>
      <span className={`kpi-badge ${isDemo ? 'kpi-badge-demo' : 'kpi-badge-real'}`}>
        {isDemo ? '⚠ Demo' : '✓ Real'}
      </span>
    </article>
  );
}
