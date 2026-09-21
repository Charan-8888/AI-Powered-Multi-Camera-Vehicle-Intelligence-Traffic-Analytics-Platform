import { useCallback, useEffect, useState } from 'react';
import { getDashboardStats, getCityIntelligence } from '../api/vehicles';
import KpiCard from '../components/KpiCard';
import AreaTrafficTable from '../components/AreaTrafficTable';
import CityMap from '../components/CityMap';
import CameraStatusGrid from '../components/CameraStatusGrid';
import AlertsPanel from '../components/AlertsPanel';
import RecentDetections from '../components/RecentDetections';

// ── Traffic status indicator ─────────────────────────────────────────────────
function TrafficStatusBar({ status }) {
  const colour = status === 'HIGH'     ? 'var(--red)'
    : status  === 'MODERATE'           ? 'var(--amber)'
    : 'var(--green)';
  const emoji = status === 'HIGH' ? '🔴' : status === 'MODERATE' ? '🟡' : '🟢';
  return (
    <div className="traffic-status-bar">
      <span style={{ color: colour, fontSize: 18 }} aria-hidden="true">{emoji}</span>
      <span className="label">City-wide traffic status:</span>
      <strong style={{ color: colour }}>{status || '—'}</strong>
      <span className="badge badge-demo" style={{ fontSize: 9, padding: '1px 6px', marginLeft: 'auto' }}>
        ⚠ Simulated threshold
      </span>
    </div>
  );
}

// ── Loading / error helpers ───────────────────────────────────────────────────
function Loading() {
  return (
    <div className="loading-wrap">
      <div className="spinner" aria-label="Loading" />
      <span>Loading city intelligence…</span>
    </div>
  );
}

function ErrorBox({ message }) {
  return <div className="error-box">⚠ {message}</div>;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats,  setStats]  = useState(null);
  const [city,   setCity]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,  setError]  = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [s, c] = await Promise.all([getDashboardStats(), getCityIntelligence()]);
      setStats(s);
      setCity(c);
    } catch (err) {
      setError(err.message || 'Could not reach the ANPR API. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Auto-refresh every 30 s
  useEffect(() => {
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, [load]);

  return (
    <div className="page-content">
      {/* ── Page header ─────────────────────────────────────────────── */}
      <header className="page-header">
        <p className="eyebrow">SIH 2025 · ANPR Vehicle Intelligence</p>
        <h1>City Dashboard</h1>
        <p>
          Real-time city-wide Automatic Number Plate Recognition — camera monitoring,
          area traffic analytics, and vehicle intelligence.
        </p>
      </header>

      {loading && <Loading />}
      {!loading && error && <ErrorBox message={error} />}

      {!loading && !error && stats && city && (
        <>
          {/* ── Traffic status bar ──────────────────────────────────── */}
          <TrafficStatusBar status={stats.traffic_status} />

          {/* ── KPI Strip ───────────────────────────────────────────── */}
          <section className="dash-section" aria-labelledby="kpi-heading">
            <div className="section-header">
              <h2 className="section-title" id="kpi-heading">City Overview</h2>
              <span className="section-sub">Live platform statistics</span>
            </div>
            <div className="kpi-grid">
              <KpiCard
                id="kpi-total-vehicles"
                icon="🚗"
                value={stats.total_vehicles?.toLocaleString()}
                label="Total Vehicles"
                accent="var(--accent)"
                isDemo={false}
              />
              <KpiCard
                id="kpi-unique-vehicles"
                icon="🪪"
                value={stats.unique_vehicles?.toLocaleString()}
                label="Unique Vehicles"
                accent="var(--purple)"
                isDemo={false}
              />
              <KpiCard
                id="kpi-total-detections"
                icon="📸"
                value={stats.total_detections?.toLocaleString()}
                label="ANPR Detections"
                accent="var(--green)"
                isDemo={false}
              />
              <KpiCard
                id="kpi-active-cameras"
                icon="📷"
                value={stats.active_cameras}
                label="Active Cameras"
                accent="var(--green)"
                isDemo={false}
              />
              <KpiCard
                id="kpi-offline-cameras"
                icon="📵"
                value={stats.offline_cameras}
                label="Offline Cameras"
                accent="var(--red)"
                isDemo={false}
              />
              <KpiCard
                id="kpi-active-alerts"
                icon="🔔"
                value={stats.active_alerts}
                label="Active Alerts"
                accent="var(--amber)"
                isDemo={true}
              />
            </div>
          </section>

          {/* ── Area Traffic + City Map ──────────────────────────────── */}
          <section className="dash-section" aria-labelledby="area-heading">
            <div className="two-col">
              {/* Area traffic */}
              <div className="card">
                <div className="section-header" style={{ marginBottom: 16 }}>
                  <h2 className="section-title" id="area-heading">Area-wise Traffic</h2>
                  <span className="section-sub">Grouped by camera zone</span>
                </div>
                <AreaTrafficTable areas={city.area_traffic} />
              </div>

              {/* City Map */}
              <div className="card">
                <div className="section-header" style={{ marginBottom: 16 }}>
                  <h2 className="section-title" id="map-heading">Camera Map</h2>
                  <span className="section-sub">
                    {city.camera_list.some(c => !c.latitude)
                      ? 'Demo coordinates where GPS not set'
                      : 'Live camera positions'}
                  </span>
                </div>
                <CityMap cameras={city.camera_list} />
              </div>
            </div>
          </section>

          {/* ── Camera Monitoring ────────────────────────────────────── */}
          <section className="dash-section card" aria-labelledby="camera-heading">
            <div className="section-header">
              <h2 className="section-title" id="camera-heading">Camera Monitoring</h2>
              <span className="section-sub">
                {stats.active_cameras} online · {stats.offline_cameras} offline
              </span>
            </div>
            <CameraStatusGrid cameras={city.camera_list} />
          </section>

          {/* ── Recent Detections + Alerts ──────────────────────────── */}
          <div className="two-col">
            <section className="card" aria-labelledby="det-heading">
              <div className="section-header">
                <h2 className="section-title" id="det-heading">Recent Detections</h2>
                <span className="section-sub">Last 12 events · Real data</span>
              </div>
              <RecentDetections detections={city.recent_detections} />
            </section>

            <section className="card" aria-labelledby="alert-heading">
              <div className="section-header">
                <h2 className="section-title" id="alert-heading">Alerts</h2>
                <span className="badge badge-demo" style={{ fontSize: 9, padding: '1px 6px' }}>
                  ⚠ Simulated
                </span>
              </div>
              <AlertsPanel alerts={city.alerts} />
            </section>
          </div>
        </>
      )}
    </div>
  );
}
