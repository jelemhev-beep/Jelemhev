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

    original_chat = llm_local.chat  # capture before patching, or _chat below would call itself

    def _chat(messages, model=None, host=None, timeout=120.0):
        return original_chat(messages, model=model, host=f"http://127.0.0.1:{port}", timeout=timeout)

    monkeypatch.setattr(cli.llm_local, "chat", _chat)
    monkeypatch.setattr(cli.llm_local, "is_available", lambda **kw: True)

    yield
    server.shutdown()
    thread.join(timeout=2)


def test_chat_command_gets_reply_and_saves_conversation(mock_ollama, capsys):
    cli.run(["chat bonjour", "quitter"])
    out = capsys.readouterr().out
    assert "reponse a: bonjour" in out

    log = secondcerveau.load_conversation("General")
    assert "bonjour" in log
    assert "reponse a: bonjour" in log


def test_chat_stays_in_conversation_mode_across_messages(mock_ollama, capsys):
    """A follow-up message shouldn't need 'chat' retyped in front of it --
    the CLI should keep answering until the user explicitly leaves chat
    mode (this was the bug: freeform follow-ups got 'Commande inconnue')."""
    cli.run(["chat bonjour", "comment ca va", "0", "quitter"])
    out = capsys.readouterr().out
    assert "reponse a: bonjour" in out
    assert "reponse a: comment ca va" in out
    assert "Commande inconnue" not in out


def test_chat_command_without_ollama_reports_clean_error(monkeypatch, capsys):
    monkeypatch.setattr(cli.llm_local, "is_available", lambda **kw: False)
    monkeypatch.setattr(cli.llm_local, "is_installed", lambda: False)
    cli.run(["chat bonjour", "quitter"])
    out = capsys.readouterr().out
    assert "ollama.com/install.sh" in out


def test_parler_command_uses_speech_to_text_and_speaks_reply(monkeypatch, mock_ollama, capsys):
    monkeypatch.setattr(cli.voice, "is_stt_available", lambda: True)
    responses = iter(["bonjour", "stop"])
    monkeypatch.setattr(cli.voice, "listen", lambda timeout=30.0: next(responses))
    spoken = []
    monkeypatch.setattr(cli.voice, "speak", lambda text: spoken.append(text) or True)

    cli.run(["parler", "quitter"])
    out = capsys.readouterr().out
    assert "reponse a: bonjour" in out
    assert spoken == ["reponse a: bonjour"]


def test_parler_command_without_stt_reports_clean_error(monkeypatch, mock_ollama, capsys):
    monkeypatch.setattr(cli.voice, "is_stt_available", lambda: False)
    cli.run(["parler", "quitter"])
    out = capsys.readouterr().out
    assert "termux-speech-to-text" in out


def test_parler_command_retries_on_unrecognized_speech(monkeypatch, mock_ollama, capsys):
    responses = iter(["", "salut", "stop"])
    monkeypatch.setattr(cli.voice, "is_stt_available", lambda: True)
    monkeypatch.setattr(cli.voice, "listen", lambda timeout=30.0: next(responses))
    monkeypatch.setattr(cli.voice, "speak", lambda text: True)

    cli.run(["parler", "quitter"])
    out = capsys.readouterr().out
    assert "rien compris" in out.lower()
    assert "reponse a: salut" in out


def test_devis_command_prints_and_saves_note(capsys):
    cli.run(["devis gravier 10 5", "quitter"])
    out = capsys.readouterr().out
    assert "gravier" in out
    assert "tonnes" in out

    notes = secondcerveau.list_notes("General")
    assert any("devis-gravier" in p.name for p in notes)


def test_note_command_saves_multiline_content(capsys):
    cli.run(["note Idee terrasse", "ligne 1", "ligne 2", "", "quitter"])
    notes = secondcerveau.list_notes("General")
    assert len(notes) == 1
    text = secondcerveau.read_note(notes[0])
    assert "ligne 1" in text
    assert "ligne 2" in text


def test_projet_command_switches_project(capsys):
    cli.run(["projet Jardin", "note test", "contenu", "", "quitter"])
    assert secondcerveau.list_notes("Jardin") != []
    assert secondcerveau.list_notes("General") == []


def test_recherche_command_finds_saved_note(capsys):
    cli.run(["note MotUnique", "contenucherchable", "", "recherche contenucherchable", "quitter"])
    out = capsys.readouterr().out
    assert "contenucherchable" in out.lower() or "MotUnique" in out


def test_unknown_command_shows_message(capsys):
    cli.run(["bidon", "quitter"])
    out = capsys.readouterr().out
    assert "Commande inconnue" in out


def test_voix_on_without_termux_api_reports_unavailable(capsys):
    cli.run(["voix on", "quitter"])
    out = capsys.readouterr().out
    assert "introuvable" in out.lower()
