import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { adminApi } from '@/api';
import type {
  FlightResponse,
  VehicleResponse,
} from '@/types/resource';
import type { Team, UserListItem } from '@/types/user';
import type { EventResponse } from '@/types/event';

type ResourceType =
  | 'events'
  | 'teams'
  | 'users'
  | 'flights'
  | 'vehicles';

interface AdminResourcePageProps {
  type: ResourceType;
  title: string;
  description: string;
}

type ResourceRow =
  | EventResponse
  | Team
  | UserListItem
  | FlightResponse
  | VehicleResponse;

export default function AdminResourcePage({
  type,
  title,
  description,
}: AdminResourcePageProps) {
  const [search, setSearch] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<ResourceRow[]>([]);
  const [error, setError] = useState('');

  async function loadData() {
    setLoading(true);
    setError('');

    try {
      let data: ResourceRow[] = [];

      if (type === 'events') {
        data = await adminApi.listEvents({ search });
      }

      if (type === 'teams') {
        data = await adminApi.listTeams({ search });
      }

      if (type === 'users') {
        data = await adminApi.listUsers(undefined, { search });
      }

      if (type === 'flights') {
        data = await adminApi.listFlights({ search });
      }

      if (type === 'vehicles') {
        data = await adminApi.listVehicles({ search });
      }

      setRows(data);
    } catch {
      setError('Không thể tải dữ liệu. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }

  useMemo(() => {
    void loadData();
  }, [type, refreshKey]);

  function renderRow(row: ResourceRow) {
    if (type === 'events') {
      const event = row as EventResponse;

      return (
        <>
          <td className="px-4 py-3 font-medium">
            {event.event_name}
          </td>
          <td className="px-4 py-3">
            {event.location}
          </td>
          <td className="px-4 py-3">
            {event.status}
          </td>
          <td className="px-4 py-3">
            {event.total_participants}
          </td>
        </>
      );
    }

    if (type === 'teams') {
      const team = row as Team;

      return (
        <>
          <td className="px-4 py-3 font-medium">
            {team.team_name}
          </td>
          <td className="px-4 py-3">
            {team.event_id}
          </td>
        </>
      );
    }

    if (type === 'users') {
      const user = row as UserListItem;

      return (
        <>
          <td className="px-4 py-3 font-medium">
            {user.full_name}
          </td>
          <td className="px-4 py-3">
            {user.emp_code}
          </td>
          <td className="px-4 py-3">
            {user.email}
          </td>
          <td className="px-4 py-3">
            {user.team_name || '—'}
          </td>
          <td className="px-4 py-3">
            {user.work_location || '—'}
          </td>
        </>
      );
    }

    if (type === 'flights') {
      const flight = row as FlightResponse;

      return (
        <>
          <td className="px-4 py-3 font-medium">
            {flight.flight_code}
          </td>
          <td className="px-4 py-3">
            {flight.direction}
          </td>
          <td className="px-4 py-3">
            {flight.origin} → {flight.destination}
          </td>
          <td className="px-4 py-3">
            {flight.assigned_count}/{flight.total_slots}
          </td>
          <td className="px-4 py-3">
            {flight.available_slots}
          </td>
        </>
      );
    }

    const vehicle = row as VehicleResponse;

    return (
      <>
        <td className="px-4 py-3 font-medium">
          {vehicle.vehicle_name}
        </td>
        <td className="px-4 py-3">
          {vehicle.route_type}
        </td>
        <td className="px-4 py-3">
          {vehicle.pickup_location} →{' '}
          {vehicle.dropoff_location || '—'}
        </td>
        <td className="px-4 py-3">
          {vehicle.assigned_count}/{vehicle.capacity}
        </td>
        <td className="px-4 py-3">
          {vehicle.captain_name || 'Chưa có'}
        </td>
      </>
    );
  }

  const headers = {
    events: ['Tên sự kiện', 'Địa điểm', 'Trạng thái', 'Số người'],
    teams: ['Tên Team', 'Event ID'],
    users: ['Họ tên', 'Mã NV', 'Email', 'Team', 'Vai trò'],
    flights: [
      'Mã chuyến',
      'Chiều',
      'Lộ trình',
      'Đã xếp',
      'Còn trống',
    ],
    vehicles: [
      'Tên xe',
      'Chặng',
      'Lộ trình',
      'Đã xếp',
      'Trưởng xe',
    ],
  }[type];

  return (
    <div className="page-container">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-blue-600">
            Admin management
          </p>

          <h1 className="text-2xl font-bold text-slate-900">
            {title}
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            {description}
          </p>
        </div>

        <Link
          to="/admin"
          className="btn-secondary"
        >
          Về Dashboard
        </Link>
      </div>

      <div className="card mt-6 p-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="input"
            placeholder="Tìm kiếm..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                setRefreshKey((value) => value + 1);
              }
            }}
          />

          <button
            className="btn-primary"
            onClick={() => setRefreshKey((value) => value + 1)}
          >
            Tìm kiếm
          </button>
        </div>
      </div>

      {loading && (
        <div className="card mt-6 p-8 text-slate-500">
          Đang tải dữ liệu...
        </div>
      )}

      {error && (
        <div className="card mt-6 p-8 text-red-600">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50">
              <tr>
                {headers.map((header) => (
                  <th
                    key={header}
                    className="whitespace-nowrap px-4 py-3 font-semibold text-slate-600"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={headers.length}
                    className="px-4 py-10 text-center text-slate-500"
                  >
                    Chưa có dữ liệu.
                  </td>
                </tr>
              ) : (
                rows.map((row, index) => (
                  <tr
                    key={String(row.id || index)}
                    className="hover:bg-slate-50"
                  >
                    {renderRow(row)}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
