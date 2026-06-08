import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

export interface Column<T> {
  key: string;
  header: ReactNode;
  /** Cell renderer. */
  render: (row: T, index: number) => ReactNode;
  align?: 'left' | 'right' | 'center';
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string | number;
  emptyMsg?: string;
  onRowClick?: (row: T) => void;
}

const alignClass = { left: 'text-left', right: 'text-right', center: 'text-center' };

export function Table<T>({
  columns,
  rows,
  rowKey,
  emptyMsg,
  onRowClick,
}: TableProps<T>) {
  return (
    <div className="-mx-1 overflow-x-auto">
      <table className="w-full min-w-full border-collapse text-[13px]">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'whitespace-nowrap px-3 py-2 text-xs font-semibold uppercase tracking-wide text-text-muted',
                  alignClass[col.align ?? 'left'],
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-8 text-center text-sm text-text-faint"
              >
                {emptyMsg ?? '—'}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={rowKey(row, i)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn(
                  'border-t border-border-soft',
                  onRowClick && 'cursor-pointer hover:bg-bg',
                )}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      'whitespace-nowrap px-3 py-2.5 text-text',
                      alignClass[col.align ?? 'left'],
                      col.className,
                    )}
                  >
                    {col.render(row, i)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
