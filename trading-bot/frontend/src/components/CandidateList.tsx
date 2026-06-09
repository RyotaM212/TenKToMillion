import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import type { Candidate } from "../api";

const columnHelper = createColumnHelper<Candidate>();

const columns = [
  columnHelper.accessor("symbol", { header: "銘柄" }),
  columnHelper.accessor("symbol_name", { header: "名称" }),
  columnHelper.accessor("strategy_name", { header: "戦略" }),
  columnHelper.accessor("score", { header: "Score", cell: (info) => info.getValue().toFixed(1) }),
];

export function CandidateList({ candidates }: { candidates: Candidate[] }) {
  const table = useReactTable({ data: candidates, columns, getCoreRowModel: getCoreRowModel() });
  return (
    <section className="panel">
      <h2>本日の候補 TOP20</h2>
      <div className="tableWrap">
        <table>
          <thead>
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id}>
                {group.headers.map((header) => (
                  <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
