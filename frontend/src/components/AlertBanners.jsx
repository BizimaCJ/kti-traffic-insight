import { BellRing } from 'lucide-react';
import { timeAgo } from '../lib/format';

export default function AlertBanners({ alerts }) {
  if (!alerts?.length) return null;
  return (
    <div className="alert-stack" role="region" aria-label="Active traffic alerts">
      {alerts.map((a) => (
        <div className="alert-banner" key={a.id}>
          <div className="ico"><BellRing size={20} /></div>
          <div>
            <strong>{a.message}</strong>
            <small>{a.road_name ? `${a.road_name} - ` : ''}issued {timeAgo(a.published_at)}</small>
          </div>
        </div>
      ))}
    </div>
  );
}
