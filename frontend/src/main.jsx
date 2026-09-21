import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import './styles.css';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import VehicleIntelligence from './pages/VehicleIntelligence';
import ScanAndTrack from './pages/ScanAndTrack';

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Navbar />
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/vehicles" element={<VehicleIntelligence />} />
          <Route path="/scan"     element={<ScanAndTrack />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
