import json
import os
import difflib

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FICHIER_MEMOIRE = os.path.join(DATA_DIR, "memoire.json")


def charger():
    if not os.path.exists(FICHIER_MEMOIRE):
        return {}
    try:
        with open(FICHIER_MEMOIRE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def sauver(memoire):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FICHIER_MEMOIRE, "w", encoding="utf-8") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)


def apprendre(question, reponse):
    memoire = charger()
    memoire[question.strip().lower()] = reponse
    sauver(memoire)


def chercher(question, seuil=0.72):
    memoire = charger()
    if not memoire:
        return None
    q = question.strip().lower()
    if q in memoire:
        return memoire[q]
    correspondances = difflib.get_close_matches(q, memoire.keys(), n=1, cutoff=seuil)
    if correspondances:
        return memoire[correspondances[0]]
    return None


def apprendre_tes_reponses():
    print("\n📖 Apprendre tes réponses")
    print("   Apprends-moi une question et sa réponse, je m'en souviendrai.")
    print("   (laisse la question vide pour revenir au menu)\n")
    while True:
        question = input("Question : ").strip()
        if not question:
            break
        reponse = input("Réponse  : ").strip()
        if not reponse:
            print("   Réponse vide, annulé.")
            continue
        apprendre(question, reponse)
        print(f"   ✅ Retenu : « {question} » → « {reponse} »\n")
    memoire = charger()
    print(f"   Total en mémoire : {len(memoire)} question(s).")


def lecon_memoire():
    print("\n=== Leçon : la mémoire ===")
    print("Un réseau de neurones n'a pas de mémoire au sens humain : ses")
    print("'souvenirs' sont les nombres (poids) réglés pendant l'entraînement.")
    print("MonIA, elle, garde aussi une mémoire simple et honnête : un fichier")
    print(f"JSON ({os.path.relpath(FICHIER_MEMOIRE)}) qui associe des questions à des réponses")
    print("que tu lui as apprises toi-même (option 26).\n")
    memoire = charger()
    if memoire:
        print(f"Exemple de ce qu'elle sait déjà ({len(memoire)} entrée(s)) :")
        for i, (q, r) in enumerate(memoire.items()):
            if i >= 5:
                print("   ...")
                break
            print(f"   - {q} → {r}")
    else:
        print("Pour l'instant sa mémoire est vide. Utilise l'option 26 pour lui")
        print("apprendre des choses !")
