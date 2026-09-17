import { Navigate } from 'react-router-dom';

import { useAuth } from '@/hooks/useAuth';

export default function RootRedirect() {
  const {
    isAuthenticated,
    hasAnyRole,
  } = useAuth();

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (
    hasAnyRole([
      'ADMIN',
      'SUPER_ADMIN',
    ])
  ) {
    return (
      <Navigate
        to="/admin"
        replace
      />
    );
  }

  return (
    <Navigate
      to="/journey"
      replace
    />
  );
}
