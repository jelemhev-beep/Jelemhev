import asyncio

import httpx

from huntkit.checks.exposed_paths import check as exposed_paths_check
from huntkit.checks.security_headers import check as security_headers_check
from huntkit.ratelimit import RateLimiter


async def fake_app(scope, receive, send):
    path = scope["path"]
    if path == "/.git/HEAD":
        body, status = b"ref: refs/heads/main\n", 200
    elif path == "/.env":
        body, status = b"SECRET_KEY=abc123\n", 200
    elif path == "/":
        body, status = b"<html><body>hello</body></html>", 200
    else:
        body, status = b"Not Found", 404
    await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"text/plain")]})
    await send({"type": "http.response.body", "body": body})


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=fake_app), base_url="http://test")


def test_security_headers_flags_missing_headers():
    async def run():
        limiter = RateLimiter(max_concurrency=5, requests_per_second=1000)
        async with _client() as client:
            return await security_headers_check("http://test/", client, limiter)

    findings = asyncio.run(run())
    titles = {f.title for f in findings}
    assert "Content-Security-Policy manquant" in titles
    assert "Strict-Transport-Security (HSTS) manquant" in titles


def test_exposed_paths_detects_git_and_env_but_not_missing_paths():
    async def run():
        limiter = RateLimiter(max_concurrency=5, requests_per_second=1000)
        async with _client() as client:
            return await exposed_paths_check("http://test/", client, limiter)

    findings = asyncio.run(run())
    titles = {f.title for f in findings}
    assert "Dépôt .git exposé" in titles
    assert "Fichier .env exposé" in titles
    # paths the fake server correctly 404s on must not produce a false positive
    assert "Backup wp-config.php exposé" not in titles
    assert len(findings) == 2
