import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../lib/api';

const NetworkContext = createContext(null);
export const useNetwork = () => useContext(NetworkContext);

export function NetworkProvider({ children }) {
  const [state, setState] = useState({ loading: true, error: null, data: null });

  const load = () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    api.network()
      .then((data) => setState({ loading: false, error: null, data }))
      .catch((error) => setState({ loading: false, error, data: null }));
  };
  useEffect(load, []);

  const value = useMemo(() => ({
    loading: state.loading,
    error: state.error,
    intersections: state.data?.intersections ?? [],
    roads: state.data?.roads ?? [],
    thresholds: state.data?.thresholds ?? { free_flow_max: 2, moderate_max: 7, heavy_max: 15, alert: 10 },
    retry: load,
  }), [state]);
  return <NetworkContext.Provider value={value}>{children}</NetworkContext.Provider>;
}
