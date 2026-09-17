import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex min-h-10 items-center rounded-lg px-3 text-sm font-medium ${isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'}`;

export default function AdminLayout() {
  const { user, logout, isLoggingOut } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-64 bg-slate-900 p-4 text-white lg:block">
        <Link to="/admin" className="block border-b border-slate-700 pb-5 text-lg font-bold">Admin Portal</Link>
        <nav className="mt-5 space-y-1">
          <NavLink to="/admin" end className={linkClass}>Tổng quan</NavLink>
          <NavLink to="/admin/events" className={linkClass}>Sự kiện</NavLink>
          <NavLink to="/admin/teams" className={linkClass}>Team</NavLink>
          <NavLink to="/admin/flights" className={linkClass}>Chuyến bay</NavLink>
          <NavLink to="/admin/vehicles" className={linkClass}>Xe</NavLink>
          <NavLink to="/admin/allocations" end className={linkClass}>Phân bổ</NavLink>
          <NavLink to="/admin/users" className={linkClass}>CBNV</NavLink>
          <NavLink to="/admin/hotels" className={linkClass}>Khách sạn</NavLink>
          <NavLink to="/admin/gala" className={linkClass}>Cấu hình Gala</NavLink>
          <NavLink to="/admin/notifications" className={linkClass}>Thông báo</NavLink>
        </nav>
      </aside>
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="flex h-16 items-center justify-between px-4 lg:ml-64 lg:px-8">
          <span className="font-semibold text-slate-900">Quản trị hệ thống</span>
          <div className="flex items-center gap-3"><span className="hidden text-sm text-slate-600 sm:inline">{user?.fullName}</span><button className="btn-secondary min-h-9 px-3 py-1.5" disabled={isLoggingOut} onClick={async () => { await logout(); navigate('/login'); }}>Đăng xuất</button></div>
        </div>
      </header>
      <main className="min-w-0 lg:ml-64"><Outlet /></main>
    </div>
  );
}