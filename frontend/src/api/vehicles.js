const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error('Unable to load data from the API.');
  return response.json();
}

// ── Existing vehicle intelligence endpoints (DO NOT CHANGE) ──────────────
export const searchVehicle = (plate) =>
  request(`/vehicles/search/?plate=${encodeURIComponent(plate)}`);

export const getTrajectory = (id) =>
  request(`/vehicles/${id}/trajectory/`);

// ── City dashboard endpoints ──────────────────────────────────────────────
export const getDashboardStats = () =>
  request('/dashboard/stats/');

export const getCityIntelligence = () =>
  request('/dashboard/city/');

// ── Scan & Track ─────────────────────────────────────────────────────────
export async function scanImage(file) {
  const form = new FormData();
  form.append('image', file);
  const response = await fetch(`${API_BASE_URL}/scan/image/`, {
    method: 'POST',
    body: form,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || `Server error: ${response.status}`);
  }
  return response.json();
}
