import json
import os
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FICHIER_VEGETAUX = os.path.join(DATA_DIR, "vegetaux.json")

TYPES_VEGETAUX = ["arbuste", "arbre", "fruitier", "vivace", "grimpante", "conifère"]
EXPOSITIONS = ["plein soleil", "mi-ombre", "ombre"]


def charger():
    if not os.path.exists(FICHIER_VEGETAUX):
        return []
    try:
        with open(FICHIER_VEGETAUX, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def sauver(vegetaux):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FICHIER_VEGETAUX, "w", encoding="utf-8") as f:
        json.dump(vegetaux, f, ensure_ascii=False, indent=2)


def _saisir_fiche():
    nom = input("Nom du végétal : ").strip()
    if not nom:
        return None
    type_vegetal = input(f"Type ({'/'.join(TYPES_VEGETAUX)}) : ").strip().lower() or "arbuste"
    exposition = input(f"Exposition ({'/'.join(EXPOSITIONS)}) : ").strip().lower() or ""
    description = input("Description (courte) : ").strip()
    photo = input("Chemin de la photo (vide si aucune) : ").strip()
    chantier = input("Chantier associé (nom, vide si aucun) : ").strip()
    return {
        "nom": nom, "type": type_vegetal, "exposition": exposition,
        "description": description, "photo": photo, "chantier": chantier,
    }


def ajouter_vegetal():
    print("\n🌱 Ajouter un végétal (fiche + photo, second cerveau)")
    fiche = _saisir_fiche()
    if not fiche:
        print("   ⚠️ Nom obligatoire, annulé.")
        return
    vegetaux = charger()
    vegetaux.append(fiche)
    sauver(vegetaux)
    print(f"   💾 Fiche « {fiche['nom']} » ajoutée ({len(vegetaux)} au total).")


def ajouter_lot_vegetaux():
    print("\n🌳 Ajouter un LOT de végétaux (arbustes/arbres/fruitiers)")
    print("   Entre les noms séparés par des virgules (ex : Laurier rose, Olivier, Figuier)")
    noms = input("Noms : ").strip()
    if not noms:
        return
    type_commun = input(f"Type commun ({'/'.join(TYPES_VEGETAUX)}) : ").strip().lower() or "arbuste"
    exposition_commune = input(f"Exposition commune ({'/'.join(EXPOSITIONS)}) : ").strip().lower() or ""
    chantier = input("Chantier associé (nom, vide si aucun) : ").strip()
    vegetaux = charger()
    ajoutes = 0
    for nom in (n.strip() for n in noms.split(",") if n.strip()):
        vegetaux.append({
            "nom": nom, "type": type_commun, "exposition": exposition_commune,
            "description": "", "photo": "", "chantier": chantier,
        })
        ajoutes += 1
    sauver(vegetaux)
    print(f"   💾 {ajoutes} végétal(aux) ajoutés en lot ({len(vegetaux)} au total).")


def rattraper_photos():
    print("\n📷 Rattraper les photos manquantes (végétaux)")
    vegetaux = charger()
    manquants = [v for v in vegetaux if not v.get("photo")]
    if not manquants:
        print("   ✅ Toutes les fiches ont déjà une photo.")
        return
    print(f"   {len(manquants)} fiche(s) sans photo :")
    for v in manquants:
        photo = input(f"   Photo pour « {v['nom']} » (chemin, vide pour passer) : ").strip()
        if photo:
            v["photo"] = photo
    sauver(vegetaux)
    print("   💾 Mise à jour terminée.")


def completer_fiches():
    print("\n📋 Compléter les fiches végétaux (infos générales)")
    vegetaux = charger()
    incompletes = [v for v in vegetaux if not v.get("exposition") or not v.get("description")]
    if not incompletes:
        print("   ✅ Toutes les fiches sont complètes.")
        return
    print(f"   {len(incompletes)} fiche(s) incomplète(s) :")
    for v in incompletes:
        print(f"\n   Fiche : {v['nom']}")
        if not v.get("exposition"):
            v["exposition"] = input(f"     Exposition ({'/'.join(EXPOSITIONS)}) : ").strip().lower()
        if not v.get("description"):
            v["description"] = input("     Description : ").strip()
    sauver(vegetaux)
    print("   💾 Fiches mises à jour.")


def relier_vegetaux_exposition():
    print("\n🌼 Relier les végétaux entre eux (même exposition)")
    vegetaux = charger()
    groupes = defaultdict(list)
    for v in vegetaux:
        exposition = v.get("exposition") or "non renseignée"
        groupes[exposition].append(v["nom"])
    if not groupes:
        print("   Aucun végétal enregistré (option 37/38 pour en ajouter).")
        return
    for exposition, noms in groupes.items():
        print(f"\n   ☀️ Exposition « {exposition} » ({len(noms)}) :")
        for nom in noms:
            print(f"      - {nom}")
