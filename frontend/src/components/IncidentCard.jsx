import { INCIDENT_TYPES } from '../lib/constants';
import { timeAgo } from '../lib/format';

export default function IncidentCard({ incident }) {
  const meta = INCIDENT_TYPES[incident.type] || INCIDENT_TYPES.OTHER;
  const Icon = meta.icon;
  const where = incident.intersection_name ? `${incident.road_name}, near ${incident.intersection_name}` : incident.road_name;
  return (
    <li className={`card incident ${incident.type}`}>
      <div className="type-ico"><Icon size={22} /></div>
      <div>
        <h3>{meta.label} <span style={{ fontWeight: 500, color: 'var(--text-soft)' }}>on {where}</span></h3>
        <p className="desc">{incident.description}</p>
        <p className="meta">
          Confirmed {timeAgo(incident.verified_at || incident.reported_at)}
          {incident.is_simulated && <span className="tag sim">Simulated</span>}
        </p>
      </div>
    </li>
  );
}
