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
- `neuralnet/losses.py` — erreur quadratique moyenne (MSE), et cross-entropy
  (associee a une sortie softmax) pour la classification multi-classes.
- `neuralnet/layer.py` — une couche dense avec `forward()` et `backward()`
  (retropropagation manuelle), optimiseur SGD avec momentum.
- `neuralnet/network.py` — empile des couches, entraine (batch complet ou
  mini-batchs melanges), sauvegarde/charge un modele en JSON.
- `neuralnet/datasets.py` — telechargement et parsing a la main du format
  binaire IDX de MNIST (`struct` + `gzip`, aucune dependance).

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

```bash
python3 examples/mnist.py
```
Le vrai jalon : entraine sur un sous-ensemble du **vrai** dataset MNIST
(chiffres manuscrits scannes, telecharges automatiquement et mis en cache
dans `~/.neuralnet_data/mnist`). Resultat mesure reellement (pas invente) :

```
Precision sur le train (4000 images) : 99.4%
Precision sur le test  (800 images, jamais vues) : 90.9%
```

Avec un reseau minuscule (32 neurones caches) et seulement 4000 exemples
d'entrainement, en Python pur, sans une seule ligne de numpy. Le dataset
complet (60000/10000 images) n'est pas utilise par defaut : sans calcul
matriciel vectorise, l'entrainement prendrait des heures. Augmente
`TRAIN_LIMIT`/`TEST_LIMIT`/`EPOCHS` en tete de `examples/mnist.py` si tu as
le temps (et la batterie).

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

Options d'entrainement : `Dense(..., momentum=0.9)` pour l'optimiseur avec
momentum, et `network.fit(X, Y, epochs=..., learning_rate=..., batch_size=32)`
pour des mini-batchs melanges au lieu du batch complet (indispensable sur de
plus gros datasets comme MNIST).

## Limites connues (assumees, pas des bugs)

- Pas d'optimiseurs avances au-dela du momentum (pas d'Adam/RMSprop).
- Softmax n'est correct que combine avec `CROSS_ENTROPY` (le gradient
  combine est simplifie mathematiquement ; l'associer a une autre loss
  donnerait un resultat faux).
- Sans numpy, l'entrainement sur de gros volumes de donnees reste lent —
  ce projet est fait pour comprendre le fonctionnement, pas pour la
  performance brute.

## Tests

```bash
pip install pytest
pytest
```

Le test le plus important (`test_network_actually_solves_xor`) verifie que
le reseau resout reellement XOR apres entrainement — pas juste qu'il ne
plante pas.
