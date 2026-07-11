import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from monia import llm_cloud


class _MockGroqHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != "/chat/completions":
            self.send_error(404)
            return

        auth = self.headers.get("Authorization", "")
        if auth != "Bearer test-key-123":
            self._json({"error": {"message": "invalid api key"}}, status=401)
            return

        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        last_message = payload["messages"][-1]["content"]
        self._json(
            {
                "choices": [
                    {"message": {"role": "assistant", "content": f"groq dit: {last_message}"}}
                ]
            }
        )

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def mock_groq():
    server = HTTPServer(("127.0.0.1", 0), _MockGroqHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=2)


def test_has_api_key_reads_env_var(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert llm_cloud.has_api_key() is False
    monkeypatch.setenv("GROQ_API_KEY", "whatever")
    assert llm_cloud.has_api_key() is True


def test_chat_without_key_raises_clear_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(llm_cloud.GroqError, match="console.groq.com"):
        llm_cloud.chat([{"role": "user", "content": "salut"}])


def test_chat_returns_reply_with_valid_key(mock_groq):
    reply = llm_cloud.chat(
        [{"role": "user", "content": "bonjour"}], host=mock_groq, api_key="test-key-123"
    )
    assert reply == "groq dit: bonjour"


def test_chat_raises_on_invalid_key(mock_groq):
    with pytest.raises(llm_cloud.GroqError, match="401"):
        llm_cloud.chat([{"role": "user", "content": "x"}], host=mock_groq, api_key="wrong-key")


def test_chat_raises_on_unreachable_host():
    with pytest.raises(llm_cloud.GroqError):
        llm_cloud.chat(
            [{"role": "user", "content": "x"}], host="http://127.0.0.1:1", api_key="k", timeout=1
        )


def test_chat_sends_browser_like_user_agent(mock_groq):
    """Groq's Cloudflare edge blocks bare/suspicious User-Agents as bot
    traffic (403, error 1010) -- guard against regressing back to no
    User-Agent header at all."""
    captured = {}
    original_do_post = _MockGroqHandler.do_POST

    def _capture(self):
        captured["ua"] = self.headers.get("User-Agent", "")
        original_do_post(self)

    _MockGroqHandler.do_POST = _capture
    try:
        llm_cloud.chat(
            [{"role": "user", "content": "bonjour"}], host=mock_groq, api_key="test-key-123"
        )
    finally:
        _MockGroqHandler.do_POST = original_do_post

    assert captured["ua"] == llm_cloud.USER_AGENT
    assert captured["ua"]
