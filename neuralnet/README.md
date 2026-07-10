# neuralnet

Un reseau de neurones (perceptron multicouche) ecrit entierement a la main
en Python pur : **aucune dependance externe**, pas meme numpy. Juste la
bibliotheque standard (`math`, `random`, `json`).

Le but est pedagogique et demonstratif : comprendre et prouver que la
retropropagation du gradient marche vraiment, sans qu'une bibliotheque ne
fasse le travail a ta place.

## Ce qui est fait main

- `neuralnet/linalg.py` — une classe `Matrix` avec multiplication,
  transposition, addition, produit terme a terme, sur des listes Python
  imbriquees (boucles `for` manuelles, pas de numpy).
- `neuralnet/activations.py` — sigmoid, tanh, ReLU, lineaire, et leurs
  derivees.
- `neuralnet/losses.py` — erreur quadratique moyenne (MSE) et sa derivee.
- `neuralnet/layer.py` — une couche dense avec `forward()` et `backward()`
  (retropropagation manuelle, mise a jour des poids par descente de
  gradient).
- `neuralnet/network.py` — empile des couches, entraine, sauvegarde/charge
  un modele en JSON.

## Demos

```bash
python3 examples/xor.py
```
Le test classique : XOR n'est pas lineairement separable, donc si le reseau
apprend a le resoudre, c'est la preuve que la couche cachee + la
retropropagation fonctionnent vraiment (un simple neurone seul ne pourrait
pas).

```bash
python3 examples/digits.py
```
Un classificateur de chiffres 0-9 sur des bitmaps 5x7 faits main (aucun
dataset externe telecharge). Teste aussi la reconnaissance sur des versions
bruitees (pixels inverses au hasard) pour verifier que le reseau generalise
un minimum, pas seulement du par-coeur.

## Utiliser la bibliotheque

```python
from neuralnet.activations import SIGMOID
from neuralnet.layer import Dense
from neuralnet.linalg import Matrix
from neuralnet.losses import MSE
from neuralnet.network import Network

network = Network(
    layers=[Dense(2, 4, SIGMOID), Dense(4, 1, SIGMOID)],
    loss=MSE,
)
network.fit(X, Y, epochs=5000, learning_rate=0.5)
predictions = network.predict(X)

network.save("mon_modele.json")
network2 = Network.load("mon_modele.json")
```

## Limites connues (assumees, pas des bugs)

- Descente de gradient "full batch" uniquement (tout le jeu de donnees a
  chaque etape), pas de mini-batchs ni d'optimiseurs avances (Adam, etc.).
- Pas de softmax/cross-entropy : la classification se fait avec sigmoid +
  MSE (plus simple, suffisant pour les demos ci-dessus).
- Sans numpy, l'entrainement sur de gros volumes de donnees serait tres
  lent — ce projet est fait pour comprendre le fonctionnement, pas pour la
  performance.

## Tests

```bash
pip install pytest
pytest
```

Le test le plus important (`test_network_actually_solves_xor`) verifie que
le reseau resout reellement XOR apres entrainement — pas juste qu'il ne
plante pas.
