from fastapi import APIRouter, Depends, Query

from kaggle_harness.api.deps import get_kaggle_service
from kaggle_harness.kaggle.client import Competition, CompetitionFile
from kaggle_harness.kaggle.service import KaggleService

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[Competition])
async def list_competitions(
    search: str | None = Query(None, description="Filter by keyword"),
    page: int = Query(1, ge=1),
    svc: KaggleService = Depends(get_kaggle_service),
) -> list[Competition]:
    return await svc.list_competitions(search=search, page=page)


@router.get("/{slug}/files", response_model=list[CompetitionFile])
async def competition_files(
    slug: str,
    svc: KaggleService = Depends(get_kaggle_service),
) -> list[CompetitionFile]:
    return await svc.competition_files(slug)
