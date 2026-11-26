import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn, Route, TimerReset } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDocumentTitle } from '../lib/hooks';
import { Field, Spinner } from '../components/ui';

export default function AdminLogin() {
  useDocumentTitle('Administrator login');
  const { user, login, expired, timeoutMinutes, ready } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (ready && user) return <Navigate to="/admin" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password) { setError('Enter your username and password.'); return; }
    setBusy(true);
    try {
      await login(username.trim(), password);
      navigate('/admin', { replace: true });
    } catch (err) {
      setError(err.message);
      setPassword('');
    } finally { setBusy(false); }
  };

  return (
    <div className="login-wrap fade-in">
      <form className="card login-card form-grid" onSubmit={submit} noValidate>
        <div>
          <span className="brand-mark"><Route size={28} /></span>
          <h1 style={{ fontSize: '1.7rem' }}>Administrator login</h1>
          <p style={{ color: 'var(--text-soft)', marginTop: 6 }}>Sign in to review reports, manage alerts and see the audit log.</p>
        </div>
        {expired && <div className="notice warn" role="alert"><TimerReset size={18} style={{ flex: 'none' }} /> Your session ended because of inactivity. Please sign in again.</div>}
        <Field label="Username" htmlFor="username">
          <input id="username" className="input" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" autoFocus />
        </Field>
        <Field label="Password" htmlFor="password">
          <div style={{ position: 'relative' }}>
            <input id="password" className="input" type={show ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" style={{ paddingRight: 52 }} />
            <button type="button" className="icon-btn" onClick={() => setShow(!show)} aria-label={show ? 'Hide password' : 'Show password'} style={{ position: 'absolute', right: 3, top: 3, width: 40, height: 40, border: 0 }}>
              {show ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </Field>
        {error && <div className="error-card" role="alert" style={{ padding: '12px 16px' }}>{error}</div>}
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>{busy ? <Spinner /> : <LogIn size={18} />} Sign in</button>
        <p className="meta" style={{ justifyContent: 'center' }}>Administrator accounts are created by the system owner. You are signed out after {timeoutMinutes} minutes of inactivity.</p>
      </form>
    </div>
  );
}
