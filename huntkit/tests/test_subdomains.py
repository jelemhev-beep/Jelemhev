import asyncio
import json

import httpx

from huntkit.recon.subdomains import passive_crtsh


async def fake_crtsh_app(scope, receive, send):
    entries = [
        {"name_value": "www.example.com\n*.api.example.com"},
        {"name_value": "unrelated.org"},
    ]
    body = json.dumps(entries).encode()
    await send(
        {"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]}
    )
    await send({"type": "http.response.body", "body": body})


def test_passive_crtsh_extracts_and_filters_by_domain():
    async def run():
        transport = httpx.ASGITransport(app=fake_crtsh_app)
        async with httpx.AsyncClient(transport=transport, base_url="https://crt.sh") as client:
            return await passive_crtsh("example.com", client)

    names = asyncio.run(run())
    assert "www.example.com" in names
    assert "api.example.com" in names  # leading wildcard stripped
    assert "unrelated.org" not in names
