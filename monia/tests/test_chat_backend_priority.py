import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from monia import cli, llm_cloud, llm_local, secondcerveau


class _MockGroqHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        last_message = payload["messages"][-1]["content"]
        body = json.dumps(
            {"choices": [{"message": {"role": "assistant", "content": f"groq: {last_message}"}}]}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def mock_groq_server():
    server = HTTPServer(("127.0.0.1", 0), _MockGroqHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=2)


def test_chat_prefers_groq_when_api_key_present(monkeypatch, mock_groq_server, capsys):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(cli.llm_cloud, "DEFAULT_HOST", mock_groq_server)

    called_local = []
    monkeypatch.setattr(cli.llm_local, "chat", lambda *a, **kw: called_local.append(True))

    cli.run(["chat bonjour", "quitter"])
    out = capsys.readouterr().out

    assert "groq: bonjour" in out
    assert called_local == []  # Ollama must never be touched when Groq works

    log = secondcerveau.load_conversation("General")
    assert "groq: bonjour" in log


def test_chat_falls_back_to_ollama_when_no_groq_key(monkeypatch, capsys):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(cli.llm_local, "is_available", lambda **kw: True)
    monkeypatch.setattr(cli.llm_local, "chat", lambda *a, **kw: "reponse locale")

    cli.run(["chat bonjour", "quitter"])
    out = capsys.readouterr().out
    assert "reponse locale" in out


def test_chat_falls_back_to_ollama_when_groq_errors(monkeypatch, capsys):
    monkeypatch.setenv("GROQ_API_KEY", "bad-key")
    monkeypatch.setattr(
        cli.llm_cloud,
        "chat",
        lambda *a, **kw: (_ for _ in ()).throw(llm_cloud.GroqError("cle invalide")),
    )
    monkeypatch.setattr(cli.llm_local, "is_available", lambda **kw: True)
    monkeypatch.setattr(cli.llm_local, "chat", lambda *a, **kw: "reponse locale de secours")

    cli.run(["chat bonjour", "quitter"])
    out = capsys.readouterr().out
    assert "Erreur Groq" in out
    assert "reponse locale de secours" in out
