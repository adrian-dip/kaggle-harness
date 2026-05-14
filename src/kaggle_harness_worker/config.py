from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gateway_url: str = "http://localhost:8743"
    worker_token: str = "change-me-in-production"
    worker_id: str = "worker-1"
    worker_labels: list[str] = []
    worker_gpu: bool = False
    worker_cpu: int = 1
    worker_memory_mb: int = 4096
    worker_poll_interval: float = 1.0
    worker_heartbeat_interval: float = 30.0
    docker_socket: str = "unix:///var/run/docker.sock"
