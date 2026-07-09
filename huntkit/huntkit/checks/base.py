from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx

from ..ratelimit import RateLimiter

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@dataclass
class Finding:
    check_name: str
    severity: str
    title: str
    detail: str = ""


CheckFn = Callable[[str, httpx.AsyncClient, RateLimiter], Awaitable[list[Finding]]]

CHECKS: dict[str, CheckFn] = {}


def register(name: str):
    def decorator(fn: CheckFn) -> CheckFn:
        CHECKS[name] = fn
        return fn

    return decorator
