from monia import cli, secondcerveau


def test_menu_shown_on_startup(capsys):
    cli.run(["0"])
    out = capsys.readouterr().out
    assert "=== MonIA ===" in out
    assert "1) Changer de projet actif" in out


def test_menu_choice_5_calculates_devis(capsys):
    cli.run(["5", "gravier 15 5", "0"])
    out = capsys.readouterr().out
    assert "gravier" in out
    assert "tonnes" in out


def test_menu_choice_3_lists_notes(capsys):
    secondcerveau.save_note("General", "test", "contenu")
    cli.run(["3", "0"])
    out = capsys.readouterr().out
    assert "test" in out.lower() or ".md" in out


def test_menu_choice_0_quits_immediately(capsys):
    cli.run(["0", "devis ceci ne doit jamais s'executer"])
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
