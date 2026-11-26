import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CircleCheck, Copy, EyeOff, Send, ShieldCheck, UserCheck } from 'lucide-react';
import { useNetwork } from '../context/NetworkContext';
import { useToast } from '../context/ToastContext';
import { api } from '../lib/api';
import { INCIDENT_TYPES } from '../lib/constants';
import { useDocumentTitle } from '../lib/hooks';
import { ErrorState, Field, Spinner } from '../components/ui';

const MAX = 1000;

export default function Report() {
  useDocumentTitle('Report an incident');
  const { roads, intersections, loading, error: netError, retry } = useNetwork();
  const toast = useToast();
  const empty = { type: '', road: '', intersection: '', description: '', reporter_name: '', reporter_contact: '' };
  const [form, setForm] = useState(empty);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);

  const set = (key) => (e) => { setForm({ ...form, [key]: e.target.value }); setErrors({ ...errors, [key]: undefined }); };

  const validate = () => {
    const next = {};
    if (!form.type) next.type = 'Choose what happened.';
    if (!form.road) next.road = 'Choose the road.';
    if (form.description.trim().length < 10) next.description = 'Please describe what you saw in at least 10 characters.';
    return next;
  };

  const submit = async (e) => {
    e.preventDefault();
    setFormError('');
    const problems = validate();
    setErrors(problems);
    if (Object.keys(problems).length) return;
    setBusy(true);
    try {
      const body = { type: form.type, road: Number(form.road), description: form.description.trim(), reporter_name: form.reporter_name.trim(), reporter_contact: form.reporter_contact.trim() };
      if (form.intersection) body.intersection = Number(form.intersection);
      const result = await api.reportIncident(body);
      setDone(result);
    } catch (err) {
      if (err.fields) setErrors(err.fields);
      setFormError(err.fields ? 'Please check the highlighted fields.' : err.message);
    } finally { setBusy(false); }
  };

  const copy = async () => {
    try { await navigator.clipboard.writeText(done.reference); toast.success('Reference copied'); } catch { toast.error('Could not copy. Please note it down.'); }
  };

  if (netError) return <ErrorState error={netError} onRetry={retry} />;

  if (done) {
    return (
      <div className="fade-in" style={{ maxWidth: 620, margin: '0 auto' }}>
        <div className="card success-card">
          <div className="check"><CircleCheck size={38} /></div>
          <h1 style={{ fontSize: '1.7rem' }}>Thank you, report received</h1>
          <p style={{ color: 'var(--text-soft)', maxWidth: '44ch' }}>{done.message}</p>
          <div className="ref-box">{done.reference}<button type="button" className="icon-btn" onClick={copy} aria-label="Copy reference"><Copy size={16} /></button></div>
          <div className="row" style={{ marginTop: 10 }}>
            <button type="button" className="btn btn-secondary" onClick={() => { setDone(null); setForm(empty); }}>Report another</button>
            <Link to="/" className="btn btn-primary">Back to overview <ArrowRight size={18} /></Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="eyebrow">Report an incident</div>
        <h1>Help other road users</h1>
        <p>Tell us what you saw. You do not need an account. An administrator checks every report before it is shown to anyone else.</p>
      </div>

      <div className="report-layout">
        <form className="card card-pad-lg form-grid" onSubmit={submit} noValidate>
          <Field label="What happened?" error={errors.type}>
            <div className="type-tiles" role="radiogroup" aria-label="Incident type">
              {Object.entries(INCIDENT_TYPES).map(([value, meta]) => {
                const Icon = meta.icon;
                return (
                  <button key={value} type="button" role="radio" aria-checked={form.type === value} className={`type-tile ${form.type === value ? 'selected' : ''}`}
                    onClick={() => { setForm({ ...form, type: value }); setErrors({ ...errors, type: undefined }); }}>
                    <Icon size={24} />{meta.label}
                  </button>
                );
              })}
            </div>
          </Field>

          <div className="form-grid two">
            <Field label="Which road?" htmlFor="road" error={errors.road}>
              <select id="road" className={`select ${errors.road ? 'invalid' : ''}`} value={form.road} onChange={set('road')} disabled={loading}>
                <option value="">Choose a road</option>
                {roads.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select>
            </Field>
            <Field label="Near (optional)" htmlFor="intersection" error={errors.intersection}>
              <select id="intersection" className="select" value={form.intersection} onChange={set('intersection')} disabled={loading}>
                <option value="">Not sure / not near one</option>
                {intersections.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
            </Field>
          </div>

          <Field label="Describe what you saw" htmlFor="description" error={errors.description}
            counter={<span className="char-count">{form.description.length} / {MAX}</span>}>
            <textarea id="description" className={`textarea ${errors.description ? 'invalid' : ''}`} maxLength={MAX} value={form.description} onChange={set('description')}
              placeholder="For example: two minibuses collided near the entrance, one lane is blocked." />
          </Field>

          <div className="form-grid two">
            <Field label="Your name (optional)" htmlFor="name" error={errors.reporter_name}>
              <input id="name" className="input" maxLength={120} value={form.reporter_name} onChange={set('reporter_name')} autoComplete="name" />
            </Field>
            <Field label="Phone or email (optional)" htmlFor="contact" error={errors.reporter_contact} hint="Only used if an administrator needs to ask a question.">
              <input id="contact" className="input" maxLength={160} value={form.reporter_contact} onChange={set('reporter_contact')} autoComplete="email" />
            </Field>
          </div>

          {formError && <div className="error-card" role="alert" style={{ padding: '12px 16px' }}>{formError}</div>}

          <div className="row spread">
            <p className="meta">Please report only what you have seen yourself.</p>
            <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? <Spinner /> : <Send size={18} />} Send report</button>
          </div>
        </form>

        <aside className="card card-pad-lg side-card">
          <h3>How it works</h3>
          <ul>
            <li><EyeOff size={20} /><span><b>Anonymous.</b> Name and contact details are optional and are never shown to other road users.</span></li>
            <li><UserCheck size={20} /><span><b>Checked by a person.</b> An administrator reviews your report and either confirms or rejects it.</span></li>
            <li><ShieldCheck size={20} /><span><b>Then shared.</b> Confirmed incidents appear on the overview and can trigger an alert.</span></li>
          </ul>
        </aside>
      </div>
    </div>
  );
}
