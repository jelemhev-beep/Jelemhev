# MonIA

Un assistant personnel en ligne de commande : mémoire persistante (second
cerveau), chat avec une IA (dans le cloud via Groq, ou en local via
Ollama), calculateur de devis, et sortie vocale. Zéro dépendance externe
— juste la bibliothèque standard Python (`urllib`, `json`, `subprocess`).

## Les briques

- **`monia/secondcerveau.py`** — mémoire persistante : notes et
  conversations stockées en fichiers markdown lisibles, organisés par
  projet (`~/.monia/secondcerveau/<Projet>/`). Pas de base de données —
  juste des fichiers, faciles à relire, sauvegarder, ou pousser sur
  GitHome.
- **`monia/llm_cloud.py`** — client pour l'API cloud de
  [Groq](https://console.groq.com) : de vrais gros modèles (Llama 3.3
  70B) qui tournent sur leurs serveurs, pas sur le téléphone. Gratuit
  (clé API requise), et bien plus capable qu'un modèle local — utilisé
  en priorité si `GROQ_API_KEY` est configuree.
- **`monia/llm_local.py`** — client pour un modèle pré-entraîné servi par
  [Ollama](https://ollama.com) en local (`llama3.2`, `qwen2.5`, etc.),
  utilisé en repli si aucune clé Groq n'est configurée. Un téléphone n'a
  généralement pas assez de RAM pour un modèle local vraiment capable —
  voir la section RAM plus bas.
- **`monia/devis.py`** — calculateur de devis matériaux (gravier, sable,
  béton...) : surface + épaisseur → volume, poids, prix estimé.
- **`monia/voice.py`** — synthèse vocale via `termux-tts-speak` (app
  Termux:API), toujours optionnelle.
- **`monia/digits.py`** — pont vers le projet [`neuralnet`](../neuralnet)
  (dossier frère dans le même dépôt) : réutilise son moteur de réseau de
  neurones et son canvas de dessin ASCII pour reconnaître des chiffres
  écrits à la main, directement depuis MonIA.
- **`monia/cli.py`** — la boucle interactive qui relie tout.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Aucune dépendance à installer pour MonIA lui-même.

### Option recommandée : Groq (cloud, gratuit, rapide, vraiment capable)

1. Crée un compte gratuit sur [console.groq.com](https://console.groq.com)
2. Génère une clé API
3. `export GROQ_API_KEY=ta_cle` (ajoute-le à `~/.bashrc` pour ne pas le
   retaper à chaque fois)

Aucune charge sur la RAM du téléphone : la question part sur internet, le
modèle tourne chez Groq, seule la réponse revient.

### Option locale : Ollama (marche hors-ligne, mais limité par la RAM)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b   # ou qwen2.5:0.5b si la RAM est trop juste
```

Pas besoin de lancer `ollama serve` toi-même : MonIA détecte qu'Ollama
n'est pas démarré et le lance automatiquement en arrière-plan au
démarrage (et retente juste avant chaque `chat` si besoin). Ça ne survit
pas à Android qui tue les processus en arrière-plan après un long moment
d'inactivité — dans ce cas MonIA le relance automatiquement au prochain
`chat`.

**Attention a la RAM** : un modèle local, meme petit, prend facilement
1 a 1.5 Go. Verifie ce qu'il te reste avec `free -h` avant de choisir la
taille du modèle. Si `GROQ_API_KEY` est configurée, Ollama n'est meme pas
sollicite -- Groq est toujours essaye en premier.

## Utilisation

```bash
python3 -m monia
```

Un menu numéroté s'affiche au démarrage — tape un chiffre, ou une commande
complète si tu préfères :

```
=== MonIA ===
  1) Discuter avec le LLM local
  2) Changer de projet actif
  3) Prendre une note
  4) Voir mes notes
  5) Rechercher dans le second cerveau
  6) Calculer un devis
  7) Voir les materiaux disponibles
  8) Dessiner un chiffre (reconnaissance neuralnet)
  9) Activer/desactiver la voix
  0) Quitter

> 6
Materiau, surface en m2, epaisseur en cm (optionnel) : gravier 20 5
Materiau      : gravier
Surface       : 20 m2
...

> 1
Ton message : comment reussir une terrasse en bois ?
...
```

Les commandes complètes marchent toujours en parallèle du menu (`chat ...`,
`devis ...`, `dessin`, `voix on|off`, `note ...`, etc.) — tape `aide` pour
tout revoir.

Chaque `devis`, `chat` et `dessin` reconnu est automatiquement sauvegardé
dans le second cerveau du projet actif — rien ne se perd en fermant le
terminal.

`dessin` nécessite que le projet `neuralnet` soit cloné juste à côté de
`monia` (dossiers frères, comme dans ce dépôt) et qu'un modèle y ait été
entraîné (`neuralnet/examples/mnist.py` ou `mnist_improved.py`).

## Tests

```bash
pip install pytest
pytest
```

Les clients Ollama et Groq sont testés contre de vrais serveurs HTTP de
test (pas des mocks qui trichent) imitant leurs API respectives, y
compris le démarrage automatique d'Ollama (`ensure_running`) et le repli
Groq -> Ollama en cas d'erreur. La CLI est testée de bout en bout : chat,
notes, devis, recherche, projets, dessin, et le menu numéroté.
