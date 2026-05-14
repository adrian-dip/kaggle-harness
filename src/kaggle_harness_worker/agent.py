from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from kaggle_harness.protocol.messages import ArtifactRef, JobReport, JobStatus
from kaggle_harness_worker.client import GatewayClient
from kaggle_harness_worker.config import WorkerSettings
from kaggle_harness_worker.executor import DockerExecutor, ExecutionResult
from kaggle_harness_worker.reporter import LogReporter

logger = structlog.get_logger()


class Agent:
    def __init__(self, settings: WorkerSettings) -> None:
        self._settings = settings
        self._client = GatewayClient(settings)
        self._executor = DockerExecutor(docker_socket=settings.docker_socket)

    async def run(self) -> None:
        await self._client.register()
        logger.info("agent.registered", worker_id=self._settings.worker_id)

        while True:
            try:
                assignment = await self._client.claim()
            except Exception as exc:
                logger.warning("agent.claim_error", error=str(exc))
                await asyncio.sleep(self._settings.worker_poll_interval)
                continue

            if assignment is None:
                await asyncio.sleep(self._settings.worker_poll_interval)
                continue

            logger.info("agent.job_claimed", job_id=str(assignment.job_id))

            try:
                bundle_url = await self._client.bundle_url(assignment.bundle_id)
            except Exception as exc:
                logger.error("agent.bundle_url_error", error=str(exc))
                await self._client.report(
                    JobReport(
                        job_id=assignment.job_id,
                        status=JobStatus.failed,
                        error=f"bundle fetch failed: {exc}",
                    )
                )
                continue

            reporter = LogReporter(self._client, assignment.job_id)
            reporter.start()

            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(assignment.job_id)
            )

            try:
                result: ExecutionResult = await self._executor.run(
                    assignment, bundle_url, reporter.push
                )
            except Exception as exc:
                result = ExecutionResult(exit_code=1, error=str(exc))
            finally:
                heartbeat_task.cancel()
                await reporter.stop()

            if result.exit_code == 0:
                artifacts = await self._upload_artifacts(result.output_files, assignment.job_id)
                await self._client.report(
                    JobReport(
                        job_id=assignment.job_id,
                        status=JobStatus.succeeded,
                        artifacts=artifacts,
                    )
                )
                logger.info("agent.job_succeeded", job_id=str(assignment.job_id), artifacts=len(artifacts))
            else:
                await self._client.report(
                    JobReport(
                        job_id=assignment.job_id,
                        status=JobStatus.failed,
                        error=result.error or f"exit code {result.exit_code}",
                    )
                )
                logger.info("agent.job_failed", job_id=str(assignment.job_id), exit_code=result.exit_code)

    async def _upload_artifacts(
        self, output_files: dict[str, Path], job_id
    ) -> list[ArtifactRef]:
        refs: list[ArtifactRef] = []
        for name, path in output_files.items():
            try:
                data = path.read_bytes()
                ref = await self._client.upload_artifact(job_id, name, data)
                refs.append(ref)
                logger.debug("agent.artifact_uploaded", name=name)
            except Exception as exc:
                logger.warning("agent.artifact_upload_error", name=name, error=str(exc))
        return refs

    async def _heartbeat_loop(self, job_id) -> None:
        while True:
            await asyncio.sleep(self._settings.worker_heartbeat_interval)
            try:
                await self._client.heartbeat(job_id)
            except Exception as exc:
                logger.warning("agent.heartbeat_error", error=str(exc))


def main() -> None:
    from kaggle_harness.logging import configure_logging
    settings = WorkerSettings()
    configure_logging(debug=False)
    asyncio.run(Agent(settings).run())


if __name__ == "__main__":
    main()
