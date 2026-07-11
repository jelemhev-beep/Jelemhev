"""Client for Groq's cloud API (https://groq.com): real, large, capable
models (e.g. Llama 3.3 70B) running on Groq's servers, not the phone.
Needs internet access and a free API key from console.groq.com, but has
no RAM/CPU cost on the device -- ideal on a phone that can't run a local
model.
"""

import json
import os
import urllib.error
import urllib.request

DEFAULT_HOST = os.environ.get("GROQ_HOST", "https://api.groq.com/openai/v1")
DEFAULT_MODEL = os.environ.get("MONIA_CLOUD_MODEL", "llama-3.3-70b-versatile")

# Groq's edge (Cloudflare) blocks requests with no/unusual User-Agent as
# bot traffic (HTTP 403, error code 1010). A normal browser-style
# User-Agent avoids that without changing anything else about the request.
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Mobile Safari/537.36"
)


class GroqError(Exception):
    pass


def has_api_key() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    host: str | None = None,
    timeout: float = 30.0,
    api_key: str | None = None,
) -> str:
    """messages: [{"role": "user"|"assistant"|"system", "content": str}, ...]
    Returns the assistant's reply text.

    `host` defaults to the module-level DEFAULT_HOST *at call time* (not
    at import time), so monkeypatching DEFAULT_HOST in tests works as
    expected instead of being baked into a stale default argument.
    """
    host = host or DEFAULT_HOST
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise GroqError(
            "Aucune cle API Groq trouvee. Cree un compte gratuit sur console.groq.com, "
            "genere une cle, puis: export GROQ_API_KEY=ta_cle"
        )

    url = f"{host.rstrip('/')}/chat/completions"
    payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise GroqError(f"Erreur API Groq ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise GroqError(f"Impossible de contacter Groq : {exc}") from exc

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GroqError(f"Reponse Groq inattendue : {body}") from exc
