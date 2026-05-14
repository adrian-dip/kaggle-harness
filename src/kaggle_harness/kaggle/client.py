from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Value objects returned by the client
# ---------------------------------------------------------------------------

class Competition(BaseModel):
    ref: str
    title: str
    url: str = ""
    deadline: datetime | None = None
    category: str = ""
    reward: str = ""
    team_count: int = 0
    user_has_entered: bool = False


class CompetitionFile(BaseModel):
    name: str
    size: int = 0
    creation_date: datetime | None = None


class Dataset(BaseModel):
    ref: str
    title: str
    size: int = 0
    last_updated: datetime | None = None
    download_count: int = 0
    vote_count: int = 0
    usability_rating: float | None = None


class Kernel(BaseModel):
    ref: str
    title: str
    author: str = ""
    last_run_time: datetime | None = None
    total_votes: int = 0
    language: str = ""
    kernel_type: str = ""


class SubmissionRef(BaseModel):
    ref: str
    message: str


class SubmissionStatus(BaseModel):
    ref: str
    file_name: str = ""
    date: datetime | None = None
    description: str = ""
    status: str = ""
    public_score: float | None = None
    private_score: float | None = None


# ---------------------------------------------------------------------------
# Abstract interface — the seam used by KaggleService and mocked in tests
# ---------------------------------------------------------------------------

class KaggleClient(ABC):
    @abstractmethod
    def competitions_list(self, *, search: str | None = None, page: int = 1) -> list[Competition]: ...

    @abstractmethod
    def competition_files(self, slug: str) -> list[CompetitionFile]: ...

    @abstractmethod
    def download_competition_files(self, slug: str, dest: Path) -> None: ...

    @abstractmethod
    def datasets_list(self, *, search: str | None = None, page: int = 1) -> list[Dataset]: ...

    @abstractmethod
    def download_dataset_files(self, slug: str, dest: Path) -> None: ...

    @abstractmethod
    def kernels_list(self, *, search: str | None = None, page: int = 1) -> list[Kernel]: ...

    @abstractmethod
    def submit(self, competition: str, file: Path, message: str) -> SubmissionRef: ...

    @abstractmethod
    def submissions(self, competition: str) -> list[SubmissionStatus]: ...


# ---------------------------------------------------------------------------
# Real implementation — wraps the official kaggle-api library (sync)
# ---------------------------------------------------------------------------

def _get(obj: object, *names: str, default=None):
    """Try attribute names in order, return first hit or default."""
    for name in names:
        val = getattr(obj, name, None)
        if val is not None:
            return val
    return default


class KaggleApiClient(KaggleClient):
    def __init__(
        self,
        kaggle_username: str | None = None,
        kaggle_key: str | None = None,
        kaggle_config_dir: str | None = None,
    ) -> None:
        import os
        if kaggle_username:
            os.environ["KAGGLE_USERNAME"] = kaggle_username
        if kaggle_key:
            os.environ["KAGGLE_KEY"] = kaggle_key
        if kaggle_config_dir:
            os.environ["KAGGLE_CONFIG_DIR"] = kaggle_config_dir

        from kaggle.api.kaggle_api_extended import KaggleApi
        self._api = KaggleApi()
        self._api.authenticate()

    # --- competitions ---

    def competitions_list(self, *, search: str | None = None, page: int = 1) -> list[Competition]:
        results = self._api.competitions_list(search=search or "", page=page)
        return [self._to_competition(c) for c in (results or [])]

    def competition_files(self, slug: str) -> list[CompetitionFile]:
        results = self._api.competition_list_files(slug)
        return [self._to_competition_file(f) for f in (results or [])]

    def download_competition_files(self, slug: str, dest: Path) -> None:
        self._api.competition_download_files(slug, path=str(dest))

    # --- datasets ---

    def datasets_list(self, *, search: str | None = None, page: int = 1) -> list[Dataset]:
        results = self._api.dataset_list(search=search or "", page=page)
        return [self._to_dataset(d) for d in (results or [])]

    def download_dataset_files(self, slug: str, dest: Path) -> None:
        self._api.dataset_download_files(slug, path=str(dest))

    # --- kernels ---

    def kernels_list(self, *, search: str | None = None, page: int = 1) -> list[Kernel]:
        results = self._api.kernels_list(search=search or "", page=page)
        return [self._to_kernel(k) for k in (results or [])]

    # --- submissions ---

    def submit(self, competition: str, file: Path, message: str) -> SubmissionRef:
        self._api.competition_submit(str(file), message, competition)
        return SubmissionRef(ref="", message=message)

    def submissions(self, competition: str) -> list[SubmissionStatus]:
        results = self._api.competitions_submissions_list(competition)
        return [self._to_submission_status(s) for s in (results or [])]

    # --- converters ---

    @staticmethod
    def _to_competition(obj: object) -> Competition:
        return Competition(
            ref=str(_get(obj, "ref") or ""),
            title=str(_get(obj, "title") or ""),
            url=str(_get(obj, "url") or ""),
            deadline=_get(obj, "deadline"),
            category=str(_get(obj, "category") or ""),
            reward=str(_get(obj, "reward") or ""),
            team_count=int(_get(obj, "teamCount") or 0),
            user_has_entered=bool(_get(obj, "userHasEntered")),
        )

    @staticmethod
    def _to_competition_file(obj: object) -> CompetitionFile:
        return CompetitionFile(
            name=str(_get(obj, "name") or ""),
            size=int(_get(obj, "size") or 0),
            creation_date=_get(obj, "creationDate"),
        )

    @staticmethod
    def _to_dataset(obj: object) -> Dataset:
        return Dataset(
            ref=str(_get(obj, "ref") or ""),
            title=str(_get(obj, "title") or ""),
            size=int(_get(obj, "size") or 0),
            last_updated=_get(obj, "lastUpdated"),
            download_count=int(_get(obj, "downloadCount") or 0),
            vote_count=int(_get(obj, "voteCount") or 0),
            usability_rating=_get(obj, "usabilityRating"),
        )

    @staticmethod
    def _to_kernel(obj: object) -> Kernel:
        return Kernel(
            ref=str(_get(obj, "ref") or ""),
            title=str(_get(obj, "title") or ""),
            author=str(_get(obj, "author") or ""),
            last_run_time=_get(obj, "lastRunTime"),
            total_votes=int(_get(obj, "totalVotes") or 0),
            language=str(_get(obj, "language") or ""),
            kernel_type=str(_get(obj, "kernelType") or ""),
        )

    @staticmethod
    def _to_submission_status(obj: object) -> SubmissionStatus:
        return SubmissionStatus(
            ref=str(_get(obj, "ref") or ""),
            file_name=str(_get(obj, "fileName") or ""),
            date=_get(obj, "date"),
            description=str(_get(obj, "description") or ""),
            status=str(_get(obj, "status") or ""),
            public_score=_get(obj, "publicScore"),
            private_score=_get(obj, "privateScore"),
        )
