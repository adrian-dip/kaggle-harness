from fastapi import APIRouter, Depends, Query

from kaggle_harness.api.deps import get_kaggle_service
from kaggle_harness.kaggle.client import Dataset
from kaggle_harness.kaggle.service import KaggleService

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[Dataset])
async def list_datasets(
    search: str | None = Query(None, description="Filter by keyword"),
    page: int = Query(1, ge=1),
    svc: KaggleService = Depends(get_kaggle_service),
) -> list[Dataset]:
    return await svc.list_datasets(search=search, page=page)
