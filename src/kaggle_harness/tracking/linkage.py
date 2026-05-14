from __future__ import annotations

from uuid import UUID

from kaggle_harness.tracking.tracker import Tracker


def tag_experiment(tracker: Tracker, run_id: str, experiment_id: UUID, name: str) -> None:
    tracker.set_tag(run_id, "kaggle.experiment_id", str(experiment_id))
    tracker.set_tag(run_id, "kaggle.experiment_name", name)


def tag_scores(tracker: Tracker, run_id: str, public: float | None, private: float | None) -> None:
    if public is not None:
        tracker.log_metric(run_id, "kaggle.public_score", public)
    if private is not None:
        tracker.log_metric(run_id, "kaggle.private_score", private)
