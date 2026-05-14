from __future__ import annotations

import io
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

import structlog

from kaggle_harness.bundles.store import BundleStore
from kaggle_harness.kaggle.service import KaggleService

logger = structlog.get_logger()


class InputsStager:
    """Downloads competition/dataset files from Kaggle into MinIO, with caching."""

    def __init__(self, kaggle: KaggleService, store: BundleStore) -> None:
        self._kaggle = kaggle
        self._store = store

    async def stage_competition(self, slug: str) -> str:
        """Return MinIO key for the staged competition zip, downloading if absent."""
        key = f"competition/{slug}.zip"
        if await self._exists(key):
            logger.debug("inputs.cache_hit", type="competition", slug=slug)
            return key
        logger.info("inputs.staging", type="competition", slug=slug)
        data = await self._download_competition(slug)
        await self._store.put(key, io.BytesIO(data))
        return key

    async def stage_dataset(self, slug: str) -> str:
        """Return MinIO key for the staged dataset zip, downloading if absent."""
        safe = slug.replace("/", "__")
        key = f"dataset/{safe}.zip"
        if await self._exists(key):
            logger.debug("inputs.cache_hit", type="dataset", slug=slug)
            return key
        logger.info("inputs.staging", type="dataset", slug=slug)
        data = await self._download_dataset(slug)
        await self._store.put(key, io.BytesIO(data))
        return key

    async def signed_url(self, key: str) -> str:
        return await self._store.signed_url(key, ttl=timedelta(hours=1))

    async def _exists(self, key: str) -> bool:
        try:
            await self._store.get(key)
            return True
        except Exception:
            return False

    async def _download_competition(self, slug: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / slug
            dest.mkdir()
            await self._kaggle.download_competition_files(slug, dest)
            return _zip_dir(dest)

    async def _download_dataset(self, slug: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / slug.replace("/", "__")
            dest.mkdir()
            await self._kaggle.download_dataset_files(slug, dest)
            return _zip_dir(dest)


def _zip_dir(directory: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in directory.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(directory))
    return buf.getvalue()
