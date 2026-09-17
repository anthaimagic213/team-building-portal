import { useEffect, useState } from 'react';
import { adminApi, eventApi } from '@/api';
import type { EventResponse } from '@/types/event';
import ImportDropzone from '@/components/admin/ImportDropzone';

export default function HotelsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState('');
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [eventId, setEventId] = useState('');
  useEffect(() => { void eventApi.listEvents().then(setEvents); }, []);

  async function importRooms() {
    if (!file) {
      setError('Vui lòng chọn file trước.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const data = await adminApi.importHotelRooms(file, eventId);
      setResult(data);
    } catch {
      setError('Import file thất bại.');
    } finally {
      setLoading(false);
    }
  }

  async function downloadTemplate() {
    const blob = await adminApi.downloadHotelTemplate();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');

    anchor.href = url;
    anchor.download = 'hotel-room-template.xlsx';
    anchor.click();

    URL.revokeObjectURL(url);
  }

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold text-slate-900">
        Quản lý khách sạn và phòng
      </h1>

      <section className="card mt-6 p-6">
        <label className="form-label">Event</label>
        <select className="input mb-5" value={eventId} onChange={(event) => setEventId(event.target.value)}><option value="">Chọn Event</option>{events.map((event) => <option key={event.id} value={event.id}>{event.event_name}</option>)}</select>
        <div className="flex flex-wrap gap-3">
          <button
            className="btn-secondary"
            onClick={downloadTemplate}
          >
            Tải template
          </button>
        </div>

        <div className="mt-5">
          <ImportDropzone onFile={setFile} />
        </div>

        {file && (
          <p className="mt-4 text-sm text-slate-600">
            File đã chọn: <strong>{file.name}</strong>
          </p>
        )}

        <button
          className="btn-primary mt-5"
          disabled={!file || !eventId || loading}
          onClick={importRooms}
        >
          {loading ? 'Đang import...' : 'Import phòng'}
        </button>

        {error && (
          <p className="mt-4 text-sm text-red-600">
            {error}
          </p>
        )}

        {result !== null && (
  <pre className="mt-5 overflow-x-auto rounded-lg bg-slate-900 p-4 text-xs text-white">
    {JSON.stringify(result, null, 2)}
  </pre>
)}

      </section>
    </div>
  );
}
