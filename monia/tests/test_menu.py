import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from monia import cli, llm_local, secondcerveau


class _MockOllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self._json({"models": [{"name": "qwen2.5:1.5b"}]})

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        last_message = payload["messages"][-1]["content"]
        self._json({"message": {"role": "assistant", "content": f"reponse a: {last_message}"}})

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def mock_ollama(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _MockOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    original_chat = llm_local.chat

    def _chat(messages, model=None, host=None, timeout=120.0):
        return original_chat(messages, model=model, host=f"http://127.0.0.1:{port}", timeout=timeout)

    monkeypatch.setattr(cli.llm_local, "chat", _chat)
    monkeypatch.setattr(cli.llm_local, "is_available", lambda **kw: True)

    yield
    server.shutdown()
    thread.join(timeout=2)


def test_menu_shown_on_startup(capsys):
    cli.run(["0"])
    out = capsys.readouterr().out
    assert "=== MonIA ===" in out
    assert "1) Discuter" in out


def test_menu_choice_1_chats(mock_ollama, capsys):
    cli.run(["1", "salut", "0"])
    out = capsys.readouterr().out
    assert "reponse a: salut" in out


def test_menu_choice_2_talks_by_voice(monkeypatch, mock_ollama, capsys):
    monkeypatch.setattr(cli.voice, "is_stt_available", lambda: True)
    responses = iter(["salut", "stop"])
    monkeypatch.setattr(cli.voice, "listen", lambda timeout=30.0: next(responses))
    monkeypatch.setattr(cli.voice, "speak", lambda text: True)

    cli.run(["2", "0"])
    out = capsys.readouterr().out
    assert "reponse a: salut" in out


def test_menu_choice_7_calculates_devis(capsys):
    cli.run(["7", "gravier 15 5", "0"])
    out = capsys.readouterr().out
    assert "gravier" in out
    assert "tonnes" in out


def test_menu_choice_5_lists_notes(capsys):
    secondcerveau.save_note("General", "test", "contenu")
    cli.run(["5", "0"])
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
