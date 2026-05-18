import uuid

from sqlalchemy.orm import Session

from v5.cache.hooks import after_config_changed
from v5.control_plane.schemas.config import TenantConfigModel


class ConfigRepository:
    def __init__(self, db: Session):
        self._db = db

    def set_config(
        self, tenant_id: str, key: str, value_json: str
    ) -> TenantConfigModel:
        existing = (
            self._db.query(TenantConfigModel)
            .filter(
                TenantConfigModel.tenant_id == tenant_id,
                TenantConfigModel.config_key == key,
            )
            .order_by(TenantConfigModel.version_number.desc())
            .first()
        )
        new_version = (existing.version_number + 1) if existing else 1
        config = TenantConfigModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            config_key=key,
            config_value_json=value_json,
            version_number=new_version,
        )
        self._db.add(config)
        self._db.commit()
        self._db.refresh(config)
        after_config_changed(tenant_id, key)
        return config

    def get_config(self, tenant_id: str, key: str) -> TenantConfigModel | None:
        return (
            self._db.query(TenantConfigModel)
            .filter(
                TenantConfigModel.tenant_id == tenant_id,
                TenantConfigModel.config_key == key,
                TenantConfigModel.status == "active",
            )
            .order_by(TenantConfigModel.version_number.desc())
            .first()
        )

    def get_all_configs(self, tenant_id: str) -> list[TenantConfigModel]:
        return (
            self._db.query(TenantConfigModel)
            .filter(
                TenantConfigModel.tenant_id == tenant_id,
                TenantConfigModel.status == "active",
            )
            .all()
        )

    def get_config_history(self, tenant_id: str, key: str) -> list[TenantConfigModel]:
        return (
            self._db.query(TenantConfigModel)
            .filter(
                TenantConfigModel.tenant_id == tenant_id,
                TenantConfigModel.config_key == key,
            )
            .order_by(TenantConfigModel.version_number.desc())
            .all()
        )
