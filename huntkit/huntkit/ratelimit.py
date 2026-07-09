import asyncio
import time


class RateLimiter:
    """Caps both concurrency and requests-per-second, per host.

    Being a good citizen matters here: most bug bounty programs specify a
    max request rate in their policy, and hammering a target is how scanners
    get IPs banned (or scope revoked).
    """

    def __init__(self, max_concurrency: int = 10, requests_per_second: float = 5.0):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def acquire(self) -> None:
        await self._semaphore.acquire()
        async with self._lock:
            now = time.monotonic()
            wait = self._last_request_at + self._min_interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()

    def release(self) -> None:
        self._semaphore.release()

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.release()
