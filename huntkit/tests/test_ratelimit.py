import asyncio
import time

from huntkit.ratelimit import RateLimiter


def test_rate_limiter_enforces_min_interval():
    async def run() -> float:
        limiter = RateLimiter(max_concurrency=5, requests_per_second=10)
        start = time.monotonic()
        for _ in range(5):
            async with limiter:
                pass
        return time.monotonic() - start

    elapsed = asyncio.run(run())
    assert elapsed >= 0.35  # 4 intervals of 0.1s between 5 sequential requests


def test_rate_limiter_caps_concurrency():
    async def run() -> int:
        limiter = RateLimiter(max_concurrency=2, requests_per_second=1000)
        active = 0
        max_active = 0

        async def task() -> None:
            nonlocal active, max_active
            async with limiter:
                active += 1
                max_active = max(max_active, active)
                await asyncio.sleep(0.05)
                active -= 1

        await asyncio.gather(*(task() for _ in range(6)))
        return max_active

    assert asyncio.run(run()) <= 2
