"use client";

import { useState, type ReactNode } from "react";
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

// ─── Types ───────────────────────────────────────────────────────────────

export type SortableColumnDef<T> = {
  key: string;
  header: string;
  align?: "left" | "center" | "right";
  render: (item: T, rowIndex: number) => ReactNode;
};

export type SortableTableProps<T> = {
  items: T[];
  getItemId: (item: T, index: number) => string;
  columns: SortableColumnDef<T>[];
  draggable?: boolean;
  onReorder?: (ids: string[]) => void;
  loading?: boolean;
  loadingText?: string;
  emptyText?: string;
  renderDragOverlay?: (item: T) => ReactNode;
};

// ─── Helpers ─────────────────────────────────────────────────────────────

const alignClass = (align?: "left" | "center" | "right"): string => {
  if (align === "right") return "text-right";
  if (align === "center") return "text-center";
  return "text-left";
};

// ─── Grip icon ───────────────────────────────────────────────────────────

const GripIcon = () => (
  <svg
    className="size-3.5"
    viewBox="0 0 16 16"
    fill="currentColor"
    aria-hidden="true"
  >
    <circle cx="5" cy="3" r="1.2" />
    <circle cx="11" cy="3" r="1.2" />
    <circle cx="5" cy="8" r="1.2" />
    <circle cx="11" cy="8" r="1.2" />
    <circle cx="5" cy="13" r="1.2" />
    <circle cx="11" cy="13" r="1.2" />
  </svg>
);

// ─── Draggable row (internal) ────────────────────────────────────────────

type DraggableRowProps<T> = {
  item: T;
  index: number;
  columns: SortableColumnDef<T>[];
  itemId: string;
  disabled?: boolean;
};

function DraggableRow<T>({
  item,
  index,
  columns,
  itemId,
  disabled = false,
}: DraggableRowProps<T>) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: itemId, disabled });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : undefined,
  };

  return (
    <tr
      ref={setNodeRef}
      style={style}
      className={`${isDragging ? "bg-zinc-50" : "hover:bg-zinc-50"}`}
    >
      {/* Grip handle */}
      <td className="w-8 px-2 py-2">
        {!disabled && (
          <button
            type="button"
            {...attributes}
            {...listeners}
            className="flex cursor-grab items-center justify-center rounded p-0.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 active:cursor-grabbing"
            title="Drag to reorder"
            tabIndex={-1}
          >
            <GripIcon />
          </button>
        )}
      </td>
      {columns.map((col) => (
        <td
          key={col.key}
          className={`px-4 py-2 ${alignClass(col.align)} text-zinc-700`}
        >
          {col.render(item, index)}
        </td>
      ))}
    </tr>
  );
}

// ─── Plain (non-draggable) row ───────────────────────────────────────────

type PlainRowProps<T> = {
  item: T;
  index: number;
  columns: SortableColumnDef<T>[];
  itemId: string;
};

function PlainRow<T>({ item, index, columns, itemId }: PlainRowProps<T>) {
  return (
    <tr key={itemId} className="hover:bg-zinc-50">
      {columns.map((col) => (
        <td
          key={col.key}
          className={`px-4 py-2 ${alignClass(col.align)} text-zinc-700`}
        >
          {col.render(item, index)}
        </td>
      ))}
    </tr>
  );
}

// ─── Empty tbody row ─────────────────────────────────────────────────────

function EmptyTbodyRow({ colSpan, text }: { colSpan: number; text: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-6 text-center text-sm text-zinc-400">
        {text}
      </td>
    </tr>
  );
}

// ─── Thead ───────────────────────────────────────────────────────────────

type TheadProps<T> = {
  columns: SortableColumnDef<T>[];
  draggable: boolean;
};

function Thead<T>({ columns, draggable }: TheadProps<T>) {
  return (
    <thead>
      <tr className="bg-zinc-50">
        {draggable && <th className="w-8 px-2 py-2" />}
        {columns.map((col) => (
          <th
            key={col.key}
            className={`whitespace-nowrap px-4 py-2 ${alignClass(col.align)} text-xs font-semibold uppercase tracking-wider text-zinc-500`}
          >
            {col.header}
          </th>
        ))}
      </tr>
    </thead>
  );
}

// ─── Main component ──────────────────────────────────────────────────────

export function SortableTable<T>({
  items,
  getItemId,
  columns,
  draggable = false,
  onReorder,
  loading = false,
  loadingText,
  emptyText = "No data available.",
  renderDragOverlay,
}: SortableTableProps<T>) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 4 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const itemIds = items.map((item, i) => getItemId(item, i));

  const colSpan = columns.length + (draggable ? 1 : 0);

  // ─── Drag handlers ───────────────────────────────────────────────────

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(String(event.active.id));
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = itemIds.indexOf(String(active.id));
    const newIndex = itemIds.indexOf(String(over.id));
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(itemIds, oldIndex, newIndex);
    await onReorder?.(reordered);
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  // ─── Active item for DragOverlay ─────────────────────────────────────

  const activeItem = activeId
    ? items.find((item, i) => getItemId(item, i) === activeId) ?? null
    : null;

  // ─── Render tbody content ────────────────────────────────────────────

  const renderedRows = () => {
    if (items.length === 0 && !loading) {
      return <EmptyTbodyRow colSpan={colSpan} text={emptyText} />;
    }

    return items.map((item, i) => {
      const id = getItemId(item, i);
      if (draggable) {
        return (
          <DraggableRow<T>
            key={id}
            item={item}
            index={i}
            columns={columns}
            itemId={id}
          />
        );
      }
      return (
        <PlainRow<T>
          key={id}
          item={item}
          index={i}
          columns={columns}
          itemId={id}
        />
      );
    });
  };

  const hasRows = items.length > 0;

  const emptyFallback = !hasRows && !loading && (
    <EmptyTbodyRow colSpan={colSpan} text={emptyText} />
  );

  // ─── Draggable table path ────────────────────────────────────────────

  const tbodyContent = (
    <tbody
      className={`divide-y divide-zinc-100 transition-opacity duration-200 ${
        loading ? "opacity-60 pointer-events-none" : ""
      }`}
    >
      {renderedRows()}
    </tbody>
  );

  const showOverlay = loading && hasRows;

  if (draggable) {
    return (
      <div className="relative">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <table className="min-w-full divide-y divide-zinc-100 text-sm">
            <Thead columns={columns} draggable />
            <SortableContext items={itemIds} strategy={verticalListSortingStrategy}>
              {hasRows || loading ? tbodyContent : <tbody>{emptyFallback}</tbody>}
            </SortableContext>
          </table>

          <DragOverlay dropAnimation={null}>
            {activeItem ? renderDragOverlay?.(activeItem) : null}
          </DragOverlay>
        </DndContext>

        {/* Loading overlay — always in DOM for smooth opacity transition */}
        <div
          aria-hidden
          className={`pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-white/50 transition-opacity duration-200 ${
            showOverlay ? "opacity-100" : "opacity-0"
          }`}
        >
          {showOverlay && <LoadingSpinner text={loadingText ?? "Saving..."} />}
        </div>
      </div>
    );
  }

  // ─── Plain table path ────────────────────────────────────────────────

  return (
    <div className="relative">
      <table className="min-w-full divide-y divide-zinc-100 text-sm">
        <Thead columns={columns} draggable={false} />
        {hasRows || loading ? tbodyContent : <tbody>{emptyFallback}</tbody>}
      </table>

      {/* Loading overlay — always in DOM for smooth opacity transition */}
      <div
        aria-hidden
        className={`pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-white/50 transition-opacity duration-200 ${
          showOverlay ? "opacity-100" : "opacity-0"
        }`}
      >
        {showOverlay && <LoadingSpinner text={loadingText ?? "Saving..."} />}
      </div>
    </div>
  );
}
