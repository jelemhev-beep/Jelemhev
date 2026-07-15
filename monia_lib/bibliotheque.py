import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
BIBLIOTHEQUE_DIR = os.path.join(DATA_DIR, "bibliotheque")
INDEX_FICHIER = os.path.join(BIBLIOTHEQUE_DIR, "index.json")


def _charger_index():
    if not os.path.exists(INDEX_FICHIER):
        return {}
    try:
        with open(INDEX_FICHIER, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _sauver_index(index):
    os.makedirs(BIBLIOTHEQUE_DIR, exist_ok=True)
    with open(INDEX_FICHIER, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def ajouter_livre(titre, chemin_source=None, texte=None):
    os.makedirs(BIBLIOTHEQUE_DIR, exist_ok=True)
    nom_fichier = "".join(c if c.isalnum() else "_" for c in titre.lower()).strip("_") + ".txt"
    destination = os.path.join(BIBLIOTHEQUE_DIR, nom_fichier)
    if chemin_source and os.path.isfile(chemin_source):
        with open(chemin_source, "r", encoding="utf-8", errors="replace") as source:
            contenu = source.read()
    else:
        contenu = texte or ""
    with open(destination, "w", encoding="utf-8") as f:
        f.write(contenu)
    index = _charger_index()
    index[titre] = nom_fichier
    _sauver_index(index)
    return destination


def grande_bibliotheque():
    print("\n📚 La Grande Bibliothèque (livres entiers, hors ligne)")
    print("  1) Ajouter un livre (depuis un fichier texte)")
    print("  2) Lister les livres")
    print("  3) Lire un livre")
    print("  4) Chercher un mot dans tous les livres")
    choix = input("Choix : ").strip()
    index = _charger_index()
    if choix == "1":
        titre = input("Titre du livre : ").strip()
        chemin = input("Chemin du fichier texte : ").strip()
        if not titre or not os.path.isfile(chemin):
            print("   ⚠️ Titre ou fichier invalide.")
            return
        destination = ajouter_livre(titre, chemin_source=chemin)
        print(f"   💾 Ajouté à la bibliothèque : {destination}")
    elif choix == "2":
        if not index:
            print("   La bibliothèque est vide.")
        for titre in index:
            print(f"   - {titre}")
    elif choix == "3":
        titre = input("Titre exact : ").strip()
        if titre not in index:
            print("   ⚠️ Livre introuvable.")
            return
        chemin = os.path.join(BIBLIOTHEQUE_DIR, index[titre])
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            contenu = f.read()
        print(f"\n{contenu[:3000]}")
        if len(contenu) > 3000:
            print("\n   [... texte tronqué, ouvre le fichier directement pour la suite ...]")
    elif choix == "4":
        mot = input("Mot à chercher : ").strip().lower()
        trouve = False
        for titre, nom_fichier in index.items():
            chemin = os.path.join(BIBLIOTHEQUE_DIR, nom_fichier)
            try:
                with open(chemin, "r", encoding="utf-8", errors="replace") as f:
                    for numero, ligne in enumerate(f, start=1):
                        if mot in ligne.lower():
                            print(f"   [{titre}] L{numero}: {ligne.strip()}")
                            trouve = True
            except OSError:
                continue
        if not trouve:
            print("   Aucune occurrence trouvée.")
    else:
        print("   Choix inconnu.")
