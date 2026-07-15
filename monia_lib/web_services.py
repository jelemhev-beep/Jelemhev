import json
import os
import random
import re
import socket
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
NOTES_DIR = os.path.join(DATA_DIR, "second_cerveau")

DICO_LOCAL = {
    "python": "Langage de programmation interprété, généraliste et lisible.",
    "algorithme": "Suite finie et non ambiguë d'instructions pour résoudre un problème.",
    "réseau": "Ensemble d'équipements reliés entre eux pour échanger des données.",
    "chiffrement": "Transformation d'une information pour la rendre inintelligible sans clé.",
    "serveur": "Programme ou machine qui répond aux requêtes d'autres programmes (clients).",
}


def _requete_json(url, timeout=6):
    with urllib.request.urlopen(url, timeout=timeout) as reponse:
        return json.loads(reponse.read().decode())


def meteo():
    print("\n🌦️ La météo")
    ville = input("Ville : ").strip()
    if not ville:
        return
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
            {"name": ville, "count": 1, "language": "fr"})
        geo = _requete_json(geo_url)
        resultats = geo.get("results")
        if not resultats:
            print("   ⚠️ Ville introuvable.")
            return
        lieu = resultats[0]
        lat, lon = lieu["latitude"], lieu["longitude"]
        meteo_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(
            {"latitude": lat, "longitude": lon, "current": "temperature_2m,wind_speed_10m,relative_humidity_2m"})
        donnees = _requete_json(meteo_url)
        actuel = donnees.get("current", {})
        print(f"   📍 {lieu.get('name')}, {lieu.get('country', '')}")
        print(f"   🌡️ Température : {actuel.get('temperature_2m')} °C")
        print(f"   💧 Humidité     : {actuel.get('relative_humidity_2m')} %")
        print(f"   💨 Vent         : {actuel.get('wind_speed_10m')} km/h")
    except Exception:
        print("   ⚠️ Pas d'accès réseau. Vérifie ta connexion internet et réessaie.")


def actualites():
    print("\n📰 Les actualités")
    sujet = input("Sujet (vide = actualités générales) : ").strip()
    try:
        if sujet:
            url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
                {"q": sujet, "hl": "fr", "gl": "FR", "ceid": "FR:fr"})
        else:
            url = "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr"
        req = urllib.request.Request(url, headers={"User-Agent": "MonIA/1.0"})
        with urllib.request.urlopen(req, timeout=6) as reponse:
            arbre = ET.fromstring(reponse.read())
        items = arbre.findall(".//item")[:8]
        if not items:
            print("   ⚠️ Aucun résultat.")
            return
        for item in items:
            titre = item.findtext("title", default="").strip()
            print(f"   • {titre}")
    except Exception:
        print("   ⚠️ Pas d'accès réseau. Vérifie ta connexion internet et réessaie.")


def dictionnaire():
    print("\n📔 Le dictionnaire")
    mot = input("Mot : ").strip().lower()
    if not mot:
        return
    if mot in DICO_LOCAL:
        print(f"   {mot} : {DICO_LOCAL[mot]}")
        return
    try:
        url = f"https://fr.wiktionary.org/api/rest_v1/page/summary/{urllib.parse.quote(mot)}"
        req = urllib.request.Request(url, headers={"User-Agent": "MonIA/1.0"})
        with urllib.request.urlopen(req, timeout=6) as reponse:
            donnees = json.loads(reponse.read().decode())
        extrait = donnees.get("extract")
        if extrait:
            print(f"   {mot} : {extrait}")
        else:
            print("   ⚠️ Pas de définition trouvée.")
    except Exception:
        print("   ⚠️ Pas d'accès réseau et mot absent du dictionnaire local restreint.")
        print(f"      (dictionnaire local : {', '.join(DICO_LOCAL)})")


def traducteur():
    print("\n🌍 Le traducteur")
    texte = input("Texte à traduire : ").strip()
    if not texte:
        return
    langue_source = input("Langue source (code, ex: fr, défaut auto) : ").strip() or "auto"
    langue_cible = input("Langue cible (code, ex: en, défaut en) : ").strip() or "en"
    try:
        url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
            {"q": texte, "langpair": f"{langue_source}|{langue_cible}"})
        donnees = _requete_json(url)
        traduction = donnees.get("responseData", {}).get("translatedText")
        if traduction:
            print(f"   → {traduction}")
        else:
            print("   ⚠️ Traduction indisponible.")
    except Exception:
        print("   ⚠️ Pas d'accès réseau. Vérifie ta connexion internet et réessaie.")


def lire_wikipedia():
    print("\n📖 Lire Wikipédia (et le retenir)")
    sujet = input("Sujet : ").strip()
    if not sujet:
        return
    try:
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sujet)}"
        req = urllib.request.Request(url, headers={"User-Agent": "MonIA/1.0"})
        with urllib.request.urlopen(req, timeout=6) as reponse:
            donnees = json.loads(reponse.read().decode())
        extrait = donnees.get("extract")
        if not extrait:
            print("   ⚠️ Article introuvable.")
            return
        print(f"\n   {donnees.get('title')}\n   {'-' * len(donnees.get('title', ''))}")
        print(f"   {extrait}\n")
        if input("   Retenir cet article dans le second cerveau ? (o/N) : ").strip().lower() == "o":
            os.makedirs(NOTES_DIR, exist_ok=True)
            nom = re.sub(r"\W+", "_", sujet.lower()).strip("_") or "article"
            chemin = os.path.join(NOTES_DIR, f"{nom}.md")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(f"# {donnees.get('title')}\n\n{extrait}\n\nSource : {url}\n")
            print(f"   💾 Retenu dans {chemin}")
    except Exception:
        print("   ⚠️ Pas d'accès réseau. Vérifie ta connexion internet et réessaie.")


def recherche_web():
    print("\n🔎 Rechercher sur le web")
    requete = input("Recherche : ").strip()
    if not requete:
        return
    try:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": requete})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MonIA)"})
        with urllib.request.urlopen(req, timeout=8) as reponse:
            html = reponse.read().decode(errors="replace")
        titres = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        liens = re.findall(r'class="result__a" href="(.*?)"', html)
        resultats = list(zip(titres, liens))[:8]
        if not resultats:
            print("   ⚠️ Aucun résultat (ou format de page inattendu).")
            return
        for titre, lien in resultats:
            titre_propre = re.sub("<.*?>", "", titre).strip()
            print(f"   • {titre_propre}\n     {lien}")
    except Exception:
        print("   ⚠️ Pas d'accès réseau. Vérifie ta connexion internet et réessaie.")


def tor_naviguer():
    print("\n🧅 Tor (naviguer anonymement)")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.5)
        try:
            s.connect(("127.0.0.1", 9050))
            proxy_dispo = True
        except OSError:
            proxy_dispo = False
    if not proxy_dispo:
        print("   ⚠️ Aucun proxy Tor local détecté sur 127.0.0.1:9050.")
        print("      Installe et lance Tor (ex : apt install tor && systemctl start tor)")
        print("      puis réessaie.")
        return
    try:
        import socks  # PySocks
    except ImportError:
        print("   ⚠️ Le paquet 'PySocks' est requis pour router le trafic via Tor.")
        print("      Installe-le avec : pip install PySocks")
        return
    url = input("URL .onion ou classique à visiter : ").strip()
    if not url:
        return
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MonIA Tor)"})
        with urllib.request.urlopen(req, timeout=20) as reponse:
            contenu = reponse.read(2000).decode(errors="replace")
        print("   ✅ Connecté via Tor. Extrait de la page :\n")
        print("   " + contenu[:800].replace("\n", " "))
    except Exception as e:
        print("   ⚠️ Échec de la connexion via Tor :", e)


QUIZ = [
    ("Quelle est la capitale de l'Australie ?", "canberra"),
    ("En quelle année a eu lieu la chute du mur de Berlin ?", "1989"),
    ("Quel est le plus grand océan du monde ?", "pacifique"),
    ("Qui a peint la Joconde ?", "leonard de vinci"),
    ("Combien y a-t-il de continents généralement reconnus ?", "7"),
]


def culture_generale():
    print("\n🎓 Culture générale — quiz")
    questions = random.sample(QUIZ, k=min(3, len(QUIZ)))
    score = 0
    for question, reponse_attendue in questions:
        rep = input(f"   {question}\n   Ta réponse : ").strip().lower()
        rep = rep.replace("é", "e").replace("è", "e")
        if reponse_attendue in rep:
            print("   ✅ Correct !\n")
            score += 1
        else:
            print(f"   ❌ Non, la réponse était : {reponse_attendue}\n")
    print(f"   Score : {score}/{len(questions)}")
