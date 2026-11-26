import { useState } from 'react';
import { CircleCheck, ClipboardCheck, Copy, Inbox, Search, UserRound, XCircle } from 'lucide-react';
import { api } from '../../lib/api';
import { INCIDENT_TYPES, STATUSES } from '../../lib/constants';
import { formatDateTime, timeAgo } from '../../lib/format';
import { useLoader } from '../../lib/hooks';
import { useToast } from '../../context/ToastContext';
import { EmptyState, ErrorState, Field, Modal, Skeleton, Spinner } from '../../components/ui';

function IncidentRow({ incident, busy, onAction, onReject }) {
  const meta = INCIDENT_TYPES[incident.type] || INCIDENT_TYPES.OTHER;
  const Icon = meta.icon;
  const s = incident.status;
  return (
    <li className="card admin-incident">
      <div className="top">
        <div className="row" style={{ gap: 12 }}>
          <div className="type-ico" style={{ width: 44, height: 44, borderRadius: 14, display: 'grid', placeItems: 'center', background: 'var(--blue-50)', color: 'var(--blue-700)' }}><Icon size={21} /></div>
          <div>
            <div className="ref">{incident.reference}</div>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-soft)' }}>{meta.label} on {incident.road_name}{incident.intersection_name ? `, near ${incident.intersection_name}` : ''}</div>
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          {incident.possible_duplicate_reference && <span className="tag warn"><Copy size={12} /> Possible duplicate of {incident.possible_duplicate_reference}</span>}
          {incident.is_simulated && <span className="tag sim">Simulated</span>}
          <span className={`badge status-${s}`}><i className="dot" />{STATUSES[s]}</span>
        </div>
      </div>
      <p className="desc">{incident.description}</p>
      <div className="facts">
        <span title={formatDateTime(incident.reported_at)}>Reported {timeAgo(incident.reported_at)}</span>
        <span><UserRound size={14} /> {incident.is_simulated ? 'Simulator' : (incident.reporter_name || 'Anonymous')}{incident.reporter_contact ? ` (${incident.reporter_contact})` : ''}</span>
        {incident.reviewed_by_name && <span><ClipboardCheck size={14} /> Handled by {incident.reviewed_by_name}</span>}
        {incident.rejection_reason && <span style={{ color: 'var(--blocked-ink)' }}><XCircle size={14} /> Reason: {incident.rejection_reason}</span>}
      </div>
      {(s === 'SUBMITTED' || s === 'UNDER_REVIEW' || s === 'VERIFIED') && (
        <div className="actions">
          {s === 'SUBMITTED' && <button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={() => onAction(incident, 'review')}>{busy ? <Spinner size={15} /> : <Search size={16} />} Start review</button>}
          {s === 'UNDER_REVIEW' && <button type="button" className="btn btn-primary btn-sm" disabled={busy} onClick={() => onAction(incident, 'verify')}>{busy ? <Spinner size={15} /> : <CircleCheck size={16} />} Verify</button>}
          {s === 'VERIFIED' && <button type="button" className="btn btn-secondary btn-sm" disabled={busy} onClick={() => onAction(incident, 'resolve')}>{busy ? <Spinner size={15} /> : <CircleCheck size={16} />} Mark resolved</button>}
          {(s === 'SUBMITTED' || s === 'UNDER_REVIEW') && <button type="button" className="btn btn-danger-soft btn-sm" disabled={busy} onClick={() => onReject(incident)}><XCircle size={16} /> Reject...</button>}
        </div>
      )}
    </li>
  );
}

export default function IncidentsPanel() {
  const toast = useToast();
  const [filter, setFilter] = useState(null);
  const { data, error, loading, reload, reloadWithSpinner } = useLoader((o) => api.adminIncidents(filter, o), [filter], { intervalMs: 20000 });
  const [busyId, setBusyId] = useState(null);
  const [rejecting, setRejecting] = useState(null);
  const [reason, setReason] = useState('');
  const [reasonError, setReasonError] = useState('');
  const [rejectBusy, setRejectBusy] = useState(false);

  const run = async (incident, action, body) => {
    setBusyId(incident.id);
    try {
      await api.incidentAction(incident.id, action, body);
      const done = { review: 'Review started', verify: 'Incident verified. An alert was created.', resolve: 'Incident marked as resolved.' }[action];
      toast.success(`${incident.reference}: ${done}`);
      await reload();
    } catch (err) {
      toast.error(err.message);
      await reload();
    } finally { setBusyId(null); }
  };

  const submitReject = async () => {
    if (!reason.trim()) { setReasonError('A rejection reason is required.'); return; }
    setRejectBusy(true);
    try {
      await api.incidentAction(rejecting.id, 'reject', { reason: reason.trim() });
      toast.success(`${rejecting.reference}: report rejected.`);
      setRejecting(null); setReason(''); setReasonError('');
      await reload();
    } catch (err) {
      setReasonError(err.fields?.reason || err.message);
    } finally { setRejectBusy(false); }
  };

  const counts = data?.counts;
  return (
    <div>
      <div className="admin-stats">
        {Object.entries(STATUSES).map(([key, label]) => (
          <button key={key} type="button" className={`admin-stat ${filter === key ? 'active' : ''}`} onClick={() => setFilter(filter === key ? null : key)} aria-pressed={filter === key}>
            <b>{counts ? counts[key] : <Skeleton h={28} w={36} />}</b><span>{label}</span>
          </button>
        ))}
      </div>

      {error && !data && <ErrorState error={error} onRetry={reloadWithSpinner} />}
      {loading && !data && <div className="stack"><Skeleton h={150} /><Skeleton h={150} /></div>}
      {data && (data.results.length === 0 ? (
        <div className="card"><EmptyState icon={Inbox} title={filter ? `No ${STATUSES[filter].toLowerCase()} incidents` : 'No incident reports yet'}>New anonymous reports will appear here for review.</EmptyState></div>
      ) : (
        <ul className="incident-list">
          {data.results.map((i) => <IncidentRow key={i.id} incident={i} busy={busyId === i.id} onAction={run} onReject={(inc) => { setRejecting(inc); setReason(''); setReasonError(''); }} />)}
        </ul>
      ))}

      {rejecting && (
        <Modal title={`Reject ${rejecting.reference}`} onClose={() => setRejecting(null)}
          actions={<>
            <button type="button" className="btn btn-ghost" onClick={() => setRejecting(null)}>Cancel</button>
            <button type="button" className="btn btn-danger" onClick={submitReject} disabled={rejectBusy}>{rejectBusy ? <Spinner /> : <XCircle size={18} />} Reject report</button>
          </>}>
          <p style={{ color: 'var(--text-soft)', marginBottom: 14 }}>Say why this report is being rejected. The reason is saved with the incident and in the audit log.</p>
          <Field label="Reason" htmlFor="reason" error={reasonError}>
            <textarea id="reason" className={`textarea ${reasonError ? 'invalid' : ''}`} value={reason} maxLength={500} onChange={(e) => { setReason(e.target.value); setReasonError(''); }} placeholder="For example: could not be confirmed, or duplicate of another report." autoFocus />
          </Field>
        </Modal>
      )}
    </div>
  );
}
