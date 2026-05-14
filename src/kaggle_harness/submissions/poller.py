from __future__ import annotations

import asyncio
from uuid import UUID

import structlog
from fastapi import FastAPI

from kaggle_harness.submissions.service import SubmissionService

logger = structlog.get_logger()

_pending: dict[UUID, asyncio.Task] = {}


def schedule(app: FastAPI, submission_id: UUID) -> None:
    """Start a background polling task for a submission."""
    task = asyncio.create_task(_poll_loop(app, submission_id))
    _pending[submission_id] = task
    task.add_done_callback(lambda _: _pending.pop(submission_id, None))


async def _poll_loop(app: FastAPI, submission_id: UUID) -> None:
    while True:
        await asyncio.sleep(30)
        try:
            async with app.state.session_factory() as session:
                svc = SubmissionService(
                    session=session,
                    kaggle=app.state.kaggle_service,
                    artifact_store=app.state.artifact_store,
                    tracker=app.state.tracker,
                )
                done = await svc.poll_once(submission_id)
                if done:
                    return
        except Exception as exc:
            logger.warning("submission.poll_error", submission_id=str(submission_id), error=str(exc))
