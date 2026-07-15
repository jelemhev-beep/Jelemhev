import json
import mimetypes
import os
import re
import struct
import urllib.parse
import urllib.request

from monia_lib import memoire, llm_local, outils_pratiques, securite

SALUTATIONS = ("salut", "bonjour", "bonsoir", "coucou", "hello", "hey")


def _reponse_generique(question):
    connue = memoire.chercher(question)
    if connue:
        return connue
    ql = question.lower()
    if any(mot in ql for mot in SALUTATIONS):
        return "Salut ! Je suis MonIA, ton IA 100% maison. Pose-moi une question ou tape 'menu'."
    if "merci" in ql:
        return "Avec plaisir !"
    if ql.endswith("?"):
        return ("Bonne question ! Je n'ai pas de réponse toute faite pour ça, mais tu peux"
                " me l'apprendre avec l'option 26, ou activer le LLM local (option 45) pour"
                " des réponses plus libres.")
    return "D'accord. Dis-m'en plus, ou tape 'menu' pour voir tout ce que je sais faire."


def discuter():
    print("\n💬 Discuter — pose-moi une question ('q' pour quitter)")
    while True:
        question = input("Toi : ").strip()
        if question.lower() in ("q", ""):
            break
        if llm_local.modele_disponible():
            reponse = llm_local.generer(question)
            print(f"MonIA : {reponse or _reponse_generique(question)}\n")
        else:
            print(f"MonIA : {_reponse_generique(question)}\n")


def ecrire_texte():
    print("\n✍️ Écrire un texte")
    sujet = input("Sujet : ").strip()
    genre = (input("Type (article/email/résumé, défaut article) : ").strip() or "article").lower()
    if not sujet:
        return
    if llm_local.modele_disponible():
        reponse = llm_local.generer(f"Écris un {genre} en français sur : {sujet}")
        if reponse:
            print(f"\n{reponse}\n")
            return
    print(f"\n--- Brouillon ({genre}) : {sujet} ---\n")
    if genre == "email":
        print(f"Objet : {sujet}\n")
        print("Bonjour,\n")
        print(f"Je vous écris au sujet de {sujet}. [développe ton propos ici]\n")
        print("Cordialement,")
    elif genre == "résumé" or genre == "resume":
        print(f"{sujet} peut se résumer en trois points clés :")
        print("1. [point principal]")
        print("2. [point secondaire]")
        print("3. [conclusion]")
    else:
        print(f"Introduction : {sujet} est un sujet qui mérite qu'on s'y attarde...")
        print("Développement : [argument 1], [argument 2], [exemple concret]")
        print("Conclusion : en résumé, [synthèse].")
    print("\n(Squelette généré localement — active le LLM local, option 45, pour un texte complet.)")


MODELES_CODE = {
    "fichier": '''with open("fichier.txt", "r", encoding="utf-8") as f:
    contenu = f.read()
print(contenu)''',
    "boucle": '''for i in range(10):
    print(i)''',
    "classe": '''class MaClasse:
    def __init__(self, valeur):
        self.valeur = valeur

    def afficher(self):
        print(self.valeur)''',
    "api": '''import urllib.request
import json

with urllib.request.urlopen("https://api.exemple.com/donnees") as reponse:
    donnees = json.loads(reponse.read().decode())
print(donnees)''',
    "tri": '''def tri_rapide(liste):
    if len(liste) <= 1:
        return liste
    pivot = liste[len(liste) // 2]
    gauche = [x for x in liste if x < pivot]
    milieu = [x for x in liste if x == pivot]
    droite = [x for x in liste if x > pivot]
    return tri_rapide(gauche) + milieu + tri_rapide(droite)''',
    "serveur": '''from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bonjour !")

HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()''',
}


def coder_python():
    print("\n🐍 Coder en Python")
    besoin = input("Décris ce dont tu as besoin (fichier/boucle/classe/api/tri/serveur/...) : ").strip()
    if llm_local.modele_disponible():
        reponse = llm_local.generer(f"Écris un code Python pour : {besoin}. Réponds uniquement avec le code.")
        if reponse:
            print(f"\n{reponse}\n")
            return
    bl = besoin.lower()
    for cle, code in MODELES_CODE.items():
        if cle in bl:
            print(f"\n```python\n{code}\n```\n")
            return
    print("\n   Je n'ai pas de modèle tout prêt pour ça. Essaie un mot-clé parmi :")
    print(f"   {', '.join(MODELES_CODE)}")
    print("   ou active le LLM local (option 45) pour du code sur mesure.")


DEPANNAGE = [
    (r"permission denied", "Permission refusée : utilise 'sudo' (avec précaution) ou vérifie les droits "
     "avec 'ls -l', puis 'chmod'/'chown' si tu es propriétaire du fichier."),
    (r"command not found|n'est pas reconnu", "Commande introuvable : vérifie l'orthographe, installe le "
     "paquet correspondant, ou vérifie que le dossier est dans ta variable $PATH."),
    (r"no such file or directory", "Fichier/dossier introuvable : vérifie le chemin avec 'pwd' et 'ls', "
     "utilise Tab pour l'autocomplétion."),
    (r"address already in use", "Port déjà utilisé : trouve le processus avec 'lsof -i :PORT' (ou "
     "'netstat -tulpn') puis arrête-le ou change de port."),
    (r"connection refused", "Connexion refusée : le service visé n'écoute probablement pas sur ce "
     "port/hôte, ou un pare-feu bloque la connexion."),
    (r"disk quota exceeded|no space left", "Plus de place disque : vérifie avec 'df -h', nettoie les "
     "gros fichiers/caches avec 'du -sh * | sort -h'."),
    (r"module.*not found|no module named", "Module Python manquant : installe-le avec "
     "'pip install <nom_du_module>' (idéalement dans un environnement virtuel)."),
]


def depanner_terminal():
    print("\n🛠️ Dépanner le terminal")
    probleme = input("Colle le message d'erreur ou décris le problème : ").strip()
    pl = probleme.lower()
    for motif, conseil in DEPANNAGE:
        if re.search(motif, pl):
            print(f"\n   → {conseil}")
            return
    if llm_local.modele_disponible():
        reponse = llm_local.generer(f"Explique et propose une solution pour ce problème de terminal : {probleme}")
        if reponse:
            print(f"\n{reponse}\n")
            return
    print("\n   Je ne reconnais pas ce message précis. Colle le message d'erreur complet,")
    print("   ou active le LLM local (option 45) pour une aide plus poussée.")


def github_assistant():
    print("\n🐙 GitHub")
    print("  1) Infos sur un dépôt (owner/repo)   2) Infos sur un utilisateur")
    choix = input("Choix : ").strip()
    try:
        if choix == "1":
            depot = input("Dépôt (ex : anthropics/claude-code) : ").strip()
            with urllib.request.urlopen(f"https://api.github.com/repos/{depot}",
                                         timeout=6) as reponse:
                d = json.loads(reponse.read().decode())
            if "message" in d and "full_name" not in d:
                print("   ⚠️", d["message"])
                return
            print(f"   ⭐ {d.get('stargazers_count')}  🍴 {d.get('forks_count')}  "
                  f"🐞 issues ouvertes : {d.get('open_issues_count')}")
            print(f"   {d.get('description')}")
            print(f"   {d.get('html_url')}")
        elif choix == "2":
            utilisateur = input("Nom d'utilisateur GitHub : ").strip()
            with urllib.request.urlopen(f"https://api.github.com/users/{utilisateur}",
                                         timeout=6) as reponse:
                d = json.loads(reponse.read().decode())
            if "message" in d and "login" not in d:
                print("   ⚠️", d["message"])
                return
            print(f"   {d.get('name') or d.get('login')} — {d.get('bio') or 'pas de bio'}")
            print(f"   Dépôts publics : {d.get('public_repos')}  Followers : {d.get('followers')}")
            print(f"   {d.get('html_url')}")
        else:
            print("   Choix inconnu.")
    except Exception:
        print("   ⚠️ Pas d'accès réseau ou dépôt/utilisateur introuvable.")


def _dimensions_image(chemin):
    try:
        with open(chemin, "rb") as f:
            entete = f.read(32)
        if entete[:8] == b"\x89PNG\r\n\x1a\n":
            largeur, hauteur = struct.unpack(">II", entete[16:24])
            return largeur, hauteur
        if entete[:2] == b"\xff\xd8":
            return None
    except OSError:
        return None
    return None


def analyser_fichier():
    print("\n📎 Analyser un fichier / une photo")
    chemin = input("Chemin du fichier : ").strip()
    if not chemin or not os.path.isfile(chemin):
        print("   ⚠️ Fichier introuvable.")
        return
    taille = os.path.getsize(chemin)
    type_mime, _ = mimetypes.guess_type(chemin)
    print(f"   Nom       : {os.path.basename(chemin)}")
    print(f"   Taille    : {taille} octets")
    print(f"   Type MIME : {type_mime or 'inconnu'}")
    extension = os.path.splitext(chemin)[1].lower()
    if extension in (".py", ".js", ".php", ".java", ".ts", ".rb", ".go", ".sh"):
        print("\n   Fichier de code détecté, lancement de l'analyse de failles :")
        securite.analyser_chemin(chemin)
    elif type_mime and type_mime.startswith("image"):
        dims = _dimensions_image(chemin)
        if dims:
            print(f"   Dimensions : {dims[0]}x{dims[1]} px")
        else:
            print("   (dimensions non déterminées sans bibliothèque d'image dédiée)")
    else:
        print("   Type non pris en charge pour une analyse approfondie.")


def voir_media():
    print("\n🖼️ Voir (images & vidéos)")
    chemin = input("Chemin du fichier : ").strip()
    if not chemin or not os.path.isfile(chemin):
        print("   ⚠️ Fichier introuvable.")
        return
    type_mime, _ = mimetypes.guess_type(chemin)
    taille = os.path.getsize(chemin)
    print(f"   Fichier   : {os.path.basename(chemin)}")
    print(f"   Taille    : {taille / 1024:.1f} Ko")
    print(f"   Type MIME : {type_mime or 'inconnu'}")
    if type_mime and type_mime.startswith("image"):
        dims = _dimensions_image(chemin)
        if dims:
            print(f"   Dimensions : {dims[0]}x{dims[1]} px")
    elif type_mime and type_mime.startswith("video"):
        import shutil
        import subprocess
        if shutil.which("ffprobe"):
            try:
                resultat = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries",
                     "format=duration:stream=width,height,codec_name",
                     "-of", "default=noprint_wrappers=1", chemin],
                    capture_output=True, text=True, timeout=10)
                print(resultat.stdout.strip())
            except Exception:
                pass
        else:
            print("   (installe 'ffmpeg' pour obtenir durée/résolution : ffprobe manquant)")
    print("   (MonIA fonctionne en terminal : pas d'aperçu graphique, seulement les métadonnées)")


def repondre(question):
    ql = question.lower()
    try:
        print(f"MonIA : = {outils_pratiques.calculer(question)}\n")
        return
    except Exception:
        pass
    if "traduis" in ql or "traduction" in ql:
        from monia_lib import web_services
        web_services.traducteur()
        return
    if "météo" in ql or "meteo" in ql:
        from monia_lib import web_services
        web_services.meteo()
        return
    if "heure" in ql and ("monde" in ql or "il est" in ql):
        outils_pratiques.heure_monde()
        return
    connue = memoire.chercher(question)
    if connue:
        print(f"MonIA : {connue}\n")
        return
    if llm_local.modele_disponible():
        reponse = llm_local.generer(question)
        if reponse:
            print(f"MonIA : {reponse}\n")
            return
    print(f"MonIA : {_reponse_generique(question)}\n")


def assistant_monia():
    print("\n⭐ Assistant MonIA — discute, calcule, traduit, sait tout")
    print("   (pose ta question, 'q' pour revenir au menu)\n")
    while True:
        question = input("Toi : ").strip()
        if question.lower() in ("q", ""):
            break
        repondre(question)
