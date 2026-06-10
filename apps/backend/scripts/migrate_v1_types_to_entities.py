"""One-time migration: create Entity definitions for v1 hardcoded domain types.

Reads the latest snapshot's ontology rows for each of the 6 hardcoded types,
creates Dataset + DatasetVersion records with JSONL storage, creates ObjectType
(Entity) definitions, publishes initial revisions, and materializes rows.

Usage:
    cd apps/backend
    python scripts/migrate_v1_types_to_entities.py

The old sync → ontology → analytics pipeline continues unchanged.
New Entity system runs in parallel with the same data.
"""

import os
import sys

# Ensure backend root is on path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from common.config import settings
from common.database import init_db, session_factory
from connection._shared import storage_root, write_jsonl_version
from dataset.domain import Dataset, DatasetStatus, DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from entity_materialization.repository import EntityMaterializationRepository
from entity_materialization.service import EntityMaterializationService, build_source_data_reader
from entity_revision.domain import (
    EntityProperty,
    SourceBinding,
)
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
from ontology.schema import (
    BudgetCodeModel,
    CostCenterModel,
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
    PayrollExpenseModel,
)
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

# ── Type definitions for migration ─────────────────────────────────────

# Each type definition: what ontology ORM to read, what fields to map,
# and which field is the primary key.
TYPE_DEFS = [
    {
        "entity_key": "department",
        "display_name": "Department",
        "description": "Organizational department (migrated from v1)",
        "model": DepartmentModel,
        "fields": [
            "id",
            "name",
            "parent_department_id",
            "status",
        ],
        "primary_key": "id",
        "id_column": "id",
    },
    {
        "entity_key": "employee",
        "display_name": "Employee",
        "description": "Employee record (migrated from v1)",
        "model": EmployeeModel,
        "fields": [
            "id",
            "department_id",
            "cost_center_id",
            "employee_code",
            "full_name",
            "employment_status",
        ],
        "primary_key": "id",
        "id_column": "id",
    },
    {
        "entity_key": "cost_center",
        "display_name": "Cost Center",
        "description": "Cost center reference (migrated from v1)",
        "model": CostCenterModel,
        "fields": ["id", "code", "name"],
        "primary_key": "id",
        "id_column": "id",
    },
    {
        "entity_key": "budget_code",
        "display_name": "Budget Code",
        "description": "Budget code reference (migrated from v1)",
        "model": BudgetCodeModel,
        "fields": ["id", "code", "name", "category"],
        "primary_key": "id",
        "id_column": "id",
    },
    {
        "entity_key": "expense_claim",
        "display_name": "Expense Claim",
        "description": "Expense claim (migrated from v1)",
        "model": ExpenseClaimModel,
        "fields": [
            "id",
            "employee_id",
            "department_id",
            "cost_center_id",
            "budget_code_id",
            "claim_type",
            "claim_date",
            "amount",
            "currency",
        ],
        "primary_key": "id",
        "id_column": "id",
    },
    {
        "entity_key": "payroll_expense",
        "display_name": "Payroll Expense",
        "description": "Payroll expense record (migrated from v1)",
        "model": PayrollExpenseModel,
        "fields": [
            "id",
            "employee_id",
            "department_id",
            "cost_center_id",
            "budget_code_id",
            "payroll_month",
            "amount",
            "currency",
            "pay_component",
        ],
        "primary_key": "id",
        "id_column": "id",
    },
]

SEMANTIC_TYPE_MAP = {
    "id": "string",
    "name": "string",
    "full_name": "string",
    "employee_code": "string",
    "employment_status": "string",
    "code": "string",
    "category": "string",
    "claim_type": "string",
    "claim_date": "date",
    "payroll_month": "string",
    "currency": "string",
    "pay_component": "string",
    "status": "string",
    "amount": "number",
    "department_id": "string",
    "employee_id": "string",
    "cost_center_id": "string",
    "budget_code_id": "string",
    "parent_department_id": "string",
}

TENANT_ID = "migration"


def _infer_semantic_type(field_name: str) -> str:
    return SEMANTIC_TYPE_MAP.get(field_name, "string")


# ── Main migration function ─────────────────────────────────────────────


def migrate(db: Session) -> list[dict]:
    """Run the v1 → Entity migration.

    Returns a summary list with one dict per migrated entity type.
    """
    obj_repo = ObjectTypeRepository(db)
    dataset_repo = DatasetRepository(db)
    version_repo = DatasetVersionRepository(db)
    rev_repo = EntityRevisionRepository(db)
    rev_service = EntityRevisionService(rev_repo, obj_repo)
    mat_repo = EntityMaterializationRepository(db)
    reader = build_source_data_reader(db)

    results: list[dict] = []

    for type_def in TYPE_DEFS:
        entity_key = type_def["entity_key"]
        display_name = type_def["display_name"]
        description = type_def["description"]
        model_cls = type_def["model"]
        fields = type_def["fields"]
        pk_field = type_def["primary_key"]

        print(f"  Migrating {display_name} ({entity_key})...")

        # ── Step 1: Read rows from ontology table ────────────────────
        rows = db.query(model_cls).all()
        if not rows:
            print(f"    No rows found for {display_name}, skipping.")
            results.append(
                {
                    "entity_type": entity_key,
                    "status": "skipped",
                    "reason": "no rows",
                }
            )
            continue

        # Convert ORM rows to dicts with only business-visible fields
        row_dicts: list[dict] = []
        for row in rows:
            d = {}
            for f in fields:
                val = getattr(row, f, None)
                # Convert datetime to ISO string
                if isinstance(val, datetime):
                    val = val.isoformat()
                d[f] = val
            row_dicts.append(d)

        print(f"    Read {len(row_dicts)} rows.")

        # ── Step 2: Write JSONL and create Dataset + DatasetVersion ──
        dataset_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())

        storage_path = write_jsonl_version(row_dicts, dataset_id, entity_key)

        dataset = Dataset(
            id=dataset_id,
            connection_id="",  # no real connection — migration artifact
            name=f"{display_name} (v1 migration)",
            source_object_name=entity_key,
            status=DatasetStatus.ACTIVE.value,
            active_version_id=version_id,
            tenant_id=TENANT_ID,
        )
        dataset_repo.save(dataset)

        version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=1,
            status=DatasetVersionStatus.READY.value,
            row_count=len(row_dicts),
            column_count=len(fields),
            storage_path=str(storage_path),
            raw_storage_path=str(storage_path),
        )
        version_repo.save(version)

        print(f"    Created dataset {dataset_id[:8]}... version {version_id[:8]}...")

        # ── Step 3: Create ObjectType (Entity) ──────────────────────
        entity_id = str(uuid.uuid4())
        obj = ObjectType(
            id=entity_id,
            tenant_id=TENANT_ID,
            object_type_key=entity_key,
            display_name=display_name,
            description=description,
            created_at=datetime.now(UTC),
        )
        obj_repo.save(obj)

        # ── Step 4: Build properties, bindings, source_node ─────────
        source_node_id = f"src-{entity_key}"

        properties: list[EntityProperty] = []
        bindings: list[SourceBinding] = []
        for idx, f in enumerate(fields):
            prop = EntityProperty(
                property_id=str(uuid.uuid4()),
                property_key=f,
                display_name=f.replace("_", " ").title(),
                semantic_type=_infer_semantic_type(f),
                is_primary_key=(f == pk_field),
                sort_order=idx,
            )
            properties.append(prop)
            bindings.append(
                SourceBinding(
                    property_key=f,
                    source_node_id=source_node_id,
                    source_field_name=f,
                    is_active=True,
                )
            )

        source_nodes = [
            {
                "source_id": source_node_id,
                "source_type": "table",
                "name": f"{display_name} (v1)",
                "reference_id": version_id,
                "fields": fields,
            }
        ]

        # ── Step 5: Create initial revision and publish ─────────────
        revision = rev_service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=TENANT_ID,
            properties=properties,
            source_bindings=bindings,
            source_nodes=source_nodes,
            publish=True,
        )

        print(f"    Published revision {revision.revision_number}")

        # ── Step 6: Materialize ─────────────────────────────────────
        mat_service = EntityMaterializationService(rev_repo, mat_repo, reader)
        stats = mat_service.materialize_entity(entity_id, revision.id)

        results.append(
            {
                "entity_type": entity_key,
                "entity_id": entity_id,
                "status": "materialized",
                "rows_read": len(row_dicts),
                "rows_inserted": stats.get("rows_inserted", 0),
                "rows_updated": stats.get("rows_updated", 0),
                "rows_tombstoned": stats.get("rows_tombstoned", 0),
            }
        )

        print(
            f"    Materialized: {stats.get('rows_inserted', 0)} inserted, {stats.get('rows_tombstoned', 0)} tombstoned"
        )

    return results


# ── CLI entrypoint ──────────────────────────────────────────────────────


def main() -> None:
    """Entrypoint for `python scripts/migrate_v1_types_to_entities.py`."""
    print("--- V1 Ontology to Entity Migration ---\n")
    print(f"Database: {settings.resolved_control_plane_database_url}")
    print(f"Storage:  {storage_root()}")
    print(f"Tenant:   {TENANT_ID}\n")

    # Initialize database engine and create tables if needed
    init_db()

    db = session_factory()()
    try:
        results = migrate(db)
    finally:
        db.close()

    print("\n=== Migration Summary ===\n")
    for r in results:
        status = r.get("status", "unknown")
        if status == "materialized":
            print(f"  ✅ {r['entity_type']}: {r['rows_inserted']} inserted, {r['rows_updated']} updated")
        elif status == "skipped":
            print(f"  ⏭  {r['entity_type']}: skipped ({r.get('reason', 'unknown')})")
        else:
            print(f"  ❌ {r['entity_type']}: {status}")

    print(f"\nDone. {len([r for r in results if r.get('status') == 'materialized'])} entities materialized.")


if __name__ == "__main__":
    main()
