# MonIA

Un assistant personnel en ligne de commande : mémoire persistante (second
cerveau), calculateur de devis, reconnaissance de chiffres dessinés (via
`neuralnet`), et sortie vocale. Zéro dépendance externe — juste la
bibliothèque standard Python.

## Les briques

- **`monia/secondcerveau.py`** — mémoire persistante : notes stockées en
  fichiers markdown lisibles, organisés par projet
  (`~/.monia/secondcerveau/<Projet>/`). Pas de base de données — juste des
  fichiers, faciles à relire, sauvegarder, ou pousser sur GitHome.
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

Aucune dépendance à installer.

## Utilisation

```bash
python3 -m monia
```

Un menu numéroté s'affiche au démarrage — tape un chiffre, ou une commande
complète si tu préfères :

```
=== MonIA ===
  1) Changer de projet actif
  2) Prendre une note
  3) Voir mes notes
  4) Rechercher dans le second cerveau
  5) Calculer un devis
  6) Voir les materiaux disponibles
  7) Dessiner un chiffre (reconnaissance neuralnet)
  8) Activer/desactiver la voix
  0) Quitter

> 5
Materiau, surface en m2, epaisseur en cm (optionnel) : gravier 20 5
Materiau      : gravier
Surface       : 20 m2
...
```

Les commandes complètes marchent toujours en parallèle du menu (`devis ...`,
`dessin`, `voix on|off`, `note ...`, etc.) — tape `aide` pour tout revoir.

Chaque `devis` et `dessin` reconnu est automatiquement sauvegardé dans le
second cerveau du projet actif — rien ne se perd en fermant le terminal.

`dessin` nécessite que le projet `neuralnet` soit cloné juste à côté de
`monia` (dossiers frères, comme dans ce dépôt) et qu'un modèle y ait été
entraîné (`neuralnet/examples/mnist.py` ou `mnist_improved.py`).

## Tests

```bash
pip install pytest
pytest
```

La CLI est testée de bout en bout : notes, devis, recherche, projets,
dessin, et le menu numéroté.
