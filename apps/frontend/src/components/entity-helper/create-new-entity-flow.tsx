"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { EntityHelperShell, type HelperStep } from "./entity-helper-shell";
import { createEntity } from "@/lib/api/semantic";
import { createInitialRevision } from "@/lib/api/entities";
import { SortableTable, type SortableColumnDef } from "@/components/shared/table";
import { ROUTES } from "@/lib/constants";

const STEPS: HelperStep[] = [
  { key: "datasource", label: "Datasource", description: "Optionally choose a backing dataset" },
  { key: "metadata", label: "Metadata", description: "Name, description, and grouping" },
  { key: "properties", label: "Properties", description: "Define and configure object properties" },
  { key: "actions", label: "Actions", description: "Preview generated actions" },
  { key: "save", label: "Save", description: "Review and create" },
];

interface CreateNewEntityFlowProps {
  onClose: () => void;
}

/**
 * Palantir-style entity creation helper.
 *
 * Steps:
 * 1. Datasource — optionally choose or skip a backing datasource.
 * 2. Metadata — display name, plural name, description, icon, groups.
 * 3. Properties — define properties, pick primary key and title key.
 * 4. Actions — preview-only generated actions.
 * 5. Save — confirm and create the entity shell immediately.
 *
 * After creation, navigates into the canonical Entity Manager.
 */
export function CreateNewEntityFlow({ onClose }: CreateNewEntityFlowProps) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ─── Datasource step state ───
  const [skipDatasource, setSkipDatasource] = useState(true);
  // (Future: selected dataset state when datasource is chosen)

  // ─── Metadata step state ───
  const [displayName, setDisplayName] = useState("");
  const [pluralName, setPluralName] = useState("");
  const [description, setDescription] = useState("");
  const [icon, setIcon] = useState("");
  const [groups, setGroups] = useState<string[]>([]);
  const [groupInput, setGroupInput] = useState("");

  // ─── Properties step state ───
  interface PropDraft {
    key: string;
    property_key: string;
    display_name: string;
    semantic_type: string;
    is_primary_key: boolean;
    is_title_key: boolean;
  }
  const [properties, setProperties] = useState<PropDraft[]>([
    { key: "1", property_key: "id", display_name: "ID", semantic_type: "string", is_primary_key: true, is_title_key: false },
  ]);

  // ─── Title key ───
  const [titleKey, setTitleKey] = useState<string | null>(null);

  // ─── Validation ───

  const canGoNext = (): boolean => {
    switch (step) {
      case 0: // Datasource — always allowed (skip is default)
        return true;
      case 1: // Metadata — requires display name
        return displayName.trim().length > 0;
      case 2: // Properties — requires at least one PK
        return properties.some((p) => p.is_primary_key);
      case 3: // Actions — always allowed (preview only)
        return true;
      case 4: // Save — always allowed
        return true;
      default:
        return false;
    }
  };

  // ─── Create ───

  const handleCreate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Create the entity shell (server generates the key)
      const entity = await createEntity({
        display_name: displayName.trim(),
        description: description.trim(),
        plural_name: pluralName.trim(),
        icon: icon.trim(),
        groups: groups,
      });

      // 2. Create initial revision with properties if defined
      if (properties.length > 0) {
        try {
          await createInitialRevision(entity.id, {
            properties: properties.map((p, i) => ({
              property_id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${i}`,
              property_key: p.property_key,
              display_name: p.display_name,
              semantic_type: p.semantic_type || "string",
              is_required: false,
              is_primary_key: p.is_primary_key,
              sort_order: i,
              format_hint: "",
            })),
          });
        } catch {
          // Initial revision is optional — the entity shell already exists
        }
      }

      // 3. Navigate to entity manager
      onClose();
      router.push(ROUTES.entityDetail(entity.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create entity");
    } finally {
      setLoading(false);
    }
  }, [displayName, description, pluralName, icon, groups, properties, onClose, router]);

  // ── Navigation ──

  const handleNext = useCallback(() => {
    setError(null);
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      // Final save step
      handleCreate();
    }
  }, [step, handleCreate]);

  const handleBack = useCallback(() => {
    setError(null);
    if (step > 0) setStep((s) => s - 1);
  }, [step]);

  // ─── Property helpers ───

  const addProperty = () => {
    const newProp: PropDraft = {
      key: String(Date.now()),
      property_key: "",
      display_name: "",
      semantic_type: "string",
      is_primary_key: false,
      is_title_key: false,
    };
    setProperties((prev) => [...prev, newProp]);
  };

  const updateProperty = (key: string, field: keyof PropDraft, value: string | boolean) => {
    setProperties((prev) =>
      prev.map((p) => {
        if (p.key !== key) return p;
        if (field === "is_primary_key" && value === true) {
          // Only one PK allowed — unset others
          return { ...p, is_primary_key: true };
        }
        if (field === "is_title_key" && value === true) {
          setTitleKey(p.property_key || p.display_name);
          return { ...p, is_title_key: true };
        }
        return { ...p, [field]: value };
      })
    );
    // Unset PK on others
    if (field === "is_primary_key" && value === true) {
      setProperties((prev) =>
        prev.map((p) => (p.key !== key ? { ...p, is_primary_key: false } : p))
      );
    }
    if (field === "is_title_key" && value === true) {
      setProperties((prev) =>
        prev.map((p) => (p.key !== key ? { ...p, is_title_key: false } : p))
      );
    }
  };

  const removeProperty = (key: string) => {
    setProperties((prev) => prev.filter((p) => p.key !== key));
  };

  const handleReorder = useCallback((orderedIds: string[]) => {
    setProperties((prev) => {
      const byKey = new Map(prev.map((p) => [p.key, p]));
      const reordered = orderedIds.map((id) => byKey.get(id)).filter(Boolean) as PropDraft[];
      // Append any items not in the ordered list (shouldn't happen, but safe)
      const seen = new Set(orderedIds);
      const remainder = prev.filter((p) => !seen.has(p.key));
      return [...reordered, ...remainder];
    });
  }, []);

  const addGroup = () => {
    const trimmed = groupInput.trim();
    if (trimmed && !groups.includes(trimmed)) {
      setGroups((prev) => [...prev, trimmed]);
      setGroupInput("");
    }
  };

  const removeGroup = (g: string) => {
    setGroups((prev) => prev.filter((x) => x !== g));
  };

  // ─── Auto-pick title key ───
  const autoPickTitleKey = () => {
    // Pick the first non-PK string property named something like "name" or "title"
    const candidate = properties.find(
      (p) =>
        !p.is_primary_key &&
        p.semantic_type === "string" &&
        (p.display_name.toLowerCase().includes("name") ||
          p.display_name.toLowerCase().includes("title") ||
          p.property_key.toLowerCase().includes("name") ||
          p.property_key.toLowerCase().includes("title"))
    );
    if (candidate) {
      setTitleKey(candidate.property_key || candidate.display_name);
      setProperties((prev) =>
        prev.map((p) => ({
          ...p,
          is_title_key: p.key === candidate.key,
        }))
      );
    }
  };

  // ─── Semantic types ───
  const SEMANTIC_TYPES = ["string", "integer", "number", "boolean", "datetime", "date"];

  // ─── Icon options ───
  const ICON_OPTIONS = [
    { value: "cube", label: "Cube" },
    { value: "user", label: "Person" },
    { value: "building", label: "Building" },
    { value: "document", label: "Document" },
    { value: "currency", label: "Money" },
    { value: "chart", label: "Chart" },
  ];

  // ─── Properties table column defs ───
  const propertyColumns: SortableColumnDef<PropDraft>[] = useMemo(
    () => [
      {
        key: "property_key",
        header: "Key",
        render: (prop) => (
          <input
            type="text"
            value={prop.property_key}
            onChange={(e) => updateProperty(prop.key, "property_key", e.target.value)}
            placeholder="key"
            className="w-24 rounded border border-zinc-200 px-2 py-1 text-xs font-mono text-zinc-900 focus:border-zinc-400 focus:outline-none"
          />
        ),
      },
      {
        key: "display_name",
        header: "Display Name",
        render: (prop) => (
          <input
            type="text"
            value={prop.display_name}
            onChange={(e) => updateProperty(prop.key, "display_name", e.target.value)}
            placeholder="Display Name"
            className="w-32 rounded border border-zinc-200 px-2 py-1 text-xs text-zinc-900 focus:border-zinc-400 focus:outline-none"
          />
        ),
      },
      {
        key: "semantic_type",
        header: "Type",
        render: (prop) => (
          <select
            value={prop.semantic_type}
            onChange={(e) => updateProperty(prop.key, "semantic_type", e.target.value)}
            className="rounded border border-zinc-200 px-2 py-1 text-xs text-zinc-900 focus:border-zinc-400 focus:outline-none"
          >
            {SEMANTIC_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        ),
      },
      {
        key: "is_primary_key",
        header: "PK",
        align: "center",
        render: (prop) => (
          <input
            type="radio"
            name="primary_key"
            checked={prop.is_primary_key}
            onChange={() => updateProperty(prop.key, "is_primary_key", true)}
            className="h-3.5 w-3.5 text-zinc-900"
          />
        ),
      },
      {
        key: "is_title_key",
        header: "Title",
        align: "center",
        render: (prop) => (
          <input
            type="radio"
            name="title_key"
            checked={prop.is_title_key}
            onChange={() => updateProperty(prop.key, "is_title_key", true)}
            className="h-3.5 w-3.5 text-zinc-900"
          />
        ),
      },
      {
        key: "actions",
        header: "",
        render: (prop) => (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              removeProperty(prop.key);
            }}
            className="text-zinc-300 hover:text-red-500"
            title="Remove property"
          >
            &times;
          </button>
        ),
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [SEMANTIC_TYPES],
  );

  const propDragOverlay = (prop: PropDraft) => (
    <div className="flex items-center gap-3 rounded border border-zinc-300 bg-white px-3 py-2 shadow-lg">
      <span className="font-mono text-xs text-zinc-500">{prop.property_key || "—"}</span>
      <span className="text-sm font-medium text-zinc-900">{prop.display_name || "—"}</span>
      <span className="ml-auto text-xs text-zinc-400">{prop.semantic_type}</span>
    </div>
  );

  return (
    <EntityHelperShell
      title="Create New Entity"
      subtitle={
        skipDatasource
          ? "Build a business object from scratch"
          : "Build a business object backed by a datasource"
      }
      steps={STEPS}
      currentStep={step}
      canGoBack={step > 0}
      canGoNext={canGoNext()}
      isLastStep={step === STEPS.length - 1}
      nextLabel={step === STEPS.length - 1 ? "Create Entity" : "Next"}
      loading={loading}
      error={error}
      onBack={handleBack}
      onNext={handleNext}
      onClose={onClose}
    >
      {/* ─── Step 0: Datasource ─── */}
      {step === 0 && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            Choose whether to start with a backing datasource or build a blank
            entity. You can attach a dataset later from the Entity Manager.
          </p>

          <div className="space-y-3">
            <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-zinc-200 p-4 transition-colors hover:border-zinc-300">
              <input
                type="radio"
                name="datasource"
                className="mt-0.5 h-4 w-4 text-zinc-900"
                checked={skipDatasource}
                onChange={() => setSkipDatasource(true)}
              />
              <div>
                <div className="text-sm font-medium text-zinc-900">
                  Continue without datasource
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  Create a blank entity shell. No empty backing dataset is
                  created. Attach source data later from the Entity Manager.
                </div>
              </div>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-zinc-200 p-4 transition-colors hover:border-zinc-300">
              <input
                type="radio"
                name="datasource"
                className="mt-0.5 h-4 w-4 text-zinc-900"
                checked={!skipDatasource}
                onChange={() => setSkipDatasource(false)}
              />
              <div>
                <div className="text-sm font-medium text-zinc-900">
                  Use existing datasource
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  Bootstrap from an existing dataset. You will select the
                  dataset in a later step after the shell is created.
                </div>
              </div>
            </label>
          </div>

          {!skipDatasource && (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
              Dataset selection will be available in the Entity Manager after
              creation. The shell is created first.
            </div>
          )}
        </div>
      )}

      {/* ─── Step 1: Metadata ─── */}
      {step === 1 && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            Provide identifying metadata for the entity. The object type key is
            generated automatically from the display name.
          </p>

          {/* Display Name */}
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">
              Display Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Employee Record"
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              autoFocus
            />
          </div>

          {/* Plural Name */}
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">
              Plural Name
            </label>
            <input
              type="text"
              value={pluralName}
              onChange={(e) => setPluralName(e.target.value)}
              placeholder="e.g. Employee Records"
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the purpose of this entity..."
              rows={3}
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            />
          </div>

          {/* Icon */}
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">
              Icon
            </label>
            <div className="flex flex-wrap gap-2">
              {ICON_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setIcon(icon === opt.value ? "" : opt.value)}
                  className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                    icon === opt.value
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Groups */}
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">
              Groups
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={groupInput}
                onChange={(e) => setGroupInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addGroup();
                  }
                }}
                placeholder="Type a group name and press Enter"
                className="flex-1 rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              />
              <button
                type="button"
                onClick={addGroup}
                className="rounded-md border border-zinc-200 px-3 py-2 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-50"
              >
                Add
              </button>
            </div>
            {groups.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {groups.map((g) => (
                  <span
                    key={g}
                    className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-700"
                  >
                    {g}
                    <button
                      type="button"
                      onClick={() => removeGroup(g)}
                      className="ml-0.5 text-zinc-400 hover:text-zinc-600"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Step 2: Properties ─── */}
      {step === 2 && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            Define the properties for this entity. Mark one as the primary key
            and optionally pick a title key for display.
          </p>

          {/* Title key auto-pick button */}
          {titleKey ? (
            <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
              Title key: <span className="font-mono font-medium text-zinc-900">{titleKey}</span>
              <button
                type="button"
                onClick={() => {
                  setTitleKey(null);
                  setProperties((prev) =>
                    prev.map((p) => ({ ...p, is_title_key: false }))
                  );
                }}
                className="ml-2 text-zinc-400 hover:text-zinc-600"
              >
                clear
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={autoPickTitleKey}
              className="rounded-md border border-dashed border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-500 transition-colors hover:border-zinc-400 hover:text-zinc-700"
            >
              Auto-pick title key
            </button>
          )}

          {/* Properties table with drag-and-drop reorder */}
          <SortableTable
            items={properties}
            getItemId={(p) => p.key}
            columns={propertyColumns}
            draggable
            onReorder={handleReorder}
            renderDragOverlay={propDragOverlay}
            emptyText="No properties defined. Add one below."
          />

          <button
            type="button"
            onClick={addProperty}
            className="rounded-md border border-dashed border-zinc-300 px-4 py-2 text-xs font-medium text-zinc-500 transition-colors hover:border-zinc-400 hover:text-zinc-700"
          >
            + Add Property
          </button>
        </div>
      )}

      {/* ─── Step 3: Actions Preview ─── */}
      {step === 3 && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            The following actions are generated based on your configuration.
            This is a preview only — full action setup happens in the Entity
            Manager after creation.
          </p>

          <div className="rounded-lg border border-zinc-200 divide-y divide-zinc-100">
            {properties.length === 0 ? (
              <div className="px-4 py-6 text-center text-sm text-zinc-400">
                No properties defined yet. Add properties in the previous step to
                see generated actions.
              </div>
            ) : (
              <>
                <div className="px-4 py-3 flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded bg-blue-100 text-xs font-medium text-blue-700">
                    R
                  </span>
                  <div>
                    <div className="text-sm font-medium text-zinc-900">
                      Read {displayName || "Entity"}
                    </div>
                    <div className="text-xs text-zinc-500">
                      Browse and search {pluralName || displayName || "records"}.
                      Returns all defined properties.
                    </div>
                  </div>
                </div>
                <div className="px-4 py-3 flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded bg-zinc-100 text-xs font-medium text-zinc-600">
                    P
                  </span>
                  <div>
                    <div className="text-sm font-medium text-zinc-900">
                      Preview {displayName || "Entity"} Properties
                    </div>
                    <div className="text-xs text-zinc-500">
                      View property metadata, types, and primary key
                      configuration.
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="rounded-md border border-zinc-100 bg-zinc-50 px-4 py-3 text-xs text-zinc-500">
            Actions are read-only previews generated from your entity schema.
            Edit, create, and delete actions will be configurable in the Entity
            Manager after the shell is created.
          </div>
        </div>
      )}

      {/* ─── Step 4: Save / Confirm ─── */}
      {step === 4 && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            Review your configuration and create the entity shell. The shell will
            appear in the registry immediately with an in-progress status.
          </p>

          <div className="rounded-lg border border-zinc-200 divide-y divide-zinc-100 text-sm">
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Name</span>
              <span className="font-medium text-zinc-900">
                {displayName || "—"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Plural Name</span>
              <span className="font-medium text-zinc-900">
                {pluralName || "—"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Object Type Key</span>
              <span className="font-mono text-xs text-zinc-500">
                Generated from name on save
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Icon</span>
              <span className="font-medium text-zinc-900">
                {icon || "—"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Groups</span>
              <span className="font-medium text-zinc-900">
                {groups.length > 0 ? groups.join(", ") : "—"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Datasource</span>
              <span className="font-medium text-zinc-900">
                {skipDatasource ? "None (blank canvas)" : "Will attach after creation"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Properties</span>
              <span className="font-medium text-zinc-900">
                {properties.length} defined
                {properties.some((p) => p.is_primary_key)
                  ? ", 1 primary key"
                  : ", no primary key"}
                {titleKey ? ", title key set" : ""}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Initial Status</span>
              <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                In Progress
              </span>
            </div>
          </div>

          <div className="rounded-md border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-800">
            The entity shell saves immediately. You will be redirected to the
            Entity Manager where you can continue configuring properties, source
            bindings, links, and publish when ready.
          </div>
        </div>
      )}
    </EntityHelperShell>
  );
}
