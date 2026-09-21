import { NavLink } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand" aria-label="ANPR City Intelligence home">
          <div className="navbar-brand-icon" aria-hidden="true">AI</div>
          <div>
            <div className="navbar-brand-text">ANPR City Intelligence</div>
            <div className="navbar-brand-sub">Vehicle Surveillance Platform</div>
          </div>
        </NavLink>

        <ul className="navbar-nav" role="list">
          <li>
            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              id="nav-dashboard"
            >
              <span className="nav-link-icon" aria-hidden="true">🏙️</span>
              Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/vehicles"
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              id="nav-vehicles"
            >
              <span className="nav-link-icon" aria-hidden="true">🚗</span>
              Vehicle Intelligence
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/scan"
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              id="nav-scan"
            >
              <span className="nav-link-icon" aria-hidden="true">🔍</span>
              Scan &amp; Track
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
}
