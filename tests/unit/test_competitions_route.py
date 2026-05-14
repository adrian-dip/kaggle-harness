"""
Unit tests for /competitions routes.
Uses a FakeKaggleClient so no real Kaggle credentials are needed.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kaggle_harness.api.app import create_app
from kaggle_harness.api.deps import get_kaggle_service
from kaggle_harness.kaggle.client import (
    Competition,
    CompetitionFile,
    Dataset,
    Kernel,
    KaggleClient,
    SubmissionRef,
    SubmissionStatus,
)
from kaggle_harness.kaggle.service import KaggleService


class FakeKaggleClient(KaggleClient):
    def competitions_list(self, *, search: str | None = None, page: int = 1) -> list[Competition]:
        all_comps = [
            Competition(
                ref="titanic",
                title="Titanic - Machine Learning from Disaster",
                url="https://www.kaggle.com/c/titanic",
                category="gettingStarted",
                reward="Knowledge",
                team_count=50000,
            ),
            Competition(
                ref="house-prices-advanced-regression-techniques",
                title="House Prices - Advanced Regression Techniques",
                url="https://www.kaggle.com/c/house-prices-advanced-regression-techniques",
                category="gettingStarted",
                reward="Knowledge",
                team_count=30000,
            ),
        ]
        if search:
            return [c for c in all_comps if search.lower() in c.title.lower()]
        return all_comps

    def competition_files(self, slug: str) -> list[CompetitionFile]:
        if slug == "titanic":
            return [
                CompetitionFile(name="train.csv", size=61194),
                CompetitionFile(name="test.csv", size=28629),
            ]
        return []

    def download_competition_files(self, slug: str, dest: Path) -> None:
        pass

    def datasets_list(self, *, search: str | None = None, page: int = 1) -> list[Dataset]:
        return []

    def download_dataset_files(self, slug: str, dest: Path) -> None:
        pass

    def kernels_list(self, *, search: str | None = None, page: int = 1) -> list[Kernel]:
        return []

    def submit(self, competition: str, file: Path, message: str) -> SubmissionRef:
        raise NotImplementedError

    def submissions(self, competition: str) -> list[SubmissionStatus]:
        return []


@pytest.fixture
def client():
    app = create_app()
    fake_svc = KaggleService(FakeKaggleClient())
    app.dependency_overrides[get_kaggle_service] = lambda: fake_svc
    with TestClient(app) as c:
        yield c


def test_list_competitions_returns_all(client):
    resp = client.get("/competitions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    refs = {c["ref"] for c in data}
    assert "titanic" in refs


def test_list_competitions_search_match(client):
    resp = client.get("/competitions?search=titanic")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ref"] == "titanic"


def test_list_competitions_search_no_match(client):
    resp = client.get("/competitions?search=zzz_nonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_competitions_response_shape(client):
    resp = client.get("/competitions")
    assert resp.status_code == 200
    comp = resp.json()[0]
    assert "ref" in comp
    assert "title" in comp
    assert "team_count" in comp


def test_competition_files(client):
    resp = client.get("/competitions/titanic/files")
    assert resp.status_code == 200
    files = resp.json()
    assert len(files) == 2
    names = {f["name"] for f in files}
    assert "train.csv" in names
    assert "test.csv" in names


def test_competition_files_unknown_slug(client):
    resp = client.get("/competitions/unknown-comp/files")
    assert resp.status_code == 200
    assert resp.json() == []
