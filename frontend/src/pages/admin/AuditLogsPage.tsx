export default function AuditLogsPage() {
  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold text-slate-900">
        Audit Log
      </h1>

      <section className="card mt-6 p-8">
        <p className="text-slate-600">
          Backend hiện chưa cung cấp endpoint audit log trong API
          frontend hiện tại.
        </p>

        <p className="mt-2 text-sm text-slate-500">
          Màn hình sẽ được kết nối khi backend phát hành API audit log.
        </p>
      </section>
    </div>
  );
}
