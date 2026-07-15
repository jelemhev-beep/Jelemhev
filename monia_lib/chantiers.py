import json
import os
import re
from collections import defaultdict
from datetime import datetime

from monia_lib import vegetaux

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEVIS_DIR = os.path.join(DATA_DIR, "devis")

# quantité par m² (approximations courantes de chantier paysager/maçonnerie)
FORMULES_MATERIAUX = {
    "gravier (paillage, épaisseur 5cm)": lambda surface: surface * 0.05,   # m3
    "terre végétale (épaisseur 20cm)": lambda surface: surface * 0.20,     # m3
    "engazonnement (gazon en rouleau)": lambda surface: surface * 1.05,    # m2 (avec 5% de perte)
    "dalles (1 dalle = 0.25m²)": lambda surface: surface / 0.25,           # nb de dalles
    "sable de pose (épaisseur 3cm)": lambda surface: surface * 0.03,       # m3
    "mortier (chape 4cm)": lambda surface: surface * 0.04,                 # m3
}


def relier_chantiers_vegetaux():
    print("\n🔗 Relier chantiers et végétaux (liens croisés du graphe)")
    plantes = vegetaux.charger()
    if not plantes:
        print("   Aucun végétal enregistré (options 37/38 pour en ajouter).")
        return
    groupes = defaultdict(list)
    for v in plantes:
        chantier = v.get("chantier") or "sans chantier"
        groupes[chantier].append(v["nom"])
    for chantier, noms in groupes.items():
        print(f"\n   🏗️ Chantier « {chantier} » ({len(noms)} végétal(aux)) :")
        for nom in noms:
            print(f"      - {nom}")


def calculateur_materiaux():
    print("\n📐 Calculateur de quantités matériaux (chantier)")
    for i, nom in enumerate(FORMULES_MATERIAUX, start=1):
        print(f"   {i}) {nom}")
    choix = input("Choix du matériau : ").strip()
    materiaux = list(FORMULES_MATERIAUX.items())
    try:
        nom, formule = materiaux[int(choix) - 1]
    except (ValueError, IndexError):
        print("   ⚠️ Choix invalide.")
        return
    try:
        surface = float(input("Surface concernée (m²) : ").strip().replace(",", "."))
    except ValueError:
        print("   ⚠️ Surface invalide.")
        return
    quantite = formule(surface)
    unite = "unités" if "dalle" in nom else "m³"
    if "engazonnement" in nom:
        unite = "m²"
    print(f"\n   Pour {surface} m² : {nom}")
    print(f"   Quantité estimée : {quantite:.2f} {unite}")
    print("   (estimation indicative, à ajuster selon les recommandations du fabricant)")


def generateur_devis():
    print("\n📄 Générateur de devis")
    client = input("Nom du client : ").strip() or "Client"
    intitule = input("Intitulé du chantier : ").strip() or "Travaux"
    print("\nAjoute les lignes du devis (description, quantité, prix unitaire €).")
    print("Laisse la description vide pour terminer.\n")
    lignes = []
    while True:
        description = input("Description : ").strip()
        if not description:
            break
        try:
            quantite = float(input("  Quantité : ").strip().replace(",", "."))
            prix_unitaire = float(input("  Prix unitaire (€) : ").strip().replace(",", "."))
        except ValueError:
            print("   ⚠️ Quantité/prix invalide, ligne ignorée.")
            continue
        lignes.append((description, quantite, prix_unitaire))

    if not lignes:
        print("   ⚠️ Aucune ligne, devis annulé.")
        return

    total_ht = sum(q * p for _, q, p in lignes)
    tva = total_ht * 0.20
    total_ttc = total_ht + tva

    os.makedirs(DEVIS_DIR, exist_ok=True)
    nom_fichier = re.sub(r"\W+", "_", f"{client}_{intitule}".lower()).strip("_")
    chemin = os.path.join(DEVIS_DIR, f"devis_{nom_fichier}_{datetime.now():%Y%m%d_%H%M%S}.md")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(f"# Devis — {intitule}\n\n**Client :** {client}\n**Date :** {datetime.now():%d/%m/%Y}\n\n")
        f.write("| Description | Quantité | Prix unitaire | Total |\n")
        f.write("|---|---|---|---|\n")
        for description, quantite, prix_unitaire in lignes:
            f.write(f"| {description} | {quantite} | {prix_unitaire:.2f} € | {quantite * prix_unitaire:.2f} € |\n")
        f.write(f"\n**Total HT :** {total_ht:.2f} €\n\n**TVA (20%) :** {tva:.2f} €\n\n")
        f.write(f"**Total TTC :** {total_ttc:.2f} €\n")

    print(f"\n   Total HT  : {total_ht:.2f} €")
    print(f"   TVA (20%) : {tva:.2f} €")
    print(f"   Total TTC : {total_ttc:.2f} €")
    print(f"\n   💾 Devis sauvegardé : {chemin}")
