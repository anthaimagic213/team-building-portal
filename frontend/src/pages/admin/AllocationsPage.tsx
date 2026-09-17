import { Link } from 'react-router-dom';

const cards = [
  {
    to: '/admin/allocations/flights',
    title: 'Phân bổ chuyến bay',
    description: 'Chạy auto allocation, xem cảnh báo và số người chưa được xếp chuyến.',
    action: 'Mở phân bổ chuyến bay',
  },
  {
    to: '/admin/allocations/vehicles',
    title: 'Phân bổ xe',
    description: 'Chọn từng chặng xe và chạy phân bổ theo chuyến bay, Team và sức chứa.',
    action: 'Mở phân bổ xe',
  },
];

export default function AllocationsPage() {
  return (
    <div className="page-container">
      <div>
        <p className="text-sm text-blue-600">Admin operations</p>
        <h1 className="text-2xl font-bold text-slate-900">Phân bổ nguồn lực</h1>
        <p className="mt-2 text-sm text-slate-500">
          Chọn module cần thực hiện. Hãy bảo đảm Event đã có người đăng ký và nguồn lực trước khi chạy.
        </p>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        {cards.map((card) => (
          <section className="card p-6" key={card.to}>
            <h2 className="text-lg font-semibold text-slate-900">{card.title}</h2>
            <p className="mt-2 min-h-12 text-sm leading-6 text-slate-600">{card.description}</p>
            <Link className="btn-primary mt-5" to={card.to}>{card.action}</Link>
          </section>
        ))}
      </div>

      <section className="card mt-6 border-amber-200 bg-amber-50 p-5">
        <h2 className="font-semibold text-amber-900">Quy trình đề xuất</h2>
        <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-amber-800">
          <li>Mở đăng ký và chờ CBNV gửi registration.</li>
          <li>Kiểm tra flight/vehicle capacity trong các màn hình nguồn lực.</li>
          <li>Chạy phân bổ chuyến bay trước.</li>
          <li>Chạy phân bổ xe theo từng route.</li>
          <li>Rà soát danh sách chưa phân bổ và xử lý manual adjustment.</li>
        </ol>
      </section>
    </div>
  );
}