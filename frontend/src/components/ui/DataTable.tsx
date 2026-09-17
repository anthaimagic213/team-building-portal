import { ReactNode } from 'react';

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

export default function DataTable<T extends { id?: string | number }>({ columns, rows, emptyMessage = 'Chưa có dữ liệu.' }: { columns: DataTableColumn<T>[]; rows: T[]; emptyMessage?: string }) {
  return <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="min-w-full divide-y divide-slate-200 text-left text-sm"><thead className="bg-slate-50"><tr>{columns.map((column) => <th key={column.key} scope="col" className={`whitespace-nowrap px-4 py-3 font-semibold text-slate-600 ${column.className || ''}`}>{column.header}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{rows.length ? rows.map((row, index) => <tr className="hover:bg-slate-50" key={String(row.id ?? index)}>{columns.map((column) => <td key={column.key} className={`px-4 py-3 text-slate-700 ${column.className || ''}`}>{column.render(row)}</td>)}</tr>) : <tr><td className="px-4 py-10 text-center text-slate-500" colSpan={columns.length}>{emptyMessage}</td></tr>}</tbody></table></div>;
}