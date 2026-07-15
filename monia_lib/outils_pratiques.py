import ast
import base64
import hashlib
import operator
import secrets
import shutil
import string
import subprocess
import urllib.request
import json
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos, ast.FloorDiv: operator.floordiv,
}


def _eval_noeud(noeud):
    if isinstance(noeud, ast.Constant) and isinstance(noeud.value, (int, float)):
        return noeud.value
    if isinstance(noeud, ast.BinOp) and type(noeud.op) in OPS:
        return OPS[type(noeud.op)](_eval_noeud(noeud.left), _eval_noeud(noeud.right))
    if isinstance(noeud, ast.UnaryOp) and type(noeud.op) in OPS:
        return OPS[type(noeud.op)](_eval_noeud(noeud.operand))
    raise ValueError("expression non autorisée")


def calculer(expression):
    arbre = ast.parse(expression, mode="eval")
    return _eval_noeud(arbre.body)


def calculatrice():
    print("\n🧮 Calculatrice — tape une expression (+ - * / // % **), 'q' pour quitter")
    while True:
        expr = input("Calcul : ").strip()
        if expr.lower() in ("q", ""):
            break
        try:
            print(f"   = {calculer(expr)}")
        except Exception:
            print("   ⚠️ Expression invalide. Exemple : 3 * (4 + 2) / 2")


def generer_mot_de_passe(longueur=16, majuscules=True, chiffres=True, symboles=True):
    alphabet = string.ascii_lowercase
    if majuscules:
        alphabet += string.ascii_uppercase
    if chiffres:
        alphabet += string.digits
    if symboles:
        alphabet += "!@#$%^&*()-_=+[]{}?"
    return "".join(secrets.choice(alphabet) for _ in range(longueur))


def evaluer_force(mdp):
    score = 0
    if len(mdp) >= 8:
        score += 1
    if len(mdp) >= 12:
        score += 1
    if any(c.islower() for c in mdp):
        score += 1
    if any(c.isupper() for c in mdp):
        score += 1
    if any(c.isdigit() for c in mdp):
        score += 1
    if any(c in string.punctuation for c in mdp):
        score += 1
    niveaux = ["très faible", "faible", "moyen", "correct", "fort", "très fort", "excellent"]
    return niveaux[min(score, len(niveaux) - 1)], score


def mots_de_passe():
    print("\n🔑 Outils mots de passe")
    print("  1) Générer un mot de passe")
    print("  2) Tester la force d'un mot de passe")
    choix = input("Choix : ").strip()
    if choix == "1":
        try:
            longueur = int(input("Longueur (défaut 16) : ").strip() or "16")
        except ValueError:
            longueur = 16
        mdp = generer_mot_de_passe(longueur)
        force, _ = evaluer_force(mdp)
        print(f"   Mot de passe : {mdp}")
        print(f"   Force estimée : {force}")
    elif choix == "2":
        mdp = input("Mot de passe à tester : ")
        force, score = evaluer_force(mdp)
        print(f"   Force estimée : {force} ({score}/6)")
    else:
        print("   Choix inconnu.")


def cesar(texte, decalage):
    resultat = []
    for c in texte:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            resultat.append(chr((ord(c) - base + decalage) % 26 + base))
        else:
            resultat.append(c)
    return "".join(resultat)


def xor_chiffrer(texte, cle):
    donnees = texte.encode("utf-8")
    cle_octets = cle.encode("utf-8")
    return bytes(b ^ cle_octets[i % len(cle_octets)] for i, b in enumerate(donnees))


def crypto_toolbox():
    print("\n🔐 Boîte à outils crypto")
    print("  1) Base64 encoder     2) Base64 décoder")
    print("  3) Hash (md5/sha1/sha256/sha512)")
    print("  4) Chiffrement César   5) Déchiffrement César")
    print("  6) XOR (chiffrer/déchiffrer, clé texte)")
    print("  7) ROT13")
    choix = input("Choix : ").strip()
    if choix == "1":
        texte = input("Texte : ")
        print("  ", base64.b64encode(texte.encode()).decode())
    elif choix == "2":
        texte = input("Base64 : ")
        try:
            print("  ", base64.b64decode(texte.encode()).decode(errors="replace"))
        except Exception as e:
            print("   ⚠️ Erreur :", e)
    elif choix == "3":
        texte = input("Texte à hasher : ")
        for algo in ("md5", "sha1", "sha256", "sha512"):
            h = hashlib.new(algo)
            h.update(texte.encode())
            print(f"   {algo:8s} : {h.hexdigest()}")
    elif choix == "4":
        texte = input("Texte : ")
        try:
            decalage = int(input("Décalage (défaut 3) : ").strip() or "3")
        except ValueError:
            decalage = 3
        print("  ", cesar(texte, decalage))
    elif choix == "5":
        texte = input("Texte chiffré : ")
        try:
            decalage = int(input("Décalage (défaut 3) : ").strip() or "3")
        except ValueError:
            decalage = 3
        print("  ", cesar(texte, -decalage))
    elif choix == "6":
        texte = input("Texte : ")
        cle = input("Clé : ")
        resultat = xor_chiffrer(texte, cle)
        print("   Résultat (hex) :", resultat.hex())
    elif choix == "7":
        texte = input("Texte : ")
        print("  ", cesar(texte, 13))
    else:
        print("   Choix inconnu.")


def outils_reseau():
    print("\n🛠️ Tes outils (nmap, whois, ping, dig...)")
    print("   ⚠️ N'utilise ces outils que sur des cibles que tu es autorisé à tester.")
    print("  1) nmap    2) whois    3) ping    4) dig")
    choix = input("Choix : ").strip()
    commandes = {"1": "nmap", "2": "whois", "3": "ping", "4": "dig"}
    outil = commandes.get(choix)
    if not outil:
        print("   Choix inconnu.")
        return
    if not shutil.which(outil):
        print(f"   ⚠️ '{outil}' n'est pas installé sur ce système.")
        print(f"      Installe-le (ex : apt install {outil}) puis réessaie.")
        return
    cible = input(f"Cible pour {outil} : ").strip()
    if not cible:
        return
    args = [outil]
    if outil == "ping":
        args += ["-c", "4", cible]
    elif outil == "nmap":
        args += ["-F", cible]
    else:
        args += [cible]
    try:
        resultat = subprocess.run(args, capture_output=True, text=True, timeout=30)
        print(resultat.stdout or resultat.stderr)
    except subprocess.TimeoutExpired:
        print("   ⚠️ Délai dépassé.")
    except Exception as e:
        print("   ⚠️ Erreur :", e)


VILLES = {
    "Paris": "Europe/Paris", "Londres": "Europe/London", "New York": "America/New_York",
    "Los Angeles": "America/Los_Angeles", "Tokyo": "Asia/Tokyo", "Sydney": "Australia/Sydney",
    "Moscou": "Europe/Moscow", "Dubai": "Asia/Dubai", "Pékin": "Asia/Shanghai",
    "São Paulo": "America/Sao_Paulo",
}


def heure_monde():
    print("\n🕐 L'heure dans le monde")
    if ZoneInfo is None:
        print("   ⚠️ Module zoneinfo indisponible sur ce Python.")
        return
    for ville, fuseau in VILLES.items():
        try:
            heure = datetime.now(ZoneInfo(fuseau))
            print(f"   {ville:12s} : {heure.strftime('%Y-%m-%d %H:%M')} ({fuseau})")
        except Exception:
            continue


def taux_change():
    print("\n💱 Taux de change")
    base = (input("Devise de départ (défaut EUR) : ").strip() or "EUR").upper()
    try:
        url = f"https://api.frankfurter.app/latest?from={base}"
        with urllib.request.urlopen(url, timeout=6) as reponse:
            donnees = json.loads(reponse.read().decode())
        print(f"   Taux depuis {base} (date : {donnees.get('date')}) :")
        for devise, taux in list(donnees.get("rates", {}).items())[:12]:
            print(f"   1 {base} = {taux} {devise}")
    except Exception:
        print("   ⚠️ Pas d'accès réseau (ou devise inconnue). Réessaie plus tard,")
        print("      ou vérifie ta connexion internet.")
