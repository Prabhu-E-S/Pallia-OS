import { cn } from "@/lib/cn";

export function Table({
  columns,
  rows,
  rowKey,
  empty,
  onRowClick,
  className = "",
}: {
  columns: { key: string; header: string; align?: "left" | "right" }[];
  rows: ReadonlyArray<Record<string, React.ReactNode>>;
  rowKey: (row: Record<string, React.ReactNode>) => string;
  empty?: React.ReactNode;
  onRowClick?: (row: Record<string, React.ReactNode>) => void;
  className?: string;
}) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-surface">
        {empty ?? (
          <div className="px-5 py-10 text-center text-sm text-muted">No records yet.</div>
        )}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-line bg-surface">
      <table className={cn("min-w-full divide-y divide-line text-sm", className)}>
        <thead className="bg-slate-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  "px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500 whitespace-nowrap",
                  col.align === "right" && "text-right",
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={cn(
                "bg-surface hover:bg-slate-50 transition-colors",
                onRowClick && "cursor-pointer",
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-4 py-3 align-middle",
                    col.align === "right" && "text-right",
                  )}
                >
                  {row[col.key as string]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}