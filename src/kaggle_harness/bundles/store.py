from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import BinaryIO

from aiobotocore.session import get_session


class BundleStore(ABC):
    @abstractmethod
    async def put(self, bundle_id: str, data: BinaryIO) -> None: ...

    @abstractmethod
    async def get(self, bundle_id: str) -> bytes: ...

    @abstractmethod
    async def signed_url(self, bundle_id: str, ttl: timedelta) -> str: ...


class MinioBundleStore(BundleStore):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._secure = secure

    def _client_ctx(self):
        proto = "https" if self._secure else "http"
        session = get_session()
        return session.create_client(
            "s3",
            endpoint_url=f"{proto}://{self._endpoint}",
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        )

    async def put(self, bundle_id: str, data: BinaryIO) -> None:
        async with self._client_ctx() as s3:
            await s3.put_object(Bucket=self._bucket, Key=bundle_id, Body=data)

    async def get(self, bundle_id: str) -> bytes:
        async with self._client_ctx() as s3:
            resp = await s3.get_object(Bucket=self._bucket, Key=bundle_id)
            return await resp["Body"].read()

    async def signed_url(self, bundle_id: str, ttl: timedelta) -> str:
        async with self._client_ctx() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": bundle_id},
                ExpiresIn=int(ttl.total_seconds()),
            )

    async def signed_put_url(self, key: str, ttl: timedelta) -> str:
        async with self._client_ctx() as s3:
            return await s3.generate_presigned_url(
                "put_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=int(ttl.total_seconds()),
            )


class ArtifactStore(MinioBundleStore):
    """Thin subclass — same storage, different bucket."""
