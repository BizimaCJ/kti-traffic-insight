import { useState } from 'react';
import { ChevronLeft, ChevronRight, ScrollText } from 'lucide-react';
import { api } from '../../lib/api';
import { formatDateTime } from '../../lib/format';
import { useLoader } from '../../lib/hooks';
import { EmptyState, ErrorState, Skeleton } from '../../components/ui';

export default function AuditPanel() {
  const [page, setPage] = useState(1);
  const { data, error, loading, reloadWithSpinner } = useLoader((o) => api.auditLog(page, o), [page]);

  if (error && !data) return <ErrorState error={error} onRetry={reloadWithSpinner} />;
  if (loading && !data) return <Skeleton h={320} className="card" />;
  if (!data.results.length) return <div className="card"><EmptyState icon={ScrollText} title="The audit log is empty">Every administrator action is recorded here with who did it and when.</EmptyState></div>;

  return (
    <div>
      <div className="card table-wrap">
        <table className="data">
          <thead><tr><th>When</th><th>Administrator</th><th>Action</th><th>Target</th><th>Details</th></tr></thead>
          <tbody>
            {data.results.map((e) => (
              <tr key={e.id}>
                <td style={{ whiteSpace: 'nowrap' }}>{formatDateTime(e.timestamp)}</td>
                <td>{e.admin_name}<div className="meta">@{e.admin_username}</div></td>
                <td><span className="tag">{e.action_label}</span></td>
                <td>{e.target_type ? `${e.target_type}${e.target_id ? ` #${e.target_id}` : ''}` : '-'}</td>
                <td style={{ color: 'var(--text-soft)' }}>{e.details || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="pager">
        <span>{data.count} entries - page {data.page} of {data.pages}</span>
        <div className="row">
          <button type="button" className="btn btn-ghost btn-sm" disabled={data.page <= 1} onClick={() => setPage(data.page - 1)}><ChevronLeft size={16} /> Newer</button>
          <button type="button" className="btn btn-ghost btn-sm" disabled={data.page >= data.pages} onClick={() => setPage(data.page + 1)}>Older <ChevronRight size={16} /></button>
        </div>
      </div>
    </div>
  );
}
