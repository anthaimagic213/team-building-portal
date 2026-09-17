import { ReactNode } from 'react';

export type ToastTone = 'success' | 'error' | 'warning' | 'info';

export interface ToastData {
  id: string;
  title?: string;
  message: string;
  tone?: ToastTone;
}

export default function Toast({ toast, onClose }: { toast: ToastData; onClose?: () => void }) {
  const toneClass: Record<ToastTone, string> = {
    success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    error: 'border-red-200 bg-red-50 text-red-800',
    warning: 'border-amber-200 bg-amber-50 text-amber-800',
    info: 'border-sky-200 bg-sky-50 text-sky-800',
  };
  const tone = toast.tone || 'info';
  return (
    <div className={`flex w-full max-w-sm items-start gap-3 rounded-xl border p-4 shadow-lg ${toneClass[tone]}`} role={tone === 'error' ? 'alert' : 'status'}>
      <div className="min-w-0 flex-1">
        {toast.title && <p className="font-semibold">{toast.title}</p>}
        <p className="text-sm">{toast.message}</p>
      </div>
      {onClose && <button type="button" className="min-h-8 min-w-8 rounded-lg hover:bg-black/5" onClick={onClose} aria-label="Đóng thông báo">×</button>}
    </div>
  );
}

export function ToastViewport({ toasts, onClose }: { toasts: ToastData[]; onClose: (id: string) => void }) {
  return <div className="pointer-events-none fixed right-4 top-4 z-[60] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3"><div className="pointer-events-auto space-y-3">{toasts.map((toast) => <Toast key={toast.id} toast={toast} onClose={() => onClose(toast.id)} />)}</div></div>;
}