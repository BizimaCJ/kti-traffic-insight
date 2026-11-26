import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { BellRing, ClipboardList, LogOut, ScrollText, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDocumentTitle } from '../lib/hooks';
import { Spinner } from '../components/ui';
import AlertsPanel from './admin/AlertsPanel';
import AuditPanel from './admin/AuditPanel';
import IncidentsPanel from './admin/IncidentsPanel';

const TABS = [
  { id: 'incidents', label: 'Incident reports', icon: ClipboardList },
  { id: 'alerts', label: 'Alerts', icon: BellRing },
  { id: 'audit', label: 'Audit log', icon: ScrollText },
];

export default function AdminDashboard() {
  useDocumentTitle('Administrator dashboard');
  const { user, ready, logout, timeoutMinutes } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('incidents');
  const [leaving, setLeaving] = useState(false);

  if (!ready) return <div className="card card-pad"><Spinner /> Checking your session...</div>;
  if (!user) return <Navigate to="/admin/login" replace />;

  const signOut = async () => { setLeaving(true); await logout(); navigate('/admin/login'); };

  return (
    <div className="fade-in">
      <div className="admin-head">
        <div>
          <div className="eyebrow">Administration</div>
          <h1>Welcome, {user.full_name}</h1>
          <p style={{ color: 'var(--text-soft)', marginTop: 4 }}><ShieldCheck size={15} style={{ verticalAlign: '-2px' }} /> You are signed out after {timeoutMinutes} minutes of inactivity. Your actions are recorded in the audit log.</p>
        </div>
        <button type="button" className="btn btn-ghost" onClick={signOut} disabled={leaving}>{leaving ? <Spinner /> : <LogOut size={18} />} Sign out</button>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} className={`tab ${tab === id ? 'active' : ''}`} onClick={() => setTab(id)}><Icon size={18} />{label}</button>
        ))}
      </div>

      {tab === 'incidents' && <IncidentsPanel />}
      {tab === 'alerts' && <AlertsPanel />}
      {tab === 'audit' && <AuditPanel />}
    </div>
  );
}
