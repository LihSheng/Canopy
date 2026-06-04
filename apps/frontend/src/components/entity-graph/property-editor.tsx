"use client";

import { useState, type ReactNode } from "react";
import {
  SortableTable,
  type SortableColumnDef,
} from "@/components/shared/table";
import type { EntityRevisionProperty, SourceBinding } from "@/lib/api/types";
import {
  PropertyEditModal,
  type SourceNodeInfo,
  type PropertyFieldValues,
} from "./property-edit-modal";

// ─── Grip icon (for DragOverlay) ────────────────────────────────────────

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

// ─── Pencil icon ────────────────────────────────────────────────────────

const PencilIcon = () => (
  <svg
    className="size-3.5"
    viewBox="0 0 16 16"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    aria-hidden="true"
  >
    <path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z" />
    <path d="M10 3l3 3" />
  </svg>
);

// ─── DragOverlay content ────────────────────────────────────────────────

type DragOverlayContentProps = {
  prop: EntityRevisionProperty;
  sourceLabel: string | null;
  semanticTypeLabel: (t: string) => string;
};

const DragOverlayContent = ({
  prop,
  sourceLabel,
  semanticTypeLabel,
}: DragOverlayContentProps) => (
  <div className="flex items-center gap-3 rounded border border-blue-300 bg-white px-4 py-2 shadow-lg">
    <GripIcon />
    <span className="text-xs font-medium text-zinc-900">{prop.display_name}</span>
    <span className="font-mono text-xs text-zinc-400">{prop.property_key}</span>
    <span className="rounded-full border border-zinc-200 px-2 py-0.5 text-xs text-zinc-600">
      {semanticTypeLabel(prop.semantic_type)}
    </span>
    {prop.is_required && (
      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
        Req
      </span>
    )}
    {sourceLabel && (
      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
        {sourceLabel}
      </span>
    )}
  </div>
);

// ─── Props ──────────────────────────────────────────────────────────────

export type PropertySavePayload = {
  /** `undefined` = create mode; present = edit mode */
  propertyId?: string;
  propertyFields: PropertyFieldValues;
  binding: SourceBinding | null;
};

type Props = {
  properties: EntityRevisionProperty[];
  sourceBindings: SourceBinding[];
  sourceNodes: SourceNodeInfo[];
  onSaveProperty: (data: PropertySavePayload) => Promise<void>;
  onRemove: (propertyId: string) => Promise<void>;
  onReorder: (propertyIds: string[]) => Promise<void>;
  disabled?: boolean;
  loading?: boolean;
};

// ─── Main component ─────────────────────────────────────────────────────

export const PropertyEditor = ({
  properties,
  sourceBindings,
  sourceNodes,
  onSaveProperty,
  onRemove,
  onReorder,
  disabled,
  loading = false,
}: Props) => {
  // ── Modal state ─────────────────────────────────────────────────────
  const [modalOpen, setModalOpen] = useState(false);
  const [modalProperty, setModalProperty] = useState<EntityRevisionProperty | null>(null);

  // ── Binding lookup ──────────────────────────────────────────────────
  const bindingMap = new Map<string, SourceBinding>();
  sourceBindings.forEach((b) => bindingMap.set(b.property_key, b));

  const getsourceLabel = (propertyKey: string): string | null => {
    const b = bindingMap.get(propertyKey);
    if (!b) return null;
    const nodeName = sourceNodes.find((sn) => sn.source_id === b.source_node_id)?.name
      || b.source_node_id;
    return `${nodeName}.${b.source_field_name}`;
  };

  const semanticTypeLabel = (t: string): string => {
    const labels: Record<string, string> = {
      string: "String",
      integer: "Integer",
      number: "Number",
      boolean: "Boolean",
      datetime: "DateTime",
      date: "Date",
    };
    return labels[t] || t;
  };

  // ── Handlers ────────────────────────────────────────────────────────

  const openEdit = (prop: EntityRevisionProperty) => {
    setModalProperty(prop);
    setModalOpen(true);
  };

  const openCreate = () => {
    setModalProperty(null);
    setModalOpen(true);
  };

  const closeModal = () => {
    if (loading) return;
    setModalOpen(false);
    setModalProperty(null);
  };

  const handleModalSave = async (data: {
    propertyFields: PropertyFieldValues;
    binding: SourceBinding | null;
  }) => {
    await onSaveProperty({
      propertyId: modalProperty?.property_id,
      ...data,
    });
  };

  const handleModalRemove = async () => {
    if (modalProperty) {
      await onRemove(modalProperty.property_id);
    }
  };

  // ── Error display placeholder (errors surface in modal) ─────────────

  // ── Column definitions ──────────────────────────────────────────────

  const columns: SortableColumnDef<EntityRevisionProperty>[] = [
    {
      key: "display_name",
      header: "Display Name",
      render: (prop) => (
        <span className="font-medium text-zinc-900">{prop.display_name}</span>
      ),
    },
    {
      key: "property_key",
      header: "Key",
      render: (prop) => (
        <span className="font-mono text-xs text-zinc-500">{prop.property_key}</span>
      ),
    },
    {
      key: "semantic_type",
      header: "Type",
      render: (prop) => (
        <span className="inline-block rounded-full border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600">
          {semanticTypeLabel(prop.semantic_type)}
        </span>
      ),
    },
    {
      key: "is_required",
      header: "Req",
      align: "center",
      render: (prop) =>
        prop.is_required ? (
          <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
            Req
          </span>
        ) : (
          <span className="text-zinc-300">{"\u2014"}</span>
        ),
    },
    {
      key: "is_primary_key",
      header: "PK",
      align: "center",
      render: (prop) =>
        prop.is_primary_key ? (
          <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
            PK
          </span>
        ) : (
          <span className="text-zinc-300">{"\u2014"}</span>
        ),
    },
    {
      key: "bound_source",
      header: "Bound Source",
      render: (prop) => {
        const label = getsourceLabel(prop.property_key);
        if (label) {
          return (
            <span className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
              {label}
            </span>
          );
        }
        if (prop.is_required) {
          return (
            <span className="inline-block rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">
              Unbound
            </span>
          );
        }
        return <span className="text-zinc-300">{"\u2014"}</span>;
      },
    },
  ];

  // ── Edit (pencil) column ────────────────────────────────────────────

  const editColumn: SortableColumnDef<EntityRevisionProperty> = {
    key: "edit",
    header: "",
    align: "right",
    render: (prop) => (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          if (!disabled) openEdit(prop);
        }}
        disabled={disabled}
        className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 disabled:cursor-not-allowed disabled:opacity-30"
        title="Edit property"
      >
        <PencilIcon />
      </button>
    ),
  };

  const allColumns = disabled ? columns : [...columns, editColumn];

  // ── DragOverlay renderer ────────────────────────────────────────────

  const renderDragOverlay = (prop: EntityRevisionProperty): ReactNode => (
    <DragOverlayContent
      prop={prop}
      sourceLabel={getsourceLabel(prop.property_key)}
      semanticTypeLabel={semanticTypeLabel}
    />
  );

  // ── Render ──────────────────────────────────────────────────────────

  return (
    <>
      <div className="rounded-lg border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
          <h3 className="text-sm font-semibold text-zinc-900">
            Properties
            <span className="ml-1.5 text-xs font-normal text-zinc-400">
              ({properties.length})
            </span>
          </h3>
          {!disabled && (
            <button
              type="button"
              onClick={openCreate}
              className="text-xs font-medium text-zinc-600 hover:text-zinc-900"
            >
              + Add Property
            </button>
          )}
        </div>

        <SortableTable
          items={properties}
          getItemId={(item) => item.property_id}
          columns={allColumns}
          draggable={!disabled && !loading}
          onReorder={onReorder}
          loading={loading}
          emptyText="No properties defined yet. Click '+ Add Property' to create one."
          renderDragOverlay={renderDragOverlay}
        />
      </div>

      {/* Property edit modal */}
      <PropertyEditModal
        open={modalOpen}
        property={modalProperty}
        existingBinding={
          modalProperty
            ? bindingMap.get(modalProperty.property_key) ?? null
            : null
        }
        sourceNodes={sourceNodes}
        onSave={handleModalSave}
        onRemove={modalProperty ? handleModalRemove : undefined}
        onClose={closeModal}
        loading={loading}
      />
    </>
  );
};
