import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { ChartLine, FlaskConical, LayoutDashboard, Menu, Route, ShieldCheck, TriangleAlert, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LINKS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/journey', label: 'Plan a journey', icon: Route },
  { to: '/report', label: 'Report incident', icon: TriangleAlert },
  { to: '/history', label: 'History', icon: ChartLine },
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();
  useEffect(() => { setOpen(false); window.scrollTo({ top: 0 }); }, [location.pathname]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand" aria-label="Kigali Traffic Insight, home">
            <span className="brand-mark"><Route size={22} /></span>
            <span className="brand-text"><strong>Kigali Traffic Insight</strong><span>Nyabugogo prototype</span></span>
          </Link>
          <button type="button" className="menu-btn" aria-label="Menu" aria-expanded={open} onClick={() => setOpen(!open)}>
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
          <nav className={`nav ${open ? 'open' : ''}`} aria-label="Main">
            {LINKS.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? 'active' : '')}><Icon size={17} />{label}</NavLink>
            ))}
            <NavLink to="/admin" className={({ isActive }) => `nav-admin ${isActive ? 'active' : ''}`}>
              <ShieldCheck size={17} />{user ? 'Dashboard' : 'Admin'}
            </NavLink>
          </nav>
        </div>
      </header>

      <div className="sim-banner" role="note">
        <div className="sim-banner-inner">
          <span className="sim-chip"><FlaskConical size={12} /> SIMULATED DATA</span>
          <span>This prototype shows simulated traffic, not live conditions. Always follow official traffic instructions.</span>
        </div>
      </div>

      <main className="page"><Outlet /></main>

      <footer className="footer">
        <div className="footer-inner">
          <div><strong>Kigali Traffic Insight</strong><br />Traffic information and incident alerts for Nyabugogo, Kigali.</div>
          <div>African Leadership University - formative assignment prototype.<br />It does not control traffic signals or replace traffic officers.</div>
        </div>
      </footer>
    </div>
  );
}
