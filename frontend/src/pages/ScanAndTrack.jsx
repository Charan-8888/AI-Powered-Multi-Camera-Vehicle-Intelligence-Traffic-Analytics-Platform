import { useRef, useState } from 'react';
import { scanImage } from '../api/vehicles';

// ── Helpers ───────────────────────────────────────────────────────────────────
const pct  = (v) => (v == null ? '—' : `${Math.round(Number(v) * 100)}%`);
const fmt  = (ts) => ts ? new Date(ts).toLocaleString('en-IN') : '—';
const fmtT = (ts) => ts ? new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—';
const fmtD = (ts) => ts ? new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
const sizeFmt = (bytes) => bytes > 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`;

// ── Sub-components ────────────────────────────────────────────────────────────

function UploadZone({ onFile }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) onFile(file);
  };

  return (
    <div
      className={`upload-zone${dragOver ? ' drag-over' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      aria-label="Click or drag an image to upload for ANPR scanning"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        id="scan-file-input"
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) onFile(file);
          e.target.value = '';         // allow same file re-upload
        }}
      />
      <div className="upload-icon" aria-hidden="true">📷</div>
      <div className="upload-title">Drop a vehicle photo here</div>
      <div className="upload-sub">or click to browse your files</div>
      <div className="upload-hint">JPEG · PNG · WebP · BMP — max 20 MB</div>
    </div>
  );
}

function Processing() {
  return (
    <div className="scan-processing card" role="status" aria-live="polite">
      <div className="spinner" />
      <strong>Running ANPR pipeline…</strong>
      <div className="scan-processing-steps">
        <div className="scan-processing-step"><span className="step-dot" />Stage 1 — Vehicle detection (YOLO11n)</div>
        <div className="scan-processing-step"><span className="step-dot" style={{ animationDelay: '0.3s' }} />Stage 2 — Plate detection (custom YOLO11n)</div>
        <div className="scan-processing-step"><span className="step-dot" style={{ animationDelay: '0.6s' }} />Stage 3 — OCR (PaddleOCR)</div>
        <div className="scan-processing-step"><span className="step-dot" style={{ animationDelay: '0.9s' }} />Checking city camera database…</div>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
        First scan loads AI models (~3–6 seconds). Subsequent scans are faster.
      </div>
    </div>
  );
}

function CameraSequence({ trajectory }) {
  if (!trajectory?.camera_sequence?.length) return null;
  const seq = trajectory.camera_sequence;
  return (
    <div className="scan-cam-sequence" aria-label="Camera sequence">
      {seq.map((cam, i) => (
        <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="scan-cam-chip">{cam}</span>
          {i < seq.length - 1 && <span className="scan-cam-arrow" aria-hidden="true">→</span>}
        </span>
      ))}
    </div>
  );
}

function TrackingDetails({ db }) {
  if (!db) return null;

  if (!db.found) {
    return (
      <div className="db-match-not-found">
        <div className="db-match-title">
          <span>🔍</span>
          <span style={{ color: 'var(--text-muted)' }}>Not found in city cameras</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {db.plate_searched
            ? `Plate "${db.plate_searched}" has no recorded detections in this city's camera network.`
            : db.reason || 'No match found.'}
        </div>
      </div>
    );
  }

  const { vehicle_type, first_seen_at, last_seen_at, trajectory, detections } = db;

  return (
    <div className="db-match-found">
      <div className="db-match-title">
        <span>✅</span>
        <span style={{ color: 'var(--green)' }}>Vehicle found in city camera network</span>
      </div>

      {/* Vehicle info */}
      <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 16px', fontSize: 13, marginBottom: 14 }}>
        <dt style={{ color: 'var(--text-muted)' }}>Type</dt>
        <dd style={{ margin: 0, fontWeight: 600 }}>{vehicle_type}</dd>
        <dt style={{ color: 'var(--text-muted)' }}>First seen</dt>
        <dd style={{ margin: 0 }}>{fmtD(first_seen_at)} {fmtT(first_seen_at)}</dd>
        <dt style={{ color: 'var(--text-muted)' }}>Last seen</dt>
        <dd style={{ margin: 0 }}>{fmtD(last_seen_at)} {fmtT(last_seen_at)}</dd>
        {trajectory && (
          <>
            <dt style={{ color: 'var(--text-muted)' }}>Total detections</dt>
            <dd style={{ margin: 0, fontWeight: 700, color: 'var(--accent)' }}>{trajectory.total_detections}</dd>
          </>
        )}
      </dl>

      {/* Camera route */}
      {trajectory?.camera_sequence?.length > 0 && (
        <>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
            Camera route
          </div>
          <CameraSequence trajectory={trajectory} />
        </>
      )}

      {/* Detection timeline */}
      {detections?.length > 0 && (
        <>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', margin: '14px 0 6px' }}>
            Detection history ({detections.length} events)
          </div>
          <div className="scan-det-list">
            {detections.map((d, i) => (
              <div className="scan-det-row" key={i}>
                <div>
                  <div className="scan-det-cam">{d.camera?.name || '—'}</div>
                  <div className="scan-det-loc">{d.camera?.location_name || ''}</div>
                </div>
                <div className="scan-det-time">
                  <div>{fmtT(d.timestamp)}</div>
                  <div>{fmtD(d.timestamp)}</div>
                  {d.plate_confidence != null && (
                    <div style={{ color: 'var(--accent)', fontWeight: 600 }}>
                      Plate {pct(d.plate_confidence)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function DetectionCard({ detection, index }) {
  const isReadable = detection.plate && detection.plate.length >= 4;
  return (
    <article className="detection-card" id={`det-card-${index}`}>
      {/* Header */}
      <div className="detection-card-header">
        <div className="detected-plate-num" aria-label={`Plate number ${detection.plate || 'unreadable'}`}>
          {detection.plate || <span style={{ color: 'var(--text-muted)', fontSize: 16 }}>Unreadable</span>}
        </div>
        <div className="detection-card-meta">
          <div className="detection-card-type">
            {detection.vehicle_type !== 'unknown' ? detection.vehicle_type : 'Image crop'}
          </div>
          <span className={`badge ${isReadable ? 'badge-online' : 'badge-offline'}`}>
            <span className="badge-dot" />
            {isReadable ? 'Plate read' : 'Partial read'}
          </span>
        </div>
      </div>

      {/* Confidence pills */}
      <div className="conf-row">
        <span className="conf-pill" title="Plate detector confidence">
          🎯 Plate det. {pct(detection.plate_confidence)}
        </span>
        <span className="conf-pill" title="OCR confidence">
          🔤 OCR {pct(detection.ocr_confidence)}
        </span>
        {detection.vehicle_type !== 'unknown' && (
          <span className="conf-pill" title="Vehicle detector confidence">
            🚗 Vehicle {pct(detection.vehicle_confidence)}
          </span>
        )}
        {detection.correction_applied && (
          <span className="conf-pill" title={`OCR originally read: ${detection.original_ocr}`}
            style={{ color: 'var(--amber)', borderColor: 'var(--amber)' }}>
            ⚡ Auto-corrected from &quot;{detection.original_ocr}&quot;
          </span>
        )}
        {detection.ocr_raw && detection.ocr_raw !== detection.plate && !detection.correction_applied && (
          <span className="conf-pill" title="Raw OCR output" style={{ color: 'var(--text-muted)' }}>
            Raw: &quot;{detection.ocr_raw}&quot;
          </span>
        )}
      </div>

      {/* DB tracking result */}
      <TrackingDetails db={detection.db_match} />
    </article>
  );
}

function ScanResults({ result, onReset }) {
  const { annotated_image, detections, fallback_mode, image_size } = result;

  return (
    <div>
      {/* Summary bar */}
      <div className="traffic-status-bar" style={{ marginBottom: 24 }}>
        <span style={{ fontSize: 20 }} aria-hidden="true">
          {detections.length > 0 ? '✅' : '⚠️'}
        </span>
        <strong>
          {detections.length === 0
            ? 'No plates detected'
            : `${detections.length} plate${detections.length > 1 ? 's' : ''} detected`}
        </strong>
        {fallback_mode && (
          <span className="badge badge-demo" style={{ fontSize: 10 }}>Fallback mode — no vehicle box</span>
        )}
        <button
          onClick={onReset}
          style={{ marginLeft: 'auto', background: 'var(--bg-surface-3)', color: 'var(--text-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '6px 14px', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit' }}
        >
          ↩ Scan another image
        </button>
      </div>

      <div className="scan-results-grid">
        {/* Left — annotated image */}
        <div className="scan-annotated">
          <div className="card" style={{ padding: 14 }}>
            <img
              src={annotated_image}
              alt="ANPR annotated result — green boxes mark detected plates, blue boxes mark vehicles"
            />
            <div className="scan-annotated-label">
              {image_size.width}×{image_size.height}px · Green = plate · Blue = vehicle
            </div>
          </div>
        </div>

        {/* Right — detection cards */}
        <div className="detection-cards">
          {detections.length === 0 ? (
            <div className="card empty-state" style={{ padding: 32 }}>
              No number plates could be detected or read in this image.
              <br /><br />
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Tips: Use a clear photo with the full vehicle visible. Avoid heavy motion blur. Minimum plate width ~80 px.
              </span>
            </div>
          ) : (
            detections.map((det, i) => (
              <DetectionCard key={i} detection={det} index={i} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ScanAndTrack() {
  const [file,    setFile]    = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState('');

  function handleFile(f) {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError('');
  }

  function reset() {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError('');
  }

  async function handleScan() {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const data = await scanImage(file);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Scan failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-content">
      {/* Header */}
      <header className="page-header">
        <p className="eyebrow">ANPR City Intelligence</p>
        <h1>Scan &amp; Track</h1>
        <p>
          Upload any vehicle photo — the AI pipeline detects the number plate, reads it,
          then checks whether that vehicle has been recorded by city cameras.
        </p>
      </header>

      {/* Upload / preview area */}
      {!result && (
        <section className="dash-section">
          {!file ? (
            <UploadZone onFile={handleFile} />
          ) : (
            <div className="card">
              <div className="preview-strip">
                <div className="preview-img-wrap">
                  <img src={preview} alt="Upload preview" className="preview-img" />
                  <button className="preview-change" onClick={reset}>✕ Remove</button>
                </div>
                <div className="preview-info">
                  <div className="preview-name">{file.name}</div>
                  <div className="preview-size">{sizeFmt(file.size)}</div>
                  <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    The image will be processed locally through:<br />
                    <strong>Vehicle detection</strong> → <strong>Plate detection</strong> → <strong>OCR</strong> → <strong>City DB lookup</strong>
                  </div>
                  <button
                    className="scan-btn"
                    onClick={handleScan}
                    disabled={loading}
                    id="scan-submit-btn"
                  >
                    {loading ? (
                      <><span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Scanning…</>
                    ) : (
                      <><span>🔍</span> Run ANPR Scan</>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {error && <div className="error-box" style={{ marginTop: 16 }}>⚠ {error}</div>}
          {loading && <Processing />}
        </section>
      )}

      {/* Results */}
      {result && !loading && (
        <section className="dash-section">
          <ScanResults result={result} onReset={reset} />
        </section>
      )}
    </div>
  );
}
