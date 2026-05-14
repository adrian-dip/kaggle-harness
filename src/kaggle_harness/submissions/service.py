from __future__ import annotations

import io
import tempfile
from pathlib import Path
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kaggle_harness.bundles.store import BundleStore
from kaggle_harness.kaggle.service import KaggleService
from kaggle_harness.submissions.models import Submission
from kaggle_harness.tracking.linkage import tag_scores
from kaggle_harness.tracking.tracker import Tracker

logger = structlog.get_logger()


class SubmissionService:
    def __init__(
        self,
        session: AsyncSession,
        kaggle: KaggleService,
        artifact_store: BundleStore,
        tracker: Tracker,
    ) -> None:
        self._session = session
        self._kaggle = kaggle
        self._artifacts = artifact_store
        self._tracker = tracker

    async def submit(
        self,
        experiment_id: UUID,
        mlflow_run_id: str | None,
        competition: str,
        store_key: str,
        message: str,
    ) -> Submission:
        artifact_bytes = await self._artifacts.get(store_key)
        filename = store_key.rsplit("/", 1)[-1]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            path.write_bytes(artifact_bytes)
            ref = await self._kaggle.submit(competition, path, message)

        sub = Submission(
            experiment_id=experiment_id,
            competition=competition,
            kaggle_ref=ref.ref,
            status="running",
        )
        self._session.add(sub)
        await self._session.commit()
        await self._session.refresh(sub)
        logger.info("submission.created", submission_id=str(sub.id), ref=ref.ref)
        return sub

    async def poll_once(self, submission_id: UUID) -> bool:
        """Check Kaggle for a score. Returns True if terminal (scored or failed)."""
        result = await self._session.execute(
            text("SELECT * FROM submissions WHERE id=:id"), {"id": submission_id}
        )
        row = result.mappings().first()
        if row is None:
            return True
        sub = Submission(**dict(row))

        statuses = await self._kaggle.submissions(sub.competition)
        match = next((s for s in statuses if s.ref == sub.kaggle_ref), None)
        if match is None:
            return False

        if match.status in ("complete", "error"):
            new_status = "scored" if match.status == "complete" else "failed"
            await self._session.execute(
                text("""
                    UPDATE submissions
                    SET status=:status, public_score=:pub, private_score=:priv
                    WHERE id=:id
                """),
                {
                    "id": submission_id,
                    "status": new_status,
                    "pub": match.public_score,
                    "priv": match.private_score,
                },
            )
            await self._session.commit()

            if new_status == "scored":
                exp_result = await self._session.execute(
                    text("SELECT mlflow_run_id FROM experiments WHERE id=:id"),
                    {"id": sub.experiment_id},
                )
                exp_row = exp_result.mappings().first()
                run_id = exp_row["mlflow_run_id"] if exp_row else None
                if run_id:
                    tag_scores(self._tracker, run_id, match.public_score, match.private_score)

            logger.info(
                "submission.scored",
                submission_id=str(submission_id),
                public=match.public_score,
            )
            return True

        return False

    async def get(self, submission_id: UUID) -> Submission | None:
        result = await self._session.execute(
            text("SELECT * FROM submissions WHERE id=:id"), {"id": submission_id}
        )
        row = result.mappings().first()
        return Submission(**dict(row)) if row else None

    async def list_for_experiment(self, experiment_id: UUID) -> list[Submission]:
        result = await self._session.execute(
            text("SELECT * FROM submissions WHERE experiment_id=:eid ORDER BY created_at"),
            {"eid": experiment_id},
        )
        return [Submission(**dict(r)) for r in result.mappings().all()]
