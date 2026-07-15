import base64
import os
import re
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RAPPORTS_DIR = os.path.join(DATA_DIR, "rapports")

MOTIFS_VULNERABLES = [
    (r"\beval\s*\(", "Utilisation de eval() — exécution de code arbitraire possible."),
    (r"\bexec\s*\(", "Utilisation de exec() — exécution de code arbitraire possible."),
    (r"pickle\.loads?\s*\(", "Désérialisation pickle non sûre (RCE possible sur données non fiables)."),
    (r"subprocess\.\w+\([^)]*shell\s*=\s*True", "subprocess avec shell=True — risque d'injection de commande."),
    (r"os\.system\s*\(", "os.system() — risque d'injection de commande si l'entrée n'est pas contrôlée."),
    (r"(?i)(api[_-]?key|secret|password|token)\s*=\s*[\"'][^\"']{4,}[\"']", "Secret/mot de passe apparemment codé en dur."),
    (r"hashlib\.md5\(", "MD5 utilisé — faible pour un usage cryptographique (mots de passe, signatures)."),
    (r"hashlib\.sha1\(", "SHA1 utilisé — faible pour un usage cryptographique."),
    (r"(?i)select .* from .* \+|f[\"'].*\bSELECT\b", "Requête SQL potentiellement construite par concaténation (injection SQL)."),
    (r"verify\s*=\s*False", "Vérification TLS désactivée (verify=False) — vulnérable au MITM."),
    (r"\byaml\.load\s*\((?!.*Loader)", "yaml.load() sans Loader sûr — désérialisation dangereuse."),
    (r"\bassert\b.*(password|auth|permission)", "Contrôle de sécurité basé sur assert — désactivé si Python lancé avec -O."),
    (r"innerHTML\s*=", "Affectation directe à innerHTML — risque de XSS si la donnée n'est pas nettoyée."),
]


def analyser_chemin(chemin):
    try:
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            lignes = f.readlines()
    except OSError as e:
        print("   ⚠️ Erreur de lecture :", e)
        return
    trouvailles = []
    for numero, ligne in enumerate(lignes, start=1):
        for motif, explication in MOTIFS_VULNERABLES:
            if re.search(motif, ligne):
                trouvailles.append((numero, ligne.strip(), explication))
    if not trouvailles:
        print("   ✅ Aucun motif à risque connu détecté (analyse heuristique, pas une garantie).")
        return
    print(f"   ⚠️ {len(trouvailles)} point(s) suspect(s) trouvé(s) :\n")
    for numero, ligne, explication in trouvailles:
        print(f"   L{numero}: {ligne}")
        print(f"        → {explication}\n")


def analyser_code():
    print("\n🕵️ Analyser du code (trouver des failles)")
    chemin = input("Chemin du fichier à analyser : ").strip()
    if not chemin or not os.path.isfile(chemin):
        print("   ⚠️ Fichier introuvable.")
        return
    analyser_chemin(chemin)


OWASP = [
    ("Injection (SQL, commande, LDAP...)", "Ne jamais construire des requêtes/commandes par concaténation. Utiliser des requêtes préparées, échapper les entrées."),
    ("Authentification défaillante", "Hasher les mots de passe (bcrypt/argon2), limiter les tentatives, utiliser du MFA."),
    ("Exposition de données sensibles", "Chiffrer en transit (TLS) et au repos, ne pas logger de secrets."),
    ("XXE (entités externes XML)", "Désactiver la résolution d'entités externes dans les parseurs XML."),
    ("Contrôle d'accès défaillant", "Vérifier les permissions côté serveur à chaque requête, pas seulement côté client."),
    ("Mauvaise configuration de sécurité", "Désactiver les fonctionnalités par défaut inutiles, garder les dépendances à jour."),
    ("XSS (Cross-Site Scripting)", "Échapper toute donnée utilisateur avant de l'injecter dans le HTML/JS."),
    ("Désérialisation non sûre", "Ne jamais désérialiser (pickle, yaml.load...) des données venant d'une source non fiable."),
    ("Utilisation de composants vulnérables", "Surveiller les CVE des dépendances, les mettre à jour régulièrement."),
    ("Journalisation et surveillance insuffisantes", "Logger les événements de sécurité, alerter sur les anomalies."),
]


def failles_lecon():
    print("\n=== Leçon : les failles (vulnérabilités) — OWASP Top 10 (résumé) ===\n")
    for i, (nom, conseil) in enumerate(OWASP, start=1):
        print(f"  {i}. {nom}")
        print(f"     → {conseil}")
    print("\n   Astuce : l'option 8 (Analyser du code) cherche automatiquement certains")
    print("   de ces motifs dans un fichier que tu lui donnes.")


def cybersecurite_assistant():
    print("\n🛡️ Cybersécurité — pose ta question, ou choisis un thème :")
    themes = {
        "1": "réseau", "2": "web", "3": "mots de passe", "4": "social engineering",
        "5": "cryptographie",
    }
    for cle, nom in themes.items():
        print(f"  {cle}) {nom}")
    choix = input("Thème (ou tape directement ta question) : ").strip()
    question = themes.get(choix, choix)
    reponses = {
        "réseau": "Segmente ton réseau, ferme les ports inutiles, utilise un pare-feu et surveille le trafic sortant.",
        "web": "Valide/échappe toutes les entrées utilisateur, utilise HTTPS partout, applique le principe du moindre privilège.",
        "mots de passe": "Utilise un gestionnaire de mots de passe, des phrases longues et uniques par service, active le MFA.",
        "social engineering": "Méfie-toi des urgences artificielles, vérifie l'identité par un second canal, forme les équipes régulièrement.",
        "cryptographie": "Préfère des algorithmes éprouvés (AES-256, SHA-256+, argon2/bcrypt), ne réinvente jamais ta propre crypto.",
    }
    print("  ", reponses.get(question, "Pose une question plus précise (réseau, web, mots de passe, "
          "social engineering, cryptographie) ou utilise l'option 7 pour l'OWASP Top 10."))


def mini_ctf():
    print("\n🚩 Mini-CTF (hacking légal, local, éducatif)")
    print("   Résous les défis pour trouver le flag caché.\n")
    defis = [
        ("Décode ce Base64 :", base64.b64encode(b"MONIA{base64_c_est_facile}").decode(),
         lambda rep: rep.strip() == "MONIA{base64_c_est_facile}"),
        ("Ce texte a été décalé de 3 lettres (César), retrouve le flag :",
         "".join(chr((ord(c) - 97 + 3) % 26 + 97) if c.islower() else c
                 for c in "monia{cesar_facile}"),
         lambda rep: rep.strip().lower() == "monia{cesar_facile}"),
    ]
    score = 0
    for enonce, donnee, verif in defis:
        print(f"   {enonce}\n   {donnee}")
        rep = input("   Ta réponse (flag) : ")
        if verif(rep):
            print("   ✅ Bravo, flag correct !\n")
            score += 1
        else:
            print("   ❌ Pas tout à fait, essaie encore une prochaine fois.\n")
    print(f"   Score : {score}/{len(defis)}")


def bug_bounty_info():
    print("\n💰 Bug bounty / HackerOne — repères")
    print("   - Ne teste QUE les cibles couvertes par un programme (scope autorisé).")
    print("   - Lis toujours la politique du programme avant de commencer.")
    print("   - Plateformes : HackerOne, Bugcrowd, Intigriti, YesWeHack.")
    print("   - Méthodologie classique : recon (sous-domaines, techno) → cartographie")
    print("     des endpoints → tests ciblés (auth, injection, logique métier) → rapport clair.")
    print("   - Un bon rapport = reproductible, avec impact et preuve de concept (PoC).")


CHECKLIST_BUG_BOUNTY = [
    "Lire entièrement la politique et le scope du programme",
    "Recon passif : sous-domaines, DNS, certificats, historique (crt.sh, etc.)",
    "Recon actif limité au scope : ports/services autorisés",
    "Cartographier l'application (routes, paramètres, rôles)",
    "Tester l'authentification et la gestion de session",
    "Tester le contrôle d'accès (IDOR, élévation de privilège)",
    "Tester les entrées utilisateur (injection, XSS, SSRF, upload)",
    "Vérifier la logique métier (contournement de workflow)",
    "Documenter chaque preuve avec étapes de reproduction",
    "Rédiger un rapport clair avec impact et remédiation",
]


def checklist_bug_bounty():
    print("\n✅ Checklist Bug Bounty")
    for i, item in enumerate(CHECKLIST_BUG_BOUNTY, start=1):
        print(f"   [{i:2d}] {item}")
    if input("\nSauvegarder cette checklist dans data/rapports ? (o/N) : ").strip().lower() == "o":
        os.makedirs(RAPPORTS_DIR, exist_ok=True)
        chemin = os.path.join(RAPPORTS_DIR, f"checklist_{datetime.now():%Y%m%d_%H%M%S}.md")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("# Checklist Bug Bounty\n\n")
            for item in CHECKLIST_BUG_BOUNTY:
                f.write(f"- [ ] {item}\n")
        print(f"   💾 Sauvegardée : {chemin}")


def generateur_rapport():
    print("\n📄 Générateur de rapport (vulnérabilité)")
    titre = input("Titre de la faille : ").strip() or "Sans titre"
    cible = input("Cible / URL / endpoint : ").strip()
    severite = input("Sévérité (faible/moyenne/haute/critique) : ").strip() or "moyenne"
    description = input("Description : ").strip()
    reproduction = input("Étapes de reproduction (séparées par ';') : ").strip()
    impact = input("Impact : ").strip()
    remediation = input("Remédiation suggérée : ").strip()

    os.makedirs(RAPPORTS_DIR, exist_ok=True)
    nom_fichier = re.sub(r"\W+", "_", titre.lower()).strip("_") or "rapport"
    chemin = os.path.join(RAPPORTS_DIR, f"{nom_fichier}_{datetime.now():%Y%m%d_%H%M%S}.md")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(f"# {titre}\n\n")
        f.write(f"**Cible :** {cible}\n\n**Sévérité :** {severite}\n\n")
        f.write(f"## Description\n{description}\n\n")
        f.write("## Étapes de reproduction\n")
        for i, etape in enumerate((s.strip() for s in reproduction.split(";") if s.strip()), start=1):
            f.write(f"{i}. {etape}\n")
        f.write(f"\n## Impact\n{impact}\n\n## Remédiation\n{remediation}\n")
    print(f"\n   💾 Rapport sauvegardé : {chemin}")
