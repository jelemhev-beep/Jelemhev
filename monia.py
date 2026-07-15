#!/usr/bin/env python3
import sys
import unittest
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monia_lib import (
    memoire, neurone, outils_pratiques, securite, web_services,
    assistant, bibliotheque, second_cerveau, vegetaux, chantiers,
    bureau, llm_local,
)

BANNIERE = "\n=== MonIA — ton IA 100% maison ===\n"

MENU = """  Les assistants (pose des questions) :
    1) Discuter                2) Écrire un texte
    3) Coder en Python         4) Dépanner le terminal
    5) GitHub                  6) Cybersécurité
    7) Failles (vulnérabilités)
    8) Analyser du code (trouver des failles)
  Les outils pratiques :
    9) Calculatrice            10) Mini-CTF (hacking légal)
    11) Outils mots de passe   12) Boîte à outils crypto
    13) Bug bounty / HackerOne  14) Checklist Bug Bounty
    15) Générateur de rapport  16) Tes outils (nmap, whois...)
    17) Culture générale       18) Lire Wikipédia (et le retenir)
    19) La météo               20) Les actualités
    21) Le dictionnaire        22) Le traducteur
    23) Voir (images & vidéos)
    24) L'heure dans le monde  25) Taux de change
    26) Apprendre tes réponses
    27) ⭐ Assistant MonIA (discute, calcule, traduit, sait tout)
    33) 📎 Analyser un fichier / une photo
    34) 🧅 Tor (naviguer anonymement)
    35) 🔎 Rechercher sur le web
    36) 📚 La Grande Bibliothèque (livres entiers, hors ligne)
    37) 🌱 Ajouter un végétal (fiche + photo, second cerveau)
    38) 🌳 Ajouter un LOT de végétaux (arbustes/arbres/fruitiers)
    39) 📷 Rattraper les photos manquantes (végétaux)
    40) 📋 Compléter les fiches végétaux (infos générales)
    41) 🧠 Chercher dans mon second cerveau (notes Obsidian)
    42) 🔗 Relier chantiers et végétaux (liens croisés du graphe)
    43) 🏛 Le Bureau de MonIA (agents Recherche + Documentation)
    44) 🌼 Relier les végétaux entre eux (même exposition)
    45) 🧬 LLM local (Qwen2.5, gratuit, expérimental — setup requis)
    46) 📐 Calculateur de quantités matériaux (chantier)
    47) 📄 Générateur de devis
  Les leçons (comprendre comment ça marche) :
    28) Le neurone               29) Apprendre y = 2x
    30) S'entraîner               31) La mémoire
    32) Le réseau (XOR)
    t) Lancer les tests    0) Quitter
"""

ASTUCE = ("\n💬 Astuce : tape un NUMÉRO, ou pose DIRECTEMENT ta question ici.\n"
          "(tape 'menu' pour revoir la liste, '0' pour quitter)\n")

ACTIONS = {
    "1": assistant.discuter,
    "2": assistant.ecrire_texte,
    "3": assistant.coder_python,
    "4": assistant.depanner_terminal,
    "5": assistant.github_assistant,
    "6": securite.cybersecurite_assistant,
    "7": securite.failles_lecon,
    "8": securite.analyser_code,
    "9": outils_pratiques.calculatrice,
    "10": securite.mini_ctf,
    "11": outils_pratiques.mots_de_passe,
    "12": outils_pratiques.crypto_toolbox,
    "13": securite.bug_bounty_info,
    "14": securite.checklist_bug_bounty,
    "15": securite.generateur_rapport,
    "16": outils_pratiques.outils_reseau,
    "17": web_services.culture_generale,
    "18": web_services.lire_wikipedia,
    "19": web_services.meteo,
    "20": web_services.actualites,
    "21": web_services.dictionnaire,
    "22": web_services.traducteur,
    "23": assistant.voir_media,
    "24": outils_pratiques.heure_monde,
    "25": outils_pratiques.taux_change,
    "26": memoire.apprendre_tes_reponses,
    "27": assistant.assistant_monia,
    "28": neurone.lecon_neurone,
    "29": neurone.lecon_apprendre_y_2x,
    "30": neurone.lecon_entrainement,
    "31": memoire.lecon_memoire,
    "32": neurone.lecon_reseau_xor,
    "33": assistant.analyser_fichier,
    "34": web_services.tor_naviguer,
    "35": web_services.recherche_web,
    "36": bibliotheque.grande_bibliotheque,
    "37": vegetaux.ajouter_vegetal,
    "38": vegetaux.ajouter_lot_vegetaux,
    "39": vegetaux.rattraper_photos,
    "40": vegetaux.completer_fiches,
    "41": second_cerveau.chercher_notes,
    "42": chantiers.relier_chantiers_vegetaux,
    "43": bureau.bureau_monia,
    "44": vegetaux.relier_vegetaux_exposition,
    "45": llm_local.llm_local,
    "46": chantiers.calculateur_materiaux,
    "47": chantiers.generateur_devis,
}


def lancer_tests():
    print("\n🧪 Lancement des tests...\n")
    racine = os.path.dirname(os.path.abspath(__file__))
    suite = unittest.TestLoader().discover(os.path.join(racine, "tests"), top_level_dir=racine)
    unittest.TextTestRunner(verbosity=2).run(suite)


def afficher_menu():
    print(BANNIERE)
    print(MENU)
    print(ASTUCE)


def dispatch(entree):
    entree = entree.strip()
    if entree in ("0", "quit", "exit"):
        return False
    if entree.lower() == "menu":
        afficher_menu()
        return True
    if entree.lower() == "t":
        lancer_tests()
        return True
    action = ACTIONS.get(entree)
    if action:
        try:
            action()
        except (KeyboardInterrupt, EOFError):
            print("\n   Interrompu.")
        except Exception as e:
            print(f"   ⚠️ Erreur inattendue : {e}")
        return True
    assistant.repondre(entree)
    return True


def main():
    afficher_menu()
    while True:
        try:
            entree = input("Toi : ")
        except (KeyboardInterrupt, EOFError):
            print("\nÀ bientôt !")
            break
        if not dispatch(entree):
            print("\nÀ bientôt !")
            break


if __name__ == "__main__":
    main()
