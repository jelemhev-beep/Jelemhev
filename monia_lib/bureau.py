import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
NOTES_DIR = os.path.join(DATA_DIR, "second_cerveau")


def _agent_recherche(sujet):
    print("   🔎 Agent Recherche : je rassemble ce que je trouve...")
    elements = []
    try:
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(sujet)}"
        req = urllib.request.Request(url, headers={"User-Agent": "MonIA/1.0"})
        with urllib.request.urlopen(req, timeout=6) as reponse:
            donnees = json.loads(reponse.read().decode())
        extrait = donnees.get("extract")
        if extrait:
            elements.append(("Wikipédia", extrait))
    except Exception:
        pass
    try:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": sujet})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MonIA)"})
        with urllib.request.urlopen(req, timeout=8) as reponse:
            html = reponse.read().decode(errors="replace")
        titres = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)[:5]
        titres_propres = [re.sub("<.*?>", "", t).strip() for t in titres]
        if titres_propres:
            elements.append(("Résultats web", "\n".join(f"- {t}" for t in titres_propres)))
    except Exception:
        pass
    if not elements:
        print("   ⚠️ Aucune source accessible (pas de réseau ?).")
    return elements


def _agent_documentation(sujet, elements):
    print("   🗂️ Agent Documentation : je rédige la note...")
    os.makedirs(NOTES_DIR, exist_ok=True)
    nom = re.sub(r"\W+", "_", sujet.lower()).strip("_") or "note"
    chemin = os.path.join(NOTES_DIR, f"{nom}.md")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(f"# {sujet}\n\n_Note générée par le Bureau de MonIA le {datetime.now():%d/%m/%Y %H:%M}_\n\n")
        for source, contenu in elements:
            f.write(f"## {source}\n{contenu}\n\n")
    return chemin


def bureau_monia():
    print("\n🏛 Le Bureau de MonIA (agents Recherche + Documentation)")
    sujet = input("Sujet à investiguer : ").strip()
    if not sujet:
        return
    elements = _agent_recherche(sujet)
    if not elements:
        return
    chemin = _agent_documentation(sujet, elements)
    print(f"\n   ✅ Note rédigée et sauvegardée : {chemin}")
    print("   (consultable aussi via l'option 41, second cerveau)")
