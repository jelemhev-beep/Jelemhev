import asyncio
import os
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import Response


async def git_http_backend(request: Request, path_info: str, project_root: Path, remote_user: str) -> Response:
    """Bridge an HTTP request to `git http-backend`, git's own CGI implementation
    of the smart HTTP protocol used by `git clone/fetch/push`.
    """
    body = await request.body()

    env = os.environ.copy()
    for key, value in request.headers.items():
        cgi_key = "HTTP_" + key.upper().replace("-", "_")
        if cgi_key in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH"):
            continue
        env[cgi_key] = value

    env.update(
        {
            "GIT_PROJECT_ROOT": str(project_root),
            "GIT_HTTP_EXPORT_ALL": "1",
            "PATH_INFO": path_info,
            "REQUEST_METHOD": request.method,
            "QUERY_STRING": request.url.query or "",
            "CONTENT_TYPE": request.headers.get("content-type", ""),
            "CONTENT_LENGTH": str(len(body)),
            "REMOTE_USER": remote_user,
            "REMOTE_ADDR": request.client.host if request.client else "",
            "GATEWAY_INTERFACE": "CGI/1.1",
            "SERVER_PROTOCOL": "HTTP/1.1",
        }
    )

    proc = await asyncio.create_subprocess_exec(
        "git",
        "http-backend",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate(input=body)
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=stderr.decode(errors="replace"))

    if b"\r\n\r\n" in stdout:
        header_blob, _, payload = stdout.partition(b"\r\n\r\n")
    else:
        header_blob, _, payload = stdout.partition(b"\n\n")

    headers = {}
    status_code = 200
    for line in header_blob.decode(errors="replace").splitlines():
        if not line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key.lower() == "status":
            status_code = int(value.split()[0])
        else:
            headers[key] = value

    return Response(content=payload, status_code=status_code, headers=headers)
