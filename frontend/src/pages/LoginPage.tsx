import { FormEvent, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { getApiErrorMessage } from '@/api/httpClient';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, isLoggingIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    try {
      const result = await login({ email, password });
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from || (result.roles.includes('ADMIN') || result.roles.includes('SUPER_ADMIN') ? '/admin' : '/journey'), { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }

  return <section className="card p-6 sm:p-8">
    <h2 className="text-xl font-bold text-slate-900">Đăng nhập</h2>
    <p className="mt-1 text-sm text-slate-500">Sử dụng tài khoản công ty của bạn</p>
    {error && <div role="alert" className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <form onSubmit={submit} className="mt-6 space-y-4">
      <label className="block"><span className="form-label">Email công ty</span><input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></label>
      <label className="block"><span className="form-label">Mật khẩu</span><input className="input" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
      <button className="btn-primary w-full" disabled={isLoggingIn}>{isLoggingIn ? 'Đang đăng nhập...' : 'Đăng nhập'}</button>
    </form>
  </section>;
}