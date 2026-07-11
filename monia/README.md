# MonIA

Un assistant personnel en ligne de commande : mémoire persistante (second
cerveau), chat avec une IA dans le cloud (Groq) — au clavier ou dicté au
micro —, calculateur de devis, reconnaissance de chiffres dessinés (via
`neuralnet`), et sortie vocale. Zéro dépendance externe — juste la
bibliothèque standard Python (`urllib`, `json`, `subprocess`).

## Les briques

- **`monia/secondcerveau.py`** — mémoire persistante : notes et
  conversations stockées en fichiers markdown lisibles, organisés par
  projet (`~/.monia/secondcerveau/<Projet>/`). Pas de base de données —
  juste des fichiers, faciles à relire, sauvegarder, ou pousser sur
  GitHome.
- **`monia/llm_cloud.py`** — client pour l'API cloud de
  [Groq](https://console.groq.com) : de vrais gros modèles (Llama 3.3
  70B) qui tournent sur leurs serveurs, pas sur le téléphone. Gratuit
  (clé API requise), et ne consomme ni RAM ni batterie du téléphone.
- **`monia/devis.py`** — calculateur de devis matériaux (gravier, sable,
  béton...) : surface + épaisseur → volume, poids, prix estimé.
- **`monia/voice.py`** — synthèse vocale (`termux-tts-speak`) et
  reconnaissance vocale (`termux-speech-to-text`) via Termux:API,
  toujours optionnelles.
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

### Chat : Groq (cloud, gratuit, rapide)

1. Crée un compte gratuit sur [console.groq.com](https://console.groq.com)
2. Génère une clé API
3. `export GROQ_API_KEY=ta_cle` (ajoute-la à `~/.bashrc` pour ne pas la
   retaper à chaque fois)

Aucune charge sur la RAM du téléphone : la question part sur internet, le
modèle tourne chez Groq, seule la réponse revient. Sans clé configurée,
tout le reste de MonIA fonctionne normalement — seules les commandes
`chat` et `parler` restent indisponibles.

`chat` reste en mode conversation tant que tu ne tapes pas `quit`, `0` ou
une ligne vide : pas besoin de retaper `chat` devant chaque message, tu
peux enchaîner les phrases directement.

### Parler à voix haute : `parler`

Installe l'app **Termux:API** (séparée de Termux) pour que
`termux-speech-to-text` existe. La commande `parler` fonctionne comme
`chat`, mais chaque message est dicté au micro au lieu d'être tapé, et
chaque réponse est lue à voix haute (`termux-tts-speak`) — pratique les
mains prises, en plein chantier ou au jardin. Dis `stop` pour revenir au
menu.

## Utilisation

```bash
python3 -m monia
```

Un menu numéroté s'affiche au démarrage — tape un chiffre, ou une commande
complète si tu préfères :

```
=== MonIA ===
  1) Discuter avec l'IA (Groq)
  2) Parler a l'IA au micro (dictee vocale)
  3) Changer de projet actif
  4) Prendre une note
  5) Voir mes notes
  6) Rechercher dans le second cerveau
  7) Calculer un devis
  8) Voir les materiaux disponibles
  9) Dessiner un chiffre (reconnaissance neuralnet)
  10) Activer/desactiver la voix
  0) Quitter

> 7
Materiau, surface en m2, epaisseur en cm (optionnel) : gravier 20 5
Materiau      : gravier
Surface       : 20 m2
...

> 1
Ton message : comment reussir une terrasse en bois ?
...
```

Les commandes complètes marchent toujours en parallèle du menu (`chat ...`,
`parler`, `devis ...`, `dessin`, `voix on|off`, `note ...`, etc.) — tape
`aide` pour tout revoir.

Chaque `devis`, `chat`/`parler` et `dessin` reconnu est automatiquement
sauvegardé dans le second cerveau du projet actif — rien ne se perd en
fermant le terminal.

`dessin` nécessite que le projet `neuralnet` soit cloné juste à côté de
`monia` (dossiers frères, comme dans ce dépôt) et qu'un modèle y ait été
entraîné (`neuralnet/examples/mnist.py` ou `mnist_improved.py`).

## Tests

```bash
pip install pytest
pytest
```

Le client Groq est testé contre un vrai serveur HTTP de test (pas un mock
qui triche) imitant son API. La CLI est testée de bout en bout : chat,
dictée vocale, notes, devis, recherche, projets, dessin, et le menu
numéroté.
