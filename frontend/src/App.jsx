import { Suspense, lazy } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NetworkProvider } from './context/NetworkContext';
import { ToastProvider } from './context/ToastContext';
import Layout from './components/Layout';
import { Skeleton } from './components/ui';
import AdminDashboard from './pages/AdminDashboard';
import AdminLogin from './pages/AdminLogin';
import NotFound from './pages/NotFound';
import Overview from './pages/Overview';
import Report from './pages/Report';

// The chart pages load on demand, which keeps the first page fast
const History = lazy(() => import('./pages/History'));
const Journey = lazy(() => import('./pages/Journey'));
const wait = (el) => <Suspense fallback={<Skeleton h={300} className="card" />}>{el}</Suspense>;

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <NetworkProvider>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<Overview />} />
                <Route path="journey" element={wait(<Journey />)} />
                <Route path="report" element={<Report />} />
                <Route path="history" element={wait(<History />)} />
                <Route path="admin" element={<AdminDashboard />} />
                <Route path="admin/login" element={<AdminLogin />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </NetworkProvider>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
