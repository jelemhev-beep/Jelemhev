#!/usr/bin/env python3
"""A tiny handmade digit classifier: 5x7 bitmap patterns for 0-9, no
external dataset needed. Proves the network can learn multi-class
classification (10 outputs, one-hot), not just a single XOR gate.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neuralnet.activations import SIGMOID  # noqa: E402
from neuralnet.layer import Dense  # noqa: E402
from neuralnet.linalg import Matrix  # noqa: E402
from neuralnet.losses import MSE  # noqa: E402
from neuralnet.network import Network  # noqa: E402

# Each digit is a 5 (wide) x 7 (tall) bitmap, flattened row-major into 35 bits.
DIGIT_BITMAPS = {
    0: ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    1: ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    2: ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    3: ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    4: ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    5: ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    6: ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    7: ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    8: ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    9: ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}


def flatten(bitmap: list[str]) -> list[float]:
    return [float(c) for row in bitmap for c in row]


def one_hot(digit: int, size: int = 10) -> list[float]:
    vec = [0.0] * size
    vec[digit] = 1.0
    return vec


def flip_random_pixels(vector: list[float], count: int) -> list[float]:
    noisy = list(vector)
    indices = random.sample(range(len(noisy)), count)
    for i in indices:
        noisy[i] = 1.0 - noisy[i]
    return noisy


def main() -> None:
    digits = sorted(DIGIT_BITMAPS)
    X = Matrix([flatten(DIGIT_BITMAPS[d]) for d in digits])
    Y = Matrix([one_hot(d) for d in digits])

    network = Network(
        layers=[
            Dense(35, 16, SIGMOID),
            Dense(16, 10, SIGMOID),
        ],
        loss=MSE,
    )

    network.fit(X, Y, epochs=3000, learning_rate=0.5, verbose=True, log_every=500)

    print("\n--- Sur les bitmaps propres (attendu: reconnaissance parfaite) ---")
    predictions = network.predict(X)
    correct = 0
    for i, d in enumerate(digits):
        predicted = predictions.data[i].index(max(predictions.data[i]))
        correct += predicted == d
        print(f"  chiffre {d} -> predit {predicted} {'OK' if predicted == d else 'FAUX'}")
    print(f"Précision sur bitmaps propres: {correct}/{len(digits)}")

    print("\n--- Avec 3 pixels bruités par chiffre (généralisation, pas garanti) ---")
    random.seed(42)
    noisy_correct = 0
    for d in digits:
        noisy_vector = flip_random_pixels(flatten(DIGIT_BITMAPS[d]), count=3)
        prediction = network.predict(Matrix([noisy_vector]))
        predicted = prediction.data[0].index(max(prediction.data[0]))
        noisy_correct += predicted == d
        print(f"  chiffre {d} (bruité) -> predit {predicted} {'OK' if predicted == d else 'FAUX'}")
    print(f"Précision sur bitmaps bruités: {noisy_correct}/{len(digits)}")


if __name__ == "__main__":
    main()
