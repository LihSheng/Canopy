from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_BACKEND_ENV_FILE, override=False)


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/canopy"
    control_plane_database_url: str | None = None
    tenant_data_database_url: str | None = None
    source_database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/source_staging"
    secret_key: str = "change-me-in-production"
    log_level: str = "INFO"
    export_storage_dir: str = ""

    model_config = {"env_file": _BACKEND_ENV_FILE, "env_file_encoding": "utf-8"}

    @property
    def resolved_control_plane_database_url(self) -> str:
        return self.control_plane_database_url or self.database_url

    @property
    def resolved_tenant_data_database_url(self) -> str:
        return self.tenant_data_database_url or self.database_url


settings = Settings()
