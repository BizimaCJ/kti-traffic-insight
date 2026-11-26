import { useEffect } from 'react';
import { CircleAlert, Loader2, RefreshCw, X } from 'lucide-react';

export const Skeleton = ({ h = 20, w = '100%', className = '', style }) => (
  <div className={`skeleton ${className}`} style={{ height: h, width: w, ...style }} aria-hidden="true" />
);

export const Spinner = ({ size = 18 }) => <Loader2 size={size} className="spin" aria-hidden="true" />;

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="empty">
      {Icon && <div className="ico"><Icon size={26} /></div>}
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="error-card" role="alert">
      <CircleAlert size={26} style={{ flex: 'none' }} />
      <div style={{ flex: 1 }}>
        <strong>We could not load this.</strong>
        <p>{error?.message || 'Something went wrong. Please try again.'}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn btn-danger-soft btn-sm" onClick={onRetry}>
          <RefreshCw size={16} /> Try again
        </button>
      )}
    </div>
  );
}

export function Field({ label, hint, error, htmlFor, children, counter }) {
  return (
    <div className="field">
      {label && <label htmlFor={htmlFor}>{label}</label>}
      {children}
      {counter}
      {hint && !error && <span className="hint">{hint}</span>}
      {error && <span className="error-text" role="alert"><CircleAlert size={14} /> {error}</span>}
    </div>
  );
}

export function Modal({ title, children, onClose, actions }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="row spread">
          <h2>{title}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        {children}
        {actions && <div className="actions">{actions}</div>}
      </div>
    </div>
  );
}

export function Segmented({ options, value, onChange, label }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} type="button" className={value === o.value ? 'active' : ''} aria-pressed={value === o.value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}
