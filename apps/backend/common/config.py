from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./herd_aggregator.db"
    source_database_url: str = "sqlite:///./source_staging.db"
    secret_key: str = "change-me-in-production"
    log_level: str = "INFO"
    export_storage_dir: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
