import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom';

import ProtectedRoute from './ProtectedRoute';
import AdminRoute from './AdminRoute';
import RepresentativeRoute from './RepresentativeRoute';
import RootRedirect from './RootRedirect';

import AuthLayout from '@/layouts/AuthLayout';
import AppLayout from '@/layouts/AppLayout';
import AdminLayout from '@/layouts/AdminLayout';

import LoginPage from '@/pages/LoginPage';
import TermsPage from '@/pages/TermsPage';

import JourneyPage from '@/pages/user/JourneyPage';
import RegistrationPage from '@/pages/user/RegistrationPage';
import GalaPage from '@/pages/user/GalaPage';
import ProfilePage from '@/pages/ProfilePage';

import AdminDashboardPage from '@/pages/admin/AdminDashboardPage';
import EventsPage from '@/pages/admin/EventsPage';
import TeamsPage from '@/pages/admin/TeamsPage';
import UsersPage from '@/pages/admin/UsersPage';
import FlightsPage from '@/pages/admin/FlightsPage';
import VehiclesPage from '@/pages/admin/VehiclesPage';
import FlightAllocationPage from '@/pages/admin/FlightAllocationPage';
import VehicleAllocationPage from '@/pages/admin/VehicleAllocationPage';
import AllocationsPage from '@/pages/admin/AllocationsPage';
import HotelsPage from '@/pages/admin/HotelsPage';
import GalaAdminPage from '@/pages/admin/GalaAdminPage';
import NotificationsPage from '@/pages/admin/NotificationsPage';
import AuditLogsPage from '@/pages/admin/AuditLogsPage';

import NotFoundPage from '@/pages/NotFoundPage';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<AuthLayout />}>
        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          path="/terms"
          element={<TermsPage />}
        />
      </Route>

      {/* Authenticated user routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route
            path="/journey"
            element={<JourneyPage />}
          />

          <Route
            path="/registration"
            element={<RegistrationPage />}
          />

          <Route
            path="/profile"
            element={<ProfilePage />}
          />
        </Route>
      </Route>

      {/* Team representative routes */}
      <Route element={<RepresentativeRoute />}>
        <Route element={<AppLayout />}>
          <Route
            path="/gala/:eventId"
            element={<GalaPage />}
          />
        </Route>
      </Route>

      {/* Admin routes */}
      <Route element={<AdminRoute />}>
        <Route element={<AdminLayout />}>
          <Route
            path="/admin"
            element={<AdminDashboardPage />}
          />

          <Route
            path="/admin/events"
            element={<EventsPage />}
          />

          <Route
            path="/admin/teams"
            element={<TeamsPage />}
          />

          <Route
            path="/admin/users"
            element={<UsersPage />}
          />

          <Route
            path="/admin/flights"
            element={<FlightsPage />}
          />

          <Route
            path="/admin/vehicles"
            element={<VehiclesPage />}
          />

          <Route
            path="/admin/allocations"
            element={<AllocationsPage />}
          />

          <Route
            path="/admin/allocations/flights"
            element={<FlightAllocationPage />}
          />

          <Route
            path="/admin/allocations/vehicles"
            element={<VehicleAllocationPage />}
          />

          <Route
            path="/admin/hotels"
            element={<HotelsPage />}
          />

          <Route
            path="/admin/gala"
            element={<GalaAdminPage />}
          />

          <Route
            path="/admin/notifications"
            element={<NotificationsPage />}
          />

          <Route
            path="/admin/audit-logs"
            element={<AuditLogsPage />}
          />
        </Route>
      </Route>

      {/* Root redirect theo role */}
      <Route
        path="/"
        element={<RootRedirect />}
      />

      {/* 404 */}
      <Route
        path="*"
        element={<NotFoundPage />}
      />
    </Routes>
  );
}
