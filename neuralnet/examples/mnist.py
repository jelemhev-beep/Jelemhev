#!/usr/bin/env python3
"""Real MNIST, real accuracy: no numpy, no framework. Downloads the
official dataset once (cached under ~/.neuralnet_data/mnist), trains a
small MLP with mini-batches + momentum + softmax/cross-entropy, and
reports accuracy on held-out test images the network never saw.

Uses a subset of the full 60k/10k MNIST by default -- pure Python matrix
multiplication has no vectorised backend, so the full dataset would take
hours. Increase TRAIN_LIMIT/TEST_LIMIT/EPOCHS if you have time to spare.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neuralnet.activations import SIGMOID, SOFTMAX  # noqa: E402
from neuralnet.datasets import load_mnist  # noqa: E402
from neuralnet.layer import Dense  # noqa: E402
from neuralnet.linalg import Matrix  # noqa: E402
from neuralnet.losses import CROSS_ENTROPY  # noqa: E402
from neuralnet.network import Network  # noqa: E402

TRAIN_LIMIT = 4000
TEST_LIMIT = 800
HIDDEN_SIZE = 32
EPOCHS = 15
BATCH_SIZE = 32
LEARNING_RATE = 0.3
MOMENTUM = 0.9


def one_hot(label: int, size: int = 10) -> list[float]:
    vec = [0.0] * size
    vec[label] = 1.0
    return vec


def accuracy(network: Network, x: Matrix, labels: list[int]) -> float:
    predictions = network.predict(x)
    correct = 0
    for i, label in enumerate(labels):
        predicted = predictions.data[i].index(max(predictions.data[i]))
        correct += predicted == label
    return correct / len(labels)


def main() -> None:
    print(f"Chargement de MNIST (train={TRAIN_LIMIT}, test={TEST_LIMIT})...")
    t0 = time.time()
    train_images, train_labels, test_images, test_labels = load_mnist(
        train_limit=TRAIN_LIMIT, test_limit=TEST_LIMIT
    )
    print(f"  charge en {time.time() - t0:.1f}s")

    x_train = Matrix(train_images)
    y_train = Matrix([one_hot(label) for label in train_labels])
    x_test = Matrix(test_images)

    network = Network(
        layers=[
            Dense(784, HIDDEN_SIZE, SIGMOID, momentum=MOMENTUM),
            Dense(HIDDEN_SIZE, 10, SOFTMAX),
        ],
        loss=CROSS_ENTROPY,
    )

    print(f"\nEntrainement : {EPOCHS} epoques, batch={BATCH_SIZE}, hidden={HIDDEN_SIZE}")
    t0 = time.time()
    network.fit(
        x_train,
        y_train,
        epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        batch_size=BATCH_SIZE,
        verbose=True,
        log_every=1,
    )
    train_time = time.time() - t0
    print(f"Entrainement termine en {train_time:.1f}s")

    train_acc = accuracy(network, x_train, train_labels)
    test_acc = accuracy(network, x_test, test_labels)

    print(f"\nPrecision sur le train ({TRAIN_LIMIT} images) : {train_acc:.1%}")
    print(f"Precision sur le test  ({TEST_LIMIT} images, jamais vues) : {test_acc:.1%}")

    network.save("mnist_model.json")
    print("\nModele sauvegarde dans mnist_model.json")


if __name__ == "__main__":
    main()
