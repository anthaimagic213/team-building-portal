import { FormEvent, useEffect, useState } from 'react';
import { adminApi, authApi, eventApi } from '@/api';
import type { Team, UserListItem } from '@/types/user';
import type { EventResponse } from '@/types/event';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';

export default function UsersPage() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [eventId, setEventId] = useState('');
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [busyUser, setBusyUser] = useState('');
  const [form, setForm] = useState({ emp_code: '', full_name: '', email: '', password: '', phone: '', work_location: 'HN', team_id: '', is_representative: false });

  const load = async (selectedEventId = eventId) => {
    const [userData, teamData] = await Promise.all([adminApi.listAllUsers(selectedEventId || undefined), adminApi.listTeams()]);
    setUsers(userData); setTeams(teamData);
  };
  useEffect(() => { void eventApi.listEvents().then((data) => { setEvents(data); if (data[0]) { setEventId(data[0].id); void load(data[0].id); } else void load(); }); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await authApi.register({ ...form, phone: form.phone || null, team_id: form.team_id || null, is_representative: false });
      setMessage('Đã tạo tài khoản.'); setOpen(false);
      setForm({ emp_code: '', full_name: '', email: '', password: '', phone: '', work_location: 'HN', team_id: '', is_representative: false });
      await load();
    } catch { setMessage('Không thể tạo tài khoản. Email hoặc mã nhân viên có thể đã tồn tại.'); }
  }

  async function toggleRepresentative(user: UserListItem) {
    const next = !user.is_representative;
    if (!window.confirm(`${next ? 'Cấp' : 'Thu hồi'} quyền đại diện Gala cho ${user.full_name}?`)) return;
    setBusyUser(user.id); setMessage('');
    if (!eventId) { setMessage('Hãy chọn Event trước khi phân quyền đại diện.'); return; }
    try { await adminApi.updateUserRepresentative(user.id, eventId, next); setMessage(`${next ? 'Đã cấp' : 'Đã thu hồi'} quyền đại diện Gala cho ${user.full_name}.`); await load(); }
    catch { setMessage('Không thể cập nhật quyền đại diện.'); }
    finally { setBusyUser(''); }
  }

  return <div className="page-container"><div className="flex flex-wrap justify-between gap-4"><div><h1 className="text-2xl font-bold">Quản lý tài khoản CBNV</h1><p className="mt-1 text-sm text-slate-500">Chỉ định đại diện Gala theo trạng thái đăng ký của từng Event.</p></div><Button onClick={() => setOpen(true)}>+ Tạo tài khoản</Button></div><div className="card mt-6 p-4"><label className="form-label">Event đang xét quyền Gala</label><select className="input" value={eventId} onChange={(e) => { setEventId(e.target.value); void load(e.target.value); }}><option value="">Chọn Event</option>{events.map((event) => <option key={event.id} value={event.id}>{event.event_name}</option>)}</select></div><div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">Chỉ user đã đăng ký và chọn “Có tham gia” trong Event được chọn, đồng thời đã có Team, mới được cấp quyền đại diện Gala.</div>{message && <p className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">{message}</p>}<div className="mt-6 overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50"><tr><th className="px-4 py-3">Họ tên</th><th className="px-4 py-3">Mã NV</th><th className="px-4 py-3">Team</th><th className="px-4 py-3">Đăng ký Event</th><th className="px-4 py-3">Tham gia</th><th className="px-4 py-3">Gala</th><th className="px-4 py-3">Thao tác</th></tr></thead><tbody className="divide-y divide-slate-100">{users.map((user) => <tr key={user.id}><td className="px-4 py-3 font-medium">{user.full_name}</td><td className="px-4 py-3">{user.emp_code}</td><td className="px-4 py-3">{user.team_name || 'Chưa gán Team'}</td><td className="px-4 py-3">{user.is_registered ? 'Đã đăng ký' : 'Chưa đăng ký'}</td><td className="px-4 py-3">{user.is_participating ? 'Có' : user.is_registered ? 'Không' : '—'}</td><td className="px-4 py-3">{user.is_representative ? <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">Đại diện</span> : <span className="text-slate-500">CBNV</span>}</td><td className="px-4 py-3"><Button variant={user.is_representative ? 'secondary' : 'primary'} className="min-h-9 px-3 py-1" loading={busyUser === user.id} disabled={!user.is_representative && (!eventId || !user.team_name || !user.is_registered || !user.is_participating)} onClick={() => void toggleRepresentative(user)}>{user.is_representative ? 'Thu hồi quyền' : 'Cấp đại diện'}</Button></td></tr>)}{users.length === 0 && <tr><td colSpan={7} className="px-4 py-10 text-center text-slate-500">Chưa có tài khoản.</td></tr>}</tbody></table></div><Modal open={open} title="Tạo tài khoản CBNV" onClose={() => setOpen(false)}><form onSubmit={submit} className="space-y-3"><input className="input" required placeholder="Mã nhân viên" value={form.emp_code} onChange={(e) => setForm({ ...form, emp_code: e.target.value })} /><input className="input" required placeholder="Họ tên" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /><input className="input" required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /><input className="input" required minLength={6} type="password" placeholder="Mật khẩu" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /><input className="input" placeholder="Số điện thoại" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /><input className="input" placeholder="Địa điểm: HN/HCM" value={form.work_location} onChange={(e) => setForm({ ...form, work_location: e.target.value })} /><select className="input" value={form.team_id} onChange={(e) => setForm({ ...form, team_id: e.target.value })}><option value="">Chọn Team (tùy chọn)</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.team_name}</option>)}</select><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_representative} onChange={(e) => setForm({ ...form, is_representative: e.target.checked })} /> Cấp quyền đại diện ngay khi tạo</label><Button className="w-full">Tạo tài khoản</Button></form></Modal></div>;
}