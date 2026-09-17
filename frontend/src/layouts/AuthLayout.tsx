import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-slate-100 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-2xl font-bold text-white shadow-lg">TB</div>
          <h1 className="mt-4 text-2xl font-bold text-slate-900">Team Building Portal</h1>
          <p className="mt-1 text-sm text-slate-500">Quản lý hành trình Team Building</p>
        </div>
        <Outlet />
      </div>
    </main>
  );
}