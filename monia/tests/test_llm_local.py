import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from monia import llm_local


class _MockOllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/api/tags":
            self._json({"models": [{"name": "llama3.2:latest"}, {"name": "phi3:latest"}]})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            last_message = payload["messages"][-1]["content"]
            self._json({"message": {"role": "assistant", "content": f"echo: {last_message}"}})
        else:
            self.send_error(404)

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def mock_ollama():
    server = HTTPServer(("127.0.0.1", 0), _MockOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=2)


def test_is_available_true_when_server_up(mock_ollama):
    assert llm_local.is_available(host=mock_ollama) is True


def test_is_available_false_for_closed_port():
    assert llm_local.is_available(host="http://127.0.0.1:1", timeout=1) is False


def test_list_models(mock_ollama):
    models = llm_local.list_models(host=mock_ollama)
    assert "llama3.2:latest" in models
    assert "phi3:latest" in models


def test_chat_returns_reply_content(mock_ollama):
    reply = llm_local.chat([{"role": "user", "content": "salut"}], host=mock_ollama)
    assert reply == "echo: salut"


def test_chat_raises_ollama_error_when_unreachable():
    with pytest.raises(llm_local.OllamaError):
        llm_local.chat([{"role": "user", "content": "x"}], host="http://127.0.0.1:1", timeout=1)


def test_ensure_running_skips_launch_when_already_available(monkeypatch, mock_ollama):
    called = []
    monkeypatch.setattr(llm_local.subprocess, "Popen", lambda *a, **kw: called.append((a, kw)))
    assert llm_local.ensure_running(host=mock_ollama) is True
    assert called == []  # no need to spawn anything, it was already up


def test_ensure_running_returns_false_when_ollama_not_installed(monkeypatch):
    monkeypatch.setattr(llm_local, "is_installed", lambda: False)
    assert llm_local.ensure_running(host="http://127.0.0.1:1", startup_timeout=1) is False


def test_ensure_running_launches_and_waits_until_reachable(monkeypatch):
    monkeypatch.setattr(llm_local, "is_installed", lambda: True)
    popen_calls = []
    monkeypatch.setattr(
        llm_local.subprocess, "Popen", lambda *a, **kw: popen_calls.append((a, kw))
    )

    availability_sequence = [False, False, True]

    def fake_is_available(host=None, timeout=None):
        return availability_sequence.pop(0) if availability_sequence else True

    monkeypatch.setattr(llm_local, "is_available", fake_is_available)
    monkeypatch.setattr(llm_local.time, "sleep", lambda _seconds: None)  # skip real waiting

    assert llm_local.ensure_running(host="http://127.0.0.1:1", startup_timeout=5) is True
    assert len(popen_calls) == 1
    assert popen_calls[0][0] == (["ollama", "serve"],)


def test_ensure_running_gives_up_after_timeout(monkeypatch):
    monkeypatch.setattr(llm_local, "is_installed", lambda: True)
    monkeypatch.setattr(llm_local.subprocess, "Popen", lambda *a, **kw: None)
    monkeypatch.setattr(llm_local, "is_available", lambda host=None, timeout=None: False)

    real_monotonic = llm_local.time.monotonic
    fake_time = [real_monotonic()]
    monkeypatch.setattr(llm_local.time, "monotonic", lambda: fake_time[0])

    def fake_sleep(_seconds):
        fake_time[0] += 1.0  # advance the fake clock past the deadline quickly

    monkeypatch.setattr(llm_local.time, "sleep", fake_sleep)

    assert llm_local.ensure_running(host="http://127.0.0.1:1", startup_timeout=3) is False
