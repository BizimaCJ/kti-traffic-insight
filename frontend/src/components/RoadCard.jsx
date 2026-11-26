import { formatTime, minutes } from '../lib/format';
import { LevelBadge, LevelMeter } from './LevelBadge';

export default function RoadCard({ road }) {
  return (
    <article className={`card road-card hover ${road.level}`}>
      <div className="row spread">
        <LevelBadge level={road.level} />
        <LevelMeter level={road.level} />
      </div>
      <h3>{road.road_name}</h3>
      <div className="metrics">
        <div className="metric"><b>{minutes(road.delay_minutes)}</b><span>Estimated delay</span></div>
        <div className="metric"><b>{Math.round(road.average_speed_kmh)}<small style={{ fontSize: '0.9rem', marginLeft: 3 }}>km/h</small></b><span>Average speed</span></div>
      </div>
      <p className="meta">
        Updated {formatTime(road.recorded_at)}
        {road.is_simulated && <span className="tag sim">Simulated</span>}
      </p>
    </article>
  );
}
