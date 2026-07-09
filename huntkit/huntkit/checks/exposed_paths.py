import httpx

from ..ratelimit import RateLimiter
from .base import Finding, register

# path -> (severity, title, marker expected in a real hit)
SENSITIVE_PATHS = {
    "/.git/HEAD": ("high", "Dépôt .git exposé", "ref:"),
    "/.git/config": ("high", "Fichier .git/config exposé", "[core]"),
    "/.env": ("critical", "Fichier .env exposé", "="),
    "/.aws/credentials": ("critical", "Identifiants AWS exposés", "aws_"),
    "/wp-config.php.bak": ("high", "Backup wp-config.php exposé", "DB_"),
    "/server-status": ("medium", "mod_status Apache exposé publiquement", "Apache"),
    "/actuator/health": ("medium", "Spring Boot Actuator exposé", "status"),
    "/swagger.json": ("low", "Documentation API Swagger exposée", "swagger"),
    "/.DS_Store": ("low", "Fichier .DS_Store exposé", ""),
}


@register("exposed_paths")
async def check(base_url: str, client: httpx.AsyncClient, limiter: RateLimiter) -> list[Finding]:
    findings = []
    for path, (severity, title, marker) in SENSITIVE_PATHS.items():
        async with limiter:
            try:
                resp = await client.get(base_url.rstrip("/") + path, timeout=10.0)
            except httpx.HTTPError:
                continue

        if resp.status_code != 200:
            continue
        if marker and marker.lower() not in resp.text.lower():
            continue

        findings.append(Finding(check_name="exposed_paths", severity=severity, title=title, detail=path))
    return findings
