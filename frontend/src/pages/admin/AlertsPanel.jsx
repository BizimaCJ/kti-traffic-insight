import { useState } from 'react';
import { BellOff, BellPlus, BellRing, Megaphone } from 'lucide-react';
import { useNetwork } from '../../context/NetworkContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../lib/api';
import { formatDateTime, timeAgo } from '../../lib/format';
import { useLoader } from '../../lib/hooks';
import { EmptyState, ErrorState, Field, Skeleton, Spinner } from '../../components/ui';

export default function AlertsPanel() {
  const toast = useToast();
  const { roads } = useNetwork();
  const { data, error, loading, reload, reloadWithSpinner } = useLoader((o) => api.adminAlerts(o), [], { intervalMs: 20000 });
  const [message, setMessage] = useState('');
  const [road, setRoad] = useState('');
  const [formError, setFormError] = useState('');
  const [busy, setBusy] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [filter, setFilter] = useState('ACTIVE');

  const publish = async (e) => {
    e.preventDefault();
    setFormError('');
    if (message.trim().length < 5) { setFormError('Write an alert message (at least 5 characters).'); return; }
    setBusy(true);
    try {
      await api.publishAlert(message.trim(), road ? Number(road) : null);
      toast.success('Alert published. It is now visible to road users.');
      setMessage(''); setRoad('');
      await reload();
    } catch (err) { setFormError(err.fields ? Object.values(err.fields)[0] : err.message); }
    finally { setBusy(false); }
  };

  const withdraw = async (alert) => {
    setBusyId(alert.id);
    try { await api.withdrawAlert(alert.id); toast.success('Alert withdrawn.'); await reload(); }
    catch (err) { toast.error(err.message); await reload(); }
    finally { setBusyId(null); }
  };

  const rows = (data?.results || []).filter((a) => filter === 'ALL' || a.status === filter);

  return (
    <div className="admin-two">
      <form className="card card-pad-lg form-grid" onSubmit={publish} noValidate>
        <div><h2>Publish an alert</h2><p style={{ color: 'var(--text-soft)', marginTop: 4 }}>Shown as a banner on the overview page until you withdraw it.</p></div>
        <Field label="Message" htmlFor="alert-message" counter={<span className="char-count">{message.length} / 300</span>}>
          <textarea id="alert-message" className={`textarea ${formError ? 'invalid' : ''}`} maxLength={300} value={message} onChange={(e) => setMessage(e.target.value)} placeholder="For example: Nyabugogo terminal is very crowded. Allow extra time." style={{ minHeight: 100 }} />
        </Field>
        <Field label="Road (optional)" htmlFor="alert-road">
          <select id="alert-road" className="select" value={road} onChange={(e) => setRoad(e.target.value)}>
            <option value="">Whole area</option>
            {roads.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </Field>
        {formError && <div className="error-card" role="alert" style={{ padding: '10px 14px' }}>{formError}</div>}
        <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? <Spinner /> : <BellPlus size={18} />} Publish alert</button>
        <div className="notice"><Megaphone size={18} style={{ flex: 'none' }} /> Alerts are also created automatically when an incident is verified or a delay reaches the threshold.</div>
      </form>

      <div>
        <div className="chips" role="group" aria-label="Filter alerts">
          {[['ACTIVE', 'Active'], ['WITHDRAWN', 'Withdrawn'], ['ALL', 'All']].map(([v, l]) => (
            <button key={v} type="button" className={`chip-btn ${filter === v ? 'active' : ''}`} onClick={() => setFilter(v)} aria-pressed={filter === v}>{l}</button>
          ))}
        </div>
        {error && !data && <ErrorState error={error} onRetry={reloadWithSpinner} />}
        {loading && !data && <div className="stack"><Skeleton h={110} /><Skeleton h={110} /></div>}
        {data && (rows.length === 0 ? (
          <div className="card"><EmptyState icon={BellOff} title={filter === 'ACTIVE' ? 'No active alerts' : 'No alerts here'}>Published and automatic alerts will be listed here.</EmptyState></div>
        ) : (
          <ul className="incident-list">
            {rows.map((a) => (
              <li key={a.id} className="card admin-incident">
                <div className="top">
                  <div className="row" style={{ gap: 10 }}><BellRing size={20} color="var(--heavy)" /><strong>{a.message}</strong></div>
                  <span className={`badge status-${a.status}`}><i className="dot" />{a.status === 'ACTIVE' ? 'Active' : 'Withdrawn'}</span>
                </div>
                <div className="facts" style={{ marginTop: 10 }}>
                  <span className="tag">{a.trigger_label}</span>
                  {a.road_name && <span>{a.road_name}</span>}
                  <span title={formatDateTime(a.published_at)}>Published {timeAgo(a.published_at)} by {a.published_by_name}</span>
                  {a.withdrawn_at && <span>Withdrawn {timeAgo(a.withdrawn_at)} by {a.withdrawn_by_name}</span>}
                  {a.status === 'ACTIVE' && a.incident_status && a.incident_status !== 'VERIFIED' && <span className="tag warn">Linked incident is {a.incident_status.toLowerCase()}</span>}
                </div>
                {a.status === 'ACTIVE' && (
                  <div className="actions"><button type="button" className="btn btn-danger-soft btn-sm" onClick={() => withdraw(a)} disabled={busyId === a.id}>{busyId === a.id ? <Spinner size={15} /> : <BellOff size={16} />} Withdraw</button></div>
                )}
              </li>
            ))}
          </ul>
        ))}
      </div>
    </div>
  );
}
