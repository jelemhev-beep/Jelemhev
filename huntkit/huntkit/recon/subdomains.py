import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import httpx

from ..ratelimit import RateLimiter

WORDLIST_PATH = Path(__file__).resolve().parent.parent / "wordlists" / "subdomains.txt"


@dataclass
class Subdomain:
    hostname: str
    ip: str | None
    source: str


def _load_wordlist() -> list[str]:
    return [line.strip() for line in WORDLIST_PATH.read_text().splitlines() if line.strip()]


async def passive_crtsh(domain: str, client: httpx.AsyncClient) -> set[str]:
    """Certificate Transparency logs (crt.sh): public data anyone can query,
    listing every certificate ever issued for the domain and its subdomains.
    """
    url = "https://crt.sh/"
    try:
        resp = await client.get(url, params={"q": f"%.{domain}", "output": "json"}, timeout=20.0)
        resp.raise_for_status()
        entries = json.loads(resp.text)
    except (httpx.HTTPError, json.JSONDecodeError, ValueError):
        return set()

    names = set()
    for entry in entries:
        for name in entry.get("name_value", "").splitlines():
            name = name.strip().lower().lstrip("*.")
            if name and name.endswith(domain):
                names.add(name)
    return names


async def _resolve(hostname: str, limiter: RateLimiter) -> str | None:
    loop = asyncio.get_running_loop()
    async with limiter:
        try:
            infos = await asyncio.wait_for(loop.getaddrinfo(hostname, None), timeout=5.0)
        except (OSError, asyncio.TimeoutError):
            return None
    if not infos:
        return None
    return infos[0][4][0]


async def brute_force(domain: str, limiter: RateLimiter, wordlist: list[str] | None = None) -> list[Subdomain]:
    words = wordlist if wordlist is not None else _load_wordlist()
    candidates = [f"{word}.{domain}" for word in words]

    results = await asyncio.gather(*(_resolve(host, limiter) for host in candidates))
    found = []
    for host, ip in zip(candidates, results):
        if ip:
            found.append(Subdomain(hostname=host, ip=ip, source="bruteforce"))
    return found


async def enumerate_subdomains(domain: str, limiter: RateLimiter) -> list[Subdomain]:
    async with httpx.AsyncClient() as client:
        passive_names = await passive_crtsh(domain, client)

    brute_results = await brute_force(domain, limiter)
    brute_hosts = {s.hostname for s in brute_results}

    results = list(brute_results)
    passive_only = passive_names - brute_hosts - {domain}
    if passive_only:
        resolved = await asyncio.gather(*(_resolve(host, limiter) for host in passive_only))
        for host, ip in zip(passive_only, resolved):
            results.append(Subdomain(hostname=host, ip=ip, source="crtsh"))

    return results
