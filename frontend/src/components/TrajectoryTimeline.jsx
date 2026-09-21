const formatTime = (value) => new Date(value).toLocaleString();
export default function TrajectoryTimeline({ trajectory, detections }) {
  if (!trajectory) return <section className="card"><h2>Trajectory</h2><p>No detections recorded.</p></section>;
  return <section className="card"><h2>Trajectory</h2><ol className="timeline">{trajectory.camera_sequence.map((camera, index) => { const detection = detections.find((item) => item.camera.name === camera); return <li key={`${camera}-${index}`}><b>{camera}</b><span>{detection?.camera.location_name || 'Demo location'} · {formatTime(detection?.timestamp)}</span></li>; })}</ol></section>;
}
