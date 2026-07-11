import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from monia import cli, llm_cloud, secondcerveau


class _MockGroqHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        last_message = payload["messages"][-1]["content"]
        self._json(
            {"choices": [{"message": {"role": "assistant", "content": f"reponse a: {last_message}"}}]}
        )

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def mock_groq(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _MockGroqHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")

    original_chat = llm_cloud.chat

    def _chat(messages, model=llm_cloud.DEFAULT_MODEL, host=None, timeout=30.0, api_key=None):
        return original_chat(
            messages, model=model, host=f"http://127.0.0.1:{port}", timeout=timeout, api_key=api_key
        )

    monkeypatch.setattr(cli.llm_cloud, "chat", _chat)

    yield
    server.shutdown()
    thread.join(timeout=2)


def test_menu_shown_on_startup(capsys):
    cli.run(["0"])
    out = capsys.readouterr().out
    assert "=== MonIA ===" in out
    assert "1) Discuter" in out


def test_menu_choice_1_chats(mock_groq, capsys):
    cli.run(["1", "salut", "0"])
    out = capsys.readouterr().out
    assert "reponse a: salut" in out


def test_menu_choice_6_calculates_devis(capsys):
    cli.run(["6", "gravier 15 5", "0"])
    out = capsys.readouterr().out
    assert "gravier" in out
    assert "tonnes" in out


def test_menu_choice_4_lists_notes(capsys):
    secondcerveau.save_note("General", "test", "contenu")
    cli.run(["4", "0"])
    out = capsys.readouterr().out
    assert "test" in out.lower() or ".md" in out


def test_menu_choice_0_quits_immediately(capsys):
    cli.run(["0", "chat ceci ne doit jamais s'executer"])
    out = capsys.readouterr().out
    assert "Commande inconnue" not in out


def test_menu_word_reprints_menu(capsys):
    cli.run(["menu", "0"])
    out = capsys.readouterr().out
    assert out.count("=== MonIA ===") >= 2  # once at startup, once from 'menu'


def test_raw_command_still_works_alongside_menu(capsys):
    """Numbers are a shortcut, not a replacement -- full commands must
    keep working exactly as before."""
    cli.run(["materiaux", "0"])
    out = capsys.readouterr().out
    assert "gravier" in out
