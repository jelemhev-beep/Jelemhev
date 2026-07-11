"""Client for a real local LLM served by Ollama (https://ollama.com), not a
from-scratch model -- training a genuine chat model from nothing is not
feasible on a phone. Ollama runs the actual model (e.g. llama3.2, phi3,
gemma2); this module just talks to its REST API over localhost.
"""

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request

DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("MONIA_MODEL", "llama3.2")


class OllamaError(Exception):
    pass


def is_available(host: str = DEFAULT_HOST, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def is_installed() -> bool:
    return shutil.which("ollama") is not None


def ensure_running(host: str = DEFAULT_HOST, startup_timeout: float = 15.0) -> bool:
    """If Ollama isn't reachable, try to launch `ollama serve` in the
    background (detached, so it doesn't die when this process does) and
    wait for it to come up. Returns True once reachable, False if the
    binary isn't installed or it didn't come up in time.

    This does not survive Android killing Termux's background processes
    -- it only removes the need to manually run `ollama serve` in a
    separate terminal each time.
    """
    if is_available(host=host, timeout=2.0):
        return True
    if not is_installed():
        return False

    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    deadline = time.monotonic() + startup_timeout
    while time.monotonic() < deadline:
        if is_available(host=host, timeout=1.0):
            return True
        time.sleep(0.5)
    return False


def list_models(host: str = DEFAULT_HOST, timeout: float = 5.0) -> list[str]:
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return []
    return [m.get("name", "") for m in data.get("models", [])]


def chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_HOST,
    timeout: float = 120.0,
) -> str:
    """messages: [{"role": "user"|"assistant"|"system", "content": str}, ...]
    Returns the assistant's reply text.
    """
    url = f"{host.rstrip('/')}/api/chat"
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise OllamaError(
            f"Impossible de contacter Ollama sur {host}. "
            f"Verifie qu'il tourne (`ollama serve`) et qu'un modele est installe "
            f"(`ollama pull {model}`)."
        ) from exc

    try:
        return body["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise OllamaError(f"Reponse Ollama inattendue: {body}") from exc
