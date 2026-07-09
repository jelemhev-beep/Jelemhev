from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import STATIC_DIR, get_secret_key
from .db import init_db
from .routers import git_smart, web

app = FastAPI(title="GitHome")
app.add_middleware(SessionMiddleware, secret_key=get_secret_key(), same_site="lax")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

init_db()

# Order matters: web routes (login/register/dashboard) must be matched before
# the generic git smart-HTTP catch-all below.
app.include_router(web.router)
app.include_router(git_smart.router)
