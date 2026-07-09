import asyncio

import httpx

from . import scope
from .checks import CHECKS, Finding
from .db import get_connection, init_db
from .ratelimit import RateLimiter
from .recon.ports import scan_host
from .recon.subdomains import enumerate_subdomains


async def _probe_base_url(hostname: str, client: httpx.AsyncClient, limiter: RateLimiter) -> str | None:
    for scheme in ("https", "http"):
        url = f"{scheme}://{hostname}"
        async with limiter:
            try:
                resp = await client.get(url, timeout=8.0, follow_redirects=True)
            except httpx.HTTPError:
                continue
        if resp.status_code < 500:
            return url
    return None


async def run_recon(
    domain: str,
    max_concurrency: int = 10,
    requests_per_second: float = 5.0,
    wordlist: list[str] | None = None,
) -> dict:
    scope.require_in_scope(domain)
    init_db()

    limiter = RateLimiter(max_concurrency=max_concurrency, requests_per_second=requests_per_second)

    subdomains = await enumerate_subdomains(domain, limiter)
    if not subdomains:
        subdomains = []

    conn = get_connection()
    try:
        for sub in subdomains:
            conn.execute(
                """
                INSERT INTO subdomains (root_domain, hostname, ip, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(root_domain, hostname) DO UPDATE SET
                    ip = excluded.ip, last_seen = datetime('now')
                """,
                (domain, sub.hostname, sub.ip, sub.source),
            )
        conn.commit()
    finally:
        conn.close()

    hosts = [s.hostname for s in subdomains if s.ip] or [domain]

    all_ports = await asyncio.gather(*(scan_host(h, limiter) for h in hosts))
    conn = get_connection()
    try:
        for host, ports in zip(hosts, all_ports):
            for op in ports:
                conn.execute(
                    """
                    INSERT INTO open_ports (hostname, port, banner) VALUES (?, ?, ?)
                    ON CONFLICT(hostname, port) DO UPDATE SET banner = excluded.banner, found_at = datetime('now')
                    """,
                    (op.hostname, op.port, op.banner),
                )
        conn.commit()
    finally:
        conn.close()

    async with httpx.AsyncClient() as client:
        base_urls = await asyncio.gather(*(_probe_base_url(h, client, limiter) for h in hosts))

        all_findings: list[tuple[str, Finding]] = []
        for host, base_url in zip(hosts, base_urls):
            if not base_url:
                continue
            for check_fn in CHECKS.values():
                findings = await check_fn(base_url, client, limiter)
                for f in findings:
                    all_findings.append((host, f))

    conn = get_connection()
    try:
        for host, f in all_findings:
            conn.execute(
                """
                INSERT INTO findings (root_domain, hostname, check_name, severity, title, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(hostname, check_name, title) DO UPDATE SET found_at = datetime('now')
                """,
                (domain, host, f.check_name, f.severity, f.title, f.detail),
            )
        conn.commit()
    finally:
        conn.close()

    return {
        "domain": domain,
        "subdomains_found": len(subdomains),
        "hosts_scanned": len(hosts),
        "findings": len(all_findings),
    }
