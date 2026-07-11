# MonIA

Un assistant personnel en ligne de commande : mémoire persistante (second
cerveau), chat avec un vrai LLM local (Ollama), calculateur de devis, et
sortie vocale. Zéro dépendance externe — juste la bibliothèque standard
Python (`urllib`, `json`, `subprocess`).

## Les briques

- **`monia/secondcerveau.py`** — mémoire persistante : notes et
  conversations stockées en fichiers markdown lisibles, organisés par
  projet (`~/.monia/secondcerveau/<Projet>/`). Pas de base de données —
  juste des fichiers, faciles à relire, sauvegarder, ou pousser sur
  GitHome.
- **`monia/llm_local.py`** — client pour un vrai modèle pré-entraîné servi
  par [Ollama](https://ollama.com) en local (`llama3.2`, `phi3`, etc.).
  Ce n'est pas un LLM fait maison : entraîner un vrai modèle de langage
  from scratch n'est pas réaliste sur un téléphone. Ollama fait tourner le
  modèle, MonIA parle juste à son API REST.
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

Aucune dépendance à installer pour MonIA lui-même. Pour le chat, installe
[Ollama](https://ollama.com) séparément et récupère un modèle :

```bash
# une fois Ollama installé
ollama serve &
ollama pull llama3.2
```

## Utilisation

```bash
python3 -m monia
```

```
MonIA - assistant personnel (tape 'aide' pour les commandes)
> projet Jardin
> devis gravier 20 5
> note Idee amenagement
Prevoir une terrasse en bois
Ajouter un massif de fleurs

> chat comment reussir une terrasse en bois ?
> voix on
> recherche terrasse
> dessin
line 4 14 23 14
predict
quit
> quitter
```

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

Le client Ollama est testé contre un vrai serveur HTTP de test (pas un
mock qui triche) qui imite l'API `/api/chat` et `/api/tags`. La CLI est
testée de bout en bout : chat, notes, devis, recherche, projets.
