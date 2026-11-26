import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight, Clock, RefreshCw, ShieldAlert, TriangleAlert, Waypoints } from 'lucide-react';
import { api } from '../lib/api';
import { LEVELS, REFRESH_MS } from '../lib/constants';
import { formatTime, newestTimestamp, timeAgo } from '../lib/format';
import { useDocumentTitle, useLoader } from '../lib/hooks';
import AlertBanners from '../components/AlertBanners';
import IncidentCard from '../components/IncidentCard';
import NetworkMap, { MapLegend } from '../components/NetworkMap';
import RoadCard from '../components/RoadCard';
import { EmptyState, ErrorState, Skeleton, Spinner } from '../components/ui';

function HeroSkeleton() {
  return <div className="hero"><Skeleton h={28} w="40%" style={{ opacity: 0.3 }} /><Skeleton h={54} w="60%" style={{ marginTop: 18, opacity: 0.3 }} /></div>;
}

export default function Overview() {
  useDocumentTitle('Traffic overview');
  const { data, error, loading, reload } = useLoader((o) => api.overview(o), [], { intervalMs: REFRESH_MS });
  const [busy, setBusy] = useState(false);

  const refresh = async () => { setBusy(true); await reload(); setBusy(false); };

  if (loading && !data) {
    return <div className="stack"><HeroSkeleton /><Skeleton h={380} className="card" /><div className="grid-3"><Skeleton h={170} /><Skeleton h={170} /><Skeleton h={170} /></div></div>;
  }
  if (error && !data) return <ErrorState error={error} onRetry={reload} />;

  const level = data.worst_level;
  const info = LEVELS[level];
  const updated = newestTimestamp(data.roads);
  const longest = data.roads.reduce((m, r) => Math.max(m, r.delay_minutes), 0);
  const roadStates = Object.fromEntries(data.roads.map((r) => [r.road_id, r]));

  return (
    <div className="fade-in">
      <AlertBanners alerts={data.alerts} />

      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-grid">
          <div>
            <div className="eyebrow">Nyabugogo terminal and nearby intersections</div>
            <h1 id="hero-title">Traffic right now</h1>
            <div className="hero-status">
              <span className={`hero-pill ${level || 'NONE'}`}>
                <i className="pulse" />
                <span className="label">{info ? `${info.label} traffic` : 'No data yet'}</span>
              </span>
            </div>
            <p className="lead">{info ? `Worst conditions on the network: ${info.text.toLowerCase()}` : 'Traffic information is not available at the moment. Please check again shortly.'}</p>
            <div className="hero-meta">
              {updated && <span className="row" style={{ gap: 6 }}><Clock size={15} /> Data from {formatTime(updated)} ({timeAgo(updated)})</span>}
              <button type="button" className="btn btn-light btn-sm" onClick={refresh} disabled={busy}>
                {busy ? <Spinner size={16} /> : <RefreshCw size={16} />} Refresh
              </button>
            </div>
            {error && <p className="meta" style={{ color: '#ffd0d8', marginTop: 10 }}>Could not refresh: {error.message} Showing the last data we have.</p>}
          </div>
          <div className="hero-stats">
            <div className="hero-stat"><b>{data.roads.length}</b><span>Roads monitored</span></div>
            <div className="hero-stat"><b>{longest === 0 ? '0' : `+${longest}`}<small style={{ fontSize: '0.9rem' }}> min</small></b><span>Longest delay</span></div>
            <div className="hero-stat"><b>{data.incidents.length}</b><span>Active incidents</span></div>
            <div className="hero-stat"><b>{data.alerts.length}</b><span>Active alerts</span></div>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="map-title">
        <div className="section-head">
          <div><h2 id="map-title">Network map</h2><p>Hover or tap a road for details. Delay is the extra time on top of free-flow travel.</p></div>
        </div>
        <div className="card map-card">
          <NetworkMap roadStates={roadStates} />
          <MapLegend />
        </div>
      </section>

      <section className="section" aria-labelledby="roads-title">
        <div className="section-head"><h2 id="roads-title">Traffic conditions</h2><p>Updates automatically every 30 seconds</p></div>
        {data.roads.length ? (
          <div className="grid-3">{data.roads.map((r) => <RoadCard key={r.road_id} road={r} />)}</div>
        ) : (
          <div className="card"><EmptyState icon={Activity} title="No traffic readings yet">Readings appear here as soon as the system records them.</EmptyState></div>
        )}
      </section>

      <section className="section" aria-labelledby="incidents-title">
        <div className="section-head"><h2 id="incidents-title">Active incidents</h2><p>Only incidents confirmed by an administrator are shown</p></div>
        {data.incidents.length ? (
          <ul className="incident-list">{data.incidents.map((i) => <IncidentCard key={i.id} incident={i} />)}</ul>
        ) : (
          <div className="card"><EmptyState icon={ShieldAlert} title="No active incidents">Nothing has been reported and confirmed right now. Safe travels.</EmptyState></div>
        )}
      </section>

      <section className="section">
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
          <Link to="/journey" className="card card-pad hover" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="row spread"><Waypoints size={26} color="var(--blue-600)" /><ArrowRight size={20} color="var(--blue-600)" /></div>
            <h3 style={{ marginTop: 12 }}>Plan a journey</h3>
            <p style={{ color: 'var(--text-soft)', marginTop: 4 }}>Enter where you are going and see the delay and the fastest route.</p>
          </Link>
          <Link to="/report" className="card card-pad hover" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="row spread"><TriangleAlert size={26} color="var(--heavy)" /><ArrowRight size={20} color="var(--blue-600)" /></div>
            <h3 style={{ marginTop: 12 }}>See something? Report it</h3>
            <p style={{ color: 'var(--text-soft)', marginTop: 4 }}>No account needed. An administrator reviews every report.</p>
          </Link>
        </div>
      </section>
    </div>
  );
}
