import { LEVELS } from '../lib/constants';

export function LevelBadge({ level }) {
  const info = LEVELS[level];
  return (
    <span className={`badge level-${level || 'NONE'}`}>
      <i className="dot" />
      {info ? info.label : 'No data'}
    </span>
  );
}

// Four bars: the number of filled bars shows the level, so colour is never the only signal.
export function LevelMeter({ level }) {
  const rank = LEVELS[level]?.rank ?? 0;
  return (
    <span className={`meter ${level || ''}`} role="img" aria-label={`Congestion ${rank} of 4`}>
      {[1, 2, 3, 4].map((i) => <i key={i} className={i <= rank ? 'on' : ''} />)}
    </span>
  );
}
