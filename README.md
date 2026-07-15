# MonIA — ton IA 100% maison

Recréation du menu MonIA (CLI Python, 100% local par défaut) : assistants,
outils pratiques, leçons de machine learning "faites main", et modules
plus avancés (LLM local, second cerveau, gestion de végétaux/chantiers).

## Lancer

```bash
python3 monia.py
```

Aucune dépendance externe n'est nécessaire pour l'essentiel du menu — tout
tourne avec la bibliothèque standard de Python 3. Les fonctionnalités qui
ont besoin d'internet (météo, actualités, traduction, Wikipédia, taux de
change, recherche web...) échouent proprement avec un message clair si le
réseau n'est pas disponible.

Deux dépendances optionnelles activent des options avancées (voir
`requirements.txt`) :

- `llama-cpp-python` — option 45, LLM local (modèle `.gguf`, ex : Qwen2.5).
  Placer le modèle à `/root/modeles/qwen2.5-1.5b-instruct-q4_k_m.gguf` ou
  définir la variable d'environnement `LLAMA_MODELE`.
- `PySocks` — option 34, navigation via Tor (nécessite aussi un service Tor
  local écoutant sur `127.0.0.1:9050`).

## Tests

```bash
python3 -m unittest discover -s tests -v
```

ou directement depuis le menu, avec l'option `t`.

## Structure

```
monia.py            point d'entrée, menu principal et dispatch
monia_lib/
  memoire.py          mémoire persistante ("apprendre tes réponses")
  neurone.py           leçons ML : neurone, y=2x, entraînement, réseau XOR
  outils_pratiques.py  calculatrice, mots de passe, crypto, réseau, heure, change
  securite.py           failles (OWASP), analyse de code, mini-CTF, bug bounty, rapports
  web_services.py       météo, actualités, dictionnaire, traducteur, Wikipédia, recherche, Tor
  assistant.py           discuter, écrire, coder, dépanner, GitHub, assistant MonIA
  bibliotheque.py        bibliothèque de livres texte, hors ligne
  second_cerveau.py      recherche dans des notes Markdown (style Obsidian)
  vegetaux.py            fiches de végétaux (ajout, photos, exposition)
  chantiers.py            liens chantiers/végétaux, calcul de matériaux, devis
  bureau.py                agents Recherche + Documentation
  llm_local.py             chargement d'un modèle .gguf via llama-cpp-python
data/                stockage local (JSON, notes, rapports, devis) — créé à l'usage
tests/               suite de tests unitaires
```

## Ce qui diffère de l'original

Cette version a été recréée à partir d'une capture d'écran du menu (pas du
code source original). Les fonctionnalités reposant sur des services
externes (météo, actualités, traduction...) utilisent des API publiques
sans clé ; le LLM local suit le même format d'avertissement que celui vu
sur la capture d'écran quand le modèle `.gguf` est absent.
