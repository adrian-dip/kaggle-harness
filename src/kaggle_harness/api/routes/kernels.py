from fastapi import APIRouter, Depends, Query

from kaggle_harness.api.deps import get_kaggle_service
from kaggle_harness.kaggle.client import Kernel
from kaggle_harness.kaggle.service import KaggleService

router = APIRouter(prefix="/kernels", tags=["kernels"])


@router.get("", response_model=list[Kernel])
async def list_kernels(
    search: str | None = Query(None, description="Filter by keyword"),
    page: int = Query(1, ge=1),
    svc: KaggleService = Depends(get_kaggle_service),
) -> list[Kernel]:
    return await svc.list_kernels(search=search, page=page)
