import httpx

from ..ratelimit import RateLimiter
from .base import Finding, register

REQUIRED_HEADERS = {
    "content-security-policy": ("low", "Content-Security-Policy manquant"),
    "strict-transport-security": ("medium", "Strict-Transport-Security (HSTS) manquant"),
    "x-content-type-options": ("low", "X-Content-Type-Options manquant"),
    "x-frame-options": ("low", "X-Frame-Options manquant (clickjacking possible)"),
}


@register("security_headers")
async def check(base_url: str, client: httpx.AsyncClient, limiter: RateLimiter) -> list[Finding]:
    async with limiter:
        try:
            resp = await client.get(base_url, timeout=10.0, follow_redirects=True)
        except httpx.HTTPError:
            return []

    headers = {k.lower() for k in resp.headers.keys()}
    findings = []
    for header, (severity, title) in REQUIRED_HEADERS.items():
        if header not in headers:
            findings.append(Finding(check_name="security_headers", severity=severity, title=title))

    server = resp.headers.get("server")
    if server:
        findings.append(
            Finding(
                check_name="security_headers",
                severity="info",
                title="Bannière serveur exposée",
                detail=server,
            )
        )
    return findings
