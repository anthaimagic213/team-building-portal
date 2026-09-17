import { FormEvent, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/api/userApi';
import { getApiErrorMessage } from '@/api/httpClient';
import useCurrentUser from '@/hooks/useCurrentUser';
import Button from '@/components/ui/Button';

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useCurrentUser();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) setPhone(user.phone || '');
  }, [user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage(''); setError('');
    if (!phone.trim() && !password) {
      setError('Hãy nhập số điện thoại hoặc mật khẩu mới.'); return;
    }
    if (password && password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp.'); return;
    }
    setSaving(true);
    try {
      await userApi.updateMe({ phone: phone.trim() || null, ...(password ? { password } : {}) });
      await queryClient.invalidateQueries({ queryKey: ['users', 'me'] });
      setPassword(''); setConfirmPassword('');
      setMessage('Cập nhật thông tin thành công.');
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally { setSaving(false); }
  }

  if (isLoading) return <div className="page-container"><div className="card p-8">Đang tải thông tin...</div></div>;
  return <div className="page-container"><section className="card mx-auto max-w-2xl p-6 sm:p-8"><h1 className="text-2xl font-bold">Thông tin tài khoản</h1><p className="mt-2 text-sm text-slate-500">Bạn chỉ có thể thay đổi số điện thoại và mật khẩu.</p><dl className="mt-6 grid gap-3 rounded-lg bg-slate-50 p-4 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">Họ tên</dt><dd className="font-medium">{user?.full_name}</dd></div><div><dt className="text-slate-500">Mã nhân viên</dt><dd className="font-medium">{user?.emp_code}</dd></div><div><dt className="text-slate-500">Email</dt><dd className="font-medium">{user?.email}</dd></div><div><dt className="text-slate-500">Team</dt><dd className="font-medium">{user?.team_name || '—'}</dd></div></dl>{message && <p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}{error && <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<form onSubmit={submit} className="mt-6 space-y-4"><label className="block"><span className="form-label">Số điện thoại</span><input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+84901234567" /></label><label className="block"><span className="form-label">Mật khẩu mới</span><input className="input" type="password" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Để trống nếu không đổi" /></label><label className="block"><span className="form-label">Xác nhận mật khẩu mới</span><input className="input" type="password" minLength={6} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} /></label><Button loading={saving}>Lưu thay đổi</Button></form></section></div>;
}