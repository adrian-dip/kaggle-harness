from __future__ import annotations

import re

import yaml
from pydantic import BaseModel, field_validator


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,62}$")


class RuntimeConfig(BaseModel):
    image: str = "runner-base:py311"
    requirements: str | None = None


class ResourceConfig(BaseModel):
    cpu: int = 1
    memory: str = "4G"
    gpu: bool = False
    labels: list[str] = []


class InputsConfig(BaseModel):
    competitions: list[str] = []
    datasets: list[str] = []


class MlflowConfig(BaseModel):
    experiment: str


class SubmitConfig(BaseModel):
    competition: str
    file: str
    message: str = "{name}"


class ExperimentManifest(BaseModel):
    name: str
    entrypoint: str
    runtime: RuntimeConfig = RuntimeConfig()
    resources: ResourceConfig = ResourceConfig()
    inputs: InputsConfig = InputsConfig()
    outputs: list[str] = []
    env: dict[str, str] = {}
    mlflow: MlflowConfig | None = None
    submit: SubmitConfig | None = None

    @field_validator("name")
    @classmethod
    def _name_is_slug(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(f"name must be a lowercase slug, got {v!r}")
        return v

    @classmethod
    def from_yaml(cls, text: str) -> "ExperimentManifest":
        data = yaml.safe_load(text)
        return cls.model_validate(data)

    def memory_mb(self) -> int:
        raw = self.resources.memory.upper()
        if raw.endswith("G"):
            return int(raw[:-1]) * 1024
        if raw.endswith("M"):
            return int(raw[:-1])
        return int(raw)
