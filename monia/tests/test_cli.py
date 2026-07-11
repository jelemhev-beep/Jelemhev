from monia import cli, secondcerveau


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
