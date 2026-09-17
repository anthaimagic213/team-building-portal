import { useEffect, useState } from 'react';
import { allocationApi, eventApi } from '@/api';
import type { EventResponse } from '@/types/event';
import type {
  RouteType,
} from '@/types/resource';
import type {
  VehicleAllocationResult,
} from '@/types/allocation';

const routes: Array<{
  value: RouteType;
  label: string;
}> = [
  { value: 'ROUTE_1', label: 'Văn phòng → Sân bay' },
  { value: 'ROUTE_2', label: 'Sân bay → Khách sạn' },
  { value: 'ROUTE_3', label: 'Khách sạn → Sân bay' },
  { value: 'ROUTE_4', label: 'Sân bay → Văn phòng' },
];

export default function VehicleAllocationPage() {
  const [route, setRoute] =
    useState<RouteType>('ROUTE_1');

  const [loading, setLoading] = useState(false);
  const [result, setResult] =
    useState<VehicleAllocationResult | null>(null);

  const [error, setError] = useState('');
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [eventId, setEventId] = useState('');
  useEffect(() => { void eventApi.listEvents().then(setEvents); }, []);

  async function runAllocation() {
    setLoading(true);
    setError('');

    try {
      const data =
        await allocationApi.runAutoVehicleAllocation(route, eventId);

      setResult(data);
    } catch {
      setError('Không thể chạy phân bổ xe.');
    } finally {
      setLoading(false);
    }
  }

  async function retryAllocation() {
    setLoading(true); setError('');
    try { setResult(await allocationApi.runAutoVehicleAllocation(route, eventId, true)); }
    catch { setError('Không thể chạy lại phân bổ xe.'); }
    finally { setLoading(false); }
  }

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold text-slate-900">
        Phân bổ xe
      </h1>

      <section className="card mt-6 p-6">
        <label className="form-label">Event</label>
        <select className="input mb-5" value={eventId} onChange={(event) => setEventId(event.target.value)}><option value="">Chọn Event</option>{events.map((event) => <option key={event.id} value={event.id}>{event.event_name}</option>)}</select>
        <label className="form-label">
          Chọn chặng xe
        </label>

        <select
          className="input"
          value={route}
          onChange={(event) =>
            setRoute(event.target.value as RouteType)
          }
        >
          {routes.map((item) => (
            <option key={item.value} value={item.value}>
              {item.value} - {item.label}
            </option>
          ))}
        </select>

        <button
          className="btn-primary mt-5"
          disabled={loading || !eventId}
          onClick={runAllocation}
        >
          {loading
            ? 'Đang phân bổ...'
            : 'Chạy Auto Vehicle Allocation'}
        </button>
        <button className="btn-secondary ml-3" disabled={loading || !eventId} onClick={retryAllocation}>Xóa phân bổ cũ và chạy lại</button>

        {error && (
          <p className="mt-4 text-sm text-red-600">
            {error}
          </p>
        )}
      </section>

      {result && (
        <section className="card mt-6 p-6">
          <h2 className="section-title">
            Kết quả {result.route_type}
          </h2>

          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-sm text-slate-500">Tổng số người</p>
              <p className="text-2xl font-bold">
                {result.total_users}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">Đã xếp xe</p>
              <p className="text-2xl font-bold text-emerald-600">
                {result.allocated_users}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">
                Chưa xếp xe
              </p>
              <p className="text-2xl font-bold text-red-600">
                {result.unallocated_users}
              </p>
            </div>
          </div>

          <p className="mt-5 text-sm text-slate-600">
            {result.message}
          </p>
        </section>
      )}
    </div>
  );
}
