import asyncio
from dataclasses import dataclass

from ..ratelimit import RateLimiter

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 587, 993, 995,
    1433, 1521, 3000, 3306, 3389, 5000, 5432, 5900, 6379, 8000, 8080,
    8081, 8443, 8888, 9000, 9090, 9200, 27017,
]


@dataclass
class OpenPort:
    hostname: str
    port: int
    banner: str


async def _grab_banner(reader: asyncio.StreamReader) -> str:
    try:
        data = await asyncio.wait_for(reader.read(128), timeout=1.0)
        return data.decode(errors="ignore").strip().replace("\r", "").replace("\n", " ")[:120]
    except (asyncio.TimeoutError, OSError):
        return ""


async def _check_port(host: str, port: int, limiter: RateLimiter, timeout: float) -> OpenPort | None:
    async with limiter:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )
        except (OSError, asyncio.TimeoutError):
            return None

    try:
        banner = await _grab_banner(reader)
    finally:
        writer.close()

    return OpenPort(hostname=host, port=port, banner=banner)


async def scan_host(
    hostname: str, limiter: RateLimiter, ports: list[int] | None = None, timeout: float = 2.0
) -> list[OpenPort]:
    port_list = ports if ports is not None else COMMON_PORTS
    results = await asyncio.gather(*(_check_port(hostname, p, limiter, timeout) for p in port_list))
    return [r for r in results if r is not None]
