const TIME_ZONE = 'Africa/Kigali';

const timeFmt = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: TIME_ZONE });
const dateTimeFmt = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: TIME_ZONE });
const dayHourFmt = new Intl.DateTimeFormat('en-GB', { weekday: 'short', hour: '2-digit', minute: '2-digit', timeZone: TIME_ZONE });

export const formatTime = (iso) => timeFmt.format(new Date(iso));
export const formatDateTime = (iso) => dateTimeFmt.format(new Date(iso));
export const formatDayHour = (iso) => dayHourFmt.format(new Date(iso));

export function timeAgo(iso, now = new Date()) {
  const minutes = Math.max(0, Math.round((now - new Date(iso)) / 60000));
  if (minutes < 1) return 'just now';
  if (minutes === 1) return '1 min ago';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? '1 day ago' : `${days} days ago`;
}

export const minutes = (n) => (n === null || n === undefined ? 'n/a' : n === 0 ? 'No delay' : `+${Math.round(n)} min`);
export const km = (n) => `${Number(n).toFixed(1)} km`;

export function newestTimestamp(roads) {
  return roads.reduce((latest, r) => (!latest || r.recorded_at > latest ? r.recorded_at : latest), null);
}

// "HH:MM" from a time input -> ISO string for the next time that clock time occurs
export function nextOccurrenceIso(hhmm) {
  const [h, m] = hhmm.split(':').map(Number);
  const d = new Date();
  d.setHours(h, m, 0, 0);
  if (d.getTime() < Date.now() - 10 * 60 * 1000) d.setDate(d.getDate() + 1);
  return d.toISOString();
}

export function nowAsTimeInput(offsetMinutes = 30) {
  const d = new Date(Date.now() + offsetMinutes * 60000);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}
