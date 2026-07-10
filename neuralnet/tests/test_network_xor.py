import random

from neuralnet.activations import SIGMOID
from neuralnet.layer import Dense
from neuralnet.linalg import Matrix
from neuralnet.losses import MSE
from neuralnet.network import Network


def _train_xor_network(seed_epochs: int = 5000) -> Network:
    random.seed(0)  # deterministic weight init: this test asserts on
    # convergence behaviour, not on backprop being merely present, so it
    # shouldn't be at the mercy of how lucky the random init was.
    network = Network(
        layers=[
            Dense(2, 4, SIGMOID),
            Dense(4, 1, SIGMOID),
        ],
        loss=MSE,
    )
    x = Matrix([[0, 0], [0, 1], [1, 0], [1, 1]])
    y = Matrix([[0], [1], [1], [0]])
    history = network.fit(x, y, epochs=seed_epochs, learning_rate=0.5)
    return network, history, x, y


def test_loss_decreases_during_training():
    _, history, _, _ = _train_xor_network()
    # loss at the end must be meaningfully lower than at the start
    assert history[-1] < history[0] * 0.1


def test_network_actually_solves_xor():
    """The real proof: XOR is not linearly separable, so a network that
    gets all 4 cases right after training must have learned a genuine
    non-linear decision boundary via the hidden layer, not just memorized
    a linear shortcut.
    """
    network, _, x, y = _train_xor_network()
    predictions = network.predict(x)
    for i in range(x.rows):
        predicted = round(predictions.data[i][0])
        expected = y.data[i][0]
        assert predicted == expected, f"input {x.data[i]} -> {predictions.data[i][0]}, expected {expected}"


def test_save_and_load_roundtrip(tmp_path):
    network, _, x, _ = _train_xor_network(seed_epochs=500)
    before = network.predict(x).data

    path = tmp_path / "xor_model.json"
    network.save(str(path))
    loaded = Network.load(str(path))
    after = loaded.predict(x).data

    assert before == after
