from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunHandle:
    run_id: str
    experiment_id: str


class Tracker(ABC):
    @abstractmethod
    def create_run(self, experiment: str, name: str) -> RunHandle: ...

    @abstractmethod
    def log_params(self, run_id: str, params: dict[str, Any]) -> None: ...

    @abstractmethod
    def log_metric(self, run_id: str, key: str, value: float, step: int | None = None) -> None: ...

    @abstractmethod
    def log_artifact(self, run_id: str, path: Path, artifact_path: str | None = None) -> None: ...

    @abstractmethod
    def set_tag(self, run_id: str, key: str, value: str) -> None: ...

    @abstractmethod
    def set_terminated(self, run_id: str, status: str) -> None: ...


class MlflowTracker(Tracker):
    def __init__(self, tracking_uri: str) -> None:
        import mlflow
        mlflow.set_tracking_uri(tracking_uri)
        self._client = mlflow.MlflowClient(tracking_uri=tracking_uri)

    def create_run(self, experiment: str, name: str) -> RunHandle:
        import mlflow
        exp = mlflow.set_experiment(experiment)
        run = self._client.create_run(exp.experiment_id, run_name=name)
        return RunHandle(run_id=run.info.run_id, experiment_id=exp.experiment_id)

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        for k, v in params.items():
            self._client.log_param(run_id, k, str(v))

    def log_metric(self, run_id: str, key: str, value: float, step: int | None = None) -> None:
        self._client.log_metric(run_id, key, value, step=step)

    def log_artifact(self, run_id: str, path: Path, artifact_path: str | None = None) -> None:
        self._client.log_artifact(run_id, str(path), artifact_path=artifact_path)

    def set_tag(self, run_id: str, key: str, value: str) -> None:
        self._client.set_tag(run_id, key, value)

    def set_terminated(self, run_id: str, status: str) -> None:
        self._client.set_terminated(run_id, status)
