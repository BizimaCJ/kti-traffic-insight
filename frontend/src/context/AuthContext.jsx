import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, setSessionExpiredHandler } from '../lib/api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [state, setState] = useState({ ready: false, user: null, timeoutMinutes: 15, expired: false });

  useEffect(() => {
    let alive = true;
    api.session()
      .then((s) => alive && setState({ ready: true, user: s.authenticated ? s.user : null, timeoutMinutes: s.session_timeout_minutes, expired: false }))
      .catch(() => alive && setState((s) => ({ ...s, ready: true })));
    return () => { alive = false; };
  }, []);

  // Any administrator request answered with 401 means the session ended (15 minutes without activity)
  useEffect(() => {
    setSessionExpiredHandler(() => setState((s) => (s.user ? { ...s, user: null, expired: true } : s)));
  }, []);

  const login = useCallback(async (username, password) => {
    const result = await api.login(username, password);
    setState({ ready: true, user: result.user, timeoutMinutes: result.session_timeout_minutes, expired: false });
  }, []);

  const logout = useCallback(async () => {
    try { await api.logout(); } catch { /* already logged out */ }
    setState((s) => ({ ...s, user: null, expired: false }));
  }, []);

  const value = useMemo(() => ({ ...state, login, logout }), [state, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
