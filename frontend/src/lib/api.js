// Every network call lives here. Components never call fetch() directly.
export class ApiError extends Error {
  constructor(message, { status = 0, code = '', fields = null, retryAfter = 0 } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields; // { fieldName: "message" } for validation errors
    this.retryAfter = retryAfter;
  }
}

let onSessionExpired = () => {};
export const setSessionExpiredHandler = (fn) => { onSessionExpired = fn; };

function getCookie(name) {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : '';
}

function firstMessage(value) {
  return Array.isArray(value) ? String(value[0]) : String(value);
}

async function request(method, path, body, { signal } = {}) {
  const headers = { Accept: 'application/json' };
  const init = { method, headers, credentials: 'same-origin', signal };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  if (method !== 'GET') {
    const token = getCookie('csrftoken');
    if (token) headers['X-CSRFToken'] = token;
  }
  let response;
  try {
    response = await fetch(path, init);
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Cannot reach the server. Check your connection and try again.', { code: 'network' });
  }
  const text = await response.text();
  let data = null;
  if (text) { try { data = JSON.parse(text); } catch { /* not JSON */ } }
  if (response.ok) return data;

  if (response.status === 401 && path.startsWith('/api/admin')) onSessionExpired();
  let message = 'Something went wrong. Please try again.';
  let fields = null;
  if (data && typeof data.detail === 'string') {
    message = data.detail;
  } else if (data && typeof data === 'object') {
    fields = Object.fromEntries(Object.entries(data).map(([k, v]) => [k, firstMessage(v)]));
    message = 'Please check the highlighted fields.';
  }
  throw new ApiError(message, { status: response.status, code: data?.code || '', fields, retryAfter: data?.retry_after || 0 });
}

const get = (path, opts) => request('GET', path, undefined, opts);
const post = (path, body, opts) => request('POST', path, body ?? {}, opts);

export const api = {
  // public
  overview: (opts) => get('/api/overview', opts),
  network: (opts) => get('/api/network', opts),
  history: (road, range, opts) => get(`/api/traffic/history?road=${road}&range=${range}`, opts),
  planJourney: (body) => post('/api/journeys', body),
  reportIncident: (body) => post('/api/incidents/report', body),
  // auth
  session: (opts) => get('/api/auth/session', opts),
  login: (username, password) => post('/api/auth/login', { username, password }),
  logout: () => post('/api/auth/logout'),
  // administrator
  adminIncidents: (status, opts) => get(`/api/admin/incidents${status ? `?status=${status}` : ''}`, opts),
  incidentAction: (id, action, body) => post(`/api/admin/incidents/${id}/${action}`, body),
  adminAlerts: (opts) => get('/api/admin/alerts', opts),
  publishAlert: (message, road) => post('/api/admin/alerts', { message, road: road || null }),
  withdrawAlert: (id) => post(`/api/admin/alerts/${id}/withdraw`),
  auditLog: (page, opts) => get(`/api/admin/audit-log?page=${page}&page_size=15`, opts),
};
