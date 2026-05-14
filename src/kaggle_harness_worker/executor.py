from __future__ import annotations

import asyncio
import io
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import docker
import httpx

from kaggle_harness.protocol.messages import JobAssignment, StagedInput


@dataclass
class ExecutionResult:
    exit_code: int
    output_files: dict[str, Path] = field(default_factory=dict)  # name → local path
    error: str | None = None


class Executor(ABC):
    @abstractmethod
    async def run(
        self,
        assignment: JobAssignment,
        bundle_url: str,
        on_log: Callable[[str], None],
    ) -> ExecutionResult: ...


class DockerExecutor(Executor):
    def __init__(self, docker_socket: str = "unix:///var/run/docker.sock") -> None:
        self._socket = docker_socket

    async def run(
        self,
        assignment: JobAssignment,
        bundle_url: str,
        on_log: Callable[[str], None],
    ) -> ExecutionResult:
        return await asyncio.to_thread(self._run_sync, assignment, bundle_url, on_log)

    def _run_sync(
        self,
        assignment: JobAssignment,
        bundle_url: str,
        on_log: Callable[[str], None],
    ) -> ExecutionResult:
        client = docker.DockerClient(base_url=self._socket)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            out_dir = Path(tmpdir) / "out"
            data_dir = Path(tmpdir) / "data"
            workspace.mkdir()
            out_dir.mkdir()
            data_dir.mkdir()

            # Fetch and unpack bundle
            try:
                resp = httpx.get(bundle_url, follow_redirects=True, timeout=120)
                resp.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    zf.extractall(workspace)
            except Exception as exc:
                return ExecutionResult(exit_code=1, error=f"bundle fetch failed: {exc}")

            # Fetch and unpack staged inputs
            for staged in assignment.staged_inputs:
                try:
                    resp = httpx.get(staged.download_url, follow_redirects=True, timeout=300)
                    resp.raise_for_status()
                    dest = data_dir / staged.local_path.lstrip("/").replace("/data/", "", 1)
                    dest.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                        zf.extractall(dest)
                except Exception as exc:
                    return ExecutionResult(exit_code=1, error=f"input fetch failed ({staged.local_path}): {exc}")

            env = dict(assignment.env)
            if assignment.mlflow_tracking_uri:
                env["MLFLOW_TRACKING_URI"] = assignment.mlflow_tracking_uri
            if assignment.mlflow_run_id:
                env["MLFLOW_RUN_ID"] = assignment.mlflow_run_id
            if assignment.mlflow_experiment_name:
                env["MLFLOW_EXPERIMENT_NAME"] = assignment.mlflow_experiment_name

            volumes = {
                str(workspace): {"bind": "/workspace", "mode": "ro"},
                str(out_dir): {"bind": "/out", "mode": "rw"},
                str(data_dir): {"bind": "/data", "mode": "ro"},
            }

            cmd = assignment.entrypoint
            if assignment.requirements_file:
                cmd = f"pip install -q -r /workspace/{assignment.requirements_file} && {cmd}"

            try:
                container = client.containers.run(
                    image=assignment.image,
                    command=["sh", "-c", cmd],
                    working_dir="/workspace",
                    environment=env,
                    volumes=volumes,
                    detach=True,
                    remove=False,
                )

                for log_line in container.logs(stream=True, follow=True):
                    on_log(log_line.decode(errors="replace").rstrip())

                result = container.wait()
                exit_code = result.get("StatusCode", 1)
                container.remove()

                if exit_code == 0:
                    output_files = self._collect_outputs(out_dir, assignment.declared_outputs)
                    return ExecutionResult(exit_code=0, output_files=output_files)
                return ExecutionResult(exit_code=exit_code)

            except Exception as exc:
                return ExecutionResult(exit_code=1, error=str(exc))

    @staticmethod
    def _collect_outputs(out_dir: Path, declared: list[str]) -> dict[str, Path]:
        files: dict[str, Path] = {}
        for name in declared:
            path = out_dir / name
            if path.exists():
                files[name] = path
        # Also collect any undeclared files
        for path in out_dir.rglob("*"):
            if path.is_file():
                rel = str(path.relative_to(out_dir))
                files.setdefault(rel, path)
        return files
