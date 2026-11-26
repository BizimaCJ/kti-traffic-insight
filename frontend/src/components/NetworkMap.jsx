import { useState } from 'react';
import { Bus } from 'lucide-react';
import { useNetwork } from '../context/NetworkContext';
import { LEVELS, LEVEL_ORDER } from '../lib/constants';
import { minutes } from '../lib/format';

const W = 1000;
const H = 560;
const place = (n) => ({ ...n, x: n.map_x * 10, y: n.map_y * 5.6 });

/**
 * Schematic map of the Nyabugogo network. Roads are coloured by traffic level, labelled with the
 * delay, and can show a planned route on top. (There is no map provider in the SRS, so this is a
 * clean schematic drawn from the intersections' positions.)
 */
export default function NetworkMap({ roadStates = {}, routeNodeIds = [], highlightRoadIds = null, originId = null, destinationId = null }) {
  const { intersections, roads } = useNetwork();
  const [hoverId, setHoverId] = useState(null);
  const nodes = Object.fromEntries(intersections.map((n) => [n.id, place(n)]));
  const routePoints = routeNodeIds.map((id) => nodes[id]).filter(Boolean).map((n) => `${n.x},${n.y}`).join(' ');

  const geometry = roads.map((road) => {
    const a = nodes[road.start_id];
    const b = nodes[road.end_id];
    return a && b ? { road, a, b, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2 } : null;
  }).filter(Boolean);
  const hover = geometry.find((g) => g.road.id === hoverId);

  return (
    <div className="map-wrap">
      <svg className="map-svg" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Schematic map of the Nyabugogo road network">
        <defs>
          <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.6" fill="#c9dbf5" /></pattern>
        </defs>
        <rect width={W} height={H} fill="url(#dots)" opacity="0.7" />
        <ellipse className="map-district" cx="200" cy="420" rx="210" ry="120" />
        <ellipse className="map-district" cx="760" cy="150" rx="230" ry="110" />
        <path className="map-river" d="M-20 520 C 220 470, 420 540, 640 500 S 940 470, 1030 505" />

        {geometry.map(({ road, a, b }) => <line key={`c${road.id}`} className="map-road-casing" x1={a.x} y1={a.y} x2={b.x} y2={b.y} strokeWidth="34" />)}

        {routePoints && <polyline className="map-route-glow" points={routePoints} strokeWidth="54" />}

        {geometry.map(({ road, a, b }) => {
          const state = roadStates[road.id];
          const level = state?.level || 'NONE';
          const dim = highlightRoadIds && !highlightRoadIds.has(road.id);
          const label = `${road.name}: ${state ? `${LEVELS[level].label}, ${minutes(state.delay_minutes)}` : 'no data yet'}`;
          return (
            <g key={road.id} tabIndex={0} role="img" aria-label={label}
               onMouseEnter={() => setHoverId(road.id)} onMouseLeave={() => setHoverId(null)}
               onFocus={() => setHoverId(road.id)} onBlur={() => setHoverId(null)}>
              <line className={`map-road ${level} ${dim ? 'dim' : ''}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} strokeWidth="22" />
              {level === 'BLOCKED' && <line className="map-road-dash" x1={a.x} y1={a.y} x2={b.x} y2={b.y} strokeWidth="5" />}
              <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="transparent" strokeWidth="56" />
            </g>
          );
        })}

        {routePoints && <polyline className="map-route-line" points={routePoints} strokeWidth="7" />}

        {geometry.map(({ road, mx, my }) => {
          const state = roadStates[road.id];
          if (!state) return null;
          return (
            <g key={`p${road.id}`} className={`map-pill ${state.level}`} transform={`translate(${mx} ${my})`}>
              <rect x="-58" y="-22" width="116" height="44" rx="22" />
              <text>{state.delay_minutes === 0 ? 'No delay' : `+${state.delay_minutes} min`}</text>
            </g>
          );
        })}

        {Object.values(nodes).map((n) => {
          const terminal = n.node_type === 'TERMINAL';
          const role = n.id === originId ? 'origin' : n.id === destinationId ? 'destination' : '';
          const r = terminal ? 36 : 24;
          const labelY = n.y < H / 2 ? n.y - r - 16 : n.y + r + 34;
          const labelX = Math.min(Math.max(n.x, 120), W - 120);
          return (
            <g key={n.id}>
              <circle className={`map-node-ring ${terminal ? 'terminal' : ''} ${role}`} cx={n.x} cy={n.y} r={r} />
              {terminal && <foreignObject x={n.x - 16} y={n.y - 16} width="32" height="32"><div style={{ color: '#fff', display: 'grid', placeItems: 'center', height: 32 }}><Bus size={26} /></div></foreignObject>}
              <text className="map-label" x={labelX} y={labelY} textAnchor="middle">{n.name}</text>
            </g>
          );
        })}
      </svg>

      {hover && (
        <div className="map-tip" style={{ left: `${(hover.mx / W) * 100}%`, top: `${(hover.my / H) * 100}%` }}>
          <strong>{hover.road.name}</strong>
          {roadStates[hover.road.id] ? (
            <>
              <div className="tip-row"><span>Level</span><b>{LEVELS[roadStates[hover.road.id].level].label}</b></div>
              <div className="tip-row"><span>Delay</span><b>{minutes(roadStates[hover.road.id].delay_minutes)}</b></div>
              <div className="tip-row"><span>Speed</span><b>{Math.round(roadStates[hover.road.id].average_speed_kmh)} km/h</b></div>
            </>
          ) : <div className="tip-row"><span>No data yet</span></div>}
        </div>
      )}
    </div>
  );
}

export function MapLegend() {
  const { thresholds: t } = useNetwork();
  const ranges = {
    FREE_FLOW: `0-${t.free_flow_max} min`,
    MODERATE: `${t.free_flow_max + 1}-${t.moderate_max} min`,
    HEAVY: `${t.moderate_max + 1}-${t.heavy_max} min`,
    BLOCKED: `${t.heavy_max + 1}+ min`,
  };
  return (
    <div className="legend" aria-label="Map legend">
      {LEVEL_ORDER.map((level) => <span key={level}><i className={level} /><b>{LEVELS[level].label}</b> {ranges[level]} extra delay</span>)}
    </div>
  );
}
