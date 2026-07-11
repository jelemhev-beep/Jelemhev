from monia import secondcerveau


def test_save_and_list_notes():
    secondcerveau.save_note("Jardin", "Idee terrasse", "Prevoir 20m2 de gravier")
    secondcerveau.save_note("Jardin", "Fournisseur", "Contact: xyz")

    notes = secondcerveau.list_notes("Jardin")
    assert len(notes) == 2
    assert all(p.suffix == ".md" for p in notes)


def test_list_notes_unknown_project_returns_empty():
    assert secondcerveau.list_notes("PasEncoreCree") == []


def test_list_projects():
    secondcerveau.save_note("Jardin", "note1", "contenu")
    secondcerveau.save_note("Cuisine", "note2", "contenu")

    assert secondcerveau.list_projects() == ["Cuisine", "Jardin"]


def test_saved_note_contains_title_and_content():
    path = secondcerveau.save_note("Jardin", "Idee terrasse", "Prevoir du gravier gris")
    text = secondcerveau.read_note(path)
    assert "Idee terrasse" in text
    assert "Prevoir du gravier gris" in text
    assert "Jardin" in text


def test_search_finds_matching_note_and_ignores_others():
    secondcerveau.save_note("Jardin", "Devis gravier", "20 tonnes de gravier gris commandees")
    secondcerveau.save_note("Cuisine", "Recette", "Pates au beurre")

    results = secondcerveau.search("gravier")
    assert len(results) == 1
    path, line = results[0]
    assert "gravier" in line.lower()


def test_search_is_case_insensitive():
    secondcerveau.save_note("Jardin", "titre", "GRAVIER en majuscules")
    results = secondcerveau.search("gravier")
    assert len(results) == 1


def test_search_scoped_to_one_project():
    secondcerveau.save_note("Jardin", "a", "motcle")
    secondcerveau.save_note("Cuisine", "b", "motcle")

    assert len(secondcerveau.search("motcle")) == 2
    assert len(secondcerveau.search("motcle", project="Jardin")) == 1
