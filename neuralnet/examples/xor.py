#!/usr/bin/env python3
"""The classic proof that a multilayer network learns something a single
linear layer cannot: XOR is not linearly separable, so if this converges,
the hidden layer + backprop genuinely works.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neuralnet.activations import SIGMOID  # noqa: E402
from neuralnet.layer import Dense  # noqa: E402
from neuralnet.linalg import Matrix  # noqa: E402
from neuralnet.losses import MSE  # noqa: E402
from neuralnet.network import Network  # noqa: E402

X = Matrix([[0, 0], [0, 1], [1, 0], [1, 1]])
Y = Matrix([[0], [1], [1], [0]])


def main() -> None:
    network = Network(
        layers=[
            Dense(2, 4, SIGMOID),
            Dense(4, 1, SIGMOID),
        ],
        loss=MSE,
    )

    network.fit(X, Y, epochs=5000, learning_rate=0.5, verbose=True, log_every=1000)

    print("\nRésultats après entraînement :")
    predictions = network.predict(X)
    for i in range(X.rows):
        a, b = X.data[i]
        predicted = predictions.data[i][0]
        expected = Y.data[i][0]
        print(f"  {int(a)} XOR {int(b)} = {predicted:.4f}  (attendu {expected}, arrondi={round(predicted)})")


if __name__ == "__main__":
    main()
