import type { ReactNode } from "react";

export interface ColumnDef {
  key: string;
  header: string;
  width?: number;
  align?: "left" | "center" | "right";
  render?: (value: unknown, row: Record<string, unknown>, rowIndex: number) => ReactNode;
}

export type RowIdentity = string;

export interface TablePage {
  current: number;
  total: number;
}

export interface TableSelection {
  selectedIds: Set<string>;
  onToggleRow: (id: string) => void;
  onToggleAll: () => void;
  allSelected: boolean;
  someSelected: boolean;
}

export interface TableState {
  columns: ColumnDef[];
  rows: Record<string, unknown>[];
  getRowId: (row: Record<string, unknown>, index: number) => RowIdentity;
  loading: boolean;
  error: string | null;
  emptyText?: string;
  errorText?: string;
  page: TablePage | null;
  onPageChange?: (page: number) => void;
  searchValue: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  totalRowCount?: number;
}
