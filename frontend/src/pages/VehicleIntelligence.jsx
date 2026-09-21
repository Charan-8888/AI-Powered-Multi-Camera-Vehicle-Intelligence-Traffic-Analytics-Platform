import { useState } from 'react';
import { getTrajectory, searchVehicle } from '../api/vehicles';
import VehicleSearch from '../components/VehicleSearch';
import VehicleSummary from '../components/VehicleSummary';
import TrajectoryTimeline from '../components/TrajectoryTimeline';
import DetectionList from '../components/DetectionList';
import TrajectoryMap from '../components/TrajectoryMap';

export default function VehicleIntelligence() {
  const [plate, setPlate]   = useState('TS09AB1234');
  const [data,  setData]    = useState(null);
  const [state, setState]   = useState({ loading: false, error: '' });

  async function onSearch(event) {
    event.preventDefault();
    setState({ loading: true, error: '' });
    setData(null);
    try {
      const vehicle = await searchVehicle(plate);
      if (!vehicle) {
        setState({ loading: false, error: 'Vehicle not found.' });
        return;
      }
      const trajectory = await getTrajectory(vehicle.id);
      setData(trajectory);
      setState({ loading: false, error: '' });
    } catch {
      setState({ loading: false, error: 'Could not reach the vehicle API.' });
    }
  }

  return (
    <main className="vi-page">
      <header>
        <p className="eyebrow">ANPR City Intelligence</p>
        <h1>Vehicle Intelligence</h1>
        <p>Search a plate number to view its full observed camera route, timestamps, and detection evidence.</p>
      </header>

      <VehicleSearch
        plate={plate}
        onPlateChange={setPlate}
        onSearch={onSearch}
        loading={state.loading}
      />

      {state.error && <p className="notice">{state.error}</p>}

      {data && (
        <div className="grid">
          <VehicleSummary    vehicle={data.vehicle}       trajectory={data.trajectory} />
          <TrajectoryMap     trajectory={data.trajectory} detections={data.detections} />
          <TrajectoryTimeline trajectory={data.trajectory} detections={data.detections} />
          <DetectionList     detections={data.detections} />
        </div>
      )}
    </main>
  );
}
