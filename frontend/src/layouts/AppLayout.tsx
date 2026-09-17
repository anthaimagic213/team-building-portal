import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex min-h-11 items-center rounded-lg px-3 text-sm font-medium transition ${isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`;

export default function AppLayout() {
  const navigate = useNavigate();
  const { user, logout, isLoggingOut } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6">
          <Link to="/journey" className="font-bold text-slate-900">Team Building Portal</Link>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-600 sm:inline">{user?.fullName || 'Người dùng'}</span>
            <button className="btn-secondary min-h-9 px-3 py-1.5" disabled={isLoggingOut} onClick={async () => { await logout(); navigate('/login'); }}>Đăng xuất</button>
          </div>
        </div>
      </header>
      <div className="mx-auto flex max-w-[1440px]">
        <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white p-4 md:block">
          <nav className="space-y-1">
            <NavLink to="/journey" className={linkClass}>Hành trình của tôi</NavLink>
            <NavLink to="/registration" className={linkClass}>Đăng ký Team Building</NavLink>
            <NavLink to="/profile" className={linkClass}>Tài khoản</NavLink>
            <NavLink to="/journey" className={linkClass}>Chọn Event Gala</NavLink>
          </nav>
        </aside>
        <main className="min-w-0 flex-1"><Outlet /></main>
      </div>
    </div>
  );
}