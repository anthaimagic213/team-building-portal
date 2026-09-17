import {
  Navigate,
  Outlet,
  useLocation,
} from 'react-router-dom';

import {
  useAuth,
} from '@/hooks/useAuth';

export default function AdminRoute() {
  const location = useLocation();

  const {
    isAuthenticated,
    hasAnyRole,
  } = useAuth();

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location,
        }}
      />
    );
  }

  const isAdmin = hasAnyRole([
    'ADMIN',
    'SUPER_ADMIN',
  ]);

  if (!isAdmin) {
    return (
      <Navigate
        to="/journey"
        replace
      />
    );
  }

  return <Outlet />;
}
