import { FormEvent, useEffect, useState } from 'react';
import { adminApi, eventApi } from '@/api';
import type { EventResponse, EventStatus } from '@/types/event';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import { EVENT_STATUS_LABELS } from '@/constants/ui';

export default function EventsPage() {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({ event_name: '', event_date_start: '', event_date_end: '', location: '', registration_deadline: '', description: '' });

  const load = async () => setEvents(await adminApi.listEvents());
  useEffect(() => { void load(); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setMessage('');
    try { await adminApi.createEvent({ ...form, description: form.description || null }); setOpen(false); setForm({ event_name: '', event_date_start: '', event_date_end: '', location: '', registration_deadline: '', description: '' }); await load(); }
    catch { setMessage('Không thể tạo Event. Kiểm tra ngày và quyền Admin.'); }
    finally { setLoading(false); }
  }

  async function changeStatus(item: EventResponse, status: EventStatus) {
    try { await eventApi.updateEventStatus(item.id, status); await load(); } catch { setMessage('Không thể chuyển trạng thái Event.'); }
  }

  async function remove(item: EventResponse) { if (!window.confirm(`Xóa Event "${item.event_name}"?`)) return; try { await adminApi.deleteEvent(item.id); await load(); } catch { setMessage('Không thể xóa Event.'); } }

  return <div className="page-container"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm text-blue-600">Admin management</p><h1 className="text-2xl font-bold">Quản lý sự kiện</h1><p className="mt-1 text-sm text-slate-500">Tạo Event, mở đăng ký và quản lý vòng đời chương trình.</p></div><Button onClick={() => setOpen(true)}>+ Tạo Event</Button></div>{message && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{message}</p>}<div className="mt-6 overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50"><tr>{['Tên Event', 'Địa điểm', 'Thời gian', 'Trạng thái', 'Thao tác'].map((x) => <th className="whitespace-nowrap px-4 py-3" key={x}>{x}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{events.map((item) => <tr key={item.id}><td className="px-4 py-3 font-medium">{item.event_name}</td><td className="px-4 py-3">{item.location}</td><td className="px-4 py-3">{new Date(item.event_date_start).toLocaleDateString('vi-VN')} – {new Date(item.event_date_end).toLocaleDateString('vi-VN')}</td><td className="px-4 py-3"><Badge tone={item.status === 'REGISTRATION_OPEN' ? 'success' : item.status.includes('IN_PROGRESS') ? 'warning' : 'info'}>{EVENT_STATUS_LABELS[item.status] || item.status}</Badge></td><td className="flex flex-wrap gap-2 px-4 py-3"><select className="input min-h-9 w-auto py-1" value="" onChange={(e) => { if (e.target.value) void changeStatus(item, e.target.value as EventStatus); }}><option value="">Đổi trạng thái</option><option value="REGISTRATION_OPEN">Mở đăng ký</option><option value="REGISTRATION_CLOSED">Đóng đăng ký</option><option value="ALLOCATION_IN_PROGRESS">Bắt đầu phân bổ</option><option value="ALLOCATION_COMPLETED">Hoàn thành phân bổ</option><option value="EVENT_ACTIVE">Sự kiện hoạt động</option><option value="EVENT_COMPLETED">Kết thúc</option></select><Button variant="danger" className="min-h-9 px-3 py-1" onClick={() => void remove(item)}>Xóa</Button></td></tr>)}{events.length === 0 && <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-500">Chưa có Event.</td></tr>}</tbody></table></div><Modal open={open} title="Tạo Event mới" onClose={() => setOpen(false)}><form onSubmit={submit} className="space-y-4"><input className="input" placeholder="Tên Event" required value={form.event_name} onChange={(e) => setForm({ ...form, event_name: e.target.value })} /><input className="input" placeholder="Địa điểm" required value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /><label className="block text-sm">Bắt đầu<input className="input mt-1" type="datetime-local" required value={form.event_date_start} onChange={(e) => setForm({ ...form, event_date_start: e.target.value })} /></label><label className="block text-sm">Kết thúc<input className="input mt-1" type="datetime-local" required value={form.event_date_end} onChange={(e) => setForm({ ...form, event_date_end: e.target.value })} /></label><label className="block text-sm">Deadline đăng ký<input className="input mt-1" type="datetime-local" required value={form.registration_deadline} onChange={(e) => setForm({ ...form, registration_deadline: e.target.value })} /></label><textarea className="input min-h-24" placeholder="Mô tả" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><Button className="w-full" loading={loading}>Tạo Event</Button></form></Modal></div>;
}
