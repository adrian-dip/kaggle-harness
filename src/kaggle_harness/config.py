from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 8743
    debug: bool = False

    database_url: str = "postgresql+asyncpg://harness:harness@localhost:5432/harness"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_bundles: str = "bundles"
    minio_bucket_artifacts: str = "artifacts"
    minio_bucket_inputs: str = "inputs"

    mlflow_tracking_uri: str = "http://localhost:5000"

    # Kaggle — env vars match what the kaggle library itself reads
    kaggle_username: str | None = None
    kaggle_key: str | None = None
    kaggle_config_dir: str | None = None

    worker_token: str = "change-me-in-production"
    worker_heartbeat_timeout_seconds: int = 120
