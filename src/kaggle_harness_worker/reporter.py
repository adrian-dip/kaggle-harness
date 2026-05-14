from __future__ import annotations

import asyncio
from typing import Callable
from uuid import UUID

from kaggle_harness_worker.client import GatewayClient


class LogReporter:
    def __init__(self, client: GatewayClient, job_id: UUID) -> None:
        self._client = client
        self._job_id = job_id
        self._seq = 0
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._drain())

    def push(self, text: str) -> None:
        self._queue.put_nowait(text)

    async def stop(self) -> None:
        self._queue.put_nowait(None)
        if self._task:
            await self._task

    async def _drain(self) -> None:
        while True:
            text = await self._queue.get()
            if text is None:
                break
            try:
                await self._client.send_log(self._job_id, self._seq, text)
                self._seq += 1
            except Exception:
                pass
