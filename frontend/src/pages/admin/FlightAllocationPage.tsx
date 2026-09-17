import { useEffect, useState } from 'react';
import { allocationApi, eventApi } from '@/api';
import type { EventResponse } from '@/types/event';
import type { FlightAllocationResult } from '@/types/allocation';
import type { FlightDirection } from '@/api/allocationApi';

export default function FlightAllocationPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] =
    useState<FlightAllocationResult | null>(null);
  const [error, setError] = useState('');
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [eventId, setEventId] = useState('');
  const [direction, setDirection] = useState<FlightDirection>('OUTBOUND');
  useEffect(() => { void eventApi.listEvents().then(setEvents); }, []);

  async function runAllocation() {
    setLoading(true);
    setError('');

    try {
      const data =
        await allocationApi.runAutoFlightAllocation(eventId, direction);

      setResult(data);
    } catch {
      setError('Không thể chạy phân bổ chuyến bay.');
    } finally {
      setLoading(false);
    }
  }

  async function retryAllocation() {
    setLoading(true); setError('');
    try { setResult(await allocationApi.runAutoFlightAllocation(eventId, direction, true)); }
    catch { setError('Không thể chạy lại phân bổ chuyến bay.'); }
    finally { setLoading(false); }
  }

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold text-slate-900">
        Phân bổ chuyến bay
      </h1>

      <p className="mt-2 text-sm text-slate-500">
        Hệ thống ưu tiên giữ các thành viên cùng Team đi cùng nhau.
      </p>

      <section className="card mt-6 p-6">
        <label className="form-label">Event</label>
        <select className="input mb-5" value={eventId} onChange={(event) => setEventId(event.target.value)}><option value="">Chọn Event</option>{events.map((event) => <option key={event.id} value={event.id}>{event.event_name}</option>)}</select>
        <label className="form-label">Chặng bay</label>
        <select className="input mb-5" value={direction} onChange={(event) => setDirection(event.target.value as FlightDirection)}><option value="OUTBOUND">Chuyến bay đi</option><option value="RETURN">Chuyến bay về</option></select>
        <button
          className="btn-primary"
          disabled={loading || !eventId}
          onClick={runAllocation}
        >
          {loading
            ? 'Đang phân bổ...'
            : 'Chạy Auto Flight Allocation'}
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
            Kết quả phân bổ
          </h2>

          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-sm text-slate-500">Tổng số người</p>
              <p className="text-2xl font-bold">
                {result.total_users}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">Đã phân bổ</p>
              <p className="text-2xl font-bold text-emerald-600">
                {result.allocated_users}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">
                Chưa phân bổ
              </p>
              <p className="text-2xl font-bold text-red-600">
                {result.unallocated_users}
              </p>
            </div>
          </div>

          <p className="mt-5 text-sm text-slate-600">
            {result.message}
          </p>

          {result.warnings.length > 0 && (
            <ul className="mt-4 list-disc pl-5 text-sm text-amber-700">
              {result.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
