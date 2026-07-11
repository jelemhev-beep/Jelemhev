from pathlib import Path

from monia import cli, digits, secondcerveau


def _make_tiny_model(tmp_path) -> Path:
    _draw_module, network_cls = digits._import_neuralnet()
    from neuralnet.activations import SIGMOID, SOFTMAX
    from neuralnet.layer import Dense
    from neuralnet.losses import CROSS_ENTROPY

    network = network_cls(layers=[Dense(784, 8, SIGMOID), Dense(8, 10, SOFTMAX)], loss=CROSS_ENTROPY)
    path = tmp_path / "tiny_model.json"
    network.save(str(path))
    return path


def test_dessin_command_predicts_and_saves_note(tmp_path, capsys):
    model_path = _make_tiny_model(tmp_path)
    cli.run([f"dessin {model_path}", "set 5 5", "predict", "quit", "quitter"])

    out = capsys.readouterr().out
    assert "Prediction" in out
    assert "sauvegarde dans le second cerveau" in out

    notes = secondcerveau.list_notes("General")
    assert any("dessin-chiffre" in p.name for p in notes)


def test_dessin_command_without_predict_saves_nothing(tmp_path, capsys):
    model_path = _make_tiny_model(tmp_path)
    cli.run([f"dessin {model_path}", "set 5 5", "quit", "quitter"])

    notes = secondcerveau.list_notes("General")
    assert not any("dessin-chiffre" in p.name for p in notes)


def test_dessin_command_returns_to_main_loop_after_quit(tmp_path, capsys):
    """'quit' must end only the drawing sub-session, not all of MonIA --
    the outer loop should keep processing whatever commands follow."""
    model_path = _make_tiny_model(tmp_path)
    cli.run([f"dessin {model_path}", "quit", "devis gravier 10 5", "quitter"])

    out = capsys.readouterr().out
    assert "Prix estime" in out


def test_dessin_command_missing_model_reports_clean_error(capsys):
    cli.run(["dessin /nonexistent/path/model.json", "quitter"])
    out = capsys.readouterr().out
    assert "Erreur" in out
    assert "introuvable" in out.lower()
