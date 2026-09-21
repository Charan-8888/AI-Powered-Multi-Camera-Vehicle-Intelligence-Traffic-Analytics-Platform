export default function VehicleSearch({ plate, onPlateChange, onSearch, loading }) {
  return <form className="search" onSubmit={onSearch}>
    <label htmlFor="plate">Search vehicle plate</label>
    <div><input id="plate" value={plate} onChange={(event) => onPlateChange(event.target.value)} placeholder="TS09AB1234" /><button disabled={loading}>{loading ? 'Searching…' : 'Search'}</button></div>
  </form>;
}
