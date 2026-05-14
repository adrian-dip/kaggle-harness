import asyncio
from pathlib import Path

from kaggle_harness.kaggle.client import (
    Competition,
    CompetitionFile,
    Dataset,
    Kernel,
    KaggleClient,
    SubmissionRef,
    SubmissionStatus,
)


class KaggleService:
    def __init__(self, client: KaggleClient) -> None:
        self._client = client

    async def list_competitions(self, *, search: str | None = None, page: int = 1) -> list[Competition]:
        return await asyncio.to_thread(self._client.competitions_list, search=search, page=page)

    async def competition_files(self, slug: str) -> list[CompetitionFile]:
        return await asyncio.to_thread(self._client.competition_files, slug)

    async def download_competition_files(self, slug: str, dest: Path) -> None:
        await asyncio.to_thread(self._client.download_competition_files, slug, dest)

    async def list_datasets(self, *, search: str | None = None, page: int = 1) -> list[Dataset]:
        return await asyncio.to_thread(self._client.datasets_list, search=search, page=page)

    async def download_dataset_files(self, slug: str, dest: Path) -> None:
        await asyncio.to_thread(self._client.download_dataset_files, slug, dest)

    async def list_kernels(self, *, search: str | None = None, page: int = 1) -> list[Kernel]:
        return await asyncio.to_thread(self._client.kernels_list, search=search, page=page)

    async def submit(self, competition: str, file: Path, message: str) -> SubmissionRef:
        return await asyncio.to_thread(self._client.submit, competition, file, message)

    async def submissions(self, competition: str) -> list[SubmissionStatus]:
        return await asyncio.to_thread(self._client.submissions, competition)
