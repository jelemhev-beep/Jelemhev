import asyncio
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from ..ratelimit import RateLimiter
from .base import Finding, register


def _parse_cert_date(value: str) -> datetime:
    return datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)


def _get_certificate(hostname: str, port: int, timeout: float) -> dict | None:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket_connect(hostname, port, timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
            return tls_sock.getpeercert()


def socket_connect(hostname: str, port: int, timeout: float):
    import socket

    sock = socket.create_connection((hostname, port), timeout=timeout)
    return sock


@register("tls_check")
async def check(base_url: str, client: httpx.AsyncClient, limiter: RateLimiter) -> list[Finding]:
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        return []
    hostname = parsed.hostname
    port = parsed.port or 443
    if not hostname:
        return []

    async with limiter:
        try:
            cert = await asyncio.wait_for(
                asyncio.to_thread(_get_certificate, hostname, port, 5.0), timeout=8.0
            )
        except (OSError, ssl.SSLError, asyncio.TimeoutError):
            return []

    if not cert:
        return []

    findings = []

    not_after = cert.get("notAfter")
    if not_after:
        try:
            expiry = _parse_cert_date(not_after)
            days_left = (expiry - datetime.now(timezone.utc)).days
            if days_left < 0:
                findings.append(
                    Finding("tls_check", "high", "Certificat TLS expiré", f"expiré depuis {-days_left} jours")
                )
            elif days_left < 14:
                findings.append(
                    Finding("tls_check", "medium", "Certificat TLS bientôt expiré", f"{days_left} jours restants")
                )
        except ValueError:
            pass

    issuer = dict(x[0] for x in cert.get("issuer", []))
    subject = dict(x[0] for x in cert.get("subject", []))
    if issuer.get("commonName") and issuer.get("commonName") == subject.get("commonName"):
        findings.append(Finding("tls_check", "medium", "Certificat auto-signé", subject.get("commonName", "")))

    return findings
