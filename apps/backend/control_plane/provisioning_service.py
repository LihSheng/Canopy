import threading
import uuid

from common.clock import utcnow
from common.database import session_factory
from cache.hooks import after_tenant_provisioned
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.schemas.database_targets import TenantDatabaseTargetModel
from control_plane.schemas.jobs import ProvisioningJobModel
from control_plane.tenant_repository import TenantRepository


def _execute_provisioning(job_id: str) -> None:
    db = session_factory()()
    try:
        job = db.query(ProvisioningJobModel).filter(ProvisioningJobModel.id == job_id).first()
        if job is None:
            return

        tenant_id = job.tenant_id
        job.status = "running"
        job.started_at = utcnow()
        job.attempt_count += 1
        db.commit()

        tenant_repo = TenantRepository(db)
        audit = AuditService(db)
        config_repo = ConfigRepository(db)

        tenant = tenant_repo.get_tenant_by_id(tenant_id)
        if tenant is None:
            raise ValueError("Tenant not found")
        if tenant.lifecycle_state != "pending":
            raise ValueError(f"Tenant {tenant_id} is not in pending state")

        db_target = TenantDatabaseTargetModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            database_kind="tenant_data",
            connection_ref=f"secret://tenants/{tenant_id}/database",
        )
        db.add(db_target)

        defaults = {
            "storage_limit": '{"max_bytes": 10737418240}',
            "queue_limit": '{"max_concurrent_jobs": 5}',
            "retention_policy": '{"days": 90}',
            "feature_flags": '{"data_import": true, "analytics": true}',
        }
        for key, value_json in defaults.items():
            config_repo.set_config(tenant_id, key, value_json)

        tenant_repo.update_lifecycle_state(tenant_id, "active")

        audit.record_event(
            tenant_id=tenant_id,
            actor_user_id="system",
            event_type="tenant.provisioned",
            payload={"tenant_id": tenant_id, "tenant_name": tenant.name},
        )

        job.status = "completed"
        job.finished_at = utcnow()
        db.commit()
        after_tenant_provisioned(tenant_id)

    except Exception as e:
        db.rollback()
        job = db.query(ProvisioningJobModel).filter(ProvisioningJobModel.id == job_id).first()
        if job is not None:
            job.status = "failed"
            job.finished_at = utcnow()
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


class ProvisioningService:
    def __init__(self, db):
        self._db = db

    def provision_tenant(self, tenant_id: str) -> ProvisioningJobModel:
        tenant_repo = TenantRepository(self._db)
        tenant = tenant_repo.get_tenant_by_id(tenant_id)
        if tenant is None:
            raise ValueError("Tenant not found")

        job = ProvisioningJobModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            job_type="provision",
            status="pending",
        )
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)

        thread = threading.Thread(
            target=_execute_provisioning,
            args=(job.id,),
            daemon=True,
            name=f"provision-{job.id}",
        )
        thread.start()

        return job

    def get_provisioning_status(self, job_id: str) -> ProvisioningJobModel | None:
        return (
            self._db.query(ProvisioningJobModel)
            .filter(ProvisioningJobModel.id == job_id)
            .first()
        )

    def list_provisioning_jobs(
        self, tenant_id: str | None = None
    ) -> list[ProvisioningJobModel]:
        q = self._db.query(ProvisioningJobModel).order_by(
            ProvisioningJobModel.created_at.desc()
        )
        if tenant_id is not None:
            q = q.filter(ProvisioningJobModel.tenant_id == tenant_id)
        return q.all()

