import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
NOTES_DIR = os.path.join(DATA_DIR, "second_cerveau")


def lister_notes():
    if not os.path.isdir(NOTES_DIR):
        return []
    return sorted(f for f in os.listdir(NOTES_DIR) if f.endswith(".md"))


def chercher_notes():
    print("\n🧠 Chercher dans mon second cerveau (notes Obsidian)")
    dossier = input(f"Dossier des notes (défaut {NOTES_DIR}) : ").strip() or NOTES_DIR
    if not os.path.isdir(dossier):
        print("   ⚠️ Ce dossier n'existe pas encore. Les notes créées via l'option 18")
        print(f"      (Lire Wikipédia) sont sauvegardées dans {NOTES_DIR}.")
        return
    requete = input("Recherche : ").strip().lower()
    if not requete:
        return
    fichiers = sorted(f for f in os.listdir(dossier) if f.endswith(".md"))
    if not fichiers:
        print("   Aucune note trouvée dans ce dossier.")
        return
    trouve = False
    for nom_fichier in fichiers:
        chemin = os.path.join(dossier, nom_fichier)
        try:
            with open(chemin, "r", encoding="utf-8", errors="replace") as f:
                lignes = f.readlines()
        except OSError:
            continue
        correspondances = [(i, l) for i, l in enumerate(lignes, start=1) if requete in l.lower()]
        if correspondances:
            trouve = True
            print(f"\n   📄 {nom_fichier}")
            for numero, ligne in correspondances[:5]:
                print(f"      L{numero}: {ligne.strip()}")
    if not trouve:
        print("   Aucune correspondance trouvée.")
