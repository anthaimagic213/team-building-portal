import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useGalaSeats } from '@/hooks/useGalaSeats';
import { getApiErrorMessage } from '@/api/httpClient';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';

export default function GalaPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const gala = useGalaSeats(eventId, { enabled: Boolean(eventId) });
  const [selected, setSelected] = useState<string[]>([]);
  const [locked, setLocked] = useState(false);
  const [message, setMessage] = useState('');

  const toggleSeat = (code: string) => {
    setMessage('');
    setSelected((current) => {
      if (current.includes(code)) return current.filter((item) => item !== code);
      if (current.length >= 1) {
        setMessage('Mỗi thành viên chỉ được chọn một ghế.');
        return current;
      }
      return [...current, code];
    });
  };

  async function lock() {
    try { await gala.lockSeats(selected); setLocked(true); setMessage('Đã giữ ghế tạm thời. Hãy xác nhận trước khi hết thời gian.'); } catch (error) { setMessage(getApiErrorMessage(error)); }
  }

  async function confirm() {
    try { await gala.confirmSeats(selected); setLocked(false); setMessage('Đã xác nhận ghế Gala thành công.'); } catch (error) { setMessage(getApiErrorMessage(error)); }
  }

  async function release() {
    try { await gala.releaseSeats(selected); setSelected([]); setLocked(false); setMessage('Đã nhả ghế.'); } catch (error) { setMessage(getApiErrorMessage(error)); }
  }

  if (!eventId || gala.isLoading) return <div className="page-container"><div className="card p-8">Đang tải sơ đồ ghế...</div></div>;
  if (gala.isError) return <div className="page-container"><div className="card p-8 text-red-600">Không thể tải sơ đồ Gala. Vui lòng thử lại sau.</div></div>;
  return <div className="page-container space-y-6"><section className="card p-6"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm text-blue-600">Gala Dinner · Event {eventId}</p><h1 className="text-2xl font-bold">Chọn ghế cho Team</h1><p className="mt-2 text-sm text-slate-500">Quyền đại diện được kiểm tra theo Event và Team.</p></div><Badge tone={locked ? 'warning' : 'info'}>{locked ? 'Đang giữ ghế' : 'Có thể chọn'}</Badge></div>{message && <p className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">{message}</p>}<div className="mt-6 grid gap-3" style={{ gridTemplateColumns: `repeat(${Math.max(1, Math.min(gala.layout?.seats.length || 1, 8))}, minmax(0, 1fr))` }}>{gala.seats.map((seat) => <button key={seat.id} type="button" disabled={locked || (seat.status !== 'AVAILABLE' && !selected.includes(seat.seat_code))} onClick={() => toggleSeat(seat.seat_code)} className={`min-h-12 rounded-lg p-3 text-sm font-semibold ${selected.includes(seat.seat_code) ? 'bg-blue-600 text-white' : seat.status === 'AVAILABLE' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'}`}>{seat.seat_code}</button>)}</div><div className="mt-6 flex flex-wrap items-center justify-between gap-3"><p className="text-sm text-slate-600">Đã chọn: <strong>{selected.length}</strong> ghế</p><div className="flex gap-2">{locked ? <><Button variant="secondary" onClick={() => void release()} loading={gala.isReleasing}>Nhả ghế</Button><Button onClick={() => void confirm()} loading={gala.isConfirming}>Xác nhận</Button></> : <Button disabled={!selected.length} onClick={() => void lock()} loading={gala.isLocking}>Giữ ghế</Button>}</div></div></section></div>;
}