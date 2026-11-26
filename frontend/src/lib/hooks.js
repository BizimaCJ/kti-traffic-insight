import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Load data on mount, whenever `deps` change, and optionally on a timer.
 * Keeps the previous data while refreshing, so the screen never flashes empty.
 */
export function useLoader(loader, deps = [], { intervalMs = 0 } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: true, updatedAt: null });
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const controllerRef = useRef(null);

  const load = useCallback(async ({ silent = false } = {}) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    if (!silent) setState((s) => ({ ...s, loading: true }));
    try {
      const data = await loaderRef.current({ signal: controller.signal });
      setState({ data, error: null, loading: false, updatedAt: new Date() });
    } catch (error) {
      if (error.name === 'AbortError') return;
      setState((s) => ({ ...s, error, loading: false }));
    }
  }, []);

  useEffect(() => {
    load();
    let timer;
    if (intervalMs) {
      timer = setInterval(() => { if (!document.hidden) load({ silent: true }); }, intervalMs);
    }
    return () => { clearInterval(timer); controllerRef.current?.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load, intervalMs, ...deps]);

  return { ...state, reload: () => load({ silent: true }), reloadWithSpinner: () => load() };
}

export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} | Kigali Traffic Insight` : 'Kigali Traffic Insight';
  }, [title]);
}
