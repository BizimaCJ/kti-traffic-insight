import { useEffect, useMemo, useState } from 'react';
import { ArrowLeftRight, CircleCheck, Clock, Flag, Info, Navigation, Route as RouteIcon, TrendingUp } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useNetwork } from '../context/NetworkContext';
import { api } from '../lib/api';
import { formatTime, km, minutes, nextOccurrenceIso, nowAsTimeInput } from '../lib/format';
import { useDocumentTitle, useLoader } from '../lib/hooks';
import { LevelBadge } from '../components/LevelBadge';
import NetworkMap, { MapLegend } from '../components/NetworkMap';
import { EmptyState, ErrorState, Field, Segmented, Spinner } from '../components/ui';

function Verdict({ result }) {
  const main = result.routes.find((r) => r.id === result.main_route_id);
  const best = result.routes.find((r) => r.id === result.recommended_route_id);
  let title; let text;
  if (!result.routes.length) { title = 'No route found'; text = result.message; }
  else if (!best) { title = 'Delay information is not available yet'; text = 'Routes are shown below. Delays will appear when the system has recorded traffic readings.'; }
  else if (best.id === main.id) { title = `${main.name} is the fastest route`; text = `About ${Math.round(main.total_minutes)} minutes, including ${minutes(main.delay_minutes).replace('+', '')} of delay.`; }
  else { title = `Take the route ${best.name.toLowerCase()}`; text = `About ${Math.round(result.time_saved_minutes)} minutes faster than the direct route right now (${Math.round(best.total_minutes)} min instead of ${Math.round(main.total_minutes)} min).`; }
  return (
    <div className="verdict">
      <div className="ico">{best && best.id !== main?.id ? <TrendingUp size={26} /> : <CircleCheck size={26} />}</div>
      <div><h2>{title}</h2><p>{text}</p></div>
    </div>
  );
}

function RouteCard({ route, selected, onSelect }) {
  return (
    <button type="button" className={`route-card ${route.is_recommended ? 'recommended' : ''} ${selected ? 'selected' : ''}`} onClick={() => onSelect(route.id)} aria-pressed={selected}>
      <div className="route-head">
        <div>
          <h3>{route.name}</h3>
          <div className="row" style={{ marginTop: 6, gap: 8 }}>
            {route.is_main && <span className="tag">Shortest distance</span>}
            <LevelBadge level={route.level} />
          </div>
        </div>
        <div className="route-total"><b>{route.total_minutes === null ? 'n/a' : Math.round(route.total_minutes)}</b><span>min total</span></div>
      </div>
      <div className="path-chips">
        {route.intersections.map((name, i) => (<span key={`${name}${i}`} className="row" style={{ gap: 6 }}>{i > 0 && <span aria-hidden="true">&rarr;</span>}<span className="chip">{name}</span></span>))}
      </div>
      <div className="route-facts">
        <span><b>{km(route.distance_km)}</b> distance</span>
        <span><b>{Math.round(route.free_flow_minutes)} min</b> without delay</span>
        <span><b>{minutes(route.delay_minutes)}</b> delay</span>
      </div>
      <ul className="segments">
        {route.segments.map((s) => (
          <li key={s.road_id}><span>{s.road_name}</span><span className="row" style={{ gap: 8 }}><span style={{ color: 'var(--muted)' }}>{minutes(s.delay_minutes)}</span><LevelBadge level={s.level} /></span></li>
        ))}
      </ul>
    </button>
  );
}

export default function Journey() {
  useDocumentTitle('Plan a journey');
  const { intersections, loading: netLoading, error: netError, retry } = useNetwork();
  const overview = useLoader((o) => api.overview(o), []);
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [mode, setMode] = useState('now');
  const [time, setTime] = useState(nowAsTimeInput(30));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    if (intersections.length && !origin) {
      const terminal = intersections.find((n) => n.node_type === 'TERMINAL') || intersections[0];
      setOrigin(String(terminal.id));
      setDestination(String((intersections.find((n) => n.id !== terminal.id) || intersections[0]).id));
    }
  }, [intersections, origin]);

  const roadStates = useMemo(() => Object.fromEntries((overview.data?.roads || []).map((r) => [r.road_id, r])), [overview.data]);
  const selected = result?.routes.find((r) => r.id === selectedId) || null;
  const highlight = useMemo(() => (selected ? new Set(selected.segments.map((s) => s.road_id)) : null), [selected]);

  const swap = () => { setOrigin(destination); setDestination(origin); };

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    if (origin === destination) { setError({ message: 'Choose a destination that is different from the origin.' }); return; }
    setBusy(true);
    try {
      const body = { origin: Number(origin), destination: Number(destination) };
      if (mode === 'later') body.departure_time = nextOccurrenceIso(time);
      const data = await api.planJourney(body);
      setResult(data);
      setSelectedId(data.recommended_route_id || data.main_route_id);
      overview.reload();
    } catch (err) {
      setError({ message: err.fields ? Object.values(err.fields)[0] : err.message });
    } finally { setBusy(false); }
  };

  if (netLoading) return <div className="card card-pad"><Spinner /> Loading the road network...</div>;
  if (netError) return <ErrorState error={netError} onRetry={retry} />;

  const hasHistory = result?.timeline?.some((p) => p.basis === 'history');
  const timelineData = result?.timeline?.map((p) => ({ label: p.offset_minutes === 0 ? 'Leave then' : `+${p.offset_minutes} min`, delay: p.delay_minutes, at: formatTime(p.depart_at) })) || [];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="eyebrow">Journey planner</div>
        <h1>Where are you going?</h1>
        <p>Enter your origin and destination to see the estimated delay and alternative routes inside the Nyabugogo area.</p>
      </div>

      <form className="card card-pad-lg journey-form" onSubmit={submit} noValidate>
        <div className="od-row">
          <Field label="From" htmlFor="origin">
            <select id="origin" className="select" value={origin} onChange={(e) => setOrigin(e.target.value)}>
              {intersections.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}
            </select>
          </Field>
          <button type="button" className="icon-btn swap" onClick={swap} aria-label="Swap origin and destination" style={{ marginBottom: 3 }}><ArrowLeftRight size={18} /></button>
          <Field label="To" htmlFor="destination">
            <select id="destination" className="select" value={destination} onChange={(e) => setDestination(e.target.value)}>
              {intersections.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}
            </select>
          </Field>
        </div>
        <div className="row" style={{ gap: 16, alignItems: 'end' }}>
          <Field label="Departure">
            <Segmented label="Departure" value={mode} onChange={setMode} options={[{ value: 'now', label: 'Leave now' }, { value: 'later', label: 'Choose a time' }]} />
          </Field>
          {mode === 'later' && (
            <Field label="Time" htmlFor="time"><input id="time" type="time" className="input" value={time} onChange={(e) => setTime(e.target.value)} style={{ width: 150 }} required /></Field>
          )}
          <button type="submit" className="btn btn-primary" disabled={busy || !origin} style={{ marginLeft: 'auto' }}>
            {busy ? <Spinner /> : <Navigation size={18} />} Find routes
          </button>
        </div>
        {error && <div className="error-card" role="alert" style={{ padding: '12px 16px' }}>{error.message}</div>}
      </form>

      {!result && !busy && (
        <div className="card section"><EmptyState icon={RouteIcon} title="Your routes will appear here">Choose two places and press Find routes.</EmptyState></div>
      )}

      {result && (
        <div className="section stack">
          <Verdict result={result} />
          {result.message && result.routes.length > 0 && <div className="notice"><Info size={18} style={{ flex: 'none' }} /> {result.message}</div>}
          {result.routes.length > 0 && (
            <div className="results-grid">
              <div className="stack">
                {result.routes.map((r) => <RouteCard key={r.id} route={r} selected={r.id === selectedId} onSelect={setSelectedId} />)}
              </div>
              <div className="stack" style={{ position: 'sticky', top: 90 }}>
                <div className="card map-card">
                  <NetworkMap roadStates={roadStates} routeNodeIds={selected?.intersection_ids || []} highlightRoadIds={highlight} originId={result.origin.id} destinationId={result.destination.id} />
                  <MapLegend />
                </div>
                <div className="card card-pad">
                  <div className="row" style={{ gap: 8, marginBottom: 6 }}><Clock size={18} color="var(--blue-600)" /><h3>If you leave later</h3></div>
                  {hasHistory ? (
                    <div style={{ width: '100%', height: 190 }}>
                      <ResponsiveContainer>
                        <BarChart data={timelineData} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dde7f5" />
                          <XAxis dataKey="label" tick={{ fontSize: 12 }} tickLine={false} />
                          <YAxis tick={{ fontSize: 12 }} tickLine={false} unit=" min" width={56} allowDecimals={false} />
                          <Tooltip formatter={(v) => [`${v} min delay`, 'Expected']} labelFormatter={(l, p) => `${l}${p?.[0] ? ` (${p[0].payload.at})` : ''}`} />
                          <Bar dataKey="delay" radius={[8, 8, 0, 0]}>
                            {timelineData.map((d, i) => <Cell key={i} fill="#3b8bf5" />)}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-soft)', fontSize: '0.9rem' }}>
                      Estimates for later departure times use past readings at the same hour. They will appear here once the system has recorded enough history.
                    </p>
                  )}
                  <p className="meta" style={{ marginTop: 8 }}><Flag size={14} /> Delay shown for the direct route. {result.departure.is_now ? (hasHistory ? 'Now uses current readings; later bars use past readings at those hours.' : 'Based on current conditions.') : result.departure.basis === 'history' ? 'Based on past readings at that hour.' : 'Based on current conditions (no history for that hour yet).'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
