import { useMemo, useState } from 'react';
import { Activity, Gauge, History as HistoryIcon, TrendingUp } from 'lucide-react';
import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useNetwork } from '../context/NetworkContext';
import { api } from '../lib/api';
import { formatDateTime, formatDayHour, formatTime, minutes } from '../lib/format';
import { useDocumentTitle, useLoader } from '../lib/hooks';
import { LevelBadge } from '../components/LevelBadge';
import { EmptyState, ErrorState, Field, Segmented, Skeleton } from '../components/ui';

const RANGES = [{ value: '24h', label: 'Last 24 hours' }, { value: '7d', label: '7 days' }, { value: '30d', label: '30 days' }];

export default function History() {
  useDocumentTitle('Traffic history');
  const { roads, thresholds } = useNetwork();
  const [road, setRoad] = useState('all');
  const [range, setRange] = useState('24h');
  const { data, error, loading, reloadWithSpinner } = useLoader((o) => api.history(road, range, o), [road, range]);

  const tick = (iso) => (range === '24h' ? formatTime(iso) : range === '7d' ? formatDayHour(iso) : formatDateTime(iso).split(',')[0]);
  const stats = useMemo(() => {
    if (!data || !data.points.length) return null;
    const avg = data.points.reduce((s, p) => s + p.avg_delay, 0) / data.points.length;
    const peak = data.points.reduce((m, p) => (p.max_delay > m.max_delay ? p : m), data.points[0]);
    return { avg: avg.toFixed(1), peak: peak.max_delay, peakAt: peak.time };
  }, [data]);

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="eyebrow">History</div>
        <h1>How traffic has behaved</h1>
        <p>Stored readings for the Nyabugogo area. Use this to see when delays are usually worst and pick a better time to travel.</p>
      </div>

      <div className="card card-pad row spread" style={{ marginBottom: 18 }}>
        <Field label="Road" htmlFor="hist-road">
          <select id="hist-road" className="select" style={{ minWidth: 260 }} value={road} onChange={(e) => setRoad(e.target.value)}>
            <option value="all">All roads (average)</option>
            {roads.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </Field>
        <Field label="Period"><Segmented label="Period" value={range} onChange={setRange} options={RANGES} /></Field>
      </div>

      {error && !data && <ErrorState error={error} onRetry={reloadWithSpinner} />}
      {loading && !data && <Skeleton h={360} className="card" />}

      {data && (data.count === 0 ? (
        <div className="card"><EmptyState icon={HistoryIcon} title="No history for this selection yet">Readings are saved automatically. Try a longer period or another road.</EmptyState></div>
      ) : (
        <>
          <div className="stat-row">
            <div className="card stat-card"><Gauge size={20} color="var(--blue-600)" /><b>{stats?.avg} min</b><span>Average delay</span></div>
            <div className="card stat-card"><TrendingUp size={20} color="var(--heavy)" /><b>+{stats?.peak} min</b><span>Worst delay ({stats && tick(stats.peakAt)})</span></div>
            <div className="card stat-card"><Activity size={20} color="var(--blue-600)" /><b>{data.count.toLocaleString()}</b><span>Readings stored</span></div>
          </div>

          <div className="card chart-card">
            <div className="row spread" style={{ marginBottom: 8 }}>
              <h3>Delay over time {data.road ? `- ${data.road.name}` : '- all roads'}</h3>
              <span className="meta"><span className="tag sim">Simulated</span> hourly average and worst reading</span>
            </div>
            <div className="chart-box">
              <ResponsiveContainer>
                <ComposedChart data={data.points} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="avgFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b8bf5" stopOpacity="0.45" /><stop offset="100%" stopColor="#3b8bf5" stopOpacity="0.02" /></linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dde7f5" />
                  <XAxis dataKey="time" tickFormatter={tick} tick={{ fontSize: 12 }} tickLine={false} minTickGap={36} />
                  <YAxis tick={{ fontSize: 12 }} tickLine={false} unit=" min" width={60} allowDecimals={false} />
                  <Tooltip labelFormatter={(l) => formatDateTime(l)} formatter={(v, name) => [`${v} min`, name === 'avg_delay' ? 'Average delay' : 'Worst delay']} />
                  <ReferenceLine y={thresholds.alert} stroke="#c81e3a" strokeDasharray="5 5" label={{ value: `Alert at ${thresholds.alert} min`, position: 'insideTopRight', fill: '#c81e3a', fontSize: 12 }} />
                  <Area type="monotone" dataKey="avg_delay" stroke="#1d6fe0" strokeWidth={3} fill="url(#avgFill)" />
                  <Line type="monotone" dataKey="max_delay" stroke="#0a2540" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <section className="section">
            <div className="section-head"><h2>Latest readings</h2></div>
            <div className="card table-wrap">
              <table className="data">
                <thead><tr><th>Time</th><th>Road</th><th>Level</th><th>Delay</th><th>Speed</th></tr></thead>
                <tbody>
                  {data.recent.map((r, i) => (
                    <tr key={`${r.road_id}-${r.recorded_at}-${i}`}>
                      <td>{formatDateTime(r.recorded_at)}</td><td>{r.road_name}</td><td><LevelBadge level={r.level} /></td>
                      <td>{minutes(r.delay_minutes)}</td><td>{Math.round(r.average_speed_kmh)} km/h</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ))}
    </div>
  );
}
