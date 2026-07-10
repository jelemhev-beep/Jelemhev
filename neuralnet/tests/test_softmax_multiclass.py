from neuralnet.activations import SIGMOID, SOFTMAX
from neuralnet.layer import Dense
from neuralnet.linalg import Matrix
from neuralnet.losses import CROSS_ENTROPY
from neuralnet.network import Network

# 3-class toy problem: label = index of the largest input feature.
SAMPLES = [
    ([3, 1, 1], 0),
    ([1, 3, 1], 1),
    ([1, 1, 3], 2),
    ([5, 2, 1], 0),
    ([2, 5, 2], 1),
    ([1, 2, 5], 2),
    ([4, 3, 1], 0),
    ([3, 4, 3], 1),
    ([2, 1, 4], 2),
]


def _one_hot(label: int, size: int = 3) -> list[float]:
    vec = [0.0] * size
    vec[label] = 1.0
    return vec


def test_softmax_cross_entropy_solves_multiclass_toy_problem():
    x = Matrix([s[0] for s in SAMPLES])
    y = Matrix([_one_hot(s[1]) for s in SAMPLES])

    network = Network(
        layers=[
            Dense(3, 8, SIGMOID),
            Dense(8, 3, SOFTMAX),
        ],
        loss=CROSS_ENTROPY,
    )

    history = network.fit(x, y, epochs=2000, learning_rate=0.3)
    assert history[-1] < history[0] * 0.2

    predictions = network.predict(x)
    for i, (_, label) in enumerate(SAMPLES):
        predicted = predictions.data[i].index(max(predictions.data[i]))
        assert predicted == label

        # softmax output must be a valid probability distribution
        row_sum = sum(predictions.data[i])
        assert abs(row_sum - 1.0) < 1e-9
